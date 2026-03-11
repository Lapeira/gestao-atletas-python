import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta
from logica import calcular_idade, determinar_escalao, validar_entrada
from werkzeug.security import generate_password_hash, check_password_hash
import time

def conectar_bd():
    conn = sqlite3.connect('atletas.db', timeout=20.0)
    conn.execute('PRAGMA journal_mode=WAL')  
    conn.execute('PRAGMA busy_timeout=10000')  
    return conn

def tabelas_existem():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND (name='atletas' OR name='pagamentos')
    """)
    
    tabelas = cursor.fetchall()
    conn.close()
    
    return len(tabelas) == 2

def tabela_usuarios_existe():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='usuarios'
    """)
    
    existe = cursor.fetchone() is not None
    conn.close()
    
    return existe

def criar_tabela():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS atletas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            data_nascimento TEXT NOT NULL,
            idade INTEGER,
            escalao TEXT,
            status_pagamento TEXT DEFAULT 'Pendente',
            data_inscricao TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def migrar_data_inscricao():
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        
        cursor.execute("PRAGMA table_info(atletas)")
        colunas = cursor.fetchall()
        if not any(coluna[1] == 'data_inscricao' for coluna in colunas):
           
            cursor.execute('ALTER TABLE atletas ADD COLUMN data_inscricao TEXT')
            
            
            data_atual = datetime.now().strftime("%Y-%m-%d")
            cursor.execute('UPDATE atletas SET data_inscricao = ? WHERE data_inscricao IS NULL', (data_atual,))
            
            conn.commit()
    finally:
        if conn:
            conn.close()

def criar_tabela_pagamentos():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            atleta_id INTEGER,
            data_pagamento TEXT NOT NULL,
            valor REAL NOT NULL,
            mes_referencia TEXT NOT NULL,
            registrado_por TEXT NOT NULL,
            FOREIGN KEY (atleta_id) REFERENCES atletas (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def criar_tabela_usuarios():
    conn = conectar_bd()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nome TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0
        )
    ''')
    
  
    try:
        hashed_password = generate_password_hash('admin123')  
        cursor.execute('INSERT INTO usuarios (username, password, nome, is_admin) VALUES (?, ?, ?, ?)',
                       ('admin', hashed_password, 'Administrador', 1))
        conn.commit()
    except sqlite3.IntegrityError:
        
        pass
    finally:
        conn.close()

def verificar_usuario(username, password):
       conn = None
       try:
           conn = conectar_bd()
           cursor = conn.cursor()
           cursor.execute('SELECT * FROM usuarios WHERE username = ?', (username,))
           user_data = cursor.fetchone()
           if user_data and check_password_hash(user_data[2], password):  
               return user_data
           return None
       finally:
           if conn:
               conn.close()

def adicionar_usuario(username, password, nome, is_admin=0):
    if not username or not password or not nome:
        raise ValueError("Todos os campos são obrigatórios")
    
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO usuarios (username, password, nome, is_admin) VALUES (?, ?, ?, ?)',
                      (username, generate_password_hash(password), nome, is_admin))
        conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("Nome de usuário já existe")
    finally:
        if conn:
            conn.close()

def remover_usuario(user_id):
    conn = conectar_bd()
    try:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM usuarios WHERE id = ?', (user_id,))
        conn.commit()
    finally:
        conn.close()

def listar_atletas_bd():
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM atletas ORDER BY nome')
        atletas = cursor.fetchall()
        
        
        for atleta in atletas:
            atualizar_status_pagamento(atleta[0])
            
        
        cursor.execute('SELECT * FROM atletas ORDER BY nome')
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def adicionar_atleta_bd(nome, data_nascimento):
    if not validar_entrada(nome, data_nascimento):
        raise ValueError("Dados inválidos")
    
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        idade = calcular_idade(data_nascimento)
        escalao = determinar_escalao(idade)
        status_inicial = "Não aplicável" if escalao == "Séniores" else "Pendente"
        data_inscricao = datetime.now().strftime("%Y-%m-%d")
        
        cursor.execute('''
            INSERT INTO atletas (nome, data_nascimento, idade, escalao, status_pagamento, data_inscricao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (nome, data_nascimento, idade, escalao, status_inicial, data_inscricao))
        
        conn.commit()
    finally:
        if conn:
            conn.close()

def remover_atleta_bd(id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM atletas WHERE id = ?', (id,))
        conn.commit()
    finally:
        if conn:
            conn.close()

def buscar_atleta_por_id(id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM atletas WHERE id = ?', (id,))
        return cursor.fetchone()
    finally:
        if conn:
            conn.close()

def verificar_pagamento_mes(atleta_id, mes_ref):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM pagamentos 
            WHERE atleta_id = ? AND mes_referencia = ?
        ''', (atleta_id, mes_ref))
        return cursor.fetchone()[0] > 0
    finally:
        if conn:
            conn.close()

def verificar_pagamento(atleta_id):
    """Verifica se o atleta está com os pagamentos em dia"""
    if not atleta_id:
        return "Pendente"
    
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        # Verifica se é Sénior
        cursor.execute('SELECT escalao, data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return "Pendente"
        escalao, data_inscricao = resultado
        if escalao == "Séniores":
            return "Não aplicável"
        
        data_inscricao = datetime.strptime(data_inscricao, "%Y-%m-%d")
        hoje = datetime.now()
        
        
        mes_atual = f"{hoje.month:02d}/{hoje.year}"
        
      
        cursor.execute('''
            SELECT COUNT(*) FROM pagamentos 
            WHERE atleta_id = ? AND mes_referencia = ?
        ''', (atleta_id, mes_atual))
        
        tem_pagamento_atual = cursor.fetchone()[0] > 0
        
        if not tem_pagamento_atual:
            return "Pendente"
            
     
        mes_verificacao = data_inscricao
        while mes_verificacao < hoje:
            mes_ref = f"{mes_verificacao.month:02d}/{mes_verificacao.year}"
            
            cursor.execute('''
                SELECT COUNT(*) FROM pagamentos 
                WHERE atleta_id = ? AND mes_referencia = ?
            ''', (atleta_id, mes_ref))
            
            if cursor.fetchone()[0] == 0:
                return "Pendente"
                
            mes_verificacao += relativedelta(months=1)
        
        return "Pago"
        
    finally:
        if conn:
            conn.close()

def atualizar_status_pagamento(atleta_id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        novo_status = verificar_pagamento(atleta_id)
        
        cursor.execute('''
            UPDATE atletas 
            SET status_pagamento = ?
            WHERE id = ?
        ''', (novo_status, atleta_id))
        
        conn.commit()
    finally:
        if conn:
            conn.close()

def registrar_pagamento(atleta_id, valor_total, data_pagamento, meses_selecionados, registrado_por):
    max_tentativas = 3
    tentativa = 0
    
    while tentativa < max_tentativas:
        conn = None
        try:
            conn = sqlite3.connect('atletas.db', timeout=20.0)
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('PRAGMA busy_timeout=10000')
            conn.isolation_level = None
            
            conn.execute('BEGIN IMMEDIATE')
            
            cursor = conn.cursor()
            meses_registrados = 0
            
            
            cursor.execute('SELECT data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
            resultado = cursor.fetchone()
            if not resultado:
                raise Exception("Atleta não encontrado")
                
            data_inscricao = datetime.strptime(resultado[0], "%Y-%m-%d")
            
            for mes_ref in meses_selecionados:
                
                mes_pagamento = datetime.strptime(mes_ref, "%m/%Y")
                
               
                if mes_pagamento.replace(day=1) >= data_inscricao.replace(day=1):
                   
                    cursor.execute('''
                        SELECT COUNT(*) FROM pagamentos 
                        WHERE atleta_id = ? AND mes_referencia = ?
                    ''', (atleta_id, mes_ref))
                    
                    if cursor.fetchone()[0] == 0:
                        cursor.execute('''
                            INSERT INTO pagamentos 
                            (atleta_id, data_pagamento, valor, mes_referencia, registrado_por)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (atleta_id, data_pagamento, 25, mes_ref, registrado_por))
                        meses_registrados += 1
            
            if meses_registrados > 0:
                novo_status = verificar_pagamento(atleta_id)
                cursor.execute('''
                    UPDATE atletas 
                    SET status_pagamento = ?
                    WHERE id = ?
                ''', (novo_status, atleta_id))
            
            conn.execute('COMMIT')
            return meses_registrados > 0
            
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e):
                tentativa += 1
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                if tentativa == max_tentativas:
                    raise Exception("Não foi possível completar a operação após várias tentativas")
                time.sleep(1)
            else:
                raise e
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            raise e
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass

def obter_historico_pagamentos(atleta_id=None):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        if atleta_id:
            cursor.execute('''
                SELECT p.id, p.atleta_id, p.data_pagamento, p.valor, 
                       p.mes_referencia, p.registrado_por, a.nome as nome_atleta
                FROM pagamentos p
                JOIN atletas a ON p.atleta_id = a.id
                WHERE p.atleta_id = ?
                ORDER BY p.data_pagamento DESC, p.mes_referencia DESC
            ''', (atleta_id,))
        else:
            cursor.execute('''
                SELECT p.id, p.atleta_id, p.data_pagamento, p.valor, 
                       p.mes_referencia, p.registrado_por, a.nome as nome_atleta
                FROM pagamentos p
                JOIN atletas a ON p.atleta_id = a.id
                ORDER BY p.data_pagamento DESC, p.mes_referencia DESC
            ''')
        return cursor.fetchall()
    finally:
        if conn:
            conn.close()

def mes_ja_pago(atleta_id, mes, ano):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        mes_ref = f"{mes:02d}/{ano}"
        
        cursor.execute('''
            SELECT COUNT(*) FROM pagamentos 
            WHERE atleta_id = ? AND mes_referencia = ?
        ''', (atleta_id, mes_ref))
        
        return cursor.fetchone()[0] > 0
    finally:
        if conn:
            conn.close()

def obter_meses_atraso(atleta_id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        
        cursor.execute('SELECT data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return []
            
        data_inscricao = datetime.strptime(resultado[0], "%Y-%m-%d")
        hoje = datetime.now()
        meses_atraso = []
        
    
        mes_atual = data_inscricao.replace(day=1)
        mes_limite = hoje.replace(day=1)
        
        while mes_atual < mes_limite:
            mes_ref = f"{mes_atual.month:02d}/{mes_atual.year}"
            if not mes_ja_pago(atleta_id, mes_atual.month, mes_atual.year):
                meses_atraso.append(mes_ref)
            mes_atual += relativedelta(months=1)
        
        return meses_atraso
    finally:
        if conn:
            conn.close()

def obter_meses_futuros(atleta_id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return []
            
        data_inscricao = datetime.strptime(resultado[0], "%Y-%m-%d")
        hoje = datetime.now()
        meses_futuros = []
        
        mes_inicial = max(data_inscricao, hoje).replace(day=1)
        mes_limite = hoje + relativedelta(months=6)
        
        mes_atual = mes_inicial
        while mes_atual <= mes_limite:
            mes_ref = f"{mes_atual.month:02d}/{mes_atual.year}"
            if not mes_ja_pago(atleta_id, mes_atual.month, mes_atual.year) and mes_atual >= hoje.replace(day=1):
                meses_futuros.append(mes_ref)  # Adiciona apenas meses que não estão pagos e são futuros
            mes_atual += relativedelta(months=1)
        
        return meses_futuros
    finally:
        if conn:
            conn.close()

            
def verificar_status_pagamentos(atleta_id):
    if not atleta_id:
        return []
        
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        cursor.execute('SELECT data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return []
            
        data_inscricao = datetime.strptime(resultado[0], "%Y-%m-%d")
        hoje = datetime.now()
        meses_status = []
        
        mes_inicial = data_inscricao.replace(day=1)
        mes_final = hoje + relativedelta(months=6)
        mes_atual = mes_inicial
        
        while mes_atual <= mes_final:
            mes_ref = mes_atual.strftime('%m/%Y')
            esta_pago = verificar_pagamento_mes(atleta_id, mes_ref)
            
            meses_status.append({
                'nome': mes_ref,
                'pago': esta_pago,
                'atrasado': not esta_pago and mes_atual < hoje.replace(day=1),
                'pendente': not esta_pago and mes_atual >= hoje.replace(day=1)
            })
            
            mes_atual += relativedelta(months=1)
        
        return meses_status
    finally:
        if conn:
            conn.close()

def obter_meses_disponiveis(atleta_id):
    conn = None
    try:
        conn = conectar_bd()
        cursor = conn.cursor()
        
        
        cursor.execute('SELECT data_inscricao FROM atletas WHERE id = ?', (atleta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return []
            
        data_inscricao = datetime.strptime(resultado[0], "%Y-%m-%d")
        hoje = datetime.now()
        meses_disponiveis = []
        
        
        mes_atual = data_inscricao.replace(day=1)
        limite_futuro = hoje + relativedelta(months=6)
        
        while mes_atual <= limite_futuro:
            mes_ref = mes_atual.strftime('%m/%Y')
            
            
            if not verificar_pagamento_mes(atleta_id, mes_ref):
                meses_disponiveis.append({
                    'mes': mes_atual.strftime('%m'),
                    'ano': mes_atual.strftime('%Y'),
                    'mes_ref': mes_ref
                })
            
            mes_atual += relativedelta(months=1)
        
        return meses_disponiveis
    finally:
        if conn:
            conn.close()
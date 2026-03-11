from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bd import (listar_atletas_bd, adicionar_atleta_bd, 
                   remover_atleta_bd, buscar_atleta_por_id, 
                   obter_historico_pagamentos, registrar_pagamento, 
                   tabelas_existem, criar_tabela, criar_tabela_pagamentos,
                   criar_tabela_usuarios, tabela_usuarios_existe, 
                   verificar_usuario, adicionar_usuario, conectar_bd,
                   verificar_status_pagamentos, obter_meses_atraso, 
                   obter_meses_futuros, mes_ja_pago, 
                   obter_meses_disponiveis, migrar_data_inscricao, 
                   remover_usuario)
from datetime import datetime
from logica import calcular_idade, determinar_escalao, verificar_pagamento, validar_entrada
from dateutil.relativedelta import relativedelta

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'


try:
    conn = conectar_bd()
    print("Conexão com o banco de dados bem-sucedida!")
    conn.close()
except Exception as e:
    print("Erro ao conectar ao banco de dados:", e)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, nome, is_admin):
        self.id = id
        self.username = username
        self.nome = nome
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        if len(user_data) >= 5:  
            return User(user_data[0], user_data[1], user_data[3], user_data[4])  
        else:
            print("Dados do usuário não estão completos:", user_data)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = verificar_usuario(username, password)
            if user:
                user_obj = User(user[0], user[1], user[3], user[4])  
                login_user(user_obj)
                return redirect(url_for('index'))
            else:
                flash('Credenciais inválidas!')
    except Exception as e:
        print("Erro no login:", e)  
        flash('Ocorreu um erro ao tentar fazer login. Tente novamente.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    atletas = listar_atletas_bd()
    return render_template('index.html', atletas=atletas)

@app.route('/adicionar_atleta', methods=['POST'])
@login_required
def adicionar_atleta():
    nome = request.form['nome']
    data_nascimento = request.form['data_nascimento']
    try:
        if not validar_entrada(nome, data_nascimento):
            raise ValueError("Dados inválidos. Verifique o nome e a data de nascimento.")
        adicionar_atleta_bd(nome, data_nascimento)
        flash('Atleta adicionado com sucesso!')
    except ValueError as e:
        flash(f'Erro ao adicionar atleta: {str(e)}')
    return redirect(url_for('index'))

@app.route('/remover_atleta/<int:id>')
@login_required
def remover_atleta(id):
    try:
        remover_atleta_bd(id)
        flash('Atleta removido com sucesso!')
    except Exception as e:
        flash(f'Erro ao remover atleta: {str(e)}')
    return redirect(url_for('index'))

@app.route('/historico_pagamentos')
@login_required
def historico_pagamentos():
    atleta_id = request.args.get('atleta_id', type=int)
    atletas = listar_atletas_bd()
    pagamentos = obter_historico_pagamentos(atleta_id)
    meses_status = verificar_status_pagamentos(atleta_id) if atleta_id else []
    return render_template('historico_pagamentos.html', 
                         pagamentos=pagamentos, 
                         atletas=atletas,
                         atleta_selecionado=atleta_id,
                         meses_status=meses_status)

@app.route('/atualizar_pagamento/<int:atleta_id>', methods=['POST'])
@login_required
def atualizar_pagamento(atleta_id):
    atleta = buscar_atleta_por_id(atleta_id)
    if atleta and atleta[4] != "Séniores":
        meses_selecionados = request.form.getlist('meses')
        if not meses_selecionados:
            flash('Selecione pelo menos um mês para pagamento')
            return redirect(url_for('index'))
        
        valor_total = len(meses_selecionados) * 25
        data_atual = datetime.now().strftime("%d/%m/%Y")
        
        try:
            sucesso = registrar_pagamento(atleta_id, valor_total, data_atual, meses_selecionados, current_user.nome)
            if sucesso:
                flash(f'Pagamento de {valor_total}€ registrado com sucesso!')
                return redirect(url_for('historico_pagamentos', atleta_id=atleta_id, updated=True))
            else:
                flash('Nenhum pagamento foi registrado. Os meses selecionados já estão pagos.')
        except Exception as e:
            flash(f'Erro ao registrar pagamento: {str(e)}')
    else:
        flash('Não é possível alterar o status de pagamento para atletas séniores.')
    return redirect(url_for('index'))

@app.route('/registar', methods=['GET', 'POST'])
def registar():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nome = request.form['nome']
        try:
            adicionar_usuario(username, password, nome)
            flash('Usuário registado com sucesso!', 'success')  
            return redirect(url_for('login'))
        except ValueError as e:
            flash(f'Erro ao registar: {str(e)}')
    return render_template('registar.html')

@app.route('/usuarios', methods=['GET'])
@login_required
def listar_usuarios():
    if not current_user.is_admin:  
        flash('Acesso negado. Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('index'))
    
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios')
    usuarios = cursor.fetchall()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/remover_usuario/<int:user_id>', methods=['POST'])
@login_required
def remover_usuario_route(user_id):
    if not current_user.is_admin:  
        flash('Acesso negado. Você não tem permissão para remover usuários.', 'danger')
        return redirect(url_for('index'))
    
    try:
        remover_usuario(user_id)
        flash('Usuário removido com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao remover usuário: {str(e)}', 'danger')
    return redirect(url_for('listar_usuarios'))  


@app.route('/alterar_senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    if request.method == 'POST':
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if nova_senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return redirect(url_for('alterar_senha'))
        
        
        try:
            conn = conectar_bd()
            cursor = conn.cursor()
            hashed_password = generate_password_hash(nova_senha)
            cursor.execute('UPDATE usuarios SET password = ? WHERE id = ?', (hashed_password, current_user.id))
            conn.commit()
            flash('Senha alterada com sucesso!', 'success')
        except Exception as e:
            flash(f'Erro ao alterar a senha: {str(e)}', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('index'))
    
    return render_template('alterar_senha.html')


@app.context_processor
def utility_processor():
    def get_user_name():
        if current_user.is_authenticated:
            return current_user.nome
        return ""
    
    def get_nome_mes(numero_mes):
        nomes_meses = {
            '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março',
            '04': 'Abril', '05': 'Maio', '06': 'Junho',
            '07': 'Julho', '08': 'Agosto', '09': 'Setembro',
            '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
        }
        return nomes_meses.get(numero_mes, numero_mes)
    
    return dict(
        get_user_name=get_user_name,
        get_nome_mes=get_nome_mes,
        hoje=datetime.now(),
        obter_meses_atraso=obter_meses_atraso,
        obter_meses_futuros=obter_meses_futuros,
        mes_ja_pago=mes_ja_pago,
        obter_meses_disponiveis=obter_meses_disponiveis
    )

if __name__ == '__main__':
    if not tabelas_existem():
        criar_tabela()
        criar_tabela_pagamentos()
    else:
        migrar_data_inscricao()
    if not tabela_usuarios_existe():
        criar_tabela_usuarios()
        try:
            adicionar_usuario('admin', generate_password_hash('admin123'), 'Administrador', is_admin=1)
        except ValueError:
            pass
    app.run(debug=True, host='0.0.0.0')
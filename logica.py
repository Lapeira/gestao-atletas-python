from datetime import datetime

def determinar_escalao(idade):
    """Determina o escalão do atleta com base na idade."""
    if idade <= 7:
        return "Petizes"
    elif idade <= 9:
        return "Traquinas"
    elif idade <= 11:
        return "Benjamins"
    elif idade <= 13:
        return "Infantis"
    elif idade <= 15:
        return "Iniciados"
    elif idade <= 17:
        return "Juvenis"
    elif idade <= 19:
        return "Juniores"
    else:
        return "Séniores" 

def calcular_idade(data_nascimento):
    """Calcula a idade com base na data de nascimento."""
    nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y")
    hoje = datetime.now()
    idade = hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    return idade

def verificar_pagamento(escalao):
    """Verifica o status de pagamento com base no escalão."""
    if escalao == "Séniores":  
        return "Não aplicável"
    else:
        return "Pendente"

def validar_entrada(nome, data_nascimento):
    """Valida a entrada dos dados do atleta."""
    if not nome or not all(c.isalpha() or c.isspace() for c in nome):  
        return False
    if not data_nascimento:
        return False
    try:
        
        nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y")
        if nascimento > datetime.now():
            return False
        return True
    except ValueError:
        return False


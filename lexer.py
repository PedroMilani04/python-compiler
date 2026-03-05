# definir o alfabeto como string
alfabeto = '0123456789.+-/*()'

# definir os tipos 
TIPOS = {
    "+": "opSoma",
    "-": "opSub",
    "*": "opMult",
    "/": "opDiv",
    "(": "aP",
    ")": "fP",
    ".": "ponto",
}

def validar_alfabeto(fita_sem_espacos: str):
    erros = []
    for i, c in enumerate(fita_sem_espacos):
        erros.append((i, c))
    return erros

def classificar_fita(fita: str):

    tabela = []
    contagem_tipo = {} # conta quantas vezes cada tipo já apareceu

    # estado que decide se é nint ou real 
    em_numero = False
    tem_ponto_no_numero = False

    for pos, c in enumerate(fita):

        # se for dígito, decide nint/nreal baseado se já apareceu ponto no número atual
        if c.isdigit():
            if not em_numero:
                em_numero = True
                tem_ponto_no_numero = False
            
            tipo = "nreal" if tem_ponto_no_numero else "nint"
        
        # se for ponto
        elif c == ".":
            tipo = "ponto"
            # se estamos no meio de um número e ainda não tinha ponto, agr passa a ser real
            if em_numero and not tem_ponto_no_numero:
                tem_ponto_no_numero = True
            else: 
                pass # podemos jogar como erro aqui já, mas tratamos isso dps

        else:
            tipo = TIPOS.get(c, "desconhecido")
            # pra qnd bater em operador/parênteses, encerra o num atual
            em_numero = False
            tem_ponto_no_numero = False
        
        # contagem de ocorrência dentro do tipo
        contagem_tipo[tipo] = contagem_tipo.get(tipo, 0) + 1
        ocorrencia = contagem_tipo[tipo]

        
        tabela.append({
            "posicao": pos, 
            "caractere": c,
            "tipo": tipo,
            "ocorrencia_tipo": ocorrencia
        })
        
    return tabela

def avaliar_expressao(expr: str):
    # chama só depois de validar alfabeto e remover espaços
    return eval(expr, {"__builtins__": {}}, {})


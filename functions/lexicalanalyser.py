import ply.lex as lex

# Lista de palavras reservadas
RESERVADO = {
    "int": "tipoInt",
    "bool": "tipoBool",
    "procedure": "funcao",
    "read": "indLer",
    "write": "indEscrever",
    "true": "true",
    "false": "false",
    "if": "IF",
    "then": "THEN",
    "else": "ELSE",
    "while": "WHILE",
    "do": "DO",
    "begin": "BEGIN",
    "end": "END"
}

# Lista de tokens
TOKENS = {
    "opSoma",
    "opSub",
    "opMult",
    "opDiv",
    "opMaior",
    "opMenor",
    "Equal",
    "abreP",
    "fechaP",
    "ponto",
    "real",
    "inteiro",
    "var"
}

tokens = list(TOKENS) + list(RESERVADO.values())

# Expressões regulares simples
t_opSoma  = r'\+'
t_opSub   = r'-'
t_opMult  = r'\*'
t_opDiv   = r'/'
t_opMaior = r'>'
t_opMenor = r'<'
t_Equal   = r'='
t_abreP   = r'\('
t_fechaP  = r'\)'
t_ponto   = r'\.'

# Ignorar comentários
t_ignore_ComentarioS = r'\\.*'
t_ignore_ComentarioL = r'\{[^}]*\}'

# Ignorar espaços e tabs
t_ignore = ' \t'

# Números reais
def t_real(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t

# Inteiros
def t_inteiro(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# Variáveis e palavras reservadas
def t_var(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = RESERVADO.get(t.value, 'var')
    return t

# Controle de linhas
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Tratamento de erro — coleta o erro em vez de só imprimir
erros_lexicos = []

def t_error(t):
    erros_lexicos.append({
        "posicao": t.lexpos,
        "caractere": t.value[0]
    })
    t.lexer.skip(1)


def analisar(codigo: str) -> dict:
    """
    Recebe o código-fonte como string.
    Retorna um dicionário com:
      - tokens:           lista de dicts {posicao, lexema, tipo, linha, ocorrencia_tipo}
      - erros:            lista de dicts {posicao, caractere}       ← caracteres inválidos
      - erros_semanticos: lista de dicts {posicao, lexema, linha}   ← vars não declaradas
    """
    global erros_lexicos
    erros_lexicos = []

    # ── Passagem 1: coleta todos os tokens ──────────────────────────────
    lexer = lex.lex()
    lexer.input(codigo)

    resultado = []
    contagem_tipo = {}

    for tok in lexer:
        tipo = tok.type
        contagem_tipo[tipo] = contagem_tipo.get(tipo, 0) + 1
        resultado.append({
            "posicao":         tok.lexpos,
            "lexema":          str(tok.value),
            "tipo":            tipo,
            "ocorrencia_tipo": contagem_tipo[tipo],
            "linha":           tok.lineno,
        })



    return {
        "tokens":           resultado,
        "erros":            list(erros_lexicos),
        "erros_semanticos": erros_semanticos,
    }
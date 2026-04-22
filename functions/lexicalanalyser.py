import ply.lex as lex

# Lista de palavras reservadas
RESERVADO = {
    "int":       "tipoInt",
    "bool":      "tipoBool",
    "program":   "programa",
    "procedure": "funcao",
    "read":      "indLer",
    "write":     "indEscrever",
    "true":      "true",
    "false":     "false",
    "if":        "IF",
    "then":      "THEN",
    "else":      "ELSE",
    "while":     "WHILE",
    "do":        "DO",
    "begin":     "BEGIN",
    "end":       "END",
    "or":        "OR",
    "and":       "AND",
    "not":       "NOT",
    "div":       "DIV",
    "var":       "tipoVar",   # palavra reservada "var" em parâmetros formais
}

# Lista de tokens
TOKENS = {
    # operadores aritméticos
    "opSoma", "opSub", "opMult", "opDiv", "DIV",
    # operadores relacionais
    "opMaior", "opMenor", "Equal", "diferente", "menorIgual", "maiorIgual",
    # operadores lógicos
    "OR", "AND", "NOT",
    # atribuição
    "atrib",
    # delimitadores
    "abre_p", "fecha_p", "abre_col", "fecha_col",
    "ponto_virgula", "virgula", "dois_pontos", "ponto",
    # literais
    "real", "inteiro",
    # identificador genérico
    "var",
}

tokens = list(TOKENS | set(RESERVADO.values()))

# -- Operadores relacionais compostos (devem vir antes dos simples) ----------
def t_diferente(t):
    r'<>'
    return t

def t_menorIgual(t):
    r'<='
    return t

def t_maiorIgual(t):
    r'>='
    return t

# -- Atribuição (:=) antes de dois_pontos (:) --------------------------------
def t_atrib(t):
    r':='
    return t

def t_dois_pontos(t):
    r':'
    return t

# -- Operadores simples -------------------------------------------------------
t_opSoma  = r'\+'
t_opSub   = r'-'
t_opMult  = r'\*'
t_opDiv   = r'/'
t_opMaior = r'>'
t_opMenor = r'<'
t_Equal   = r'='

# -- Delimitadores ------------------------------------------------------------
t_abre_p      = r'\('
t_fecha_p     = r'\)'
t_abre_col    = r'\['
t_fecha_col   = r'\]'
t_ponto_virgula = r';'
t_virgula     = r','
t_ponto       = r'\.'

# -- Ignorar comentários (devem estar ANTES de t_ignore) ---------------------
# Comentário de bloco: { ... }
t_ignore_ComentarioL = r'\{[^}]*\}'
# Comentário de linha: // ...
t_ignore_ComentarioS = r'//[^\n]*'

# Ignorar espaços e tabs
t_ignore = ' \t'

# -- Números reais (antes de inteiro) ----------------------------------------
def t_real(t):
    r'[0-9]+\.[0-9]+'
    t.value = float(t.value)
    return t

# -- Inteiros -----------------------------------------------------------------
def t_inteiro(t):
    r'[0-9]+'
    t.value = int(t.value)
    return t

# -- Identificadores e palavras reservadas ------------------------------------
def t_var(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = RESERVADO.get(t.value, 'var')
    return t

# -- Controle de linhas -------------------------------------------------------
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# -- Tratamento de erro léxico ------------------------------------------------
erros_lexicos = []

def t_error(t):
    erros_lexicos.append({
        "posicao":    t.lexpos,
        "caractere":  t.value[0],
    })
    t.lexer.skip(1)


# ============================================================================
# Interface pública
# ============================================================================
def analisar(codigo: str) -> dict:
    """
    Recebe o código-fonte como string.
    Retorna um dicionário com:
      - tokens:           lista de dicts {posicao, lexema, tipo, linha, ocorrencia_tipo}
      - erros:            lista de dicts {posicao, caractere}
      - erros_semanticos: lista de dicts {posicao, lexema, linha}
    """
    global erros_lexicos
    erros_lexicos = []

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

    # ── Passagem 2: descobrir variáveis declaradas ───────────────────────────
    # Reconhece: tipoInt/tipoBool <id> {, <id>}
    # Também marca como "não-variável" ids que seguem 'program' ou 'procedure'
    TIPOS_DECLARACAO = {"tipoInt", "tipoBool"}
    # Tokens cujo identificador seguinte NÃO é uma variável do programa
    CONTEXTO_NAO_VAR = {"programa", "funcao"}

    declaradas = set()
    ids_nao_var = set()  # posições de tokens 'var' que são nomes de prog/proc

    i = 0
    while i < len(resultado):
        tok = resultado[i]

        # Nome do programa ou procedimento — não é variável
        if tok["tipo"] in CONTEXTO_NAO_VAR:
            if i + 1 < len(resultado) and resultado[i + 1]["tipo"] == "var":
                ids_nao_var.add(resultado[i + 1]["posicao"])
            i += 1
            continue

        # Declaração de variável: tipo seguido de lista de ids
        if tok["tipo"] in TIPOS_DECLARACAO:
            i += 1
            # percorre a lista: id {, id}
            while i < len(resultado):
                if resultado[i]["tipo"] == "var":
                    declaradas.add(resultado[i]["lexema"])
                    i += 1
                    # próximo pode ser vírgula (continua lista) ou outra coisa (fim)
                    if i < len(resultado) and resultado[i]["tipo"] == "virgula":
                        i += 1  # consome a vírgula e continua
                    else:
                        break
                else:
                    break
            continue

        i += 1

    # ── Passagem 3: checar usos de 'var' não declaradas ─────────────────────
    erros_semanticos = []
    for i, tok in enumerate(resultado):
        if tok["tipo"] == "var":
            # é nome de programa ou procedimento — ignora
            if tok["posicao"] in ids_nao_var:
                continue
            # é a própria declaração (vem logo após tipoInt/tipoBool) — ignora
            if i > 0 and resultado[i - 1]["tipo"] in TIPOS_DECLARACAO:
                continue
            # foi declarada — ignora
            if tok["lexema"] in declaradas:
                continue
            erros_semanticos.append({
                "posicao": tok["posicao"],
                "lexema":  tok["lexema"],
                "linha":   tok["linha"],
            })

    return {
        "tokens":           resultado,
        "erros":            list(erros_lexicos),
        "erros_semanticos": erros_semanticos,
    }
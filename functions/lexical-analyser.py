from dataclasses import dataclass
import ply.lex as lex

#Lista de palavras reservadas
RESERVADO={
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
#Lista de tokens
TOKENS = {
    "opSoma",
    "opSub",
    "opMult",
    "opDiv",
    "opMaior",
    "opMenor",
    "abreP",
    "fechaP",
    "ponto",
    "real",
    "inteiro",
    "var",
    "ComentarioS",  #Comentário Simples
    "ComentarioL"   #Comentário Longo
} 
tokens = list(TOKENS)+ list(RESERVADO.values())

#Expressões regulares
def lexico():
    t_opSoma = r'\+'
    t_opSub = r'-'
    t_opMult = r'\*'
    t_opDiv =  r'/'
    t_opMaior = r'>'
    t_opMenor = r'<'
    t_abreP = r'\('
    t_fechaP = r'\)'
    t_ponto = r'.'
    t_ignore_ComentarioS = r'\\.*'
    t_ignore_ComentarioL = r'\{.*\}'
    digito= r'([0-9])'
    t_ignore  = ' \t'

    def t_real(t):
        r'[0-9][0-9]*\.[0-9][0-9]*'
        t.value = float(t.value)
        return t

    def t_inteiro(t):
        r'\digito+'
        t.value = int(t.value)
        return t

    def t_var(t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = RESERVADO.get(t.value, 'var')
        return t

    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    #Tratamento de erros
    def t_error(t):
        print("O caractere '%s' não pertence ao alfabeto definido" % t.value[0])
        t.lexer.skip(1)
    return lex.lex()
lexcial_Analyser =  lex.lex()

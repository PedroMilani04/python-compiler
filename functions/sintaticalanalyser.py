"""
sintaticalanalyser.py
Analisador sintático descendente recursivo para a linguagem LALG
(Pascal Simplificado) — baseado na gramática do PDF de especificação.

Recebe a lista de tokens produzida por lexicalanalyser.analisar()
e retorna {"erros_sintaticos": [...]}.

Cada erro tem o formato:
  {
    "linha":     int,
    "posicao":   int,
    "encontrado": str,   # tipo do token encontrado (ou "EOF")
    "esperado":  str,    # descrição do que era esperado
    "lexema":    str,    # lexema do token problemático
  }

Estratégia de recuperação de erros:
  Ao encontrar um token inesperado o parser registra o erro e avança
  o cursor até atingir um token de sincronização (conjunto FOLLOW do
  não-terminal corrente) antes de retornar ao chamador.
"""

from __future__ import annotations
from typing import Optional

# ---------------------------------------------------------------------------
# Conjuntos de sincronização usados na recuperação de erros
# ---------------------------------------------------------------------------
_SYNC_COMANDO   = {"ponto_virgula", "END", "ELSE", "EOF"}
_SYNC_EXPRESSAO = {"ponto_virgula", "THEN", "DO", "END", "ELSE",
                   "fecha_p", "fecha_col", "EOF"}
_SYNC_DECL_VAR  = {"ponto_virgula", "BEGIN", "procedure", "EOF"}


class _Token:
    """Wrapper leve sobre o dict produzido pelo lexer."""
    __slots__ = ("tipo", "lexema", "linha", "posicao")

    def __init__(self, d: dict):
        self.tipo    = d["tipo"]
        self.lexema  = str(d["lexema"])
        self.linha   = d["linha"]
        self.posicao = d["posicao"]

    def __repr__(self):
        return f"<{self.tipo} '{self.lexema}' L{self.linha}>"


_EOF = _Token({"tipo": "EOF", "lexema": "EOF", "linha": -1, "posicao": -1})


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
class Parser:
    def __init__(self, tokens: list[dict]):
        # Filtra tokens que não pertencem à gramática (erros léxicos já
        # reportados pelo analisador léxico não devem atrapalhar o sintático)
        self._tokens: list[_Token] = [_Token(t) for t in tokens]
        self._pos: int = 0
        self.erros: list[dict] = []

    # ------------------------------------------------------------------ utils
    def _peek(self) -> _Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return _EOF

    def _advance(self) -> _Token:
        t = self._peek()
        if t is not _EOF:
            self._pos += 1
        return t

    def _check(self, *tipos: str) -> bool:
        return self._peek().tipo in tipos

    def _consome(self, tipo: str, descricao: str = "") -> Optional[_Token]:
        """Consome o token esperado ou registra erro e retorna None."""
        t = self._peek()
        if t.tipo == tipo:
            self._advance()
            return t
        esperado = descricao or tipo
        self._erro(t, esperado)
        return None

    def _erro(self, tok: _Token, esperado: str):
        self.erros.append({
            "linha":      tok.linha,
            "posicao":    tok.posicao,
            "encontrado": tok.tipo,
            "lexema":     tok.lexema,
            "esperado":   esperado,
        })

    def _sincroniza(self, *conjuntos):
        """Avança até encontrar um token em algum dos conjuntos de sinc."""
        sync = set()
        for c in conjuntos:
            sync |= c
        sync.add("EOF")
        while self._peek().tipo not in sync:
            self._advance()

    # ================================================================ gramática
    # Regra 1: <programa> ::= program <identificador> ; <bloco> .
    def programa(self):
        self._consome("programa", "program")
        self._consome("var",      "<identificador>")
        self._consome("ponto_virgula", ";")
        self._bloco()
        self._consome("ponto", ".")

    # Regra 2: <bloco> ::= [<parte decl vars>] [<parte decl subrot>] <cmd composto>
    def _bloco(self):
        # parte de declarações de variáveis (começa com tipoInt ou tipoBool)
        if self._check("tipoInt", "tipoBool"):
            self._parte_decl_vars()

        # parte de declarações de subrotinas (começa com procedure)
        while self._check("funcao"):   # funcao == "procedure"
            self._decl_procedimento()

        # comando composto obrigatório
        self._cmd_composto()

    # ---------------------------------------------------------------- Declarações
    # Regra 3: <parte decl vars> ::= <decl vars> {; <decl vars>} ;
    # O ";" final da seção é consumido aqui; se não vier outro tipo após ";",
    # o ";" não é consumido (pertence ao bloco externo ou não existe).
    def _parte_decl_vars(self):
        self._decl_vars()
        # Enquanto houver ";" seguido de outro tipo, é outra declaração
        while self._check("ponto_virgula"):
            # LL(2): espia o token após o ";"
            prox_pos = self._pos + 1
            prox_tipo = (
                self._tokens[prox_pos].tipo
                if prox_pos < len(self._tokens)
                else "EOF"
            )
            if prox_tipo in ("tipoInt", "tipoBool"):
                self._advance()   # consome ";"
                self._decl_vars()
            else:
                # ";" pertence ao separador de comandos ou ao bloco — para
                self._advance()   # consome o ";" final da seção de declarações
                break

    # Regra 4: <decl vars> ::= <tipo> <lista de ids>
    def _decl_vars(self):
        if not self._check("tipoInt", "tipoBool"):
            self._erro(self._peek(), "int | bool")
            self._sincroniza(_SYNC_DECL_VAR)
            return
        self._advance()   # consome tipo
        self._lista_ids()

    # Regra 5: <lista de ids> ::= <id> {, <id>}
    def _lista_ids(self):
        self._consome("var", "<identificador>")
        while self._check("virgula"):
            self._advance()
            self._consome("var", "<identificador>")

    # Regra 7: <decl procedimento> ::= procedure <id> [<params formais>] ; <bloco>
    def _decl_procedimento(self):
        self._consome("funcao", "procedure")
        self._consome("var", "<identificador>")
        if self._check("abre_p"):
            self._params_formais()
        self._consome("ponto_virgula", ";")
        self._bloco()

    # Regra 8: <params formais> ::= ( <seção> {; <seção>} )
    def _params_formais(self):
        self._consome("abre_p", "(")
        self._secao_params()
        while self._check("ponto_virgula"):
            self._advance()
            self._secao_params()
        self._consome("fecha_p", ")")

    # Regra 9: <seção params formais> ::= [var] <lista ids> : <id>
    def _secao_params(self):
        if self._check("tipoVar"):   # token "var" como palavra reservada
            self._advance()
        self._lista_ids()
        self._consome("dois_pontos", ":")
        self._consome("var", "<identificador>")

    # ---------------------------------------------------------------- Comandos
    # Regra 10: <cmd composto> ::= begin <cmd> {; <cmd>} end
    def _cmd_composto(self):
        self._consome("BEGIN", "begin")
        self._comando()
        while self._check("ponto_virgula"):
            self._advance()
            # "end" pode vir direto após ";" (comando vazio permitido)
            if self._check("END"):
                break
            self._comando()
        self._consome("END", "end")

    # Regra 11: <comando> ::= <atrib> | <chamada proc> | <cmd composto>
    #                        | <cmd condicional> | <cmd repetitivo>
    def _comando(self):
        tok = self._peek()

        if tok.tipo == "var":
            # pode ser atribuição ou chamada de procedimento
            # olha o próximo token: se for ":=" é atribuição, caso contrário chamada
            self._advance()  # consome o identificador
            if self._check("atrib"):          # :=
                self._advance()               # consome :=
                self._expressao()
            elif self._check("abre_p"):       # chamada com argumentos
                self._advance()
                self._lista_expressoes()
                self._consome("fecha_p", ")")
            # else: chamada sem parâmetros — identificador já foi consumido, ok

        elif tok.tipo in ("indLer", "indEscrever"):
            # read/write são tratados como chamada de procedimento
            self._advance()
            if self._check("abre_p"):
                self._advance()
                self._lista_expressoes()
                self._consome("fecha_p", ")")

        elif tok.tipo == "BEGIN":
            self._cmd_composto()

        elif tok.tipo == "IF":
            self._cmd_condicional()

        elif tok.tipo == "WHILE":
            self._cmd_repetitivo()

        elif tok.tipo in _SYNC_COMANDO:
            # comando vazio / final de bloco — não consome, deixa o chamador lidar
            pass

        else:
            self._erro(tok, "comando válido (atribuição, if, while, begin, read, write)")
            self._sincroniza(_SYNC_COMANDO)

    # Regra 12: <atribuição> ::= <variável> := <expressão>
    # (inline em _comando acima)

    # Regra 14: <cmd condicional> ::= if <expr> then <cmd> [else <cmd>]
    def _cmd_condicional(self):
        self._consome("IF", "if")
        self._expressao()
        self._consome("THEN", "then")
        self._comando()
        if self._check("ELSE"):
            self._advance()
            self._comando()

    # Regra 15: <cmd repetitivo> ::= while <expr> do <cmd>
    def _cmd_repetitivo(self):
        self._consome("WHILE", "while")
        self._expressao()
        self._consome("DO", "do")
        self._comando()

    # ---------------------------------------------------------------- Expressões
    # Regra 16: <expressão> ::= <expr simples> [<relação> <expr simples>]
    def _expressao(self):
        self._expr_simples()
        if self._check("Equal", "diferente", "opMenor", "menorIgual",
                       "maiorIgual", "opMaior"):
            self._advance()   # consome operador relacional
            self._expr_simples()

    # Regra 18: <expr simples> ::= [+|-] <termo> {(+|-|or) <termo>}
    def _expr_simples(self):
        if self._check("opSoma", "opSub"):
            self._advance()
        self._termo()
        while self._check("opSoma", "opSub", "OR"):
            self._advance()
            self._termo()

    # Regra 19: <termo> ::= <fator> {(*|div|and) <fator>}
    def _termo(self):
        self._fator()
        while self._check("opMult", "DIV", "AND"):
            self._advance()
            self._fator()

    # Regra 20: <fator> ::= <variável> | <número> | ( <expressão> ) | not <fator>
    def _fator(self):
        tok = self._peek()

        if tok.tipo == "var":
            self._advance()
            # <variável> pode ter índice: id [ <expressão> ]
            if self._check("abre_col"):
                self._advance()
                self._expressao()
                self._consome("fecha_col", "]")

        elif tok.tipo in ("inteiro", "real"):
            self._advance()

        elif tok.tipo in ("true", "false"):
            self._advance()

        elif tok.tipo == "abre_p":
            self._advance()
            self._expressao()
            self._consome("fecha_p", ")")

        elif tok.tipo == "NOT":
            self._advance()
            self._fator()

        else:
            self._erro(tok, "fator (variável, número, '(' ou 'not')")
            self._sincroniza(_SYNC_EXPRESSAO)

    # Regra 22: <lista de expressões> ::= <expressão> {, <expressão>}
    def _lista_expressoes(self):
        self._expressao()
        while self._check("virgula"):
            self._advance()
            self._expressao()


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------
def analisar_sintatico(tokens: list[dict]) -> dict:
    """
    Recebe a lista de tokens de lexicalanalyser.analisar()["tokens"]
    e retorna {"erros_sintaticos": [...]}.
    """
    # Remove tokens cujo tipo não faz parte da gramática
    # (ex: comentários que porventura passem, ou tipos internos do PLY)
    parser = Parser(tokens)
    parser.programa()

    # Se sobrou token antes do EOF, reporta
    sobra = parser._peek()
    if sobra.tipo != "EOF":
        parser._erro(sobra, "fim do programa (EOF)")

    return {"erros_sintaticos": parser.erros}
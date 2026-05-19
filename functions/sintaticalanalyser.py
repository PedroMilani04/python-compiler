"""
sintaticalanalyser.py
Analisador sintático descendente recursivo para a linguagem LALG
(Pascal Simplificado) — baseado na gramática do PDF de especificação.

Recebe a lista de tokens produzida por lexicalanalyser.analisar()
e retorna {"erros_sintaticos": [...], "arvore": ParseNode | None}.

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
# Nó da árvore sintática
# ---------------------------------------------------------------------------
class ParseNode:
    """Nó de uma árvore sintática preditiva (top-down)."""

    def __init__(self, label: str, token_lexema: str = ""):
        self.label: str = label                  # nome da regra ou terminal
        self.lexema: str = token_lexema          # valor do token (apenas folhas terminais)
        self.children: list[ParseNode] = []

    def add(self, child: "ParseNode") -> "ParseNode":
        """Adiciona um filho e retorna o filho (encadeamento)."""
        if child is not None:
            self.children.append(child)
        return child

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def __repr__(self) -> str:
        return f"ParseNode({self.label!r}, lexema={self.lexema!r}, children={len(self.children)})"


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

    def _consome(self, tipo: str, descricao: str = "") -> Optional[ParseNode]:
        """Consome o token esperado; retorna um nó terminal ou None."""
        t = self._peek()
        if t.tipo == tipo:
            self._advance()
            return ParseNode(f"[{tipo}]", t.lexema)
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
    def programa(self) -> ParseNode:
        node = ParseNode("<programa>")
        node.add(self._consome("programa", "program"))
        node.add(self._consome("var",      "<identificador>"))
        node.add(self._consome("ponto_virgula", ";"))
        node.add(self._bloco())
        node.add(self._consome("ponto", "."))
        return node

    # Regra 2: <bloco> ::= [<parte decl vars>] [<parte decl subrot>] <cmd composto>
    def _bloco(self) -> ParseNode:
        node = ParseNode("<bloco>")
        if self._check("tipoInt", "tipoBool"):
            node.add(self._parte_decl_vars())

        while self._check("funcao"):   # funcao == "procedure"
            node.add(self._decl_procedimento())

        node.add(self._cmd_composto())
        return node

    # ---------------------------------------------------------------- Declarações
    # Regra 3: <parte decl vars> ::= <decl vars> {; <decl vars>} ;
    def _parte_decl_vars(self) -> ParseNode:
        node = ParseNode("<parte-decl-vars>")
        node.add(self._decl_vars())
        while self._check("ponto_virgula"):
            prox_pos = self._pos + 1
            prox_tipo = (
                self._tokens[prox_pos].tipo
                if prox_pos < len(self._tokens)
                else "EOF"
            )
            if prox_tipo in ("tipoInt", "tipoBool"):
                node.add(ParseNode("[;]", ";"))
                self._advance()   # consome ";"
                node.add(self._decl_vars())
            else:
                node.add(ParseNode("[;]", ";"))
                self._advance()   # consome o ";" final da seção de declarações
                break
        return node

    # Regra 4: <decl vars> ::= <tipo> <lista de ids>
    def _decl_vars(self) -> ParseNode:
        node = ParseNode("<decl-vars>")
        if not self._check("tipoInt", "tipoBool"):
            self._erro(self._peek(), "int | bool")
            self._sincroniza(_SYNC_DECL_VAR)
            return node
        t = self._advance()
        node.add(ParseNode(f"[{t.tipo}]", t.lexema))
        node.add(self._lista_ids())
        return node

    # Regra 5: <lista de ids> ::= <id> {, <id>}
    def _lista_ids(self) -> ParseNode:
        node = ParseNode("<lista-ids>")
        node.add(self._consome("var", "<identificador>"))
        while self._check("virgula"):
            node.add(ParseNode("[,]", ","))
            self._advance()
            node.add(self._consome("var", "<identificador>"))
        return node

    # Regra 7: <decl procedimento> ::= procedure <id> [<params formais>] ; <bloco>
    def _decl_procedimento(self) -> ParseNode:
        node = ParseNode("<decl-procedimento>")
        node.add(self._consome("funcao", "procedure"))
        node.add(self._consome("var", "<identificador>"))
        if self._check("abre_p"):
            node.add(self._params_formais())
        node.add(self._consome("ponto_virgula", ";"))
        node.add(self._bloco())
        return node

    # Regra 8: <params formais> ::= ( <seção> {; <seção>} )
    def _params_formais(self) -> ParseNode:
        node = ParseNode("<params-formais>")
        node.add(self._consome("abre_p", "("))
        node.add(self._secao_params())
        while self._check("ponto_virgula"):
            node.add(ParseNode("[;]", ";"))
            self._advance()
            node.add(self._secao_params())
        node.add(self._consome("fecha_p", ")"))
        return node

    # Regra 9: <seção params formais> ::= [var] <lista ids> : <id>
    def _secao_params(self) -> ParseNode:
        node = ParseNode("<secao-params>")
        if self._check("tipoVar"):
            node.add(ParseNode("[tipoVar]", "var"))
            self._advance()
        node.add(self._lista_ids())
        node.add(self._consome("dois_pontos", ":"))
        node.add(self._consome("var", "<identificador>"))
        return node

    # ---------------------------------------------------------------- Comandos
    # Regra 10: <cmd composto> ::= begin <cmd> {; <cmd>} end
    def _cmd_composto(self) -> ParseNode:
        node = ParseNode("<cmd-composto>")
        node.add(self._consome("BEGIN", "begin"))
        node.add(self._comando())
        while self._check("ponto_virgula"):
            node.add(ParseNode("[;]", ";"))
            self._advance()
            if self._check("END"):
                break
            node.add(self._comando())
        node.add(self._consome("END", "end"))
        return node

    # Regra 11: <comando> ::= <atrib> | <chamada proc> | <cmd composto>
    #                        | <cmd condicional> | <cmd repetitivo>
    def _comando(self) -> ParseNode:
        node = ParseNode("<comando>")
        tok = self._peek()

        if tok.tipo == "var":
            id_node = ParseNode(f"[var]", tok.lexema)
            self._advance()
            if self._check("atrib"):
                atrib_node = ParseNode("<atribuição>")
                atrib_node.add(id_node)
                atrib_node.add(ParseNode("[:=]", ":="))
                self._advance()
                atrib_node.add(self._expressao())
                node.add(atrib_node)
            elif self._check("abre_p"):
                call_node = ParseNode("<chamada-proc>")
                call_node.add(id_node)
                call_node.add(ParseNode("[(]", "("))
                self._advance()
                call_node.add(self._lista_expressoes())
                call_node.add(self._consome("fecha_p", ")"))
                node.add(call_node)
            else:
                # chamada sem parâmetros
                call_node = ParseNode("<chamada-proc>")
                call_node.add(id_node)
                node.add(call_node)

        elif tok.tipo in ("indLer", "indEscrever"):
            io_node = ParseNode(f"<{tok.lexema}>")
            io_node.add(ParseNode(f"[{tok.tipo}]", tok.lexema))
            self._advance()
            if self._check("abre_p"):
                io_node.add(ParseNode("[(]", "("))
                self._advance()
                io_node.add(self._lista_expressoes())
                io_node.add(self._consome("fecha_p", ")"))
            node.add(io_node)

        elif tok.tipo == "BEGIN":
            node.add(self._cmd_composto())

        elif tok.tipo == "IF":
            node.add(self._cmd_condicional())

        elif tok.tipo == "WHILE":
            node.add(self._cmd_repetitivo())

        elif tok.tipo in _SYNC_COMANDO:
            # comando vazio — não consome
            node.add(ParseNode("<vazio>"))

        else:
            self._erro(tok, "comando válido (atribuição, if, while, begin, read, write)")
            self._sincroniza(_SYNC_COMANDO)

        return node

    # Regra 14: <cmd condicional> ::= if <expr> then <cmd> [else <cmd>]
    def _cmd_condicional(self) -> ParseNode:
        node = ParseNode("<cmd-if>")
        node.add(self._consome("IF", "if"))
        node.add(self._expressao())
        node.add(self._consome("THEN", "then"))
        node.add(self._comando())
        if self._check("ELSE"):
            node.add(ParseNode("[else]", "else"))
            self._advance()
            node.add(self._comando())
        return node

    # Regra 15: <cmd repetitivo> ::= while <expr> do <cmd>
    def _cmd_repetitivo(self) -> ParseNode:
        node = ParseNode("<cmd-while>")
        node.add(self._consome("WHILE", "while"))
        node.add(self._expressao())
        node.add(self._consome("DO", "do"))
        node.add(self._comando())
        return node

    # ---------------------------------------------------------------- Expressões
    # Regra 16: <expressão> ::= <expr simples> [<relação> <expr simples>]
    def _expressao(self) -> ParseNode:
        node = ParseNode("<expressão>")
        node.add(self._expr_simples())
        if self._check("Equal", "diferente", "opMenor", "menorIgual",
                       "maiorIgual", "opMaior"):
            t = self._advance()
            node.add(ParseNode(f"[{t.tipo}]", t.lexema))
            node.add(self._expr_simples())
        return node

    # Regra 18: <expr simples> ::= [+|-] <termo> {(+|-|or) <termo>}
    def _expr_simples(self) -> ParseNode:
        node = ParseNode("<expr-simples>")
        if self._check("opSoma", "opSub"):
            t = self._advance()
            node.add(ParseNode(f"[{t.tipo}]", t.lexema))
        node.add(self._termo())
        while self._check("opSoma", "opSub", "OR"):
            t = self._advance()
            node.add(ParseNode(f"[{t.tipo}]", t.lexema))
            node.add(self._termo())
        return node

    # Regra 19: <termo> ::= <fator> {(*|div|and) <fator>}
    def _termo(self) -> ParseNode:
        node = ParseNode("<termo>")
        node.add(self._fator())
        while self._check("opMult", "DIV", "AND"):
            t = self._advance()
            node.add(ParseNode(f"[{t.tipo}]", t.lexema))
            node.add(self._fator())
        return node

    # Regra 20: <fator> ::= <variável> | <número> | ( <expressão> ) | not <fator>
    def _fator(self) -> ParseNode:
        node = ParseNode("<fator>")
        tok = self._peek()

        if tok.tipo == "var":
            self._advance()
            var_node = ParseNode("[var]", tok.lexema)
            if self._check("abre_col"):
                idx_node = ParseNode("<índice>")
                idx_node.add(var_node)
                idx_node.add(ParseNode("[(]", "["))
                self._advance()
                idx_node.add(self._expressao())
                idx_node.add(self._consome("fecha_col", "]"))
                node.add(idx_node)
            else:
                node.add(var_node)

        elif tok.tipo in ("inteiro", "real"):
            self._advance()
            node.add(ParseNode(f"[{tok.tipo}]", str(tok.lexema)))

        elif tok.tipo in ("true", "false"):
            self._advance()
            node.add(ParseNode(f"[{tok.tipo}]", tok.lexema))

        elif tok.tipo == "abre_p":
            node.add(ParseNode("[(]", "("))
            self._advance()
            node.add(self._expressao())
            node.add(self._consome("fecha_p", ")"))

        elif tok.tipo == "NOT":
            node.add(ParseNode("[NOT]", "not"))
            self._advance()
            node.add(self._fator())

        else:
            self._erro(tok, "fator (variável, número, '(' ou 'not')")
            self._sincroniza(_SYNC_EXPRESSAO)

        return node

    # Regra 22: <lista de expressões> ::= <expressão> {, <expressão>}
    def _lista_expressoes(self) -> ParseNode:
        node = ParseNode("<lista-expr>")
        node.add(self._expressao())
        while self._check("virgula"):
            node.add(ParseNode("[,]", ","))
            self._advance()
            node.add(self._expressao())
        return node


# ---------------------------------------------------------------------------
# Interface pública
# ---------------------------------------------------------------------------
def analisar_sintatico(tokens: list[dict]) -> dict:
    """
    Recebe a lista de tokens de lexicalanalyser.analisar()["tokens"]
    e retorna {
        "erros_sintaticos": [...],
        "arvore": ParseNode | None
    }.
    """
    parser = Parser(tokens)
    arvore = parser.programa()

    sobra = parser._peek()
    if sobra.tipo != "EOF":
        parser._erro(sobra, "fim do programa (EOF)")

    return {
        "erros_sintaticos": parser.erros,
        "arvore": arvore,
    }
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "functions"))

import streamlit as st
import pandas as pd
from lexicalanalyser import analisar
from sintaticalanalyser import analisar_sintatico

# ============ UI Streamlit ===============

st.set_page_config(page_title="Compilador LALG", layout="centered")
st.title("🔬 Compilador LALG")
st.caption("Digite ou cole o código-fonte abaixo para análise:")

codigo = st.text_area(
    "Código-fonte",
    value=(
        "program exemplo;\n"
        "int x, y;\n"
        "begin\n"
        "  x := 10;\n"
        "  y := x + 3;\n"
        "  if x > 5 then\n"
        "    write(y)\n"
        "end."
    ),
    height=200,
)

analisar_btn = st.button("🔎 Analisar", use_container_width=True)

if analisar_btn:
    if not codigo.strip():
        st.warning("Por favor, insira algum código para analisar.")
    else:
        # ── Análise Léxica ─────────────────────────────────────────────
        resultado_lex        = analisar(codigo)
        tokens               = resultado_lex["tokens"]
        erros_lex            = resultado_lex["erros"]
        erros_semanticos     = resultado_lex["erros_semanticos"]

        # ── Análise Sintática ──────────────────────────────────────────
        resultado_sin        = analisar_sintatico(tokens)
        erros_sintaticos     = resultado_sin["erros_sintaticos"]

        tem_erro = erros_lex or erros_semanticos or erros_sintaticos

        # ── Status geral ───────────────────────────────────────────────
        if not tem_erro:
            st.success("✅ Análise concluída sem erros.")

        # ── Erros léxicos ──────────────────────────────────────────────
        if erros_lex:
            msgs = ", ".join(
                [f'pos {e["posicao"]}: "{e["caractere"]}"' for e in erros_lex]
            )
            st.error(f"❌ Caractere(s) fora do alfabeto: {msgs}")

        # ── Erros semânticos ───────────────────────────────────────────
        if erros_semanticos:
            st.error("❌ Identificador(es) usado(s) sem declaração prévia:")
            df_sem = pd.DataFrame(erros_semanticos).rename(columns={
                "linha":   "Linha",
                "posicao": "Posição",
                "lexema":  "Identificador",
            })[["Linha", "Posição", "Identificador"]]
            st.dataframe(df_sem, use_container_width=True, hide_index=True)

        # ── Erros sintáticos ───────────────────────────────────────────
        if erros_sintaticos:
            st.error("❌ Erro(s) sintático(s) encontrado(s):")
            df_sin = pd.DataFrame(erros_sintaticos).rename(columns={
                "linha":      "Linha",
                "posicao":    "Posição",
                "lexema":     "Encontrado (lexema)",
                "encontrado": "Encontrado (tipo)",
                "esperado":   "Esperado",
            })[["Linha", "Posição", "Encontrado (lexema)", "Encontrado (tipo)", "Esperado"]]
            st.dataframe(df_sin, use_container_width=True, hide_index=True)

        # ── Tabela de tokens ───────────────────────────────────────────
        if tokens:
            st.subheader("Tabela Léxica")

            posicoes_erro = {e["posicao"] for e in erros_semanticos}
            df = pd.DataFrame(tokens)
            df = df[~df["posicao"].isin(posicoes_erro)]

            df = df.rename(columns={
                "posicao":         "Posição",
                "lexema":          "Lexema",
                "tipo":            "Tipo",
                "ocorrencia_tipo": "Ocorrência",
                "linha":           "Linha",
            })[["Linha", "Posição", "Lexema", "Tipo", "Ocorrência"]]

            st.dataframe(df, use_container_width=True, hide_index=True)

            with st.expander("📊 Resumo por tipo de token"):
                resumo = (
                    df.groupby("Tipo")
                    .agg(Total=("Lexema", "count"))
                    .reset_index()
                    .sort_values("Total", ascending=False)
                )
                st.dataframe(resumo, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum token reconhecido.")

# ── Rodapé informativo ─────────────────────────────────────────────────────────
with st.expander("📖 Tokens reconhecidos"):
    st.markdown("""
| Categoria | Tokens |
|-----------|--------|
| **Tipos** | `tipoInt`, `tipoBool` |
| **Palavras-chave** | `IF`, `THEN`, `ELSE`, `WHILE`, `DO`, `BEGIN`, `END` |
| **Lógicos** | `AND`, `OR`, `NOT`, `DIV` |
| **Funções** | `funcao` (procedure), `indLer` (read), `indEscrever` (write) |
| **Literais** | `true`, `false` |
| **Operadores aritméticos** | `opSoma`, `opSub`, `opMult`, `opDiv` |
| **Operadores relacionais** | `opMaior`, `opMenor`, `Equal`, `diferente`, `menorIgual`, `maiorIgual` |
| **Atribuição** | `atrib` (`:=`) |
| **Delimitadores** | `abre_p`, `fecha_p`, `abre_col`, `fecha_col`, `ponto_virgula`, `virgula`, `dois_pontos`, `ponto` |
| **Literais numéricos** | `inteiro`, `real` |
| **Identificadores** | `var` |
    """)
    st.markdown("""
**Comentários ignorados:**
- Linha: `// comentário aqui`
- Bloco: `{ comentário aqui }`
    """)
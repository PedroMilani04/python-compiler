import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "functions"))

import streamlit as st
import pandas as pd
from lexicalanalyser import analisar

# ============ UI Streamlit ===============

st.set_page_config(page_title="Compilador", layout="centered")
st.title("🔬 Compilador")
st.caption("Digite ou cole o código-fonte abaixo para análise:")

codigo = st.text_area(
    "Código-fonte",
    value="int x\nx = 10 + 3.5\nif x > 5 then begin write x end",
    height=160,
)

analisar_btn = st.button("🔎 Analisar", use_container_width=True)

if analisar_btn:
    if not codigo.strip():
        st.warning("Por favor, insira algum código para analisar.")
    else:
        resultado = analisar(codigo)
        tokens            = resultado["tokens"]
        erros             = resultado["erros"]
        erros_semanticos  = resultado["erros_semanticos"]

        tem_erro = erros or erros_semanticos

        # ── Status geral ───────────────────────────────────────────────
        if not tem_erro:
            st.success("✅ Análise concluída sem erros.")

        # ── Erros léxicos (caracteres inválidos) ───────────────────────
        if erros:
            msgs = ", ".join([f'pos {e["posicao"]}: "{e["caractere"]}"' for e in erros])
            st.error(f"❌ Caractere(s) fora do alfabeto: {msgs}")

        # ── Erros semânticos (variáveis não declaradas) ────────────────
        if erros_semanticos:
            st.error("❌ Identificador(es) usado(s) sem declaração prévia:")
            df_sem = pd.DataFrame(erros_semanticos).rename(columns={
                "linha":   "Linha",
                "posicao": "Posição",
                "lexema":  "Identificador",
            })[["Linha", "Posição", "Identificador"]]
            st.dataframe(df_sem, use_container_width=True, hide_index=True)

        # ── Tabela de tokens ───────────────────────────────────────────
        if tokens:
            st.subheader("Tabela Léxica")

            # Remove da tabela os tokens que já aparecem na lista de erros semânticos
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
| **Funções** | `funcao`, `indLer`, `indEscrever` |
| **Literais** | `true`, `false` |
| **Operadores** | `opSoma`, `opSub`, `opMult`, `opDiv`, `opMaior`, `opMenor`, `Equal` |
| **Delimitadores** | `abreP`, `fechaP`, `ponto` |
| **Literais numéricos** | `inteiro`, `real` |
| **Identificadores** | `var` |
    """)
    st.markdown("""
**Comentários ignorados:**
- Linha: `\\ comentário aqui`
- Bloco: `{ comentário aqui }`
    """)
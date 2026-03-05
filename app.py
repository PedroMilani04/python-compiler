import streamlit as st
import pandas as pd

from lexer import alfabeto, validar_alfabeto, classificar_fita, avaliar_expressao

st.set_page_config(page_title="Calculadora", layout="centered")
st.title("Calculadora")
st.caption("Digite uma expressão:")

expr = st.text_input("Expressão", value="(12+3.5)*2")
fita = expr.replace(" ", "")

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("🔎 Analisar léxico", use_container_width=True)
with col2:
    calcular = st.button("✅ Calcular resultado", use_container_width=True)

if analisar or calcular:
    if not fita:
        st.error("Digite uma expressão primeiro.")
        st.stop()

    erros = validar_alfabeto(fita)
    if erros:
        msg = ", ".join([f'pos {i}: "{c}"' for i, c in erros])
        st.error(f"Caracter(es) fora do alfabeto: {msg}")
        st.stop()

    tabela = classificar_fita(fita)
    df = pd.DataFrame(tabela)

    if analisar:
        st.success("Análise léxica concluída.")
        st.subheader("Tabela de tokens")
        st.dataframe(df, use_container_width=True, hide_index=True)

    if calcular:
        try:
            resultado = avaliar_expressao(fita)
            st.success(f"Resultado: **{resultado}**")
            st.subheader("Tabela de tokens (para conferência)")
            st.dataframe(df, use_container_width=True, hide_index=True)
        except ZeroDivisionError:
            st.error("Erro: divisão por zero.")
        except Exception as e:
            st.error(f"Não foi possível calcular a expressão. Erro: {e}")

with st.expander("Ver regras do alfabeto"):
    st.write(f"Alfabeto permitido: `{alfabeto}`")
    st.write("Tipos: nint, nreal, opSoma, opSub, opMult, opDiv, aP, fP, ponto")
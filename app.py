import streamlit as st
import pandas as pd

# =========== ANALISADOR LÉXICO ===========

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
        if c not in alfabeto:
            erros.append((i, c))
    return erros

def classificar_fita(fita: str):

    tabela = []
    contagem_tipo = {} # conta quantas vezes cada tipo já apareceu

    # estado que decide se é nint ou real 
    em_numero = False
    tem_ponto_no_numero = False

    for pos, c in enumerate(fita):

        # >>> IGNORA caracteres fora do alfabeto
        if c not in alfabeto:
            continue

        # se for dígito, decide nint/nreal baseado se já apareceu ponto no número atual
        if c.isdigit():
            if not em_numero:
                em_numero = True
                tem_ponto_no_numero = False
            
            tipo = "nreal" if tem_ponto_no_numero else "nint"
        
        # se for ponto
        elif c == ".":
            tipo = "ponto"
            if em_numero and not tem_ponto_no_numero:
                tem_ponto_no_numero = True

        else:
            tipo = TIPOS.get(c)
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

# --- Avaliação segura (opcional) ---
# Aqui a gente permite somente números, operadores + - * / e parênteses e ponto.
# A validação do alfabeto já barra qualquer outra coisa.
def avaliar_expressao(expr: str):
    # usando eval apenas depois de validar o alfabeto e remover espaços
    # e com builtins bloqueado
    return eval(expr, {"__builtins__": {}}, {})



# ============ UI Streamlit ===============

st.set_page_config(page_title="Calculadora", layout="centered")
st.title("Calculadora")
st.caption("Digite uma expressão: ")

expr = st.text_input("Expressão", value="(12+3.5)*2")

col1, col2 = st.columns(2)
with col1:
    analisar = st.button("🔎 Analisar léxico", use_container_width=True)
with col2:
    calcular = st.button("✅ Calcular resultado", use_container_width=True)

# Sempre trabalhar com a fita sem espaços
fita = expr.replace(" ", "")

if analisar or calcular:


    
    # tabela de tokens
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


    erros = validar_alfabeto(fita)
    if erros:
        msg = ", ".join([f'pos {i}: "{c}"' for i, c in erros])
        st.error(f"Caracter(es) fora do alfabeto: {msg}")


with st.expander("Ver regras do alfabeto"):
    st.write(f"Alfabeto permitido: `{alfabeto}`")
    st.write("Tipos: nint, nreal, opSoma, opSub, opMult, opDiv, aP, fP, ponto")


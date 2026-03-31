    # ── Passagem 2: descobrir variáveis declaradas ───────────────────────
    # Uma variável é declarada quando o token anterior é tipoInt ou tipoBool
TIPOS_DECLARACAO = {"tipoInt", "tipoBool"}
declaradas = set()

for i, tok in enumerate(resultado):
    if tok["tipo"] in TIPOS_DECLARACAO:
        if i + 1 < len(resultado) and resultado[i + 1]["tipo"] == "var":
            declaradas.add(resultado[i + 1]["lexema"])

    # ── Passagem 3: checar usos de 'var' não declaradas ─────────────────
erros_semanticos = []
for i, tok in enumerate(resultado):
    if tok["tipo"] == "var":
        # é a própria declaração (vem logo após tipoInt/tipoBool) → ok
        if i > 0 and resultado[i - 1]["tipo"] in TIPOS_DECLARACAO:
            continue
        # foi declarada anteriormente → ok
        if tok["lexema"] in declaradas:
            continue
        # uso sem declaração
        erros_semanticos.append({
            "posicao": tok["posicao"],
            "lexema":  tok["lexema"],
            "linha":   tok["linha"],
        })
"""
tree_renderer.py
Converte uma ParseNode (sintaticalanalyser) em um grafo Graphviz DOT
para exibição no Streamlit com st.graphviz_chart.
"""

from __future__ import annotations
from sintaticalanalyser import ParseNode


def _escape(text: str) -> str:
    """Escapa caracteres especiais do DOT."""
    return (
        text.replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("<", "\\<")
            .replace(">", "\\>")
            .replace("{", "\\{")
            .replace("}", "\\}")
            .replace("|", "\\|")
    )


def _build_dot(node: ParseNode, lines: list[str], counter: list[int]) -> str:
    """Percorre a árvore em DFS e emite declarações de nó + arestas."""
    node_id = f"n{counter[0]}"
    counter[0] += 1

    is_terminal = node.is_leaf() or node.label.startswith("[")

    if is_terminal:
        # Folha / terminal: exibe label + lexema
        display = _escape(node.label)
        if node.lexema and node.lexema != node.label.strip("[]"):
            display += f"\\n'{_escape(node.lexema)}'"
        lines.append(
            f'  {node_id} [label="{display}" '
            f'shape=box style="filled,rounded" '
            f'fillcolor="#1e3a5f" fontcolor="#a8d8f0" '
            f'fontname="Consolas,monospace" fontsize=10];'
        )
    else:
        # Não-terminal: exibe apenas o nome da regra
        display = _escape(node.label)
        lines.append(
            f'  {node_id} [label="{display}" '
            f'shape=ellipse style=filled '
            f'fillcolor="#0d2137" fontcolor="#56c8e8" '
            f'fontname="Arial Bold" fontsize=11];'
        )

    for child in node.children:
        child_id = _build_dot(child, lines, counter)
        lines.append(f'  {node_id} -> {child_id} [color="#2a6a9a" penwidth=1.2];')

    return node_id


def parse_tree_to_dot(root: ParseNode) -> str:
    """
    Retorna a string DOT do grafo da árvore sintática.
    Pronta para passar a st.graphviz_chart().
    """
    lines: list[str] = []
    lines.append("digraph ParseTree {")
    lines.append('  graph [rankdir=TB bgcolor="#060e1a" splines=ortho nodesep=0.4 ranksep=0.6];')
    lines.append('  edge  [arrowsize=0.6];')
    counter = [0]
    _build_dot(root, lines, counter)
    lines.append("}")
    return "\n".join(lines)

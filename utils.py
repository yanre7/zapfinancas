"""Funções utilitárias de formatação."""
import unicodedata


def sem_acento(texto):
    """Remove acentos: 'pão' -> 'pao'."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def formatar_brl(valor):
    """1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"  # 1,234.50
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")

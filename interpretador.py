"""Interpreta mensagens de gasto ("mercado 25,90 #casa") e define a categoria."""
import re
from dataclasses import dataclass

from utils import sem_acento

# Palavras-chave (sem acento e em minúsculo) usadas para categorizar automaticamente.
# Sinta-se livre para ampliar as listas ou criar novas categorias.
CATEGORIAS = {
    "Alimentação": [
        "mercado", "supermercado", "padaria", "pao", "restaurante", "lanche", "ifood",
        "pizza", "almoco", "jantar", "cafe", "acougue", "feira", "hamburguer", "sorvete",
    ],
    "Transporte": [
        "uber", "onibus", "metro", "gasolina", "combustivel", "estacionamento",
        "passagem", "bilhete", "trem", "pedagio", "taxi",
    ],
    "Moradia": ["aluguel", "condominio", "luz", "agua", "internet", "gas", "iptu"],
    "Saúde": ["farmacia", "remedio", "consulta", "medico", "dentista", "exame"],
    "Lazer": ["cinema", "netflix", "spotify", "bar", "show", "jogo", "streaming", "festa", "viagem"],
    "Educação": ["curso", "livro", "faculdade", "mensalidade", "xerox", "udemy"],
}

CATEGORIA_PADRAO = "Outros"

PALAVRA_PARA_CATEGORIA = {
    palavra: categoria for categoria, palavras in CATEGORIAS.items() for palavra in palavras
}
CATEGORIAS_CONHECIDAS = {sem_acento(nome).lower(): nome for nome in CATEGORIAS}
CATEGORIAS_CONHECIDAS[sem_acento(CATEGORIA_PADRAO).lower()] = CATEGORIA_PADRAO

# Número com ou sem "R$": aceita 25, 25,90, 25.90 e 1.234,56
REGEX_VALOR = re.compile(r"(?:R\$\s*)?(\d+(?:[.,]\d+)*)", re.IGNORECASE)
REGEX_TAG = re.compile(r"#(\w+)")


@dataclass
class Gasto:
    item: str
    valor: float
    categoria: str


def converter_valor(texto):
    """Converte '1.234,56', '25,90' ou '25.90' em float."""
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")
    elif "." in texto:
        # '1.234' (milhar) vs '25.90' (decimal)
        if len(texto.rsplit(".", 1)[1]) == 3:
            texto = texto.replace(".", "")
    return float(texto)


def categorizar(item):
    """Descobre a categoria pelas palavras do item."""
    for palavra in re.findall(r"[a-z0-9]+", sem_acento(item).lower()):
        if palavra in PALAVRA_PARA_CATEGORIA:
            return PALAVRA_PARA_CATEGORIA[palavra]
    return CATEGORIA_PADRAO


def categoria_da_tag(tag):
    """'#alimentacao' -> 'Alimentação'. Tags desconhecidas viram categorias novas."""
    chave = sem_acento(tag).lower()
    return CATEGORIAS_CONHECIDAS.get(chave, tag.capitalize())


def interpretar_gasto(mensagem):
    """Retorna um Gasto ou None. Aceita 'mercado 25,90' ou '25,90 mercado #casa'."""
    tag = REGEX_TAG.search(mensagem)
    categoria_manual = categoria_da_tag(tag.group(1)) if tag else None
    texto = REGEX_TAG.sub(" ", mensagem)

    achados = list(REGEX_VALOR.finditer(texto))
    if not achados:
        return None
    ultimo = achados[-1]  # usa o último número da mensagem
    try:
        valor = converter_valor(ultimo.group(1))
    except ValueError:
        return None

    item = (texto[: ultimo.start()] + " " + texto[ultimo.end():]).strip(" -:,\n")
    item = re.sub(r"\s+", " ", item)
    if not item or valor <= 0:
        return None

    item = item[0].upper() + item[1:]
    return Gasto(item, valor, categoria_manual or categorizar(item))

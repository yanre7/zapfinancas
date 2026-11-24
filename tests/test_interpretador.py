import pytest

from interpretador import interpretar_gasto
from utils import formatar_brl


@pytest.mark.parametrize(
    "mensagem, item, valor, categoria",
    [
        ("mercado 25,90", "Mercado", 25.90, "Alimentação"),
        ("uber 18.50", "Uber", 18.50, "Transporte"),
        ("1.234,56 aluguel", "Aluguel", 1234.56, "Moradia"),
        ("R$ 10 pão", "Pão", 10.0, "Alimentação"),
        ("farmácia 42", "Farmácia", 42.0, "Saúde"),
        ("presente da mãe 80", "Presente da mãe", 80.0, "Outros"),
    ],
)
def test_gastos_validos(mensagem, item, valor, categoria):
    gasto = interpretar_gasto(mensagem)
    assert gasto is not None
    assert gasto.item == item
    assert gasto.valor == pytest.approx(valor)
    assert gasto.categoria == categoria


def test_tag_manual_tem_prioridade():
    assert interpretar_gasto("uber 30 #lazer").categoria == "Lazer"


def test_tag_sem_acento_e_tag_nova():
    assert interpretar_gasto("curso 90 #educacao").categoria == "Educação"
    assert interpretar_gasto("presente 80 #familia").categoria == "Familia"


@pytest.mark.parametrize("mensagem", ["abc", "0 mercado", "25,90", ""])
def test_mensagens_invalidas(mensagem):
    assert interpretar_gasto(mensagem) is None


def test_formatar_brl():
    assert formatar_brl(1234.5) == "R$ 1.234,50"
    assert formatar_brl(0) == "R$ 0,00"

import pytest
from twilio.request_validator import RequestValidator

from app import create_app

NUMERO = "whatsapp:+5521991810372"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DB_PATH", str(tmp_path / "teste.db"))
    monkeypatch.delenv("NUMERO_PERMITIDO", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    return create_app().test_client()


def enviar(client, texto, numero=NUMERO, **kwargs):
    resposta = client.post("/webhook", data={"From": numero, "Body": texto}, **kwargs)
    return resposta.get_data(as_text=True)


def test_fluxo_completo(client):
    assert "Registrado: Mercado – R$ 25,90 [Alimentação]" in enviar(client, "mercado 25,90")
    enviar(client, "uber 18,50")
    assert "R$ 44,40" in enviar(client, "total")

    por_categoria = enviar(client, "categorias")
    assert "Alimentação" in por_categoria and "Transporte" in por_categoria

    assert "Uber" in enviar(client, "ultimos")
    assert "Apaguei: Uber" in enviar(client, "apagar")
    assert "R$ 25,90" in enviar(client, "total")


def test_mensagem_nao_entendida(client):
    assert "Não entendi" in enviar(client, "bla bla")


def test_dados_separados_por_numero(client):
    enviar(client, "mercado 10", numero="whatsapp:+5511111111111")
    assert "R$ 0,00" in enviar(client, "total", numero="whatsapp:+5522222222222")


def test_numero_nao_permitido_e_ignorado(client, monkeypatch):
    monkeypatch.setenv("NUMERO_PERMITIDO", NUMERO)
    assert "<Message>" not in enviar(client, "mercado 10", numero="whatsapp:+5500000000000")
    assert "<Message>" in enviar(client, "mercado 10")


def test_assinatura_do_twilio(client, monkeypatch):
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "segredo")
    dados = {"From": NUMERO, "Body": "mercado 10"}

    sem_assinatura = client.post("/webhook", data=dados)
    assert sem_assinatura.status_code == 403

    assinatura = RequestValidator("segredo").compute_signature("http://localhost/webhook", dados)
    valida = client.post("/webhook", data=dados, headers={"X-Twilio-Signature": assinatura})
    assert valida.status_code == 200
    assert "Registrado" in valida.get_data(as_text=True)

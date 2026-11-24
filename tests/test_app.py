import os
import pytest
from flask import Flask

os.environ.setdefault("VERIFY_TOKEN", "token_teste_ci")
os.environ.setdefault("WHATSAPP_TOKEN", "token_ficticio_ci")
os.environ.setdefault("PHONE_NUMBER_ID", "123456789")
os.environ.setdefault("APP_SECRET", "")
os.environ.setdefault("NUMERO_PERMITIDO", "")

import app as app_module


def _obter_flask_app() -> Flask:
    for obj in vars(app_module).values():
        if isinstance(obj, Flask):
            return obj
    if hasattr(app_module, "create_app"):
        return app_module.create_app()
    raise RuntimeError("Nenhuma instância Flask encontrada em app.py")


@pytest.fixture
def client():
    flask_app = _obter_flask_app()
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def test_healthcheck_raiz(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_webhook_verificacao_sucesso(client):
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "token_teste_ci",
            "hub.challenge": "987654321",
        },
    )
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "987654321"


def test_webhook_verificacao_token_invalido(client):
    resp = client.get(
        "/webhook",
        query_string={
            "hub.mode": "subscribe",
            "hub.verify_token": "token_errado",
            "hub.challenge": "987654321",
        },
    )
    assert resp.status_code == 403


def test_webhook_post_payload_vazio(client):
    resp = client.post(
        "/webhook",
        json={"object": "whatsapp_business_account", "entry": []},
    )
    assert resp.status_code == 200
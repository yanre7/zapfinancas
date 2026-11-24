"""Servidor Flask que recebe as mensagens do WhatsApp (via Meta Cloud API) e grava no SQLite."""
import hashlib
import hmac
import os

import requests
from dotenv import load_dotenv

load_dotenv()  # lê o arquivo .env, se existir

from flask import Flask, abort, jsonify, request  # noqa: E402
from werkzeug.middleware.proxy_fix import ProxyFix  # noqa: E402

import db  # noqa: E402
from interpretador import interpretar_gasto  # noqa: E402
from utils import formatar_brl  # noqa: E402

AJUDA = (
    " *Bot de gastos*\n"
    "Registre assim: `mercado 25,90` ou `uber 18.50`\n"
    "Para escolher a categoria: `cinema 40 #lazer`\n\n"
    "Comandos:\n"
    "• *total* – total gasto no mês\n"
    "• *categorias* – gastos do mês por categoria\n"
    "• *ultimos* – últimos 5 gastos\n"
    "• *apagar* – apaga o último gasto\n"
    "• *ajuda* – mostra esta mensagem"
)


def processar(numero, mensagem):
    """Recebe o texto do usuário e devolve o texto da resposta."""
    texto = mensagem.strip()
    comando = texto.lower()

    if comando in ("ajuda", "help", "oi", "ola", "olá", "menu"):
        return AJUDA

    if comando == "total":
        return f"📊 Total do mês: *{formatar_brl(db.total_do_mes(numero))}*"

    if comando in ("categorias", "categoria"):
        linhas = db.total_por_categoria(numero)
        total = sum(linha["total"] for linha in linhas)
        if not linhas or total <= 0:
            return "Nenhum gasto registrado neste mês."
        itens = [
            f"• {l['categoria']} – {formatar_brl(l['total'])} ({l['total'] / total:.0%})"
            for l in linhas
        ]
        return "*Gastos do mês por categoria:*\n" + "\n".join(itens)

    if comando in ("ultimos", "últimos"):
        linhas = db.ultimos_gastos(numero)
        if not linhas:
            return "Você ainda não registrou nenhum gasto."
        itens = [
            f"• {g['item']} – {formatar_brl(g['valor'])} [{g['categoria']}] "
            f"({g['criado_em'][:16]})"
            for g in linhas
        ]
        return "*Últimos gastos:*\n" + "\n".join(itens)

    if comando == "apagar":
        apagado = db.apagar_ultimo(numero)
        if apagado is None:
            return "Não há gastos para apagar."
        return f"Apaguei: {apagado[0]} – {formatar_brl(apagado[1])}"

    gasto = interpretar_gasto(texto)
    if gasto is None:
        return (
            "Não entendi  Mande no formato `mercado 25,90`. "
            "Digite *ajuda* para ver os comandos."
        )

    db.adicionar_gasto(numero, gasto.item, gasto.valor, gasto.categoria)
    total = db.total_do_mes(numero)
    return (
        f" Registrado: {gasto.item} – {formatar_brl(gasto.valor)} [{gasto.categoria}]\n"
        f"Total do mês: {formatar_brl(total)}"
    )


def assinatura_valida(payload_bruto, cabecalho_assinatura, app_secret):
    """Valida o cabeçalho X-Hub-Signature-256 enviado pela Meta."""
    if not cabecalho_assinatura.startswith("sha256="):
        return False
    esperado = hmac.new(
        app_secret.encode("utf-8"), payload_bruto, hashlib.sha256
    ).hexdigest()
    recebido = cabecalho_assinatura.split("=", 1)[1]
    return hmac.compare_digest(esperado, recebido)


def enviar_whatsapp(destinatario, texto):
    """Envia uma mensagem de texto via WhatsApp Cloud API."""
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_id = os.environ.get("PHONE_NUMBER_ID")
    versao = os.environ.get("GRAPH_API_VERSION", "v21.0")

    if not token or not phone_id:
        raise RuntimeError("WHATSAPP_TOKEN e PHONE_NUMBER_ID devem estar configurados no .env")

    url = f"https://graph.facebook.com/{versao}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destinatario,
        "type": "text",
        "text": {"body": texto},
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    resp.raise_for_status()


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    db.init_db()

    @app.route("/webhook", methods=["GET"])
    def verificar_webhook():
        """Handshake inicial exigido pela Meta ao configurar a URL do Webhook."""
        modo = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        desafio = request.args.get("hub.challenge")

        if modo == "subscribe" and token == os.environ.get("VERIFY_TOKEN"):
            return desafio, 200
        abort(403)

    @app.route("/webhook", methods=["POST"])
    def webhook():
        app_secret = os.environ.get("APP_SECRET")
        if app_secret:
            assinatura = request.headers.get("X-Hub-Signature-256", "")
            if not assinatura_valida(request.get_data(), assinatura, app_secret):
                abort(403)

        dados = request.get_json(silent=True) or {}
        permitido = os.environ.get("NUMERO_PERMITIDO")

        # Percorre a estrutura padrão de eventos da WhatsApp Cloud API
        for entry in dados.get("entry", []):
            for change in entry.get("changes", []):
                valor = change.get("value", {})
                # Ignora eventos de status (enviado, entregue, lido) que não têm "messages"
                for msg in valor.get("messages", []):
                    if msg.get("type") != "text":
                        continue

                    numero = msg.get("from", "")
                    if permitido and numero != permitido:
                        continue

                    texto = msg.get("text", {}).get("body", "")
                    resposta = processar(numero, texto)
                    enviar_whatsapp(numero, resposta)

        # A Meta exige retorno HTTP 200 rápido para não reenviar o evento
        return jsonify({"status": "ok"}), 200

    @app.route("/")
    def saude():
        return "Bot de gastos no ar"

    return app


if __name__ == "__main__":
    create_app().run(port=5000, debug=True)
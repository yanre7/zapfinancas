# ZapFinanças — Assistente Pessoal de Controle de Gastos via WhatsApp

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

> **Nota:** Este é um **projeto pessoal** desenvolvido para uso próprio e estudo prático de integração com webhooks, segurança de APIs REST e persistência leve de dados.

O **ZapFinanças** é um bot financeiro construído em Python e Flask que permite registrar, categorizar e consultar despesas diárias diretamente por mensagens de texto no WhatsApp, armazenando todo o histórico localmente em um banco SQLite.

---

## Arquitetura e Fluxo de Funcionamento

1. **Entrada:** O usuário envia uma mensagem de texto pelo WhatsApp (ex.: `mercado 45,90` ou `resumo`).
2. **Webhook:** A **WhatsApp Cloud API (Meta)** encaminha o evento `POST /webhook` via túnel HTTPS (`ngrok`) para o servidor Flask local.
3. **Validação:** A aplicação valida a assinatura `X-Hub-Signature-256` (quando `APP_SECRET` está definido) e verifica se o remetente corresponde ao `NUMERO_PERMITIDO`.
4. **Processamento e Persistência:** O módulo `utils.py` interpreta o comando/valor, grava o lançamento no banco `gastos.db` (SQLite) e monta a resposta formatada.
5. **Saída:** O servidor dispara a resposta de volta ao usuário através do endpoint `/messages` da Meta Graph API.

---

## Funcionalidades

- **Registro rápido em linguagem natural:** Envie `<descrição> <valor>` (aceitando vírgula ou ponto decimal, como `uber 18,50` ou `lanche 22.00`) para salvar uma despesa instantaneamente.
- **Consultas e comandos:** Suporte aos comandos `resumo` (total acumulado e detalhamento) e `ajuda` (lista de instruções).
- **Segurança no Webhook:**
  - Handshake de verificação `GET /webhook` via `VERIFY_TOKEN`.
  - Verificação criptográfica de integridade via HMAC SHA-256 (`APP_SECRET`).
  - Lista de permissão por número (`NUMERO_PERMITIDO`) para restringir o uso ao proprietário do bot.
- **Zero dependências de banco externo:** Persistência local automática com `sqlite3`.

---

## Estrutura do Repositório

```text
zapfinancas/
├── app.py                # Servidor Flask, rotas do webhook e comunicação com a Graph API
├── utils.py              # Parser de mensagens, regras de negócio e queries SQLite
├── requirements.txt      # Dependências principais da aplicação
├── requirements-dev.txt  # Dependências de desenvolvimento e testes
├── .env.example          # Modelo das variáveis de ambiente necessárias
├── .gitignore            # Regras de exclusão (oculta .env, gastos.db e .venv)
└── LICENSE               # Licença MIT
```

---

## Como Executar Localmente

### 1. Clonar o repositório e preparar o ambiente virtual
```bash
git clone [https://github.com/SEU-USUARIO/zapfinancas.git](https://github.com/SEU-USUARIO/zapfinancas.git)
cd zapfinancas

# Criando e ativando o ambiente virtual (Windows)
python -m venv .venv
.venv\Scripts\activate

# Instalando as dependências
pip install -r requirements.txt
```

### 2. Configurar as variáveis de ambiente
Copie o arquivo de exemplo e preencha com suas credenciais do painel [Meta for Developers](https://developers.facebook.com/):
```bash
copy .env.example .env
```

### 3. Iniciar o servidor Flask e o túnel HTTPS
Em um primeiro terminal, execute a aplicação:
```bash
python app.py
```

Em um segundo terminal, exponha a porta `5000` com o `ngrok` e cadastre a URL gerada (`https://seu-subdominio.ngrok-free.dev/webhook`) na seção de Webhooks do aplicativo na Meta:
```bash
ngrok http 5000
```

---

## Limitação Conhecida em Ambiente de Testes (Meta Cloud API — Erro `130497`)

Este projeto foi originalmente estruturado com Twilio e migrado para a **WhatsApp Cloud API oficial da Meta**. 

Em contas de desenvolvedor **sem verificação empresarial (CNPJ / Business Verification)** utilizando o número de teste norte-americano (`+1 555...`), a Meta permite o recebimento normal dos payloads no webhook (`POST /webhook` retorna `200 OK`), mas bloqueia o envio ativo de respostas para destinatários no Brasil (`+55`) com o código de erro **`130497`** (*"Business account is restricted from messaging users in this country"*).

Para operar com respostas ativas em produção no Brasil, é necessário concluir a **Verificação da Empresa** no Meta Business Suite e vincular um número de telefone brasileiro (`+55`) dedicado à conta do WhatsApp Business.
   
---

## Licença

Distribuído sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
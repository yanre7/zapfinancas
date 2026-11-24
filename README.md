# Bot de Gastos no WhatsApp

Bot de WhatsApp para controlar gastos pessoais: você manda uma mensagem como `mercado 25,90`, o bot registra o item, o valor e a categoria em um banco **SQLite** e responde com o total do mês.

## Funcionalidades

- Registro de gastos por mensagem de texto (`mercado 25,90`, `uber 18.50`, `1.234,56 aluguel`, `R$ 10 pão`)
- **Categorias automáticas** por palavra-chave (Alimentação, Transporte, Moradia, Saúde, Lazer, Educação) ou escolhidas na mão com `#tag`
- Consultas pelo próprio WhatsApp: total do mês, gastos por categoria, últimos gastos e desfazer o último registro
- Exportação para CSV (abre direto no Excel em português)
- Cada número de WhatsApp enxerga apenas os próprios dados
- Segurança: restrição por número e validação da assinatura do Twilio
- Testes automatizados (pytest) rodando no GitHub Actions

## Como usar

| Mensagem | O que faz |
|---|---|
| `mercado 25,90` | Registra o gasto (categoria automática) |
| `cinema 40 #lazer` | Registra escolhendo a categoria |
| `total` | Total gasto no mês |
| `categorias` | Gastos do mês por categoria, com percentual |
| `ultimos` | Últimos 5 gastos |
| `apagar` | Apaga o último gasto |
| `ajuda` | Lista os comandos |

## Tecnologias

Python · Flask · SQLite · Twilio WhatsApp API · pytest · GitHub Actions

## Instalação

```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd bot-gastos

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env             # Windows: copy .env.example .env
```

Edite o `.env` com seu número e o Auth Token do Twilio (veja `.env.example`).

## Conectando ao WhatsApp (Twilio Sandbox)

1. Crie uma conta no [Twilio](https://www.twilio.com/) e abra o **WhatsApp Sandbox** (Messaging → Try it out → Send a WhatsApp message). Envie a mensagem de ativação pelo seu WhatsApp.
2. Rode o servidor:
   ```bash
   python app.py
   ```
3. Em outro terminal, exponha a porta com o [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 5000
   ```
4. No sandbox do Twilio, em **When a message comes in**, coloque `https://SEU-ENDERECO.ngrok-free.app/webhook` com método **POST**.
5. Mande `mercado 25,90` para o número do sandbox.

> O ngrok gratuito troca o endereço a cada reinício. Se isso acontecer, atualize a URL no Twilio.

## Banco de dados

Os dados ficam no arquivo `gastos.db` (criado automaticamente). Para visualizar no VS Code, use a extensão **SQLite3 Editor** e abra o arquivo.

Tabela `gastos`:

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | INTEGER | Chave primária |
| `numero` | TEXT | Número do WhatsApp de quem registrou |
| `item` | TEXT | Descrição do gasto |
| `valor` | REAL | Valor em reais |
| `categoria` | TEXT | Categoria do gasto |
| `criado_em` | TEXT | Data e hora do registro |

## Exportar para planilha

```bash
python exportar.py                       # tudo → gastos_export.csv
python exportar.py --mes 2026-11         # só um mês
python exportar.py --saida relatorio.csv
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Segurança

- **Nunca** suba o `.env` ou o `gastos.db` para o GitHub (já estão no `.gitignore`).
- Defina `NUMERO_PERMITIDO` para o bot ignorar qualquer número que não seja o seu.
- Defina `TWILIO_AUTH_TOKEN` para aceitar apenas requisições assinadas pelo Twilio.

## Estrutura do projeto

```
bot-gastos/
├── app.py              # servidor Flask, webhook e comandos
├── db.py               # acesso ao SQLite
├── interpretador.py    # leitura das mensagens e categorias
├── utils.py            # formatação (R$, remoção de acentos)
├── exportar.py         # exportação para CSV
├── tests/              # testes automatizados
├── .github/workflows/  # CI com GitHub Actions
├── .env.example        # modelo de configuração
└── requirements.txt
```

## Licença

[MIT](LICENSE)

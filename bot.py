import os
import threading
import uuid
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import mercadopago
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# =========================
# CONFIGURAÇÕES
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

VALOR_PIX = 5.00


# =========================
# MERCADO PAGO
# =========================

if not MERCADOPAGO_ACCESS_TOKEN:
    raise RuntimeError(
        "MERCADOPAGO_ACCESS_TOKEN nao configurado."
    )

sdk = mercadopago.SDK(MERCADOPAGO_ACCESS_TOKEN)


# =========================
# TELEGRAM
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá!\n\n"
        "Bem-vindo ao Pix Pagamentos.\n\n"
        "💰 Para gerar um Pix de R$ 5,00, envie:\n"
        "/pix"
    )


async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:

        email = (
            f"telegram_{update.effective_user.id}"
            "@example.com"
        )

        payment_data = {
            "transaction_amount": VALOR_PIX,
            "description": "Pagamento Pix - Telegram",
            "payment_method_id": "pix",
            "payer": {
                "email": email
            }
        }

        request_options = mercadopago.config.RequestOptions()

        request_options.custom_headers = {
            "x-idempotency-key": str(uuid.uuid4())
        }

        response = sdk.payment().create(
            payment_data,
            request_options
        )

        payment = response.get(
            "response",
            {}
        )

        if not payment:
            await update.message.reply_text(
                "❌ Não foi possível criar o pagamento."
            )
            return

        status = payment.get("status")

        if status not in [
            "pending",
            "in_process"
        ]:
            print(
                "Resposta Mercado Pago:",
                payment
            )

            await update.message.reply_text(
                "❌ O Mercado Pago retornou um erro.\n"
                f"Status: {status}"
            )
            return

        payment_id = payment.get("id")

        pix_data = (
            payment
            .get("point_of_interaction", {})
            .get("transaction_data", {})
        )

        qr_code = pix_data.get("qr_code")

        mensagem = (
            "💰 *Pagamento Pix criado!*\n\n"
            "Valor: *R$ 5,00*\n"
            f"ID do pagamento: `{payment_id}`\n\n"
        )

        if qr_code:

            mensagem += (
                "📋 *Pix Copia e Cola:*\n\n"
                f"`{qr_code}`\n\n"
                "Copie o código acima e faça o pagamento "
                "pelo seu banco."
            )

        else:

            mensagem += (
                "⚠️ O Mercado Pago não retornou "
                "o código Pix.\n"
                "Verifique os logs do Render."
            )

        await update.message.reply_text(
            mensagem,
            parse_mode="Markdown"
        )

        print(
            "Pagamento criado:",
            payment
        )

    except Exception as e:

        print(
            "ERRO AO CRIAR PIX:",
            repr(e)
        )

        await update.message.reply_text(
            "❌ Ocorreu um erro ao criar o Pix.\n"
            "Verifique os logs do servidor."
        )


# =========================
# SERVIDOR DO RENDER
# =========================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        html = """
        <!DOCTYPE html>
        <html lang="pt-BR">

        <head>
            <meta charset="UTF-8">

            <meta
                name="viewport"
                content="width=device-width, initial-scale=1.0"
            >

            <title>Pix Pagamentos</title>
        </head>

        <body>

            <h1>Pix Pagamentos</h1>

            <p>
                Sistema de pagamentos Pix
                integrado ao Telegram.
            </p>

            <p>
                Geração de cobranças Pix
                de forma rápida e segura.
            </p>

        </body>

        </html>
        """

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            html.encode("utf-8")
        )


    def do_POST(self):

        if self.path == "/webhook":

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            body = self.rfile.read(
                content_length
            )

            try:

                data = json.loads(
                    body.decode("utf-8")
                )

                print(
                    "WEBHOOK MERCADO PAGO:",
                    data
                )

            except Exception:

                print(
                    "WEBHOOK RECEBIDO:",
                    body.decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

            self.send_response(200)

            self.end_headers()

            self.wfile.write(
                b"OK"
            )

        else:

            self.send_response(404)

            self.end_headers()


    def log_message(
        self,
        format,
        *args
    ):
        pass


def start_web_server():

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(
        f"Servidor web iniciado na porta {port}"
    )

    server.serve_forever()


# =========================
# INICIALIZAÇÃO
# =========================

def main():

    if not TELEGRAM_TOKEN:

        raise RuntimeError(
            "TELEGRAM_TOKEN nao configurado."
        )

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    app = (
        Application
        .builder()
        .token(TELEGRAM_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "pix",
            pix
        )
    )

    print(
        "Bot iniciado!"
    )

    app.run_polling()


if __name__ == "__main__":

    main()

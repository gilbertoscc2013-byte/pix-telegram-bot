import os
import json
import uuid
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import mercadopago

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)


# =========================================================
# CONFIGURAÇÕES
# =========================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

PORT = int(os.environ.get("PORT", 10000))


# =========================================================
# TELEGRAM
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá!\n\n"
        "Bem-vindo ao Pix Pagamentos.\n\n"
        "Use /pix para gerar uma cobrança Pix."
    )


async def pix(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not MP_ACCESS_TOKEN:
        await update.message.reply_text(
            "❌ Mercado Pago ainda não está configurado."
        )
        return

    # Valor de teste
    valor = 1.00

    try:

        sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

        pagamento = {
            "transaction_amount": valor,
            "description": "Pagamento Pix - Bot Telegram",
            "payment_method_id": "pix",
            "payer": {
                "email": "teste@exemplo.com"
            }
        }

        opções_de_solicitação = mercadopago.config.Opções de solicitação()
opções_de_solicitação.cabeçalhos_personalizados = {
    'x-idempotency-key': str(uuid.uuid4())
}
        resultado = sdk.payment().create(
            pagamento,
            request_options
        )

        resposta = resultado["response"]

        if "point_of_interaction" not in resposta:

            print("RESPOSTA MERCADO PAGO:")
            print(resposta)

            await update.message.reply_text(
                "❌ Não foi possível gerar o Pix."
            )
            return

        transacao = resposta["point_of_interaction"]

        dados_pix = transacao["transaction_data"]

        codigo_pix = dados_pix["qr_code"]

        await update.message.reply_text(
            "💰 PIX GERADO\n\n"
            f"Valor: R$ {valor:.2f}\n\n"
            "📋 Pix Copia e Cola:\n\n"
            f"{codigo_pix}\n\n"
            "Após o pagamento, o sistema receberá a confirmação."
        )

        print("PAGAMENTO CRIADO:")
        print(resposta)

    except Exception as e:

        print("ERRO AO GERAR PIX:")
        print(repr(e))

        await update.message.reply_text(
            "❌ Ocorreu um erro ao gerar o Pix."
        )


# =========================================================
# WEBHOOK MERCADO PAGO
# =========================================================

class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/":

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/plain; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                b"Pix Telegram Bot online!"
            )

            return

        self.send_response(404)
        self.end_headers()


    def do_POST(self):

        # Aceita /webhook e também /webhook com parâmetros
        if not self.path.startswith("/webhook"):

            self.send_response(404)
            self.end_headers()

            return

        try:

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

                data = json.loads(body)

            except Exception:

                data = body.decode(
                    "utf-8",
                    errors="ignore"
                )

            print("================================")
            print("WEBHOOK MERCADO PAGO RECEBIDO")
            print("================================")
            print("URL:", self.path)
            print("DADOS:", data)

            # Responder rapidamente ao Mercado Pago
            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.end_headers()

            self.wfile.write(
                b'{"status":"received"}'
            )

        except Exception as e:

            print(
                "ERRO NO WEBHOOK:",
                repr(e)
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.end_headers()

            self.wfile.write(
                b'{"status":"received"}'
            )


    def log_message(
        self,
        format,
        *args
    ):

        pass


# =========================================================
# SERVIDOR WEB
# =========================================================

def start_web_server():

    server = HTTPServer(
        ("0.0.0.0", PORT),
        HealthHandler
    )

    print(
        f"Servidor HTTP iniciado na porta {PORT}"
    )

    server.serve_forever()


# =========================================================
# MAIN
# =========================================================

def main():

    if not TELEGRAM_TOKEN:

        raise RuntimeError(
            "TELEGRAM_TOKEN não configurado."
        )

    print("Iniciando servidor HTTP...")

    threading.Thread(
        target=start_web_server,
        daemon=True
    ).start()

    print("Servidor HTTP iniciado.")

    print("Iniciando bot Telegram...")

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

    print("Bot iniciado!")

    app.run_polling()


if __name__ == "__main__":

    main()

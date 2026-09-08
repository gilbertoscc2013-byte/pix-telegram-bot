import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Olá!\n\n"
        "Bem-vindo ao Pix Pagamentos.\n"
        "O bot está funcionando!"
    )


def main():
    if not TOKEN:
        raise RuntimeError("TELEGRAM_TOKEN não configurado.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Bot iniciado!")
    app.run_polling()


if __name__ == "__main__":
    main()

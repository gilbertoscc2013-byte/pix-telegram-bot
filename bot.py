def do_POST(self):
    # Apenas aceita na rota /webhook
    if self.path != "/webhook":
        self.send_response(404)
        self.end_headers()
        return

    try:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        # Tenta ler como JSON, senão lê como texto
        try:
            data = json.loads(body)
        except:
            data = body.decode("utf-8", errors="ignore")

        print("WEBHOOK RECEBIDO:")
        print(data)

        # Responde 200 IMEDIATAMENTE para o Mercado Pago parar de reenviar
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')

    except Exception as e:
        print("ERRO NO WEBHOOK:", repr(e))
        self.send_response(200) # Sempre 200 para não gerar erro no MP
        self.end_headers()

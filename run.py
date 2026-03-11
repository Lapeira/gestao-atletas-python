import webview
import threading
from app import app  # Importa o seu aplicativo Flask

def run_flask():
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)  # Desativa o reloader

if __name__ == '__main__':
    # Inicia o servidor Flask em uma thread separada
    threading.Thread(target=run_flask).start()
    
    # Cria a janela do pywebview
    webview.create_window('Gestão de Atletas', 'http://127.0.0.1:5000', width=800, height=600)
    webview.start()
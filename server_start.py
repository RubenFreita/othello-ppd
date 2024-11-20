from server import OthelloServer
import argparse

def main():
    parser = argparse.ArgumentParser(description='Inicia o servidor Othello')
    parser.add_argument('--port', type=int, default=5000, help='Porta do servidor (padrão: 5000)')
    args = parser.parse_args()
    
    server = OthelloServer(port=args.port)
    try:
        print("Servidor iniciado. Pressione Ctrl+C para encerrar.")
        server.start()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")

if __name__ == "__main__":
    main()

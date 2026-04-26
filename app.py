from core.local_api import start_server
from gui.app import run_gui


if __name__ == "__main__":
    server = start_server(host="127.0.0.1", port=8765)
    try:
        run_gui("http://127.0.0.1:8765")
    finally:
        server.shutdown()

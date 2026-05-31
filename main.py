import subprocess
import sys
import time

def iniciar_sistema():
    print("iniciando API")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", "8000"]
    )
    time.sleep(2)

    print("Iniciando interfaz grafica")
    gui_process = subprocess.Popen([sys.executable, "app_gui.py"])

    try:
        gui_process.wait()
        
    except KeyboardInterrupt:
        print("Cerrando programa")
        
    finally:
        print("Apagando API")
        api_process.terminate()
        api_process.wait()

if __name__ == "__main__":
    iniciar_sistema()
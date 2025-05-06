import threading
import datetime
import requests
import json
from .storage import get_config, update_message

def write_log_to_file(log_data):
    # Esta función se encarga de escribir en el archivo .txt
    with open("log_file.txt", "w") as file:
        json.dump([log_data], file, indent=4)

def enqueue_forward(msg_id: int, payload: str):
    def _task():
        cfg = get_config()
        try:
            # Ya no se necesita cert/verify: Nginx hace el mTLS
            resp = requests.post(
                cfg.mirth_url,
                data=payload,
            )
            status = 'forwarded' if resp.status_code < 300 else 'error'
            code = resp.status_code
            text = resp.text
        except Exception as e:
            status = 'error'
            code = None
            text = str(e)

        # Actualizar el mensaje con la respuesta
        update_message(
            msg_id,
            status=status,
            forwarded_at=datetime.datetime.utcnow().isoformat(),
            response_code=code,
            response=text
        )
        
        # Crear el diccionario con la información que deseas escribir
        log_data = {
            "created_at": datetime.datetime.utcnow().isoformat(),
            "forwarded_at": datetime.datetime.utcnow().isoformat(),
            "id": msg_id,
            "message": payload,
            "response": text,
            "response_code": code,
            "status": status
        }

        # Llamar a la función para escribir el log en el archivo .txt
        write_log_to_file(log_data)

    # Ejecutar el proceso en un hilo para no bloquear el servidor
    thread = threading.Thread(target=_task, daemon=True)
    thread.start()

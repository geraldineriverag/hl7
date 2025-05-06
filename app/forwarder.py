import threading
import socket
from datetime import datetime
import requests

from .storage import get_config, get_destination, get_message, update_message
from .models import Protocol


def enqueue_forward(msg_id: int, payload: str, dest_id: int = None) -> None:
    """
    Envía de forma asíncrona el mensaje HL7 al destino configurado.

    - msg_id: ID del log en la BD.
    - payload: mensaje HL7 crudo.
    - dest_id: opcional, si se omite usa el active_dest_id de AppConfig.
    """
    def _task():
        # 0) Si el estado ya cambió (cancelado o reintentado), abortar
        current = get_message(msg_id)
        if not current or current.status != 'pending':
            return

        # 1) Determinar destino: explícito o por config global
        cfg = get_config()
        target = dest_id or cfg.active_dest_id
        dest = get_destination(int(target))

        if not dest:
            update_message(
                msg_id,
                status='error',
                forwarded_at=datetime.utcnow().isoformat(),
                error_type='DestinationError',
                error_detail=f"Destino {target} no encontrado"
            )
            return

        try:
            # 2a) HTTP/HTTPS
            if dest.protocol in (Protocol.HTTP, Protocol.HTTPS):
                url = f"{dest.protocol.value}://{dest.host}:{dest.port}{dest.path}"
                cert = (dest.cert_path, dest.cert_path) if dest.use_tls else None
                resp = requests.post(url, data=payload, cert=cert)
                resp.raise_for_status()
                status = 'ok'
                code = resp.status_code
                text = resp.text

            # 2b) MLLP
            elif dest.protocol == Protocol.MLLP:
                VT = b"\x0b";
                FS = b"\x1c";
                CR = b"\x0d"
                packet = VT + payload.encode('utf-8') + FS + CR
                addr = (dest.host, dest.port)
                with socket.create_connection(addr, timeout=10) as sock:
                    sock.sendall(packet)
                    data = b''
                    while True:
                        chunk = sock.recv(1024)
                        if not chunk:
                            break
                        data += chunk
                        if data.endswith(FS + CR):
                            break
                status = 'ok'
                code = 0
                text = data.decode('utf-8', errors='ignore')

            else:
                raise ValueError(f"Protocolo no soportado: {dest.protocol}")

            # 3) Actualizar log con éxito
            update_message(
                msg_id,
                status=status,
                forwarded_at=datetime.utcnow().isoformat(),
                response_code=code,
                response=text
            )

        except Exception as exc:
            # 4) Actualizar log con datos de error
            update_message(
                msg_id,
                status='error',
                forwarded_at=datetime.utcnow().isoformat(),
                error_type=type(exc).__name__,
                error_detail=str(exc)
            )

    thread = threading.Thread(target=_task, daemon=True)
    thread.start()


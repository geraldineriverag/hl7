from flask import Blueprint, request, jsonify, current_app
from .storage import (
    save_message,
    list_messages,
    get_message,
    get_config,
    save_config
)
from .forwarder import enqueue_forward
from .models import AppConfig

# Blueprint para recepción HL7
hl7_bp = Blueprint('hl7', __name__)
# Blueprint para configuración
config_bp = Blueprint('config', __name__)
# Blueprint para logs
logs_bp = Blueprint('logs', __name__)

@hl7_bp.route('/hl7', methods=['POST'])
def receive_hl7():
    payload = request.get_data(as_text=True)
    msg = save_message(payload)
    enqueue_forward(msg.id, payload)
    return jsonify({'id': msg.id, 'status': msg.status}), 202

@config_bp.route('/config', methods=['GET'])
def get_config_endpoint():
    # get_config devuelve una instancia de AppConfig
    cfg: AppConfig = get_config()
    return jsonify(cfg.to_dict()), 200

@config_bp.route('/config', methods=['POST'])
def post_config_endpoint():
    data = request.get_json()
    # Construye un AppConfig válido a partir del JSON recibido
    cfg = AppConfig(
        mirth_url   = data.get('mirth_url', cfg.mirth_url if (cfg:=current_app.config['HL7_FORWARDER']) else ''),
        use_mtls    = data.get('use_mtls', False),
        client_cert = data.get('client_cert', ''),
        client_key  = data.get('client_key', ''),
        ca_cert     = data.get('ca_cert', '')
    )
    # Persiste en disco
    save_config(cfg.to_dict())
    # Recarga la configuración en memoria
    current_app.config['HL7_FORWARDER'] = cfg
    return jsonify(cfg.to_dict()), 200

@logs_bp.route('/logs', methods=['GET'])
def list_logs_endpoint():
    msgs = list_messages()
    return jsonify([m.to_dict() for m in msgs]), 200

@logs_bp.route('/logs/<int:msg_id>', methods=['GET'])
def get_log_endpoint(msg_id):
    m = get_message(msg_id)
    if not m:
        return jsonify({'error': 'Log no encontrado'}), 404
    return jsonify(m.to_dict()), 200

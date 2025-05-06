from flask import Blueprint, request, jsonify
from .storage import (
    save_message,
    list_messages,
    get_message,
    get_config,
    save_config,
    list_destinations,
    save_destination,
    delete_destination
)
from .forwarder import enqueue_forward
from .models import AppConfig

# Blueprints
hl7_bp = Blueprint('hl7', __name__, url_prefix='/hl7')
config_bp = Blueprint('config', __name__, url_prefix='/api/config')
logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')
dest_bp = Blueprint('destinations', __name__, url_prefix='/api/destinations')

# HL7 Reception
@hl7_bp.route('', methods=['POST'])
def receive_hl7():
    payload = request.get_data(as_text=True)
    # Obtener configuración global
    cfg: AppConfig = get_config()
    # Destino explícito o predeterminado
    dest_id = request.args.get('dest_id') or cfg.active_dest_id
    if dest_id is None:
        return jsonify({'error': 'No hay destino configurado'}), 400

    # Guardar log y enviar asíncrono
    log = save_message(payload, int(dest_id))
    enqueue_forward(log.id, payload, int(dest_id))
    return jsonify(log.to_dict()), 202

# Configuration endpoints
@config_bp.route('', methods=['GET'])
def get_config_endpoint():
    cfg = get_config()
    return jsonify(cfg.to_dict()), 200

@config_bp.route('', methods=['POST'])
def post_config_endpoint():
    data = request.get_json() or {}
    # Espera keys: active_dest_id, use_mtls, client_cert, client_key, ca_cert
    save_config(data)
    return jsonify(data), 200

# Destinations CRUD
@dest_bp.route('', methods=['GET'])
def list_destinations_endpoint():
    dests = list_destinations()
    return jsonify([d.to_dict() for d in dests]), 200

@dest_bp.route('', methods=['POST'])
def save_destination_endpoint():
    data = request.get_json() or {}
    try:
        dest = save_destination(data)
        return jsonify(dest.to_dict()), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@dest_bp.route('/<int:dest_id>', methods=['DELETE'])
def delete_destination_endpoint(dest_id):
    try:
        delete_destination(dest_id)
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# Logs endpoints
@logs_bp.route('', methods=['GET'])
def list_logs_endpoint():
    logs = list_messages()
    return jsonify([l.to_dict() for l in logs]), 200

@logs_bp.route('/<int:msg_id>', methods=['GET'])
def get_log_endpoint(msg_id):
    log = get_message(msg_id)
    if not log:
        return jsonify({'error': 'Log no encontrado'}), 404
    return jsonify(log.to_dict()), 200

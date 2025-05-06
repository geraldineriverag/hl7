import os
import json
from flask import Flask, render_template
from .models import AppConfig

def create_app():
    # 1. Define rutas absolutas a carpetas clave
    base_dir      = os.path.abspath(os.path.dirname(__file__))        
    project_root  = os.path.abspath(os.path.join(base_dir, '..'))      
    templates_dir = os.path.join(project_root, 'templates')            
    config_file   = os.path.join(project_root, 'config', 'config.json')

    # 2. Crea la app indicando la carpeta de templates
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder=templates_dir
    )

    # 3. Carga config.json (solo la ruta al JSON, no mezclar con templates)
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            cfg_dict = json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error cargando config.json: {e}")
    app.config['HL7_FORWARDER'] = AppConfig(**cfg_dict)

    # 4. Registra tus APIs (blueprints)
    from .server import hl7_bp, config_bp, logs_bp
    app.register_blueprint(hl7_bp)
    app.register_blueprint(config_bp, url_prefix='/api')
    app.register_blueprint(logs_bp, url_prefix='/api')

    # 5. Ruta raíz que renderiza index.html desde templates/
    @app.route('/')
    def index():
        return render_template('index.html')

    return app

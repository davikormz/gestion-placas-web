from flask import Flask, render_template, jsonify, request
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.shared.db import DatabaseConnection
from src.desktop.utils.db_config import DBConfig

app = Flask(__name__)

# Conexión a la base de datos
db_config = DBConfig()
db = DatabaseConnection(db_config.get_connection_config())

@app.route('/')
def index():
    """Página principal que muestra las placas y sus costos."""
    return render_template('index.html')

@app.route('/api/placas')
def get_placas():
    """API para obtener todas las placas."""
    placas = db.execute_query("SELECT * FROM placas", fetch=True)
    return jsonify(placas)

@app.route('/api/placas_con_costos')
def get_placas_con_costos():
    """API para obtener placas con sus costos asociados directamente de la base de datos."""
    placas = db.execute_query("SELECT * FROM placas", fetch=True)
    costos = db.execute_query("SELECT * FROM costos", fetch=True)
    
    costos_dict = {}
    for costo in costos:
        key = f"{float(costo['ancho'])}-{float(costo['alto'])}"
        costo_por_placa = costo['costo_set'] / costo['placas_por_set'] if costo['placas_por_set'] > 0 else 0
        costos_dict[key] = {
            'costo': costo_por_placa,
            'moneda': costo['moneda']
        }
    
    result = []
    for placa in placas:
        placa_copy = dict(placa)
        key = f"{float(placa['ancho'])}-{float(placa['alto'])}"
        if key in costos_dict:
            placa_copy['costo'] = costos_dict[key]['costo']
            placa_copy['moneda'] = costos_dict[key]['moneda']
        else:
            placa_copy['costo'] = None
            placa_copy['moneda'] = None
        result.append(placa_copy)
    
    return jsonify(result)

@app.route('/api/costos')
def get_costos():
    """API para obtener todos los costos."""
    costos = db.execute_query("SELECT * FROM costos", fetch=True)
    return jsonify(costos)

@app.route('/api/envios')
def get_envios():
    """API para obtener todos los envíos."""
    envios = db.execute_query("SELECT * FROM envios", fetch=True)
    return jsonify(envios)

@app.route('/envios')
def envios_page():
    """Página que muestra los envíos."""
    return render_template('envios.html')

@app.route('/api/papeles')
def get_papeles():
    """API para obtener todos los papeles."""
    papeles = db.execute_query("SELECT * FROM papeles", fetch=True)
    return jsonify(papeles)

@app.route('/cotizacion')
def cotizacion_page():
    """Página que muestra el módulo de cotización."""
    return render_template('cotizacion.html')

if __name__ == '__main__':
    web_config = db_config.get_connection_config().get('web', {})
    host = web_config.get('host', '0.0.0.0')
    port = web_config.get('port', 5000)
    debug = web_config.get('debug', True)
    app.run(host=host, port=port, debug=debug)
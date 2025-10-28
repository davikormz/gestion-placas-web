import os
import pymysql
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/placas')
def get_placas():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM placas")
        placas = cursor.fetchall()
    conn.close()
    return jsonify(placas)

@app.route('/api/placas_con_costos')
def get_placas_con_costos():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM placas")
        placas = cursor.fetchall()
        cursor.execute("SELECT * FROM costos")
        costos = cursor.fetchall()
    conn.close()

    costos_dict = {}
    for costo in costos:
        key = f"{float(costo['ancho'])}-{float(costo['alto'])}"
        placas_por_set = costo.get('placas_por_set', 0)
        costo_por_placa = costo['costo_set'] / placas_por_set if placas_por_set > 0 else 0
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
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM costos")
        costos = cursor.fetchall()
    conn.close()
    return jsonify(costos)

@app.route('/api/envios')
def get_envios():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM envios")
        envios = cursor.fetchall()
    conn.close()
    return jsonify(envios)

@app.route('/envios')
def envios_page():
    return render_template('envios.html')

@app.route('/api/papeles')
def get_papeles():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM papeles")
        papeles = cursor.fetchall()
    conn.close()
    return jsonify(papeles)

@app.route('/cotizacion')
def cotizacion_page():
    return render_template('cotizacion.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

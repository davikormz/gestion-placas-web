import os
import pymysql
# importaciones para login y seguridad
from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# --- Clave Secreta ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'clave-secreta-para-desarrollo-local')

# --- Configuración de Flask-Login ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 
login_manager.login_message = 'Por favor, inicia sesión para ver esta página.'
login_manager.login_message_category = 'info' 

def get_db_connection():
    return pymysql.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASS"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

# --- Clase de Usuario para Flask-Login ---
class Proveedor(UserMixin):
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash
    
    def get_id(self):
        return self.id

# --- "Cargador de Usuario" para Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM proveedores WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return Proveedor(id=user_data['id'], email=user_data['email'], password_hash=user_data['password_hash'])
    
    return None

# --- Tus rutas existentes (Completas y Protegidas) ---

@app.route('/')
@login_required 
def index():
    return render_template('envios.html')

@app.route('/api/placas')
@login_required 
def get_placas():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # ---- MODIFICADO ----
        # Filtramos por el email del usuario logueado
        # (Asumiendo que 'placas' también tiene una columna 'destinatario')
        cursor.execute("SELECT * FROM placas WHERE destinatario = %s", (current_user.email,))
        placas = cursor.fetchall()
    conn.close()
    return jsonify(placas)

@app.route('/api/placas_con_costos')
@login_required 
def get_placas_con_costos():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # ---- MODIFICADO ----
        # Filtramos 'placas' por el email del usuario logueado
        cursor.execute("SELECT * FROM placas WHERE destinatario = %s", (current_user.email,))
        placas = cursor.fetchall()
        
        # 'costos' parece ser una tabla genérica, así que la traemos completa
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
@login_required 
def get_costos():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM costos") # Esta tabla es genérica, sin filtro
        costos = cursor.fetchall()
    conn.close()
    return jsonify(costos)

@app.route('/api/envios')
@login_required 
def get_envios():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # ---- MODIFICADO ----
        # ¡Esta es la modificación clave para 'envios.html'!
        # Solo trae los envíos cuyo 'destinatario' es el email del usuario logueado
        cursor.execute("SELECT * FROM envios WHERE destinatario = %s", (current_user.email,))
        envios = cursor.fetchall()
    conn.close()
    return jsonify(envios)

@app.route('/envios')
@login_required 
def envios_page():
    return render_template('envios.html')

@app.route('/api/papeles')
@login_required 
def get_papeles():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM papeles") # Esta tabla es genérica, sin filtro
        papeles = cursor.fetchall()
    conn.close()
    return jsonify(papeles)

@app.route('/cotizacion')
@login_required 
def cotizacion_page():
    return render_template('cotizacion.html')

# --- NUEVAS RUTAS DE AUTENTICACIÓN ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('envios_page')) 
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM proveedores WHERE email = %s", (email,))
            user_data = cursor.fetchone()
        conn.close()
        
        if user_data:
            proveedor_obj = Proveedor(id=user_data['id'], email=user_data['email'], password_hash=user_data['password_hash'])
            if check_password_hash(proveedor_obj.password_hash, password):
                login_user(proveedor_obj)
                flash('Inicio de sesión exitoso.', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('envios_page'))
            
        flash('Email o contraseña incorrectos. Intenta de nuevo.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required 
def logout():
    logout_user()
    flash('Has cerrado sesión.', 'info')
    return redirect(url_for('login'))

# --- RUTA DE REGISTRO DESHABILITADA ---
# Se comenta para que nadie pueda registrarse.
# Para registrar un nuevo proveedor, descomenta temporalmente esta ruta,
# registra al usuario desde la web y vuelve a comentarla.
#
# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('envios_page'))

#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
        
#         conn = get_db_connection()
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM proveedores WHERE email = %s", (email,))
#             existing_user = cursor.fetchone()
            
#             if existing_user:
#                 flash('Ese email ya está registrado. Por favor, inicia sesión.', 'warning')
#                 return redirect(url_for('login'))
            
#             hashed_password = generate_password_hash(password)
#             cursor.execute("INSERT INTO proveedores (email, password_hash) VALUES (%s, %s)",
#                            (email, hashed_password))
#             conn.commit() 
            
#         conn.close()
        
#         flash('¡Registro exitoso! Ahora puedes iniciar sesión.', 'success')
#         return redirect(url_for('login'))

#     return render_template('register.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


import os
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

def conectar_db():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return psycopg2.connect(db_url)
    raise Exception('DATABASE_URL no está configurada')

def init_db():
    conn = conectar_db()
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS personas (
                id SERIAL PRIMARY KEY,
                dni VARCHAR(20) NOT NULL UNIQUE,
                nombre VARCHAR(100) NOT NULL,
                apellido VARCHAR(100) NOT NULL,
                direccion TEXT,
                telefono VARCHAR(20)
            );
        """)
    conn.commit()
    conn.close()

def crear_persona(dni, nombre, apellido, direccion, telefono):
    conn = conectar_db()
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO personas (dni, nombre, apellido, direccion, telefono) VALUES (%s, %s, %s, %s, %s);",
            (dni, nombre, apellido, direccion, telefono)
        )
    conn.commit()
    conn.close()

def obtener_registros():
    conn = conectar_db()
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, dni, nombre, apellido, direccion, telefono FROM personas ORDER BY apellido ASC;")
        registros = cursor.fetchall()
    conn.close()
    return registros

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    dni = request.form.get('dni')
    nombre = request.form.get('nombre')
    apellido = request.form.get('apellido')
    direccion = request.form.get('direccion')
    telefono = request.form.get('telefono')
    
    crear_persona(dni, nombre, apellido, direccion, telefono)
    return redirect(url_for('index', exito=1))

@app.route('/administrar')
def administrar():
    registros = obtener_registros()
    # Se pasa 'personas' y 'registros' para mantener compatibilidad con las plantillas
    return render_template('administrar.html', personas=registros, registros=registros)

@app.route('/eliminar/<dni>', methods=['POST'])
def eliminar_registro(dni):
    conn = conectar_db()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM personas WHERE dni = %s;", (dni,))
    conn.commit()
    conn.close()
    return redirect(url_for('administrar'))

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
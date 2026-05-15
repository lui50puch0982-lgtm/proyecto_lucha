from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'fbla_bolivia_2026_key'

# Asociaciones preestablecidas según departamentos de Bolivia
ASOCIACIONES = [
    "La Paz", "Santa Cruz", "Cochabamba", 
    "Chuquisaca", "Tarija", "Potosí", 
    "Oruro", "Beni", "Pando"
]

def get_db_connection():
    conn = sqlite3.connect('sambo_bolivia.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS luchadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_completo TEXT NOT NULL,
                ci TEXT NOT NULL,
                asociacion TEXT NOT NULL,
                division TEXT NOT NULL,
                estilo TEXT NOT NULL,
                sexo TEXT NOT NULL,
                peso REAL NOT NULL,
                categoria TEXT NOT NULL,
                documentacion_ok INTEGER DEFAULT 0,
                pago_realizado INTEGER DEFAULT 0
            )
        """)
        conn.commit()

def obtener_categoria(peso, division, estilo, sexo):
    p = float(peso)
    if division == "U-17":
        if sexo == "Damas":
            if p <= 43: return "43 Kgrs"
            if p <= 49: return "49 Kgrs"
            if p <= 57: return "57 Kgrs"
            if p <= 65: return "65 Kgrs"
            return "73 Kgrs"
        else: # Varones U-17
            if estilo == "Greco":
                if p <= 48: return "48 Kgrs"
                if p <= 55: return "55 Kgrs"
                if p <= 65: return "65 Kgrs"
                if p <= 80: return "80 Kgrs"
                return "110 Kgrs"
            else: # Libre
                if p <= 45: return "45 Kgrs"
                if p <= 51: return "51 Kgrs"
                if p <= 60: return "60 Kgrs"
                if p <= 71: return "71 Kgrs"
                return "92 Kgrs"
    else: # SENIOR
        if sexo == "Damas":
            if p <= 50: return "50 Kgrs"
            if p <= 53: return "53 Kgrs"
            if p <= 57: return "57 Kgrs"
            if p <= 62: return "62 Kgrs"
            if p <= 68: return "68 Kgrs"
            return "76 Kgrs"
        else: # Varones Senior
            if estilo == "Greco":
                if p <= 60: return "60 Kgrs"
                if p <= 67: return "67 Kgrs"
                if p <= 77: return "77 Kgrs"
                if p <= 87: return "87 Kgrs"
                if p <= 97: return "97 Kgrs"
                return "130 Kgrs"
            else: # Libre
                if p <= 57: return "57 Kgrs"
                if p <= 65: return "65 Kgrs"
                if p <= 74: return "74 Kgrs"
                if p <= 86: return "86 Kgrs"
                if p <= 97: return "97 Kgrs"
                return "125 Kgrs"

init_db()

# --- VISTAS DEL ATLETA ---

@app.route('/')
def registro():
    return render_template('atleta/registro.html', asociaciones=ASOCIACIONES)

@app.route('/inscribir', methods=['POST'])
def inscribir():
    nombre = request.form['nombre_completo']
    ci = request.form['ci']
    asoc = request.form['asociacion']
    div = request.form['division']
    est = request.form['estilo']
    sex = request.form['sexo']
    peso = request.form['peso']
    cat = obtener_categoria(peso, div, est, sex)

    with get_db_connection() as conn:
        conn.execute("""INSERT INTO luchadores (nombre_completo, ci, asociacion, division, estilo, sexo, peso, categoria) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (nombre, ci, asoc, div, est, sex, peso, cat))
        conn.commit()
    return render_template('atleta/exito.html')

# --- VISTAS DEL ADMINISTRADOR ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user == 'admin' and pw == 'Fbla2026':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        flash('Credenciales incorrectas')
    return render_template('admin/login.html')

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        luchadores = conn.execute("SELECT * FROM luchadores ORDER BY asociacion").fetchall()
    return render_template('admin/dashboard.html', luchadores=luchadores)

@app.route('/admin/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    l = conn.execute("SELECT * FROM luchadores WHERE id = ?", (id,)).fetchone()

    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        peso = request.form['peso']
        asoc = request.form['asociacion']
        # Al editar el peso, recalculamos la categoría automáticamente
        cat = obtener_categoria(peso, l['division'], l['estilo'], l['sexo'])
        
        conn.execute("UPDATE luchadores SET nombre_completo=?, peso=?, asociacion=?, categoria=? WHERE id=?",
                     (nombre, peso, asoc, cat, id))
        conn.commit()
        conn.close()
        return redirect(url_for('dashboard'))
    
    conn.close()
    return render_template('admin/editar.html', l=l, asociaciones=ASOCIACIONES)

@app.route('/admin/eliminar/<int:id>')
def eliminar(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        conn.execute("DELETE FROM luchadores WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/update_status/<int:id>/<string:campo>')
def update_status(id, campo):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    with get_db_connection() as conn:
        # Solo permite actualizar pago_realizado o documentacion_ok
        if campo in ['pago_realizado', 'documentacion_ok']:
            conn.execute(f"UPDATE luchadores SET {campo} = 1 WHERE id = ?", (id,))
            conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
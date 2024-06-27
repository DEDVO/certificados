from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base_de_datos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'tu_clave_secreta'
db = SQLAlchemy(app)


class Persona(db.Model):
    __tablename__ = 'persona'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    numero_identificacion = db.Column(db.String(50), unique=True, nullable=False)


class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(128), nullable=False)

    persona = db.relationship('Persona', backref=db.backref('usuario', uselist=False))

    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password)


class HistorialEmpleo(db.Model):
    __tablename__ = 'historial_empleo'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    fecha_retiro = db.Column(db.Date)
    cargo = db.Column(db.String(100), nullable=False)

    persona = db.relationship('Persona', backref=db.backref('historial_empleo', lazy=True))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        numero_identificacion = request.form['numero_identificacion']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        persona = Persona(nombre=nombre, numero_identificacion=numero_identificacion)
        db.session.add(persona)
        db.session.flush()

        usuario = Usuario(persona_id=persona.id, correo=correo)
        usuario.set_password(contrasena)
        db.session.add(usuario)
        db.session.commit()

        flash('Usuario registrado con éxito', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        usuario = Usuario.query.filter_by(correo=correo).first()

        if usuario and usuario.check_password(contrasena):
            session['usuario_id'] = usuario.id
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'error')
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    return render_template('dashboard.html', usuario=usuario)


@app.route('/historial_empleo', methods=['GET', 'POST'])
def historial_empleo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        fecha_ingreso = datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date()
        fecha_retiro = request.form['fecha_retiro']
        if fecha_retiro:
            fecha_retiro = datetime.strptime(fecha_retiro, '%Y-%m-%d').date()
        else:
            fecha_retiro = None
        cargo = request.form['cargo']
        persona_id = session['usuario_id']

        historial = HistorialEmpleo(persona_id=persona_id, fecha_ingreso=fecha_ingreso, fecha_retiro=fecha_retiro,
                                    cargo=cargo)
        db.session.add(historial)
        db.session.commit()

        flash('Historial de empleo agregado con éxito', 'success')
        return redirect(url_for('dashboard'))
    return render_template('historial_empleo.html')


@app.route('/logout')
def logout():
    session.pop('usuario_id', None)
    flash('Has cerrado sesión', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    if not os.path.exists('certificados'):
        os.makedirs('certificados')
    with app.app_context():
        db.create_all()
    app.run(debug=True)

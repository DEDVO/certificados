from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


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
    tipo_contrato = db.Column(db.String(50), nullable=False)
    salario = db.Column(db.Numeric(10, 2), nullable=False)
    ciudad = db.Column(db.String(50), nullable=False)

    persona = db.relationship('Persona', backref=db.backref('historial_empleo', lazy=True))

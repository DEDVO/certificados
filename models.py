from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Creación de una instancia de SQLAlchemy para interactuar con la base de datos
db = SQLAlchemy()

# Definición de la clase Persona, que representa la tabla 'persona' en la base de datos
class Persona(db.Model):
    __tablename__ = 'persona'  # Nombre de la tabla en la base de datos
    id = db.Column(db.Integer, primary_key=True)  # Columna para el ID único de la persona
    nombre = db.Column(db.String(100), nullable=False)  # Columna para el nombre de la persona
    numero_identificacion = db.Column(db.String(50), unique=True, nullable=False)  # Columna para el número de identificación único

# Definición de la clase Usuario, que representa la tabla 'usuario' en la base de datos
class Usuario(db.Model):
    __tablename__ = 'usuario'  # Nombre de la tabla en la base de datos
    id = db.Column(db.Integer, primary_key=True)  # Columna para el ID único del usuario
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), unique=True, nullable=False)  # Columna para la relación con la tabla persona
    correo = db.Column(db.String(100), unique=True, nullable=False)  # Columna para el correo electrónico único del usuario
    contrasena_hash = db.Column(db.String(128), nullable=False)  # Columna para almacenar el hash de la contraseña del usuario

    persona = db.relationship('Persona', backref=db.backref('usuario', uselist=False))  # Relación con la tabla Persona

    # Método para establecer la contraseña del usuario y almacenar su hash
    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password)

    # Método para verificar si la contraseña proporcionada coincide con la almacenada (hash)
    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password)

# Definición de la clase HistorialEmpleo, que representa la tabla 'historial_empleo' en la base de datos
class HistorialEmpleo(db.Model):
    __tablename__ = 'historial_empleo'  # Nombre de la tabla en la base de datos
    id = db.Column(db.Integer, primary_key=True)  # Columna para el ID único del historial de empleo
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)  # Columna para la relación con la tabla persona
    fecha_ingreso = db.Column(db.Date, nullable=False)  # Columna para la fecha de ingreso al empleo
    fecha_retiro = db.Column(db.Date)  # Columna opcional para la fecha de retiro del empleo
    cargo = db.Column(db.String(100), nullable=False)  # Columna para el cargo en el empleo
    tipo_contrato = db.Column(db.String(50), nullable=False)  # Columna para el tipo de contrato
    salario = db.Column(db.Numeric(10, 2), nullable=False)  # Columna para el salario del empleo
    ciudad = db.Column(db.String(50), nullable=False)  # Columna para la ciudad donde se desempeñó el empleo

    persona = db.relationship('Persona', backref=db.backref('historial_empleo', lazy=True))  # Relación con la tabla Persona

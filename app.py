# Importación de módulos necesarios
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from fpdf import FPDF
import locale
import re

# Configuración de la localización para el formato de fecha en español
locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

# Inicialización de la aplicación Flask
app = Flask(__name__, template_folder='templates')

# Configuración de la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///base_de_datos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Clave secreta para la gestión de sesiones y mensajes flash
app.config['SECRET_KEY'] = 'tu_clave_secreta'

# Inicialización de la extensión SQLAlchemy
db = SQLAlchemy(app)

# ======== PROGRAMACIÓN ORIENTADA A OBJETOS ======== #
# Definición de clases como modelos de base de datos
# Las clases Persona, Usuario e HistorialEmpleo son ejemplos de POO.
# Cada clase representa una tabla en la base de datos con atributos que
# mapean a las columnas de la tabla y métodos para operar sobre los datos.
# =================================================== #

# Modelo de la tabla 'persona'
class Persona(db.Model):
    __tablename__ = 'persona'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    numero_identificacion = db.Column(db.String(50), unique=True, nullable=False)

# Modelo de la tabla 'usuario'
class Usuario(db.Model):
    __tablename__ = 'usuario'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), unique=True, nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contrasena_hash = db.Column(db.String(128), nullable=False)

    # Relación uno a uno con la tabla 'persona'
    persona = db.relationship('Persona', backref=db.backref('usuario', uselist=False))

    # Método para configurar la contraseña encriptada
    def set_password(self, password):
        self.contrasena_hash = generate_password_hash(password)

    # Método para verificar la contraseña encriptada
    def check_password(self, password):
        return check_password_hash(self.contrasena_hash, password)

# Modelo de la tabla 'historial_empleo'
class HistorialEmpleo(db.Model):
    __tablename__ = 'historial_empleo'
    id = db.Column(db.Integer, primary_key=True)
    persona_id = db.Column(db.Integer, db.ForeignKey('persona.id'), nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    fecha_retiro = db.Column(db.Date)
    cargo = db.Column(db.String(100), nullable=False)
    tipo_contrato = db.Column(db.String(50), nullable=False)  # Tipo de contrato
    salario = db.Column(db.Numeric(10, 2), nullable=False)  # Salario
    ciudad = db.Column(db.String(50), nullable=False)  # Ciudad

    # Relación de uno a muchos con la tabla 'persona'
    persona = db.relationship('Persona', backref=db.backref('historial_empleo', lazy=True))

# Ruta para la página principal
@app.route('/')
def index():
    return render_template('index.html')

#Cerrar Sesion
@app.route('/cerrar_sesion', methods=['POST'])
def cerrar_sesion():
    session.pop('usuario_id', None)
    return redirect(url_for('login'))


# Ruta para el registro de usuarios
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        numero_identificacion = request.form['numero_identificacion']
        correo = request.form['correo']
        contrasena = request.form['contrasena']

        # Validaciones
        nombre_valido = re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre) is not None
        password_valido = (len(contrasena) > 8 and 
                           re.search(r'[A-Z]', contrasena) and 
                           re.search(r'[\d]', contrasena) and 
                           re.search(r'[!@#$%^&*(),.?":{}|<>]', contrasena))
        numero_valido = re.match(r'^\d{8,10}$', numero_identificacion) is not None

        # Si hay errores, no procesar el formulario y regresar a la misma página
        if not (nombre_valido and password_valido and numero_valido):
            return redirect(url_for('registro'))

        # Crear y agregar una nueva persona a la base de datos
        persona = Persona(nombre=nombre, numero_identificacion=numero_identificacion)
        db.session.add(persona)
        db.session.flush()  # Obtiene el ID antes de commit

        # Crear y agregar un nuevo usuario a la base de datos
        usuario = Usuario(persona_id=persona.id, correo=correo)
        usuario.set_password(contrasena)
        db.session.add(usuario)
        db.session.commit()

        flash('Usuario registrado con éxito', 'success')
        return redirect(url_for('login'))
    return render_template('registro.html')

# Ruta para el inicio de sesión de usuarios
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        contrasena = request.form['contrasena']
        usuario = Usuario.query.filter_by(correo=correo).first()

        # Verificar credenciales del usuario
        if usuario and usuario.check_password(contrasena):
            session['usuario_id'] = usuario.id
            flash('Inicio de sesión exitoso', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Correo o contraseña incorrectos', 'error')
    return render_template('login.html')

# Ruta para el dashboard del usuario
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get(session['usuario_id'])
    return render_template('dashboard.html', usuario=usuario, persona=usuario.persona)

# Ruta para agregar historial de empleo
@app.route('/agregar_historial_empleo', methods=['POST'])
def agregar_historial_empleo():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    # Procesar los datos del formulario
    fecha_ingreso = datetime.strptime(request.form['fecha_ingreso'], '%Y-%m-%d').date()
    fecha_retiro = request.form['fecha_retiro']
    if fecha_retiro:
        fecha_retiro = datetime.strptime(fecha_retiro, '%Y-%m-%d').date()
    else:
        fecha_retiro = None
    cargo = request.form['cargo']
    tipo_contrato = request.form['tipo_contrato']  # Recibe tipo de contrato
    salario = request.form['salario']  # Recibe salario
    ciudad = request.form['ciudad']  # Recibe ciudad
    persona_id = Usuario.query.get(session['usuario_id']).persona_id

    # Crear y agregar un nuevo historial de empleo
    historial = HistorialEmpleo(persona_id=persona_id, fecha_ingreso=fecha_ingreso, fecha_retiro=fecha_retiro, cargo=cargo, tipo_contrato=tipo_contrato, salario=salario, ciudad=ciudad)
    db.session.add(historial)
    db.session.commit()

    flash('Historial de empleo agregado con éxito', 'success')
    return redirect(url_for('dashboard'))

# Ruta para generar el certificado en PDF
@app.route('/generar_certificado', methods=['POST'])
def generar_certificado():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    id_historial = request.form['id_historial']
    historial = HistorialEmpleo.query.get(id_historial)

    if not historial:
        flash('No se encontró el historial de empleo.', 'error')
        return redirect(url_for('dashboard'))

    persona = Persona.query.get(historial.persona_id)
    if not persona:
        flash('No se encontró a la persona en la base de datos.', 'error')
        return redirect(url_for('dashboard'))

    # Definir el nombre del archivo PDF
    filename = f"certificados/{persona.nombre}_{persona.numero_identificacion}_{historial.id}.pdf"
    create_pdf(persona.nombre, persona.numero_identificacion, historial, filename)
    return send_file(filename, as_attachment=True)

# Función para crear el PDF del certificado
def create_pdf(nombre, numero_identificacion, historial, filename):
    # Clase personalizada de FPDF para el certificado
    class PDF(FPDF):
        def header(self):
            # Agregar imagen de encabezado
            try:
                self.image('static/img/logo.jpeg', x=10, y=8, w=33)
            except Exception as e:
                print(f"Error al cargar la imagen: {e}")

            self.set_font("Arial", size=12)
            self.cell(0, 10, txt="R-DTH-0932-24", ln=True, align='R')
            self.set_font("Arial", 'B', 14)
            self.cell(0, 10, txt="EMPRESA S.A.S", ln=True, align='C')
            self.set_font("Arial", size=12)
            self.cell(0, 10, txt="NIT 123456789-4", ln=True, align='C')
            self.cell(0, 10, txt="CERTIFICA", ln=True, align='C')
            self.ln(10)

        def footer(self):
            # Footer con información de la página
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, txt=f"Página {self.page_no()}", ln=True, align='C')

        def watermark(self):
            # Agregar marca de agua
            self.set_text_color(220, 220, 220)  # Color gris claro
            self.image('static/img/logo.jpeg', x=70, y=120, w=100, h=100)

    # Crear instancia de la clase PDF personalizada
    pdf = PDF()
    pdf.add_page()
    pdf.watermark()

    # Detalles del certificado
    pdf.set_text_color(0, 0, 0)  # Restaurar color negro para el texto normal
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=(
        f"Que el (la) señor(a) {nombre.upper()}, identificado(a) con la "
        f"cédula de Ciudadanía No {numero_identificacion}, labora en esta compañía así:\n\n"
        f"FECHA DE INGRESO: {historial.fecha_ingreso.strftime('%d DE %B DE %Y').upper()}\n"
        f"CARGO DESEMPEÑADO: {historial.cargo.upper()}\n"
        f"TIPO DE CONTRATO: {historial.tipo_contrato.upper()}\n"
        f"SALARIO BASICO: $ {historial.salario:,.2f}\n"
        f"CIUDAD: {historial.ciudad.upper()}\n"
        "Se expide la presente certificación a solicitud del interesado(a) en la ciudad de "
        f"Bogotá D.C el {datetime.now().strftime('%d')} de {datetime.now().strftime('%B')} del año "
        f"{datetime.now().strftime('%Y')}.\n\n"
        "Cordialmente,"
    ))

    pdf.ln(20)
    pdf.cell(0, 10, txt="DEIVER ANDRES ORDOSGOITIA VILLADIEGO", ln=True, align='C')
    pdf.cell(0, 10, txt="Representante legal", ln=True, align='C')
    pdf.cell(0, 10, txt="NIT: 123456789-4", ln=True, align='C')
    pdf.cell(0, 10, txt="Tel. (601)1234567 EXT.4103-4101 Cel. 1234567890", ln=True, align='C')

    # Guardar el archivo PDF
    pdf.output(filename)

# Entrada principal de la aplicación
if __name__ == '__main__':
    # Crear el directorio para los certificados si no existe
    if not os.path.exists('certificados'):
        os.makedirs('certificados')

    # Crear las tablas de la base de datos si no existen
    with app.app_context():
        db.create_all()

    # Ejecutar la aplicación en modo de depuración
    app.run(debug=True)

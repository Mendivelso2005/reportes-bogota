from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

app = Flask(__name__)

# ========================================
# CONFIGURACIÓN SQLITE (BASE DE DATOS LOCAL)
# ========================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reportes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'MiApp-BogotaCiudadana-2024!Reportes@Seguros789'

# Configurar zona horaria de Colombia
COLOMBIA_TZ = pytz.timezone('America/Bogota')

# Inicializar base de datos
db = SQLAlchemy(app)

# MODELO DE DATOS
class Reporte(db.Model):
    __tablename__ = 'reportes'
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    entidad = db.Column(db.String(100), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(COLOMBIA_TZ))
    imagen = db.Column(db.String(255), nullable=True)

    def to_dict(self):
        fecha = self.fecha_creacion
        if fecha.tzinfo is None:
            fecha = COLOMBIA_TZ.localize(fecha)
        else:
            fecha = fecha.astimezone(COLOMBIA_TZ)
        return {
            'id': self.id,
            'tipo': self.tipo,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'lat': self.lat,
            'lng': self.lng,
            'entidad': self.entidad,
            'fecha_creacion': fecha.strftime('%Y-%m-%d %H:%M:%S'),
            'imagen': self.imagen
        }

# Crear tablas
with app.app_context():
    db.create_all()
    print("✅ Base de datos SQLite creada: reportes.db")

# RUTAS
@app.route('/')
def index():
    reportes = Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
    return render_template('index.html', reportes=[r.to_dict() for r in reportes])

@app.route('/reportes')
def lista_reportes():
    reportes = Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
    return render_template('reportes.html', reportes=[r.to_dict() for r in reportes])

@app.route('/reporte', methods=['POST'])
def agregar_reporte():
    try:
        if request.content_type.startswith('multipart/form-data'):
            tipo = request.form.get('tipo')
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            lat = request.form.get('lat')
            lng = request.form.get('lng')
            entidad = request.form.get('entidad')
            imagen = request.files.get('imagen')
            filename = None
            if imagen and imagen.filename:
                filename = secure_filename(imagen.filename)
                ruta_imagen = os.path.join('static', 'images', filename)
                imagen.save(os.path.join(app.root_path, ruta_imagen))
            nuevo_reporte = Reporte(
                tipo=tipo,
                nombre=nombre,
                descripcion=descripcion,
                lat=lat,
                lng=lng,
                entidad=entidad,
                imagen=filename
            )
            db.session.add(nuevo_reporte)
            db.session.commit()
            print(f"✅ Reporte #{nuevo_reporte.id} guardado con imagen")
            return jsonify({
                'status': 'success',
                'message': 'Reporte agregado correctamente',
                'reporte': nuevo_reporte.to_dict()
            }), 201
        else:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Datos vacíos'}), 400
            campos_requeridos = ['tipo', 'nombre', 'descripcion', 'lat', 'lng', 'entidad']
            for campo in campos_requeridos:
                if campo not in data:
                    return jsonify({'error': f'Falta el campo: {campo}'}), 400
            nuevo_reporte = Reporte(
                tipo=data['tipo'],
                nombre=data['nombre'],
                descripcion=data['descripcion'],
                lat=data['lat'],
                lng=data['lng'],
                entidad=data['entidad']
            )
            db.session.add(nuevo_reporte)
            db.session.commit()
            print(f"✅ Reporte #{nuevo_reporte.id} guardado")
            return jsonify({
                'status': 'success',
                'message': 'Reporte agregado correctamente',
                'reporte': nuevo_reporte.to_dict()
            }), 201
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/eliminar/<int:id>', methods=['DELETE'])
def eliminar_reporte(id):
    try:
        reporte = Reporte.query.get_or_404(id)
        db.session.delete(reporte)
        db.session.commit()
        
        print(f"✅ Reporte #{id} eliminado")
        
        return jsonify({
            'status': 'success',
            'message': 'Reporte eliminado correctamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reportes', methods=['GET'])
def api_reportes():
    reportes = Reporte.query.order_by(Reporte.fecha_creacion.desc()).all()
    return jsonify([r.to_dict() for r in reportes])

if __name__ == '__main__':
    pass  # Render y gunicorn gestionan el servidor
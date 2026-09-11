from datetime import datetime
from mongoengine import (
    Document, StringField, EmailField,
    BooleanField, DateTimeField
)
import bcrypt

class Usuario(Document):
   
    nombre_completo = StringField(required=True, max_length=150)
    correo = EmailField(required=True, unique=True, max_length=254)
    contrasena = StringField(required=True, max_length=128)
    rol = StringField(
        required=True,
        choices=['usuario', 'administrador'],
        default='usuario',
        max_length=20
    )
    activo = BooleanField(default=True)
    fecha_registro = DateTimeField(default=datetime.utcnow)

    # Configuración de la colección en MongoDB
    meta = {
        'collection': 'usuarios',
        'indexes': ['correo', 'rol', 'activo']
    }

    def set_contrasena(self, contrasena_plana):
       
        salt = bcrypt.gensalt(rounds=10)
        self.contrasena = bcrypt.hashpw(
            contrasena_plana.encode('utf-8'), salt
        ).decode('utf-8')

    def verificar_contrasena(self, contrasena_plana):
        
        return bcrypt.checkpw(
            contrasena_plana.encode('utf-8'),
            self.contrasena.encode('utf-8')
        )

    @property
    def is_authenticated(self):
        # Compatible con checks de Django/DRF que esperan este atributo
        return True

    @property
    def is_anonymous(self):
        return False
    

    def __str__(self):
        return f"{self.nombre_completo} ({self.correo})"
from django.contrib import admin
from .models import Insumo, Entrega,UsuarioPermiso# Importa los modelos

# Registra los modelos en el admin
admin.site.register(Insumo)
admin.site.register(Entrega)
admin.site.register(UsuarioPermiso)
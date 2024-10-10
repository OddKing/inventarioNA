# inventario/forms.py
from django import forms
from .models import Entrega
from django.contrib.auth.models import User

class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['insumo', 'cantidad_entregada', 'fecha_entrega', 'usuario']

    # Opcionalmente, puedes personalizar los widgets
    # para el campo de usuario si lo necesitas
    usuario = forms.ModelChoiceField(
        queryset=User.objects.all().exclude(pk=1),  # Asegúrate de importar el modelo User
        empty_label="Seleccione un usuario"
    )

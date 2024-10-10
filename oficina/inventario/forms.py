# inventario/forms.py
from django import forms
from .models import Entrega,Insumo
from django.contrib.auth.models import User

class EntregaForm(forms.ModelForm):
    class Meta:
        model = Entrega
        fields = ['insumo', 'cantidad_entregada', 'fecha_entrega', 'usuario']
        widgets = {
            'fecha_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cantidad_entregada': forms.NumberInput(attrs={'class': 'form-control'}),
            'insumo': forms.Select(attrs={'class': 'form-control'}),
            'usuario': forms.Select(attrs={'class': 'form-control'}),
        }

    usuario = forms.ModelChoiceField(
        queryset=User.objects.all().exclude(pk=1),
        empty_label="Seleccione un usuario",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['insumo'].queryset = Insumo.objects.filter(cantidad__gt=0)

        for field_name, field in self.fields.items():
            # Personalizar la clase de las etiquetas
            field.label = field.label

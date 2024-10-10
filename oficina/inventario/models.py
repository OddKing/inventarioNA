from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse
import uuid
from django.contrib.auth.models import User
from django.db import models

class Insumo(models.Model):
    nombre = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Entrega(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    cantidad_entregada = models.PositiveIntegerField()
    fecha_entrega = models.DateTimeField(default=timezone.now)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    confirmado = models.BooleanField(default=False)
    token_confirmacion = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f"Entrega de {self.insumo.nombre} a {self.usuario.username} el {self.fecha_entrega}"

    def get_confirmacion_url(self):
        return reverse('confirmar_entrega', args=[str(self.token_confirmacion)])

class UsuarioPermiso(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    puede_iniciar_sesion = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    

class Devolucion(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE, related_name='devoluciones')
    cantidad = models.PositiveIntegerField()
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_devolucion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cantidad} de {self.insumo.nombre} devuelto por {self.usuario.username}"
from .models import Insumo, Entrega #agregar punto
from django.template.loader import render_to_string # type: ignore
from django.utils.html import strip_tags # type: ignore
from django.contrib.auth import authenticate, login # type: ignore
from django.shortcuts import render, redirect,get_object_or_404 # type: ignore
from django.contrib import messages # type: ignore
from .models import UsuarioPermiso
from django.contrib.auth.decorators import login_required # type: ignore
from .forms import EntregaForm
from .correo import Correo
from django.contrib import messages # type: ignore

def pagina_inicial(request):
    insumos = Insumo.objects.filter(cantidad=0)  # Insumos con cantidad 0
    entregas = Entrega.objects.filter(confirmado=False)  # Entregas no confirmadas
    return render(request, 'pagina_inicial.html', {'insumos': insumos, 'entregas': entregas})




def confirmar_entrega(request, token):
    entrega = get_object_or_404(Entrega, token_confirmacion=token)

    if not entrega.confirmado:
        # Actualizar la cantidad del insumo
        insumo = entrega.insumo
        if insumo.cantidad >= entrega.cantidad_entregada:
            insumo.cantidad -= entrega.cantidad_entregada
            insumo.save()

            # Marcar la entrega como confirmada
            entrega.confirmado = True
            entrega.save()

            # Enviar mensaje de éxito al usuario
            messages.success(request, 'La entrega ha sido confirmada exitosamente.')
        else:
            # Enviar mensaje de error si la cantidad del insumo es insuficiente
            messages.error(request, 'No hay suficiente cantidad disponible para confirmar la entrega.')
    else:
        # Entrega ya confirmada
        messages.info(request, 'Esta entrega ya ha sido confirmada anteriormente.')

    return redirect('pagina_inicial')



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.usuariopermiso.puede_iniciar_sesion:
                login(request, user)
                return redirect('crear_entrega')
            else:
                messages.error(request, 'No tienes permiso para acceder a esta plataforma.')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
            
    return render(request, 'login.html')



@login_required(login_url='/login')
def crear_entrega(request, insumo_id=None):
    if not hasattr(request.user, 'usuariopermiso') or not request.user.usuariopermiso.puede_iniciar_sesion:
        return redirect('login')  # Redirigir a la página de inicio de sesión si el usuario no está autorizado

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.usuario = request.user  # Guardar el usuario actual

            # Si se proporciona un ID de insumo, obtener el insumo correspondiente
            if insumo_id:
                insumo = Insumo.objects.get(id=insumo_id)
                entrega.insumo = insumo
        
            entrega.save()
            
            # Enviar correo de confirmación
            subject = 'Confirma la recepción del insumo'
            html_message = render_to_string('correo_confirmacion.html', {
                'usuario': request.user,
                'entrega': entrega,
                'confirmacion_url': entrega.get_confirmacion_url(),
            })
            plain_message = strip_tags(html_message)
            from_email = 'correo.na@gmail.com'
            to_email = 'carlos.campana@nameaction.com'
            
            notificador = Correo('correo.na@gmail.com', 'uoeltvyzagdnobkp', 'smtp.gmail.com', 587)
            if notificador.enviar([to_email], subject, plain_message, from_email):
                messages.success(request, 'Correo enviado exitosamente.')
            else:
                messages.error(request, 'Hubo un problema al enviar el correo.')
            notificador.cerrar()

            return redirect('pagina_inicial')  # Redirigir a la página inicial después de guardar
    else:
        form = EntregaForm()

    return render(request, 'crear_entrega.html', {'form': form})

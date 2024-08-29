
from .models import Insumo, Entrega
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .models import UsuarioPermiso
from django.contrib.auth.decorators import login_required
from .forms import EntregaForm
from .correo import Correo

def pagina_inicial(request):
    insumos = Insumo.objects.filter(cantidad=0)  # Insumos con cantidad 0
    entregas = Entrega.objects.filter(confirmado=False)  # Entregas no confirmadas
    return render(request, 'pagina_inicial.html', {'insumos': insumos, 'entregas': entregas})



def crear_entrega(request, insumo_id):
    notificador=Correo('correo.na@gmail.com','uoeltvyzagdnobkp','smtp.gmail.com',587)
    insumo = Insumo.objects.get(id=insumo_id)
    entrega = Entrega.objects.create(insumo=insumo, usuario=request.user)
    
    # Enviar correo de confirmación
    subject = 'Confirma la recepción del insumo'
    html_message = render_to_string('correo_confirmacion.html', {
        'usuario': request.user,
        'entrega': entrega,
        'confirmacion_url': entrega.get_confirmacion_url(),
    })
    plain_message = strip_tags(html_message)
    from_email = 'correo.na@gmail.com'
    to_email = request.user.email
    
    # to, subject, message, name_from, html=False, documents=None, cc=[], bcc=[], firma_img=None
    result = notificador.enviar([to_email],subject, plain_message, from_email)
    return render(request, 'pagina_inicial.html', {'entrega': entrega})





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
        else:
            # Aquí puedes manejar el caso en que la cantidad del insumo es insuficiente.
            # Por ejemplo, enviar una notificación o manejar un error.
            pass

    return redirect('pagina_inicial')  # Redirige a la página inicial o a una página de éxito



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



@login_required
def crear_entrega(request):
    if not hasattr(request.user, 'usuariopermiso') or not request.user.usuariopermiso.puede_iniciar_sesion:
        return redirect('login')  # Redirigir a la página de inicio de sesión si el usuario no está autorizado

    if request.method == 'POST':
        form = EntregaForm(request.POST)
        if form.is_valid():
            entrega = form.save(commit=False)
            entrega.usuario = form.cleaned_data['usuario']  # Asegurarse de que el usuario seleccionado se guarde
            entrega.save()
            return redirect('pagina_inicial')
    else:
        form = EntregaForm()
    return render(request, 'crear_entrega.html', {'form': form})
from .models import Insumo, Entrega #agregar punto
from django.template.loader import render_to_string # type: ignore
from django.utils.html import strip_tags # type: ignore
from django.contrib.auth import authenticate, login, logout# type: ignore
from django.shortcuts import render, redirect,get_object_or_404 # type: ignore
from django.contrib import messages # type: ignore
from .models import UsuarioPermiso
from django.contrib.auth.decorators import login_required # type: ignore
from .forms import EntregaForm,CargarInsumoFormSet
from .correo import Correo
from django.contrib import messages # type: ignore
from django.contrib.auth.models import User

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

    return render(request, 'confirmado.html')



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.usuariopermiso.puede_iniciar_sesion:
                login(request, user)
                return redirect('pagina_inicial')
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
            entrega.usuario= form.cleaned_data['usuario']

            host=request.META['HTTP_HOST']

            # entrega.usuario = request.user  # Guardar el usuario actual

            # Si se proporciona un ID de insumo, obtener el insumo correspondiente
            #insumo_id = form.cleaned_data.get('insumo')
            insumo_id= request.POST.get('insumo')
            print(insumo_id)
            if insumo_id:
                insumo = Insumo.objects.get(id=insumo_id)
                entrega.insumo = insumo

                cantidad_solicitada=form.cleaned_data['cantidad_entregada']
                print(insumo.cantidad >= cantidad_solicitada)
                if insumo.cantidad >= cantidad_solicitada:
                    entrega.save()
                    url='http://'+host+entrega.get_confirmacion_url()
                    # Enviar correo de confirmación
                    subject = 'Confirma la recepción del insumo'
                    print(entrega.usuario.first_name)
                    html_message = render_to_string('correo_confirmacion.html', {
                        'usuario': entrega.usuario.first_name,
                        'entrega': entrega,
                        'confirmacion_url': url,
                    })
                    plain_message = strip_tags(html_message)
                    from_email = 'correo.na@gmail.com'
                    #to_email = 'carlos.campana@nameaction.com'
                    to_email=entrega.usuario.email   
                    #print(url)         
                    notificador = Correo('correo.na@gmail.com', 'uoeltvyzagdnobkp', 'smtp.gmail.com', 587)
                    if notificador.enviar([to_email], subject, plain_message, from_email):
                        messages.success(request, 'Correo enviado exitosamente.')
                    else:
                        messages.error(request, 'Hubo un problema al enviar el correo.'+' '+host)
                    notificador.cerrar()

                    return redirect('pagina_inicial')  # Redirigir a la página inicial después de guardar
                else:
                    messages.error(request, 'No hay suficiente cantidad de este insumo disponible.')
                    return redirect('pagina_inicial')  # Mensaje de error si no hay suficiente cantidad
    else:
        form = EntregaForm()

    return render(request, 'crear_entrega.html', {'form': form})


@login_required(login_url='/login')
def listar_entregas(request):
    # Obtener todos los usuarios para el dropdown
    usuarios = User.objects.all().exclude(pk=1)
    usuario_seleccionado = request.GET.get('usuario')
    
    # Filtrar las entregas por el usuario seleccionado, si existe
    if usuario_seleccionado:
        entregas = Entrega.objects.filter(usuario__id=usuario_seleccionado, cantidad_entregada__gt=0,confirmado=1)
    else:
        entregas = Entrega.objects.none()  # No mostrar entregas si no hay un usuario seleccionado

    return render(request, 'listar_entregas.html', {
        'entregas': entregas,
        'usuarios': usuarios,
        'usuario_seleccionado': usuario_seleccionado
    })

@login_required(login_url='/login')
def registrar_devolucion(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id)
    insumo = entrega.insumo
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        if 0 < cantidad <= entrega.cantidad_entregada:
            # Actualizar la cantidad del insumo y la cantidad de la entrega
            insumo.cantidad += cantidad
            insumo.save()
            entrega.cantidad_entregada-= cantidad
            entrega.save()
            messages.success(request, 'Devolución registrada exitosamente.')
            subject = 'Informe de la devolucion'
            html_message = render_to_string('correo_devolucion.html', {
                        'usuario': entrega.usuario.first_name,
                        'entrega': entrega,
                    })
            plain_message = strip_tags(html_message)
            from_email = 'correo.na@gmail.com'
            #to_email = 'carlos.campana@nameaction.com'
            to_email=entrega.usuario.email
            notificador = Correo('correo.na@gmail.com', 'uoeltvyzagdnobkp', 'smtp.gmail.com', 587)
            if notificador.enviar([to_email,'carlos.campana@nameaction.com'], subject, plain_message, from_email):
                messages.success(request, 'Correo enviado exitosamente.')
            else:
                messages.error(request, 'Hubo un problema al enviar el correo.')
            notificador.cerrar()
        else:
            messages.error(request, 'La cantidad debe ser positiva y no superar la cantidad entregada.')
        return redirect('listar_entregas')
    return render(request, 'devolucion_form.html', {'entrega': entrega, 'insumo': insumo})

def logout_view(request):
    logout(request)
    return redirect('pagina_inicial') 


@login_required(login_url='/login')
def cargar_insumos(request):
    if request.method == 'POST':
        formset = CargarInsumoFormSet(request.POST, queryset=Insumo.objects.none())
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Insumos cargados exitosamente.')
            return redirect('pagina_inicial')
        else:
            messages.error(request, 'Error al cargar los insumos. Revisa los datos.')
    else:
        formset = CargarInsumoFormSet(queryset=Insumo.objects.none())
    
    return render(request, 'cargar_insumo.html', {'formset': formset})

@login_required(login_url='/login')
def reenviar_confirmacion(request, entrega_id):
    entrega = get_object_or_404(Entrega, id=entrega_id)

    # Aquí envías el correo de confirmación nuevamente, como lo hiciste anteriormente
    # Asumiendo que ya tienes la lógica para enviar el correo de confirmación.

    host = request.META['HTTP_HOST']
    url = 'http://' + host + entrega.get_confirmacion_url()  # Método para obtener la URL de confirmación

    subject = 'Urgente Confirma la recepción del insumo'
    html_message = render_to_string('correo_confirmacion.html', {
        'usuario': entrega.usuario.first_name,
        'entrega': entrega,
        'confirmacion_url': url,
    })
    plain_message = strip_tags(html_message)
    from_email = 'correo.na@gmail.com'
    to_email = entrega.usuario.email

    notificador = Correo('correo.na@gmail.com', 'uoeltvyzagdnobkp', 'smtp.gmail.com', 587)
    if notificador.enviar([to_email], subject, plain_message, from_email):
        messages.success(request, 'Correo de confirmación reenviado exitosamente.')
    else:
        messages.error(request, 'Hubo un problema al reenviar el correo.')

    notificador.cerrar()
    return redirect('pagina_inicial')
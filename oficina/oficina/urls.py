
from django.contrib import admin
from django.urls import path
from inventario import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login_view, name='login'),
    path('', views.pagina_inicial, name='pagina_inicial'),
    path('crear-entrega/', views.crear_entrega, name='crear_entrega'),
    path('confirmar-entrega/<uuid:token>/', views.confirmar_entrega, name='confirmar_entrega'),
    path('entregas/', views.listar_entregas, name='listar_entregas'),
    path('devolucion/<int:entrega_id>/', views.registrar_devolucion, name='registrar_devolucion'),
    path('logout/', views.logout_view, name='logout'),
    path('cargar-insumos/', views.cargar_insumos, name='cargar_insumos'),
    path('reenviar-confirmacion/<int:entrega_id>/', views.reenviar_confirmacion, name='reenviar_confirmacion'),
    path('reporteria-insumos/', views.reporteria_insumos, name='reporteria_insumos'),
]


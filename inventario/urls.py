from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.catalogo_view, name='catalogo'),
    path('producto/nuevo/', views.crear_producto_view, name='crear_producto'),
    path('producto/<int:producto_id>/transaccion/', views.transaccion_pin_view, name='transaccion_pin'),
    path('modulo/<slug:modulo_slug>/', views.en_construccion_view, name='en_construccion'),
]

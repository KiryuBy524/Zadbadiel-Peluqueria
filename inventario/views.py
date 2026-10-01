from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Q

from .models import Operador, Producto, MovimientoInventario
from .forms import LoginForm, ProductoForm, TransaccionPinForm


def operador_context_processor(request):
    """Agrega el operador activo al contexto de las plantillas. Parámetros: request."""
    operador_id = request.session.get('operador_id')
    if operador_id:
        try:
            operador = Operador.objects.get(id=operador_id, is_active=True)
            return {'operador_activo': operador}
        except Operador.DoesNotExist:
            request.session.flush()
    return {'operador_activo': None}


def operador_required(view_func):
    """Verifica que exista un operador con sesión activa. Parámetros: view_func."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        """Ejecuta la vista si la sesión es válida. Parámetros: request, *args, **kwargs."""
        operador_id = request.session.get('operador_id')
        if not operador_id:
            messages.warning(request, "Debe ingresar su PIN para acceder al sistema.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login_view(request):
    """Autentica al operador mediante PIN numérico. Parámetros: request."""
    if request.session.get('operador_id'):
        return redirect('catalogo')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            operador = form.operador_autenticado
            request.session['operador_id'] = operador.id
            request.session['operador_nombre'] = operador.nombre
            request.session['operador_rol'] = operador.rol
            messages.success(
                request,
                f"Sesión iniciada: {operador.nombre}"
            )
            return redirect('catalogo')
        else:
            for error in form.non_field_errors():
                messages.error(request, f"{error}")
            for field, errors in form.errors.items():
                if field != '__all__':
                    for error in errors:
                        messages.error(request, f"{error}")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    """Cierra la sesión activa del operador. Parámetros: request."""
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente.")
    return redirect('login')


@operador_required
def catalogo_view(request):
    """Muestra el catálogo de productos y resumen de stock. Parámetros: request."""
    query = request.GET.get('q', '').strip()
    productos = Producto.objects.filter(is_active=True)

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) |
            Q(marca__icontains=query) |
            Q(codigo_barra__icontains=query)
        )

    total_productos = productos.count()
    quiebres_stock = sum(1 for p in productos if p.semaforo_general == 'rojo')
    alertas_stock = sum(1 for p in productos if p.semaforo_general == 'amarillo')
    stock_seguro = sum(1 for p in productos if p.semaforo_general == 'verde')

    context = {
        'productos': productos,
        'query': query,
        'total_productos': total_productos,
        'quiebres_stock': quiebres_stock,
        'alertas_stock': alertas_stock,
        'stock_seguro': stock_seguro,
    }
    return render(request, 'catalogo.html', context)


@operador_required
def crear_producto_view(request):
    """Registra un nuevo producto en el catálogo. Parámetros: request."""
    operador_id = request.session.get('operador_id')
    operador = Operador.objects.get(id=operador_id)

    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                producto = form.save()
                if producto.stock_bodega > 0:
                    MovimientoInventario.objects.create(
                        producto=producto,
                        operador=operador,
                        tipo_movimiento='INGRESO',
                        cantidad=producto.stock_bodega,
                        formato='BODEGA',
                        comentario="Carga inicial (Bodega)"
                    )
                if producto.stock_retail > 0:
                    MovimientoInventario.objects.create(
                        producto=producto,
                        operador=operador,
                        tipo_movimiento='INGRESO',
                        cantidad=producto.stock_retail,
                        formato='RETAIL',
                        comentario="Carga inicial (Retail)"
                    )
            messages.success(request, f"Producto '{producto.nombre}' registrado correctamente.")
            return redirect('catalogo')
        else:
            messages.error(request, "Por favor corrija los errores en el formulario.")
    else:
        form = ProductoForm()

    return render(request, 'crear_producto.html', {'form': form})


@operador_required
def transaccion_pin_view(request, producto_id):
    """Registra entradas y salidas de stock con confirmación de PIN. Parámetros: request, producto_id."""
    producto = get_object_or_404(Producto, id=producto_id, is_active=True)

    if request.method == 'POST':
        form = TransaccionPinForm(request.POST)
        if form.is_valid():
            accion = form.cleaned_data['accion']
            cantidad = form.cleaned_data['cantidad']
            operador_autorizado = form.operador_autorizado
            comentario = form.cleaned_data.get('comentario', '')

            error_stock = False
            if accion == 'VENTA':
                if producto.stock_retail < cantidad:
                    messages.error(
                        request,
                        f"Stock insuficiente en Retail. Disponible: {producto.stock_retail} unidades. "
                        f"Solicitado: {cantidad} unidades."
                    )
                    error_stock = True
            elif accion == 'CONSUMO_INTERNO':
                if producto.stock_bodega < cantidad:
                    messages.error(
                        request,
                        f"Stock insuficiente en Bodega. Disponible: {producto.stock_bodega} unidades. "
                        f"Solicitado: {cantidad} unidades."
                    )
                    error_stock = True

            if not error_stock:
                with transaction.atomic():
                    if accion == 'VENTA':
                        producto.stock_retail -= cantidad
                        tipo_mov = 'VENTA'
                        formato_mov = 'RETAIL'
                        nota_defecto = "Venta a cliente en mostrador"
                    elif accion == 'CONSUMO_INTERNO':
                        producto.stock_bodega -= cantidad
                        tipo_mov = 'CONSUMO_INTERNO'
                        formato_mov = 'BODEGA'
                        nota_defecto = "Apertura para uso en salón"
                    elif accion == 'INGRESO_BODEGA':
                        producto.stock_bodega += cantidad
                        tipo_mov = 'INGRESO'
                        formato_mov = 'BODEGA'
                        nota_defecto = "Entrada a bodega"
                    elif accion == 'INGRESO_RETAIL':
                        producto.stock_retail += cantidad
                        tipo_mov = 'INGRESO'
                        formato_mov = 'RETAIL'
                        nota_defecto = "Entrada a vitrina retail"

                    producto.save()

                    nota_final = comentario.strip() if comentario.strip() else nota_defecto

                    MovimientoInventario.objects.create(
                        producto=producto,
                        operador=operador_autorizado,
                        tipo_movimiento=tipo_mov,
                        cantidad=cantidad,
                        formato=formato_mov,
                        comentario=nota_final
                    )

                messages.success(
                    request,
                    f"Operación realizada por {operador_autorizado.nombre}. "
                    f"{dict(form.fields['accion'].choices).get(accion)}: {cantidad} u. "
                    f"Stock actual: Bodega {producto.stock_bodega} u, Retail {producto.stock_retail} u."
                )
                return redirect('catalogo')
        else:
            for error in form.non_field_errors():
                messages.error(request, f"{error}")
            for field, errors in form.errors.items():
                if field != '__all__':
                    for error in errors:
                        messages.error(request, f"{error}")
    else:
        tipo_preseleccion = request.GET.get('tipo', 'VENTA')
        initial_data = {'cantidad': 1}
        if tipo_preseleccion in ['VENTA', 'CONSUMO_INTERNO', 'INGRESO_BODEGA', 'INGRESO_RETAIL']:
            initial_data['accion'] = tipo_preseleccion
        form = TransaccionPinForm(initial=initial_data)

    context = {
        'producto': producto,
        'form': form,
    }
    return render(request, 'transaccion_pin.html', context)


@operador_required
def en_construccion_view(request, modulo_slug):
    """Muestra la vista de módulos en desarrollo. Parámetros: request, modulo_slug."""
    modulos_info = {
        'cctv': {
            'titulo': 'Historial y Auditoría (CCTV Sync)',
            'descripcion': (
                'Módulo para vincular movimientos de inventario con grabaciones del local.'
            ),
            'fase': 'En desarrollo'
        },
        'mermas': {
            'titulo': 'Reportes y Estadísticas de Mermas',
            'descripcion': (
                'Módulo para calcular diferencias entre consumos registrados y existencias reales.'
            ),
            'fase': 'En desarrollo'
        },
        'multilocal': {
            'titulo': 'Gestión Multilocal',
            'descripcion': (
                'Módulo para transferencias entre sucursales y control unificado.'
            ),
            'fase': 'En desarrollo'
        },
    }

    modulo = modulos_info.get(modulo_slug, {
        'titulo': 'Módulo en Construcción',
        'descripcion': 'Esta sección estará disponible en una próxima versión.',
        'fase': 'En desarrollo'
    })

    return render(request, 'en_construccion.html', {'modulo': modulo})

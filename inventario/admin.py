from django.contrib import admin
from .models import Operador, Producto, MovimientoInventario


@admin.register(Operador)
class OperadorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rol', 'is_active', 'fecha_creacion')
    list_filter = ('rol', 'is_active')
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo_barra',
        'nombre',
        'marca',
        'branch_id',
        'stock_bodega',
        'stock_retail',
        'umbral_minimo',
        'is_active'
    )
    list_filter = ('branch_id', 'is_active', 'marca')
    search_fields = ('nombre', 'marca', 'codigo_barra')


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = (
        'timestamp',
        'producto',
        'operador',
        'tipo_movimiento',
        'cantidad',
        'formato'
    )
    list_filter = ('tipo_movimiento', 'formato', 'timestamp')
    search_fields = ('producto__nombre', 'operador__nombre', 'comentario')
    readonly_fields = ('timestamp',)

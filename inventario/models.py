from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Operador(models.Model):
    ROL_CHOICES = [
        ('DUEÑO', 'Dueño(a)'),
        ('CAJERA', 'Cajera'),
        ('ESTILISTA', 'Estilista'),
    ]

    nombre = models.CharField(max_length=100, verbose_name="Nombre Completo")
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='ESTILISTA', verbose_name="Rol")
    pin = models.CharField(max_length=128, verbose_name="PIN")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Operador"
        verbose_name_plural = "Operadores"
        ordering = ['nombre']

    def __str__(self):
        """Devuelve el nombre del operador. Parámetros: self."""
        return self.nombre

    def set_pin(self, raw_pin):
        """Hashea y asigna el PIN. Parámetros: self, raw_pin."""
        self.pin = make_password(str(raw_pin).strip())

    def check_pin(self, raw_pin):
        """Comprueba si el PIN ingresado coincide. Parámetros: self, raw_pin."""
        return check_password(str(raw_pin).strip(), self.pin)


class Producto(models.Model):
    codigo_barra = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="Código de Barras / Interno"
    )
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Producto")
    marca = models.CharField(max_length=100, verbose_name="Marca")
    branch_id = models.CharField(
        max_length=20,
        default="LOCAL-01",
        db_index=True,
        verbose_name="Sucursal"
    )
    stock_bodega = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Bodega"
    )
    stock_retail = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock Retail"
    )
    umbral_minimo = models.PositiveIntegerField(
        default=5,
        verbose_name="Umbral Mínimo"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Modificación")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        """Devuelve el nombre, marca y código del producto. Parámetros: self."""
        return f"{self.nombre} - {self.marca} [{self.codigo_barra}]"

    @property
    def stock_total(self):
        """Calcula la suma de stock en bodega y retail. Parámetros: self."""
        return self.stock_bodega + self.stock_retail

    def get_estado_semaforo(self, stock_valor):
        """Determina el estado del semáforo según el stock. Parámetros: self, stock_valor."""
        if stock_valor == 0:
            return 'rojo'
        elif stock_valor <= self.umbral_minimo:
            return 'amarillo'
        return 'verde'

    @property
    def semaforo_bodega(self):
        """Obtiene el semáforo para bodega. Parámetros: self."""
        return self.get_estado_semaforo(self.stock_bodega)

    @property
    def semaforo_retail(self):
        """Obtiene el semáforo para retail. Parámetros: self."""
        return self.get_estado_semaforo(self.stock_retail)

    @property
    def semaforo_general(self):
        """Obtiene el semáforo más crítico del producto. Parámetros: self."""
        if self.stock_bodega == 0 or self.stock_retail == 0:
            return 'rojo'
        elif self.stock_bodega <= self.umbral_minimo or self.stock_retail <= self.umbral_minimo:
            return 'amarillo'
        return 'verde'


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO_CHOICES = [
        ('VENTA', 'Venta Comercial (Retail)'),
        ('CONSUMO_INTERNO', 'Apertura / Consumo Interno (Bodega)'),
        ('INGRESO', 'Ingreso / Reposición de Stock'),
    ]

    FORMATO_CHOICES = [
        ('BODEGA', 'Bodega (Uso Interno)'),
        ('RETAIL', 'Retail (Venta)'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name="Producto"
    )
    operador = models.ForeignKey(
        Operador,
        on_delete=models.PROTECT,
        related_name='movimientos',
        verbose_name="Operador Responsable"
    )
    tipo_movimiento = models.CharField(
        max_length=20,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name="Tipo de Movimiento"
    )
    cantidad = models.PositiveIntegerField(verbose_name="Cantidad")
    formato = models.CharField(
        max_length=10,
        choices=FORMATO_CHOICES,
        verbose_name="Formato Afectado"
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha y Hora"
    )
    comentario = models.TextField(
        blank=True,
        default="",
        verbose_name="Comentario"
    )

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ['-timestamp']

    def __str__(self):
        """Devuelve la descripción del movimiento realizado. Parámetros: self."""
        return f"{self.tipo_movimiento} - {self.cantidad}u de {self.producto.nombre} por {self.operador.nombre} ({self.timestamp:%d/%m/%Y %H:%M})"

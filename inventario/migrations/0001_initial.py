import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operador',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, verbose_name='Nombre Completo')),
                ('rol', models.CharField(choices=[('DUEÑO', 'Dueño(a)'), ('CAJERA', 'Cajera'), ('ESTILISTA', 'Estilista')], default='ESTILISTA', max_length=20, verbose_name='Rol')),
                ('pin', models.CharField(max_length=128, verbose_name='PIN de Seguridad (Hasheado)')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')),
            ],
            options={
                'verbose_name': 'Operador',
                'verbose_name_plural': 'Operadores',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo_barra', models.CharField(db_index=True, max_length=50, unique=True, verbose_name='Código de Barras / Interno')),
                ('nombre', models.CharField(max_length=150, verbose_name='Nombre del Producto')),
                ('marca', models.CharField(max_length=100, verbose_name='Marca')),
                ('branch_id', models.CharField(db_index=True, default='LOCAL-01', max_length=20, verbose_name='Identificador de Sucursal')),
                ('stock_bodega', models.PositiveIntegerField(default=0, verbose_name='Stock Bodega (Uso Profesional Interno)')),
                ('stock_retail', models.PositiveIntegerField(default=0, verbose_name='Stock Retail (Venta a Clientes)')),
                ('umbral_minimo', models.PositiveIntegerField(default=5, verbose_name='Umbral Mínimo de Alerta')),
                ('is_active', models.BooleanField(default=True, verbose_name='Activo (No Eliminado)')),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True, verbose_name='Última Modificación')),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='MovimientoInventario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo_movimiento', models.CharField(choices=[('VENTA', 'Venta Comercial (Retail)'), ('CONSUMO_INTERNO', 'Apertura / Consumo Interno (Bodega)'), ('INGRESO', 'Ingreso / Reposición de Stock')], max_length=20, verbose_name='Tipo de Movimiento')),
                ('cantidad', models.PositiveIntegerField(verbose_name='Cantidad')),
                ('formato', models.CharField(choices=[('BODEGA', 'Bodega (Uso Interno)'), ('RETAIL', 'Retail (Venta)')], max_length=10, verbose_name='Formato Afectado')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Fecha y Hora Exacta')),
                ('comentario', models.TextField(blank=True, default='', verbose_name='Comentario / Motivo')),
                ('operador', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos', to='inventario.operador', verbose_name='Operador Responsable')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='movimientos', to='inventario.producto', verbose_name='Producto')),
            ],
            options={
                'verbose_name': 'Movimiento de Inventario',
                'verbose_name_plural': 'Movimientos de Inventario',
                'ordering': ['-timestamp'],
            },
        ),
    ]

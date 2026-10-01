from django.test import TestCase, Client
from django.urls import reverse
from inventario.models import Operador, Producto, MovimientoInventario


class InventarioModelTests(TestCase):
    def setUp(self):
        """Configura los datos base de prueba. Parámetros: self."""
        self.operador = Operador(nombre="Julieta Gómez", rol="DUEÑO")
        self.operador.set_pin("1234")
        self.operador.save()

        self.producto = Producto.objects.create(
            codigo_barra="TEST-001",
            nombre="Champú Prueba",
            marca="Marca Test",
            branch_id="LOCAL-01",
            stock_bodega=10,
            stock_retail=5,
            umbral_minimo=5
        )

    def test_pin_hashing_and_validation(self):
        """Verifica el hasheo y la validación de PIN. Parámetros: self."""
        self.assertTrue(self.operador.check_pin("1234"))
        self.assertFalse(self.operador.check_pin("9999"))
        self.assertNotEqual(self.operador.pin, "1234")

    def test_calculo_semaforos(self):
        """Verifica los estados del semáforo según el stock. Parámetros: self."""
        self.assertEqual(self.producto.semaforo_bodega, 'verde')
        self.assertEqual(self.producto.semaforo_retail, 'amarillo')

        self.producto.stock_retail = 0
        self.producto.save()
        self.assertEqual(self.producto.semaforo_retail, 'rojo')

    def test_soft_delete_preserva_registros(self):
        """Verifica que la baja lógica preserve el registro. Parámetros: self."""
        self.producto.is_active = False
        self.producto.save()
        self.assertEqual(Producto.objects.filter(is_active=False).count(), 1)


class InventarioFlujosViewTests(TestCase):
    def setUp(self):
        """Configura los datos base de prueba. Parámetros: self."""
        self.client = Client()
        self.operador = Operador(nombre="Jonathan Soto", rol="CAJERA")
        self.operador.set_pin("5678")
        self.operador.save()

        self.producto = Producto.objects.create(
            codigo_barra="PROD-100",
            nombre="Mascarilla Capilar",
            marca="Test Lab",
            branch_id="LOCAL-01",
            stock_bodega=8,
            stock_retail=6,
            umbral_minimo=3
        )

    def test_login_con_pin_correcto_e_incorrecto(self):
        """Prueba la autenticación con PIN correcto e incorrecto. Parámetros: self."""
        response_bad = self.client.post(reverse('login'), {'pin': '0000'})
        self.assertEqual(response_bad.status_code, 200)
        self.assertIsNone(self.client.session.get('operador_id'))

        response_ok = self.client.post(reverse('login'), {'pin': '5678'})
        self.assertRedirects(response_ok, reverse('catalogo'))
        self.assertEqual(self.client.session.get('operador_id'), self.operador.id)

    def test_acceso_protegido_sin_login(self):
        """Verifica la redirección a login sin sesión activa. Parámetros: self."""
        response = self.client.get(reverse('catalogo'))
        self.assertRedirects(response, reverse('login'))

    def test_transaccion_critica_con_pin_exitoso(self):
        """Prueba el descuento de stock con PIN válido. Parámetros: self."""
        self.client.post(reverse('login'), {'pin': '5678'})

        url = reverse('transaccion_pin', args=[self.producto.id])
        response = self.client.post(url, {
            'accion': 'VENTA',
            'cantidad': 2,
            'pin_autorizacion': '5678',
            'comentario': 'Venta regular en mostrador'
        })
        self.assertRedirects(response, reverse('catalogo'))

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_retail, 4)

        movimiento = MovimientoInventario.objects.filter(producto=self.producto).first()
        self.assertIsNotNone(movimiento)
        self.assertEqual(movimiento.tipo_movimiento, 'VENTA')
        self.assertEqual(movimiento.cantidad, 2)
        self.assertEqual(movimiento.formato, 'RETAIL')
        self.assertEqual(movimiento.operador, self.operador)

    def test_transaccion_rechazada_por_pin_invalido(self):
        """Verifica el rechazo si el PIN de confirmación es inválido. Parámetros: self."""
        self.client.post(reverse('login'), {'pin': '5678'})
        url = reverse('transaccion_pin', args=[self.producto.id])
        response = self.client.post(url, {
            'accion': 'VENTA',
            'cantidad': 1,
            'pin_autorizacion': '9999',
            'comentario': 'Intento no autorizado'
        })
        self.assertEqual(response.status_code, 200)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_retail, 6)

    def test_transaccion_rechazada_por_stock_insuficiente(self):
        """Verifica el rechazo cuando el stock es insuficiente. Parámetros: self."""
        self.client.post(reverse('login'), {'pin': '5678'})
        url = reverse('transaccion_pin', args=[self.producto.id])
        response = self.client.post(url, {
            'accion': 'VENTA',
            'cantidad': 50,
            'pin_autorizacion': '5678',
            'comentario': 'Intento excesivo'
        })
        self.assertEqual(response.status_code, 200)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_retail, 6)

    def test_paginas_en_construccion(self):
        """Verifica la respuesta en páginas en construcción. Parámetros: self."""
        self.client.post(reverse('login'), {'pin': '5678'})
        for slug in ['cctv', 'mermas', 'multilocal']:
            response = self.client.get(reverse('en_construccion', args=[slug]))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "Volver al Catálogo")

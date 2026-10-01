from django import forms
from .models import Producto, Operador


class LoginForm(forms.Form):
    pin = forms.CharField(
        max_length=10,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input-pin',
            'placeholder': '••••',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autofocus': 'autofocus',
            'autocomplete': 'off',
            'aria-label': 'PIN'
        }),
        label="PIN",
        help_text=""
    )

    def clean_pin(self):
        """Valida el PIN ingresado y asigna el operador autenticado. Parámetros: self."""
        raw_pin = self.cleaned_data.get('pin', '').strip()
        if not raw_pin.isdigit():
            raise forms.ValidationError("El PIN debe contener únicamente dígitos numéricos.")
        
        operadores = Operador.objects.filter(is_active=True)
        operador_encontrado = None
        for op in operadores:
            if op.check_pin(raw_pin):
                operador_encontrado = op
                break
        
        if not operador_encontrado:
            raise forms.ValidationError("PIN incorrecto o el operador no se encuentra activo.")
        
        self.operador_autenticado = operador_encontrado
        return raw_pin


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'codigo_barra',
            'nombre',
            'marca',
            'branch_id',
            'stock_bodega',
            'stock_retail',
            'umbral_minimo',
        ]
        widgets = {
            'codigo_barra': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 7801234567890 o SHAMP-01',
                'required': True,
                'autocomplete': 'off'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Champú Reparador Keratina 1L',
                'required': True
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. L\'Oréal Professionnel / Wella',
                'required': True
            }),
            'branch_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'LOCAL-01',
                'title': 'Identificador de sucursal'
            }),
            'stock_bodega': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'stock_retail': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'value': '0'
            }),
            'umbral_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '5'
            }),
        }
        labels = {
            'codigo_barra': 'Código de barras',
            'nombre': 'Nombre',
            'marca': 'Marca',
            'branch_id': 'Sucursal',
            'stock_bodega': 'Stock bodega',
            'stock_retail': 'Stock retail',
            'umbral_minimo': 'Umbral mínimo',
        }
        help_texts = {
            'stock_bodega': 'Uso interno en salón.',
            'stock_retail': 'Venta directa a clientes.',
            'umbral_minimo': 'Nivel para alerta de stock bajo.',
        }

    def clean_codigo_barra(self):
        """Valida que el código de barra sea único entre productos activos. Parámetros: self."""
        codigo = self.cleaned_data.get('codigo_barra', '').strip().upper()
        qs = Producto.objects.filter(codigo_barra=codigo, is_active=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Ya existe un producto activo registrado con este código.")
        return codigo


class TransaccionPinForm(forms.Form):
    ACCION_CHOICES = [
        ('VENTA', 'Venta (Retail)'),
        ('CONSUMO_INTERNO', 'Consumo interno (Bodega)'),
        ('INGRESO_BODEGA', 'Ingreso a bodega'),
        ('INGRESO_RETAIL', 'Ingreso a retail'),
    ]

    accion = forms.ChoiceField(
        choices=ACCION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control select-accion'}),
        label="Tipo de Operación"
    )
    cantidad = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control input-cantidad',
            'min': '1',
            'value': '1'
        }),
        label="Cantidad a Procesar"
    )
    pin_autorizacion = forms.CharField(
        max_length=10,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control input-pin-confirm',
            'placeholder': 'Ingrese su PIN',
            'inputmode': 'numeric',
            'pattern': '[0-9]*',
            'autocomplete': 'off'
        }),
        label="PIN de confirmación",
        help_text="Ingrese el PIN del operador para confirmar."
    )
    comentario = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Motivo o detalle de la operación...'
        }),
        label="Comentario (opcional)"
    )

    def clean_pin_autorizacion(self):
        """Valida el PIN de confirmación para autorizar la operación. Parámetros: self."""
        pin_ingresado = self.cleaned_data.get('pin_autorizacion', '').strip()
        if not pin_ingresado.isdigit():
            raise forms.ValidationError("El PIN de autorización debe contener dígitos numéricos.")
        
        operadores = Operador.objects.filter(is_active=True)
        operador_autorizado = None
        for op in operadores:
            if op.check_pin(pin_ingresado):
                operador_autorizado = op
                break
        
        if not operador_autorizado:
            raise forms.ValidationError("PIN de autorización incorrecto. Operación rechazada.")
        
        self.operador_autorizado = operador_autorizado
        return pin_ingresado

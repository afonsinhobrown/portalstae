from django import forms
from .models import Equipamento, MovimentacaoEquipamento, CategoriaEquipamento, TipoEquipamento, Armazem
from recursoshumanos.models import Sector

class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = [
            'tipo', 'numero_serie', 'matricula', 'marca', 'modelo',
            'ano_aquisicao', 'fornecedor', 'estado', 'sector_atual',
            'funcionario_responsavel', 'atributos_especificos'
        ]
        widgets = {
            'ano_aquisicao': forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2030}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'fornecedor': forms.TextInput(attrs={'class': 'form-control'}),
            'atributos_especificos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'JSON format'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'NumberInput', 'Select', 'Textarea']:
                field.widget.attrs.setdefault('class', 'form-control')

class MovimentacaoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEquipamento
        fields = ['sector_destino', 'motivo', 'observacoes']
        widgets = {
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'NumberInput', 'Select', 'Textarea']:
                field.widget.attrs.setdefault('class', 'form-control')

class CategoriaEquipamentoForm(forms.ModelForm):
    class Meta:
        model = CategoriaEquipamento
        fields = ['nome', 'codigo', 'descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'NumberInput', 'Select', 'Textarea']:
                field.widget.attrs.setdefault('class', 'form-control')

class ArmazemForm(forms.ModelForm):
    class Meta:
        model = Armazem
        fields = ['sector', 'nome', 'localizacao', 'responsavel', 'capacidade']
        widgets = {
            'localizacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.widget.__class__.__name__ in ['TextInput', 'NumberInput', 'Select', 'Textarea']:
                field.widget.attrs.setdefault('class', 'form-control')
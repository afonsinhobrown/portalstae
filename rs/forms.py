from django import forms
from .models import PlanoLogistico

class PlanoLogisticoForm(forms.ModelForm):
    class Meta:
        model = PlanoLogistico
        fields = ['nome', 'tipo', 'descricao', 'data_inicio', 'data_fim', 'orcamento_total']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}), # Ajustar se não for choices
            'descricao': forms.Textarea(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'orcamento_total': forms.NumberInput(attrs={'class': 'form-control'}),
        }

from .models import TipoDocumento

class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['nome', 'codigo', 'template_html']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Boletim de Voto Autárquicas'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: BOLETIM_AUT_2024'}),
            'template_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Conteúdo ou caminho do template...'}),
        }

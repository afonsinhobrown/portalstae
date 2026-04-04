from django import forms
from .models import (
    FaseEleitoral, RiscoPlaneamento, OrcamentoPlaneamento, 
    NecessidadePessoal, DetalheTerritorial, MarcoCritico
)

class FaseEleitoralForm(forms.ModelForm):
    class Meta:
        model = FaseEleitoral
        fields = ['nome', 'data_inicio', 'data_fim', 'ordem', 'cor_identificacao', 'completada']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Recenseamento'}),
            'cor_identificacao': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class RiscoPlaneamentoForm(forms.ModelForm):
    class Meta:
        model = RiscoPlaneamento
        fields = ['area', 'descricao', 'nivel_probabilidade', 'nivel_impacto', 'plano_mitigacao', 'estado']
        widgets = {
            'area': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'plano_mitigacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nivel_probabilidade': forms.Select(attrs={'class': 'form-select'}),
            'nivel_impacto': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class OrcamentoPlaneamentoForm(forms.ModelForm):
    class Meta:
        model = OrcamentoPlaneamento
        fields = ['categoria', 'valor_previsto', 'valor_executado']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'valor_previsto': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_executado': forms.NumberInput(attrs={'class': 'form-control'}),
        }

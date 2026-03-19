from django import forms
from .models import ResultadoMesa

class ResultadoMesaForm(forms.ModelForm):
    class Meta:
        model = ResultadoMesa
        fields = ['mesa', 'partido', 'votos_validos', 'votos_nulos', 'votos_brancos', 'reclamacoes']
        widgets = {
            'mesa': forms.Select(attrs={'class': 'form-control'}),
            'partido': forms.Select(attrs={'class': 'form-control'}),
            'votos_validos': forms.NumberInput(attrs={'class': 'form-control'}),
            'votos_nulos': forms.NumberInput(attrs={'class': 'form-control'}),
            'votos_brancos': forms.NumberInput(attrs={'class': 'form-control'}),
            'reclamacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

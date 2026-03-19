from django import forms
from .models import Eleicao, EventoEleitoral

class EleicaoForm(forms.ModelForm):
    class Meta:
        model = Eleicao
        fields = ['nome', 'tipo', 'ano', 'data_votacao', 'descricao', 'limite_candidatos', 'vagas_assembleia', 'percentual_apuramento', 'obs_legais']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_votacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'limite_candidatos': forms.NumberInput(attrs={'class': 'form-control'}),
            'vagas_assembleia': forms.NumberInput(attrs={'class': 'form-control'}),
            'percentual_apuramento': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'obs_legais': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EventoForm(forms.ModelForm):
    class Meta:
        model = EventoEleitoral
        fields = ['nome', 'data_inicio', 'data_fim', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Evento'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descrição'}),
        }

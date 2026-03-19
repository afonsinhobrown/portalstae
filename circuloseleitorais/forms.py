from django import forms
from .models import CirculoEleitoral, PostoVotacao

class CirculoForm(forms.ModelForm):
    class Meta:
        model = CirculoEleitoral
        fields = ['eleicao', 'nome', 'codigo', 'provincia', 'num_eleitores', 'num_mandatos', 'num_mesas', 'ativo']
        widgets = {
            'eleicao': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'num_eleitores': forms.NumberInput(attrs={'class': 'form-control'}),
            'num_mandatos': forms.NumberInput(attrs={'class': 'form-control'}),
            'num_mesas': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class PostoForm(forms.ModelForm):
    class Meta:
        model = PostoVotacao
        fields = ['nome', 'codigo', 'endereco', 'num_mesas']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'num_mesas': forms.NumberInput(attrs={'class': 'form-control'}),
        }

from django import forms
from .models import Partido, LiderancaPartido

class PartidoForm(forms.ModelForm):
    class Meta:
        model = Partido
        fields = [
            'sigla', 'nome_completo', 'nome_abreviado',
            'numero_registo', 'data_fundacao', 'data_registo',
            'presidente', 'secretario_geral',
            'simbolo', 'cor_primaria', 'cor_secundaria',
            'email', 'telefone', 'website',
            'endereco_sede', 'provincia_sede', 'distrito_sede',
            'estatutos', 'manifesto', 'notas'
        ]
        widgets = {
            'data_fundacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_registo': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cor_primaria': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'cor_secundaria': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'estatutos': forms.FileInput(attrs={'class': 'form-control'}),
            'manifesto': forms.FileInput(attrs={'class': 'form-control'}),
            'notas': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(PartidoForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs['class'] = 'form-control'

class LiderancaForm(forms.ModelForm):
    class Meta:
        model = LiderancaPartido
        fields = ['cargo', 'nome', 'data_inicio', 'data_fim', 'ativo']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

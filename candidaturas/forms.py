from django import forms
from .models import InscricaoPartidoEleicao, ListaCandidatura, Candidato

class InscricaoPartidoForm(forms.ModelForm):
    class Meta:
        model = InscricaoPartidoEleicao
        fields = ['partido', 'eleicao', 'scope_provincia', 'scope_circulo', 'status']
        widgets = {
            'partido': forms.Select(attrs={'class': 'form-control'}),
            'eleicao': forms.Select(attrs={'class': 'form-control'}),
            'scope_provincia': forms.Select(attrs={'class': 'form-control'}),
            'scope_circulo': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

class ListaCandidaturaForm(forms.ModelForm):
    class Meta:
        model = ListaCandidatura
        fields = ['inscricao', 'circulo', 'cargo_disputado']
        widgets = {
            'inscricao': forms.Select(attrs={'class': 'form-control'}),
            'circulo': forms.Select(attrs={'class': 'form-control'}),
            'cargo_disputado': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CandidatoForm(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = ['nome_completo', 'bi_numero', 'numero_eleitor', 'posicao', 'tipo', 'categoria', 'genero', 'data_nascimento', 'foto']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'bi_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_eleitor': forms.TextInput(attrs={'class': 'form-control'}),
            'posicao': forms.NumberInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ImportarListaForm(forms.Form):
    arquivo_csv = forms.FileField(label="Ficheiro CSV da Lista", help_text="Carregamento em massa de candidatos (Layout: Nome, BI, Eleitor, Posicao, Genero...)")

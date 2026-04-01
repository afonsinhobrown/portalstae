from django import forms
from eleicao.models import Eleicao
from .models import PlanoLogistico, CategoriaMaterial, TipoMaterial, MaterialEleitoral, TipoDocumento

class EleicaoForm(forms.ModelForm):
    data_votacao = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    class Meta:
        model = Eleicao
        fields = ['nome', 'tipo', 'ano', 'data_votacao', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Eleições Autárquicas 2028'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2028'}),
            'data_votacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class TipoDocumentoForm(forms.ModelForm):
    class Meta:
        model = TipoDocumento
        fields = ['nome', 'codigo', 'template_html']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Boletim de Voto Autárquicas'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: BOLETIM_AUT_2024'}),
            'template_html': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Conteúdo ou caminho do template...'}),
        }

class CategoriaMaterialForm(forms.ModelForm):
    class Meta:
        model = CategoriaMaterial
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Material Sensível'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Breve descrição da categoria...'}),
        }

class TipoMaterialForm(forms.ModelForm):
    class Meta:
        model = TipoMaterial
        fields = ['categoria', 'nome', 'descricao']
        widgets = {
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Urna de Votação'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Especificações técnicas...'}),
        }

class PlanoLogisticoForm(forms.ModelForm):
    class Meta:
        model = PlanoLogistico
        fields = ['nome', 'tipo_operacao', 'eleicao', 'data_inicio', 'data_fim', 'orcamento_total', 'responsavel', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Planificação Geral 2028'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-control'}),
            'eleicao': forms.Select(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'orcamento_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class MaterialEleitoralForm(forms.ModelForm):
    class Meta:
        model = MaterialEleitoral
        fields = ['plano', 'item', 'tipo_dinamico', 'ano_referencia', 'quantidade_adquirida_referencia', 'preco_unitario_referencia', 'quantidade_existente', 'quantidade_planeada', 'preco_unitario', 'descricao']
        widgets = {
            'plano': forms.Select(attrs={'class': 'form-control'}),
            'item': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Urnas de Votação (Nacional)'}),
            'tipo_dinamico': forms.Select(attrs={'class': 'form-control'}),
            'ano_referencia': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2024'}),
            'quantidade_adquirida_referencia': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantidade_adquirida_referencia'}),
            'preco_unitario_referencia': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_preco_unitario_referencia'}),
            'quantidade_existente': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantidade_existente'}),
            'quantidade_planeada': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantidade_planeada'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_preco_unitario'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

from .models import AlocacaoLogistica

class AlocacaoLogisticaForm(forms.ModelForm):
    class Meta:
        model = AlocacaoLogistica
        fields = ['unidade', 'quantidade_necessaria', 'quantidade_existente']
        widgets = {
            'unidade': forms.Select(attrs={'class': 'form-control'}),
            'quantidade_necessaria': forms.NumberInput(attrs={'class': 'form-control'}),
            'quantidade_existente': forms.NumberInput(attrs={'class': 'form-control'}),
        }

from .models import AtividadePlano

class AtividadePlanoForm(forms.ModelForm):
    class Meta:
        model = AtividadePlano
        fields = ['plano', 'nome', 'tipo_atividade', 'responsaveis', 'envolvidos', 'custo_estimado', 'material_necessario', 'data_prevista', 'descricao']
        widgets = {
            'plano': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Formação de Brigadistas'}),
            'tipo_atividade': forms.Select(attrs={'class': 'form-control'}),
            'responsaveis': forms.TextInput(attrs={'class': 'form-control'}),
            'envolvidos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'custo_estimado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'material_necessario': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'data_prevista': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

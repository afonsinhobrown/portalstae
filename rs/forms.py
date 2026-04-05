from django import forms
from .models import (
    PlanoLogistico, FaseEleitoral, RiscoPlaneamento, OrcamentoPlaneamento, 
    NecessidadePessoal, DetalheTerritorial, MarcoCritico,
    MaterialEleitoral, AtividadePlano, AlocacaoLogistica
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

class MaterialEleitoralForm(forms.ModelForm):
    class Meta:
        model = MaterialEleitoral
        fields = [
            'item', 'tipo_dinamico', 'localizacao_destino', 'quantidade_existente', 'quantidade_planeada', 
            'preco_unitario', 'eleicao_referencia', 'ano_referencia',
            'quantidade_adquirida_referencia', 'preco_unitario_referencia', 'por_distrito'
        ]
        labels = {
            'item': 'Descrição do Item / Material',
            'tipo_dinamico': 'Categoria Logística (Tipo)',
            'localizacao_destino': 'Província / Círculo Alvo (Geografia)',
            'quantidade_existente': 'Quantidade Existente (Stock)',
            'quantidade_planeada': 'Nova Quantidade a Adquirir',
            'preco_unitario': 'Preço Unitário Estimado (MZN)',
            'eleicao_referencia': 'Eleição de Referência (Histórico)',
            'ano_referencia': 'Ano Manual Base',
            'quantidade_adquirida_referencia': 'Qtd. Adquirida na Referência',
            'preco_unitario_referencia': 'Preço Unit. na Referência',
            'por_distrito': 'Cálculo por Distrito?',
        }
        widgets = {
            'item': forms.TextInput(attrs={'id': 'id_item', 'class': 'form-control', 'placeholder': 'Ex: Cabine de Votação'}),
            'tipo_dinamico': forms.Select(attrs={'id': 'id_tipo_dinamico', 'class': 'form-select'}),
            'quantidade_existente': forms.NumberInput(attrs={'id': 'id_qtd_ext', 'class': 'form-control', 'min': 0}),
            'quantidade_planeada': forms.NumberInput(attrs={'id': 'id_qtd_planeada', 'class': 'form-control', 'min': 0}),
            'preco_unitario': forms.NumberInput(attrs={'id': 'id_preco_unitario', 'class': 'form-control', 'step': '0.01'}),
            'eleicao_referencia': forms.Select(attrs={'id': 'id_eleicao_ref', 'class': 'form-select'}),
            'ano_referencia': forms.NumberInput(attrs={'id': 'id_ano_ref', 'class': 'form-control'}),
            'localizacao_destino': forms.Select(attrs={'id': 'id_localizacao_destino', 'class': 'form-select'}, choices=[('', '--- Filtro Provincial ---')] + AlocacaoLogistica.DIRECOES_STAE),
            'quantidade_adquirida_referencia': forms.NumberInput(attrs={'id': 'id_quantidade_adquirida_referencia', 'class': 'form-control'}),
            'preco_unitario_referencia': forms.NumberInput(attrs={'id': 'id_preco_unitario_referencia', 'class': 'form-control', 'step': '0.01'}),
            'por_distrito': forms.CheckboxInput(attrs={'id': 'id_por_distrito', 'class': 'form-check-input'}),
        }

class PlanoLogisticoForm(forms.ModelForm):
    class Meta:
        model = PlanoLogistico
        fields = ['nome', 'tipo_operacao', 'eleicao', 'eleicao_referencia', 'data_inicio', 'data_fim', 'orcamento_total', 'responsavel', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_operacao': forms.Select(attrs={'class': 'form-select'}),
            'eleicao': forms.Select(attrs={'class': 'form-select'}),
            'eleicao_referencia': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'orcamento_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AtividadePlanoForm(forms.ModelForm):
    class Meta:
        model = AtividadePlano
        fields = ['nome', 'descricao', 'data_prevista', 'custo_estimado', 'responsaveis', 'envolvidos', 'tipo_atividade', 'sector_responsavel', 'funcionario_responsavel', 'material_necessario']
        widgets = {
            'nome': forms.TextInput(attrs={'id': 'id_nome', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'id': 'id_descricao', 'class': 'form-control', 'rows': 2}),
            'data_prevista': forms.DateInput(attrs={'id': 'id_data_prevista', 'type': 'date', 'class': 'form-control'}),
            'custo_estimado': forms.NumberInput(attrs={'id': 'id_custo_estimado', 'class': 'form-control'}),
            'responsaveis': forms.Textarea(attrs={'id': 'id_responsaveis', 'class': 'form-control', 'rows': 2, 'placeholder': 'Nomes da Equipa...'}),
            'envolvidos': forms.Textarea(attrs={'id': 'id_envolvidos', 'class': 'form-control', 'rows': 2}),
            'tipo_atividade': forms.Select(attrs={'id': 'id_tipo_atividade', 'class': 'form-select'}),
            'sector_responsavel': forms.Select(attrs={'id': 'id_sector_responsavel', 'class': 'form-select'}),
            'funcionario_responsavel': forms.Select(attrs={'id': 'id_funcionario_responsavel', 'class': 'form-select'}),
            'material_necessario': forms.Textarea(attrs={'id': 'id_material_necessario', 'class': 'form-control', 'rows': 2}),
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

from django import forms
from .models import Concurso, Juri, CadernoEncargos, Proposta, InscricaoConcurso, AcompanhamentoExecucao, Contrato, Fornecedor, ItemCadernoEncargos

class ConcursoForm(forms.ModelForm):
    class Meta:
        model = Concurso
        fields = ['titulo', 'tipo', 'descricao', 'criterio_avaliacao', 'peso_tecnico', 'peso_financeiro', 'data_abertura', 'data_encerramento', 'valor_estimado', 'status', 'documento_anuncio']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Aquisição de Material de Votação'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'criterio_avaliacao': forms.Select(attrs={'class': 'form-control'}),
            'peso_tecnico': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 70'}),
            'peso_financeiro': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 30'}),
            'data_abertura': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_encerramento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'documento_anuncio': forms.FileInput(attrs={'class': 'form-control'}),
        }

class JuriForm(forms.ModelForm):
    class Meta:
        model = Juri
        fields = ['presidente', 'vogal_1', 'secretario', 'data_nomeacao']
        widgets = {
            'presidente': forms.TextInput(attrs={'class': 'form-control', 'list': 'lista_funcionarios', 'placeholder': 'Nome do Presidente (Pesquisar RH)'}),
            'vogal_1': forms.TextInput(attrs={'class': 'form-control', 'list': 'lista_funcionarios', 'placeholder': 'Nome do Vogal (Pesquisar RH)'}),
            'secretario': forms.TextInput(attrs={'class': 'form-control', 'list': 'lista_funcionarios', 'placeholder': 'Nome do Secretário (Pesquisar RH)'}),
            'data_nomeacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class CadernoEncargosForm(forms.ModelForm):
    class Meta:
        model = CadernoEncargos
        fields = ['objeto_concurso', 'especificacoes_tecnicas', 'condicoes_administrativas', 'clausulas_contratuais', 
                  'obrigacoes_contratante', 'obrigacoes_contratado', 'prazo_execucao_dias', 'garantia_exigida', 'documento_pdf']
        widgets = {
            'objeto_concurso': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descreva o objeto do concurso...'}),
            'especificacoes_tecnicas': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detalhes técnicos...'}),
            'condicoes_administrativas': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Critérios, Prazos, Penalidades...'}),
            'clausulas_contratuais': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Disposições legais e regras...'}),
            'obrigacoes_contratante': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'obrigacoes_contratado': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prazo_execucao_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'garantia_exigida': forms.NumberInput(attrs={'class': 'form-control'}),
            'documento_pdf': forms.FileInput(attrs={'class': 'form-control'}),
        }

class PropostaForm(forms.ModelForm):
    # Campo apenas para label e validação base, o 'multiple' é tratado manualmente no HTML
    arquivos_imagem = forms.ImageField(
        label="Digitalização da Proposta (Imagens)",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        required=True,
        help_text="Seleccione as fotografias ou imagens digitalizadas da proposta."
    )

    class Meta:
        model = Proposta
        fields = ['inscricao']
        labels = {
            'inscricao': 'Seleccionar Empresa Inscrita',
        }
        widgets = {
            'inscricao': forms.Select(attrs={'class': 'form-control'}),
        }

class InscricaoConcursoForm(forms.ModelForm):
    comprovativo_pagamento = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    class Meta:
        model = InscricaoConcurso
        fields = ['empresa_nome', 'nuit', 'representante_nome', 'representante_contacto', 'valor_pago', 'comprovativo_pagamento', 'caderno_entregue']
        help_texts = {'comprovativo_pagamento': 'Opcional. Carregue apenas se houver comprovativo externo.'}
        widgets = {
            'empresa_nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da Empresa'}),
            'nuit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'NUIT'}),
            'representante_nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do Representante'}),
            'representante_contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone/Email'}),
            'valor_pago': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Valor da Taxa (MT)'}),
            'comprovativo_pagamento': forms.FileInput(attrs={'class': 'form-control'}),
            'caderno_entregue': forms.CheckboxInput(attrs={'class': 'form-check-input', 'style': 'margin-left:10px;'}),
        }

class AvaliacaoPropostaForm(forms.ModelForm):
    class Meta:
        model = Proposta
        fields = ['pontuacao_tecnica', 'pontuacao_financeira', 'observacoes_juri']
        widgets = {
            'pontuacao_tecnica': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'pontuacao_financeira': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacoes_juri': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class AnuncioForm(forms.ModelForm):
    class Meta:
        model = Concurso
        fields = ['local_entrega', 'preco_caderno', 'texto_anuncio']
        widgets = {
            'local_entrega': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_caderno': forms.NumberInput(attrs={'class': 'form-control'}),
            'texto_anuncio': forms.Textarea(attrs={'class': 'form-control', 'rows': 15}),
        }

# --- Novos Formulários de Gestão Centralizada ---

class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'nuit', 'email', 'telefone', 'endereco', 'categoria', 'banco', 'nib', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'nuit': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'banco': forms.TextInput(attrs={'class': 'form-control'}),
            'nib': forms.TextInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class ContratoForm(forms.ModelForm):
    class Meta:
        model = Contrato
        fields = ['numero_contrato', 'sector', 'tipo_servico', 'preco_unitario', 'data_inicio', 'data_fim', 'valor_total', 'documento', 'ativo']
        widgets = {
            'numero_contrato': forms.TextInput(attrs={'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-control'}),
            'tipo_servico': forms.TextInput(attrs={'class': 'form-control'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'valor_total': forms.NumberInput(attrs={'class': 'form-control'}),
            'documento': forms.FileInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from django.forms import inlineformset_factory
from .models import ItemContrato

class ItemContratoForm(forms.ModelForm):
    class Meta:
        model = ItemContrato
        fields = ['descricao', 'preco_unitario']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Gasolina, Manutenção Geral'}),
            'preco_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Inline Formset para Itens no Contrato
# extra=1 permite adicionar 1 novo item, can_delete=True permite remover existentes
ItemContratoFormSet = inlineformset_factory(
    Contrato, ItemContrato, form=ItemContratoForm,
    extra=1, can_delete=True
)

class ItemCadernoEncargosForm(forms.ModelForm):
    class Meta:
        model = ItemCadernoEncargos
        fields = ['descricao', 'quantidade_estimada', 'unidade']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Fornecimento de Gasolina'}),
            'quantidade_estimada': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Litros, Meses'}),
        }

ItemCadernoEncargosFormSet = inlineformset_factory(
    CadernoEncargos, ItemCadernoEncargos, form=ItemCadernoEncargosForm,
    extra=1, can_delete=True
)

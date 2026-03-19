from django import forms
from django.core.exceptions import ValidationError
from datetime import date
import json

# IMPORTE TODOS OS MODELOS NECESSÁRIOS
from .models import (
    Solicitante,
    PedidoCredencial,
    CredencialEmitida,
    TipoCredencial,
    Evento,
    ModeloCredencial,
    CredencialFuncionario,
    ConfiguracaoEmergencia,
    BeneficiarioPedido
)


class SolicitanteForm(forms.ModelForm):
    class Meta:
        model = Solicitante
        fields = [
            'numero_identificacao',
            'tipo',
            'nome_completo',
            'genero',
            'nacionalidade',
            'numero_bi',
            'data_validade_bi',  # ← CORREÇÃO: este existe!
            'nif',
            'nup',
            'nome_empresa',  # ← CORREÇÃO: em vez de nome_colectivo
            'numero_registo_comercial',  # ← CORREÇÃO: em vez de numero_registo
            'nif_empresa',
            'documento_identificacao',
            'email',
            'telefone',
            'endereco',
            'provincia',
            'distrito',
            'foto'
        ]
        widgets = {
            'data_validade_bi': forms.DateInput(attrs={'type': 'date'}),
            'endereco': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_numero_bi(self):
        numero_bi = self.cleaned_data.get('numero_bi')
        if numero_bi:
            if Solicitante.objects.filter(numero_bi=numero_bi).exclude(id=self.instance.id).exists():
                raise ValidationError("Já existe um solicitante com este número de BI.")
        return numero_bi

    def clean_nif(self):
        nif = self.cleaned_data.get('nif')
        if nif:
            if Solicitante.objects.filter(nif=nif).exclude(id=self.instance.id).exists():
                raise ValidationError("Já existe um solicitante com este NIF.")
        return nif


class TipoCredencialForm(forms.ModelForm):
    class Meta:
        model = TipoCredencial
        fields = ['nome', 'descricao', 'cor', 'ordem', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Imprensa, Observador...'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descrição curta do tipo...'}),
            'cor': forms.TextInput(attrs={'class': 'form-control', 'type': 'color', 'style': 'height: 38px;'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }



class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ['nome', 'categoria', 'descricao', 'data_inicio', 'data_fim', 'abrangencia', 'provincia', 'local', 'limite_participantes', 'permite_pedidos_remotos', 'ativo', 'logotipo']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control', 'id': 'id_categoria'}),
            'abrangencia': forms.Select(attrs={'class': 'form-control', 'id': 'id_abrangencia'}),
            'provincia': forms.Select(attrs={'class': 'form-control', 'id': 'id_provincia'}),
            'local': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_local'}),
            'limite_participantes': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class BeneficiarioPedidoForm(forms.ModelForm):
    class Meta:
        model = BeneficiarioPedido
        fields = ['nome_completo', 'numero_bi', 'cargo_funcao', 'foto']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_bi': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo_funcao': forms.TextInput(attrs={'class': 'form-control'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
        }

BeneficiarioFormSet = forms.inlineformset_factory(
    PedidoCredencial, BeneficiarioPedido,
    form=BeneficiarioPedidoForm,
    extra=1,
    can_delete=True
)

class PedidoCredencialForm(forms.ModelForm):
    class Meta:
        model = PedidoCredencial
        fields = [
            'solicitante', 'tipo_credencial', 'evento', 'abrangencia', 
            'provicia_abrangencia', 'motivo', 'data_inicio', 'data_fim',
            'carta_solicitacao', 'copia_identificacao', 'quantidade'
        ]
        widgets = {
            'solicitante': forms.Select(attrs={'class': 'form-control select2'}),
            'tipo_credencial': forms.Select(attrs={'class': 'form-control'}),
            'evento': forms.Select(attrs={'class': 'form-control'}),
            'abrangencia': forms.Select(attrs={'class': 'form-control'}),
            'provicia_abrangencia': forms.Select(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'carta_solicitacao': forms.FileInput(attrs={'class': 'form-control'}),
            'copia_identificacao': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Garantir que existam tipos de credencial (Seeding de emergência)
        if not TipoCredencial.objects.exists():
            tipos = [
                {'nome': 'Acesso Geral', 'cor': '#6c757d', 'ordem': 10},
                {'nome': 'Imprensa', 'cor': '#17a2b8', 'ordem': 1},
                {'nome': 'Observador Nacional', 'cor': '#28a745', 'ordem': 2},
                {'nome': 'Observador Internacional', 'cor': '#fd7e14', 'ordem': 3},
                {'nome': 'Delegado de Candidatura', 'cor': '#007bff', 'ordem': 4},
                {'nome': 'VIP / Convidado', 'cor': '#6f42c1', 'ordem': 5},
                {'nome': 'Staff / Técnico', 'cor': '#343a40', 'ordem': 6},
            ]
            for t in tipos:
                TipoCredencial.objects.get_or_create(
                    nome=t['nome'], 
                    defaults={'cor': t['cor'], 'ordem': t['ordem'], 'ativo': True}
                )

        self.fields['evento'].required = True
        self.fields['tipo_credencial'].queryset = TipoCredencial.objects.filter(ativo=True)
        self.fields['evento'].queryset = Evento.objects.filter(ativo=True)


class PedidoRemotoForm(forms.ModelForm):
    # Campos para criar solicitante
    nome_completo = forms.CharField(max_length=200)
    email = forms.EmailField()
    telefone = forms.CharField(max_length=20)
    nacionalidade = forms.CharField(max_length=100, initial="Moçambicana")
    numero_bi = forms.CharField(max_length=20, required=False)

    class Meta:
        model = PedidoCredencial
        # ⬇⬇⬇ USE CAMPOS REAIS ⬇⬇⬇
        fields = [
            'tipo_credencial',
            'evento',
            'data_inicio',  # ← CORRETO (não data_evento)
            'motivo',  # ← CORRETO (não justificativa)
            'quantidade',
            'observacoes_analise'
            # REMOVA: area_atuacao, carta_solicitacao, outros_documentos, foto_pedido
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Descreva a justificativa para o pedido de credencial...'}),
            'observacoes_analise': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Garantir que existam tipos de credencial (Seeding de emergência)
        if not TipoCredencial.objects.exists():
            tipos = [
                {'nome': 'Acesso Geral', 'cor': '#6c757d', 'ordem': 10},
                {'nome': 'Imprensa', 'cor': '#17a2b8', 'ordem': 1},
                {'nome': 'Observador Nacional', 'cor': '#28a745', 'ordem': 2},
                {'nome': 'Observador Internacional', 'cor': '#fd7e14', 'ordem': 3},
                {'nome': 'Delegado de Candidatura', 'cor': '#007bff', 'ordem': 4},
                {'nome': 'VIP / Convidado', 'cor': '#6f42c1', 'ordem': 5},
                {'nome': 'Staff / Técnico', 'cor': '#343a40', 'ordem': 6},
            ]
            for t in tipos:
                TipoCredencial.objects.get_or_create(
                    nome=t['nome'], 
                    defaults={'cor': t['cor'], 'ordem': t['ordem'], 'ativo': True}
                )

        self.fields['tipo_credencial'].queryset = TipoCredencial.objects.filter(ativo=True)
        self.fields['evento'].queryset = Evento.objects.filter(ativo=True, permite_pedidos_remotos=True)

    def clean_data_inicio(self):  # ← MUDAR NOME TAMBÉM
        data_inicio = self.cleaned_data.get('data_inicio')
        if data_inicio and data_inicio < date.today():
            raise ValidationError("A data do evento não pode ser no passado.")
        return data_inicio


class AnalisePedidoForm(forms.ModelForm):
    class Meta:
        model = PedidoCredencial
        fields = ['status', 'observacoes_analise']
        widgets = {
            'observacoes_analise': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Observações sobre a análise do pedido...'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class EmitirCredencialForm(forms.ModelForm):
    """Formulário para emissão de credencial"""

    class Meta:
        model = CredencialEmitida
        fields = ['modelo']
        widgets = {
            'modelo': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas modelos ativos
        self.fields['modelo'].queryset = ModeloCredencial.objects.filter(ativo=True)
        self.fields['modelo'].empty_label = "-- Selecione um modelo --"

    def clean_modelo(self):
        modelo = self.cleaned_data.get('modelo')
        if not modelo:
            raise forms.ValidationError("É necessário selecionar um modelo de credencial.")
        return modelo



class CredencialFuncionarioForm(forms.ModelForm):
    class Meta:
        model = CredencialFuncionario
        fields = ['funcionario', 'tipo_credencial', 'modelo', 'data_validade']
        widgets = {
            'funcionario': forms.Select(attrs={'class': 'form-control'}),
            'tipo_credencial': forms.Select(attrs={'class': 'form-control'}),
            'modelo': forms.Select(attrs={'class': 'form-control'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar opções
        self.fields['tipo_credencial'].queryset = TipoCredencial.objects.filter(ativo=True)
        self.fields['modelo'].queryset = ModeloCredencial.objects.filter(ativo=True)

    def clean_data_validade(self):
        data_validade = self.cleaned_data.get('data_validade')
        if data_validade and data_validade <= date.today():
            raise ValidationError("A data de validade deve ser futura.")
        return data_validade


class VerificacaoOfflineForm(forms.Form):
    codigo_offline = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o código offline (ex: STAE001-AB12CD34)',
            'class': 'form-control form-control-lg',
            'autocomplete': 'off'
        })
    )
    latitude = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    longitude = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )


class EmergenciaBloqueioForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoEmergencia
        fields = ['nome', 'tipo_bloqueio', 'evento', 'provincia', 'tipo_credencial', 'motivo']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 3}),
            'tipo_bloqueio': forms.Select(attrs={'id': 'id_tipo_bloqueio'}),
            'evento': forms.Select(attrs={'class': 'campo-condicional', 'data-tipo': 'evento'}),
            'provincia': forms.TextInput(attrs={'class': 'campo-condicional', 'data-tipo': 'provincia'}),
            'tipo_credencial': forms.Select(attrs={'class': 'campo-condicional', 'data-tipo': 'tipo_credencial'}),
        }


class BuscaSolicitanteForm(forms.Form):
    q = forms.CharField(required=False, label='Pesquisar', widget=forms.TextInput(attrs={
        'placeholder': 'Nome, email, BI ou NIF...',
        'class': 'form-control'
    }))
    tipo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os tipos')] + Solicitante.tipo.field.choices,  # ← CORRETO
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FiltroPedidosForm(forms.Form):
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos os status')] + PedidoCredencial.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tipo_credencial = forms.ModelChoiceField(
        required=False,
        queryset=TipoCredencial.objects.filter(ativo=True),
        empty_label="Todos os tipos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class VerificacaoCredencialForm(forms.Form):
    codigo_verificacao = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'placeholder': 'Digite o código de verificação...',
            'class': 'form-control',
            'autocomplete': 'off'
        })
    )
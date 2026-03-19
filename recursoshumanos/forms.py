from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    Funcionario, Sector, Licenca,
    AvaliacaoDesempenho, Promocao, SaldoFerias,
    PedidoFerias, Competencia, CompetenciaAvaliada,
    CanalComunicacao, Mensagem, DocumentoInstitucional,
    RelatorioAtividade, NotificacaoSistema, ConfiguracaoNotificacao
)
import base64
from datetime import date, timedelta
from django.utils import timezone


# ========== FORMULÁRIO DE FUNCIONÁRIO ==========
class FuncionarioForm(forms.ModelForm):
    foto_webcam = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        label=""
    )

    class Meta:
        model = Funcionario
        fields = [
            'nome_completo',
            'data_nascimento',
            'genero',
            'estado_civil',
            'numero_bi',
            'data_emissao_bi',
            'local_emissao_bi',
            'nuit',
            'data_emissao_nuit',
            'niss',
            'data_inscricao_inss',
            'sector',
            'funcao',
            'data_admissao',
            'telefone',
            'telefone_alternativo',
            'email_pessoal',
            'email_institucional',
            'endereco',
            'bairro',
            'distrito',
            'provincia',
            'banco',
            'nome_banco_outro',
            'tipo_conta',
            'numero_conta',
            'nib',
            'nub',
            'foto',
            'data_emissao_cartao',
            'data_validade_cartao',
            'nacionalidade',
            'naturalidade',
            'nome_pai',
            'nome_mae',
            'contacto_emergencia',
            'parentesco_emergencia',
        ]

        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_emissao_bi': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_emissao_nuit': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_inscricao_inss': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_emissao_cartao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_validade_cartao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome_completo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'nuit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '9-12 dígitos'}),
            'niss': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da Segurança Social'}),
            'numero_bi': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Número do Bilhete de Identidade'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+258 8X XXX XXXX'}),
            'telefone_alternativo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Telefone alternativo'}),
            'email_pessoal': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'email.pessoal@exemplo.com'}),
            'email_institucional': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nome@stae.gov.mz'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'distrito': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Distrito'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Província'}),
            'numero_conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da conta bancária'}),
            'nib': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Identificação Bancária'}),
            'nub': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número Único Bancário'}),
            'foto': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'sector': forms.Select(attrs={'class': 'form-select'}),
            'funcao': forms.Select(attrs={'class': 'form-select'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'estado_civil': forms.Select(attrs={'class': 'form-select'}),
            'banco': forms.Select(attrs={'class': 'form-select'}),
            'tipo_conta': forms.Select(attrs={'class': 'form-select'}),
            'nacionalidade': forms.TextInput(attrs={'class': 'form-control', 'value': 'Moçambicana'}),
            'naturalidade': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Cidade/Província de nascimento'}),
            'nome_pai': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo do pai'}),
            'nome_mae': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo da mãe'}),
            'contacto_emergencia': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Telefone de emergência'}),
            'parentesco_emergencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Parentesco'}),
            'local_emissao_bi': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Local onde foi emitido o BI'}),
            'nome_banco_outro': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Especifique o nome do banco'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campos_obrigatorios = [
            'nome_completo', 'data_nascimento', 'genero', 'estado_civil',
            'nuit', 'niss', 'sector', 'funcao', 'data_admissao',
            'telefone', 'endereco', 'banco', 'tipo_conta', 'numero_conta', 'nib'
        ]

        for campo in campos_obrigatorios:
            if campo in self.fields:
                self.fields[campo].required = True

        if not self.instance.pk:
            hoje = date.today()
            dois_anos = date(hoje.year + 2, hoje.month, hoje.day)
            self.initial['data_validade_cartao'] = dois_anos
            self.initial['data_emissao_cartao'] = hoje
            self.initial['nacionalidade'] = 'Moçambicana'

    def clean_nuit(self):
        nuit = self.cleaned_data.get('nuit')
        if nuit:
            if not nuit.isdigit():
                raise ValidationError("NUIT deve conter apenas números.")
            if len(nuit) < 9 or len(nuit) > 12:
                raise ValidationError("NUIT deve ter entre 9 e 12 dígitos.")
        return nuit

    def clean_niss(self):
        niss = self.cleaned_data.get('niss')
        if niss and not niss.isdigit():
            raise ValidationError("NISS deve conter apenas números.")
        return niss

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            telefone = ''.join(filter(str.isdigit, telefone))
            if len(telefone) < 9:
                raise ValidationError("Número de telefone inválido.")
        return telefone

    def clean_banco(self):
        banco = self.cleaned_data.get('banco')
        nome_banco_outro = self.cleaned_data.get('nome_banco_outro')
        if banco == 'outro' and not nome_banco_outro:
            raise ValidationError("Por favor, especifique o nome do banco.")
        return banco

    def save(self, commit=True):
        instance = super().save(commit=False)

        foto_webcam = self.cleaned_data.get('foto_webcam')
        if foto_webcam and 'data:image' in foto_webcam:
            try:
                format, imgstr = foto_webcam.split(';base64,')
                ext = format.split('/')[-1]
                from django.core.files.base import ContentFile
                data = ContentFile(base64.b64decode(imgstr), name=f'webcam_{instance.nuit}.{ext}')
                if not instance.foto:
                    instance.foto = data
            except Exception:
                pass

        if commit:
            instance.save()
            self.save_m2m()

        return instance


# ========== FORMULÁRIO DE PEDIDO DE FÉRIAS (CRÍTICO) ==========
class PedidoFeriasForm(forms.ModelForm):
    class Meta:
        model = PedidoFerias
        fields = ['data_inicio', 'data_fim', 'dias_solicitados', 'observacao',
                  'local_ferias', 'contacto_emergencia']

        widgets = {
            'data_inicio': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'data_fim': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True
            }),
            'dias_solicitados': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 30,
                'placeholder': 'Dias que deseja tirar'
            }),
            'observacao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observações sobre suas férias'
            }),
            'local_ferias': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Onde pretende passar as férias?'
            }),
            'contacto_emergencia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Contacto em caso de emergência'
            }),
        }

        labels = {
            'data_inicio': 'Data de Início das Férias',
            'data_fim': 'Data de Término das Férias',
            'dias_solicitados': 'Quantidade de Dias',
            'observacao': 'Observações',
            'local_ferias': 'Local das Férias',
            'contacto_emergencia': 'Contacto de Emergência',
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')
        dias_solicitados = cleaned_data.get('dias_solicitados')

        if data_inicio and data_fim:
            if data_fim < data_inicio:
                raise ValidationError("A data de término deve ser posterior à data de início.")

            if data_inicio < date.today():
                raise ValidationError("Não pode solicitar férias com data retroativa.")

            dias_reais = (data_fim - data_inicio).days + 1

            if dias_solicitados:
                if dias_solicitados != dias_reais:
                    raise ValidationError(
                        f"Dias solicitados ({dias_solicitados}) não correspondem ao período ({dias_reais} dias).")
            else:
                cleaned_data['dias_solicitados'] = dias_reais

        if dias_solicitados and dias_solicitados > 30:
            raise ValidationError("Não é possível solicitar mais de 30 dias de férias de uma vez.")

        if dias_solicitados and dias_solicitados < 5:
            raise ValidationError("Mínimo de 5 dias para férias.")

        return cleaned_data


# ========== FORMULÁRIO DE LICENÇA ==========
class LicencaForm(forms.ModelForm):
    class Meta:
        model = Licenca
        fields = ['tipo', 'data_inicio', 'data_fim', 'motivo', 'local_ferias', 'contacto_emergencia']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'local_ferias': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        data_fim = cleaned_data.get('data_fim')

        if data_inicio and data_fim:
            if data_fim < data_inicio:
                raise ValidationError("Data de término deve ser posterior à data de início.")

            if data_inicio < date.today():
                raise ValidationError("Não pode solicitar licença com data retroativa.")

        return cleaned_data


# ========== FORMULÁRIO DE AVALIAÇÃO ==========
class AvaliacaoDesempenhoForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoDesempenho
        fields = ['periodo', 'observacoes', 'pontos_fortes', 'areas_melhoria']
        widgets = {
            'periodo': forms.TextInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pontos_fortes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'areas_melhoria': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ========== FORMULÁRIO DE PROMOÇÃO ==========
class PromocaoForm(forms.ModelForm):
    class Meta:
        model = Promocao
        fields = ['data_promocao', 'cargo_atual', 'nivel_atual', 'salario_atual', 'motivo', 'observacoes']
        widgets = {
            'data_promocao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cargo_atual': forms.TextInput(attrs={'class': 'form-control'}),
            'nivel_atual': forms.TextInput(attrs={'class': 'form-control'}),
            'salario_atual': forms.NumberInput(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ========== FORMULÁRIO DE SETOR ==========
class SectorForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ['codigo', 'nome', 'descricao', 'direcao', 'chefe']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'direcao': forms.Select(attrs={'class': 'form-select'}),
            'chefe': forms.Select(attrs={'class': 'form-select'}),
        }


# ========== FORMULÁRIO DE SALDO DE FÉRIAS ==========
class SaldoFeriasForm(forms.ModelForm):
    class Meta:
        model = SaldoFerias
        fields = ['ano', 'dias_disponiveis', 'dias_gozados']
        widgets = {
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_disponiveis': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_gozados': forms.NumberInput(attrs={'class': 'form-control'}),
        }


# ========== FORMULÁRIO DE COMPETÊNCIA ==========
class CompetenciaForm(forms.ModelForm):
    class Meta:
        model = Competencia
        fields = ['nome', 'descricao', 'peso']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


# ========== FORMULÁRIO DE COMPETÊNCIA AVALIADA ==========
class CompetenciaAvaliadaForm(forms.ModelForm):
    class Meta:
        model = CompetenciaAvaliada
        fields = ['competencia', 'pontuacao', 'observacao']
        widgets = {
            'competencia': forms.HiddenInput(),
            'pontuacao': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


# ========== FORMULÁRIO DE CANAL DE COMUNICAÇÃO ==========
class CanalComunicacaoForm(forms.ModelForm):
    class Meta:
        model = CanalComunicacao
        fields = ['nome', 'descricao', 'tipo', 'enviar_para_todos']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'enviar_para_todos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ========== FORMULÁRIO DE MENSAGEM ==========
class MensagemForm(forms.ModelForm):
    arquivo = forms.FileField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Mensagem
        fields = ['conteudo', 'arquivo']
        widgets = {
            'conteudo': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Digite sua mensagem...'}),
        }


# ========== FORMULÁRIO DE DOCUMENTO INSTITUCIONAL ==========
class DocumentoInstitucionalForm(forms.ModelForm):
    class Meta:
        model = DocumentoInstitucional
        fields = ['tipo', 'titulo', 'descricao', 'data_documento', 'classificacao', 'publico']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'data_documento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'classificacao': forms.Select(attrs={'class': 'form-select'}),
            'publico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ========== FORMULÁRIO DE RELATÓRIO DE ATIVIDADE ==========
class RelatorioAtividadeForm(forms.ModelForm):
    class Meta:
        model = RelatorioAtividade
        fields = ['titulo', 'tipo', 'descricao', 'periodo_inicio', 'periodo_fim',
                  'atividades_realizadas', 'resultados', 'dificuldades', 'recomendacoes', 'publico']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'periodo_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periodo_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'atividades_realizadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'resultados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'dificuldades': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'recomendacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'publico': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ========== FORMULÁRIO DE CONFIGURAÇÃO DE NOTIFICAÇÃO ==========
class ConfiguracaoNotificacaoForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoNotificacao
        fields = ['mostrar_licencas', 'mostrar_avaliacoes', 'mostrar_documentos',
                  'mostrar_mensagens', 'mostrar_sistema', 'som_notificacoes']
        widgets = {
            'mostrar_licencas': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_avaliacoes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_documentos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_mensagens': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mostrar_sistema': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'som_notificacoes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# ========== FORMULÁRIOS DE FILTRO E PESQUISA ==========
class FiltroLicencaForm(forms.Form):
    tipo = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + Licenca.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + Licenca.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    ano = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ano'})
    )


class FiltroFuncionarioForm(forms.Form):
    setor = forms.ModelChoiceField(
        queryset=Sector.objects.all(),
        required=False,
        empty_label="Todos os setores",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos'), ('ativos', 'Ativos'), ('inativos', 'Inativos')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    funcao = forms.ChoiceField(
        choices=[('', 'Todas funções')] + Funcionario.FUNCAO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# ========== FORMULÁRIO DE PAREÇER DO CHEFE ==========
class ParecerChefeForm(forms.Form):
    parecer = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
        label="Parecer"
    )

    decisao = forms.ChoiceField(
        choices=[('aprovar', 'Aprovar'), ('rejeitar', 'Rejeitar')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Decisão"
    )


# ========== FORMULÁRIO DE PAREÇER DO DIRETOR ==========
class ParecerDiretorForm(forms.Form):
    parecer = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': True}),
        label="Parecer/Autorização"
    )

    decisao = forms.ChoiceField(
        choices=[('autorizar', 'Autorizar'), ('reprovar', 'Reprovar')],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label="Decisão Final"
    )


# ========== FORMULÁRIO DE LOGIN PERSONALIZADO ==========
class RHAuthenticationForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Usuário'})
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Senha'})
    )
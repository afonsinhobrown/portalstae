from django import forms
from .models import Funcionario, Sector, Licenca, AvaliacaoDesempenho, Promocao, SaldoFerias
import base64
from datetime import date


class FuncionarioForm(forms.ModelForm):
    foto_webcam = forms.CharField(
        widget=forms.HiddenInput(),
        required=False,
        label=""
    )

    class Meta:
        model = Funcionario
        # NÃO INCLUIR numero_identificacao - será gerado automaticamente
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
            'nuit': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '9-12 dígitos', 'pattern': '[0-9]{9,12}'}),
            'niss': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da Segurança Social'}),
            'numero_bi': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Número do Bilhete de Identidade'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+258 8X XXX XXXX'}),
            'telefone_alternativo': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Telefone alternativo (opcional)'}),
            'email_pessoal': forms.EmailInput(
                attrs={'class': 'form-control', 'placeholder': 'email.pessoal@exemplo.com'}),
            'email_institucional': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'nome@stae.gov.mz'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'distrito': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Distrito'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Província'}),
            'numero_conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número da conta bancária'}),
            'nib': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número de Identificação Bancária'}),
            'nub': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Número Único Bancário (opcional)'}),
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
            'parentesco_emergencia': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Parentesco (ex: Pai, Mãe, Irmão)'}),
            'local_emissao_bi': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Local onde foi emitido o BI'}),
            'nome_banco_outro': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Especifique o nome do banco'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Definir campos obrigatórios
        campos_obrigatorios = [
            'nome_completo',
            'data_nascimento',
            'genero',
            'estado_civil',
            'nuit',
            'niss',
            'sector',
            'funcao',
            'data_admissao',
            'telefone',
            'endereco',
            'banco',
            'tipo_conta',
            'numero_conta',
            'nib',
        ]

        for field in campos_obrigatorios:
            if field in self.fields:
                self.fields[field].required = True

        # Campos não obrigatórios
        campos_opcionais = [
            'numero_bi',
            'telefone_alternativo',
            'email_pessoal',
            'email_institucional',
            'nub',
            'foto',
            'nome_banco_outro',
            'bairro',
            'distrito',
            'provincia',
            'data_emissao_bi',
            'data_emissao_nuit',
            'data_inscricao_inss',
            'local_emissao_bi',
            'nacionalidade',
            'naturalidade',
            'nome_pai',
            'nome_mae',
            'contacto_emergencia',
            'parentesco_emergencia',
            'data_emissao_cartao',
            'data_validade_cartao',
        ]

        for field in campos_opcionais:
            if field in self.fields:
                self.fields[field].required = False

        # Definir data de validade padrão (2 anos a partir de hoje)
        if not self.instance.pk:  # Apenas para novos registros
            hoje = date.today()
            dois_anos = date(hoje.year + 2, hoje.month, hoje.day)
            self.initial['data_validade_cartao'] = dois_anos
            self.initial['data_emissao_cartao'] = hoje

        # Definir nacionalidade padrão
        self.initial['nacionalidade'] = 'Moçambicana'

    def clean_nuit(self):
        nuit = self.cleaned_data.get('nuit')
        if nuit:
            # Validar formato NUIT (9-12 dígitos)
            if not nuit.isdigit():
                raise forms.ValidationError("NUIT deve conter apenas números.")
            if len(nuit) < 9 or len(nuit) > 12:
                raise forms.ValidationError("NUIT deve ter entre 9 e 12 dígitos.")
        return nuit

    def clean_niss(self):
        niss = self.cleaned_data.get('niss')
        if niss and not niss.isdigit():
            raise forms.ValidationError("NISS deve conter apenas números.")
        return niss

    def clean_nib(self):
        nib = self.cleaned_data.get('nib')
        if nib and not nib.isdigit():
            raise forms.ValidationError("NIB deve conter apenas números.")
        return nib

    def clean_telefone(self):
        telefone = self.cleaned_data.get('telefone')
        if telefone:
            # Remover espaços e caracteres especiais
            telefone = ''.join(filter(str.isdigit, telefone))
            if len(telefone) < 9:
                raise forms.ValidationError("Número de telefone inválido.")
        return telefone

    def clean_banco(self):
        banco = self.cleaned_data.get('banco')
        nome_banco_outro = self.cleaned_data.get('nome_banco_outro')

        if banco == 'outro' and not nome_banco_outro:
            raise forms.ValidationError("Por favor, especifique o nome do banco.")

        return banco

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Processar foto da webcam
        foto_webcam = self.cleaned_data.get('foto_webcam')
        if foto_webcam and 'data:image' in foto_webcam:
            try:
                format, imgstr = foto_webcam.split(';base64,')
                ext = format.split('/')[-1]

                from django.core.files.base import ContentFile
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'webcam_{instance.nuit}.{ext}'
                )

                if not instance.foto:  # Só salva se não tiver foto já
                    instance.foto = data
            except Exception as e:
                print(f"Erro ao processar foto webcam: {str(e)}")

        if commit:
            instance.save()
            self.save_m2m()

        return instance


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


class SaldoFeriasForm(forms.ModelForm):
    class Meta:
        model = SaldoFerias
        fields = ['ano', 'dias_disponiveis', 'dias_gozados']
        widgets = {
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_disponiveis': forms.NumberInput(attrs={'class': 'form-control'}),
            'dias_gozados': forms.NumberInput(attrs={'class': 'form-control'}),
        }
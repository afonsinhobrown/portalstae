# dfec/forms.py - VERSÃO FINAL CORRIGIDA
from django import forms
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

# Importe CORRETO - importa TUDO do modelo
from .models import *
from .models.completo import (
    ManualCompleto, PlanoAtividade, Formacao, Participante, 
    Turma, Brigada, Eleicao, Manual, CapituloManual, 
    ComentarioManual, ImagemManual, ObjetivoInstitucional, Atividade
)


# ========== MÓDULO 1: PLANIFICAÇÃO ==========

class ObjetivoInstitucionalForm(forms.ModelForm):
    class Meta:
        model = ObjetivoInstitucional
        fields = ['ano', 'titulo', 'descricao', 'ativo']
        widgets = {
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Melhorar a Eficiência na Educação Cívica'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PlanoAtividadeForm(forms.ModelForm):
    class Meta:
        model = PlanoAtividade
        fields = ['nome', 'objetivo_institucional', 'nivel', 'provincia', 'plano_pai',
                  'tipo', 'descricao', 'objetivos_especificos', 'status',
                  'data_inicio_planeada', 'data_fim_planeada',
                  'orcamento_planeado', 'responsavel_principal', 'extensao_possivel']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do plano'}),
            'objetivo_institucional': forms.Select(attrs={'class': 'form-select'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'plano_pai': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('EDUCACAO_CIVICA', 'Educação Cívica'),
                ('FORMACAO', 'Formação'),
                ('OPERACIONAL', 'Operacional'),
                ('OUTRO', 'Outro')
            ]),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Descrição básica'}),
            'objetivos_especificos': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Objetivos específicos para este ano/província'}),
            'status': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('planeado', 'Planeado'),
                ('aprovado', 'Aprovado'),
                ('em_execucao', 'Em Execução'),
                ('concluido', 'Concluído'),
                ('suspenso', 'Suspenso'),
                ('cancelado', 'Cancelado'),
            ]),
            'data_inicio_planeada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim_planeada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'orcamento_planeado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'responsavel_principal': forms.Select(attrs={'class': 'form-select'}),
            'extensao_possivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar planos pai aos nacionais ativos
        self.fields['plano_pai'].queryset = PlanoAtividade.objects.filter(nivel='CENTRAL', ativo=True)
        # Limitar objetivos aos ativos
        self.fields['objetivo_institucional'].queryset = ObjetivoInstitucional.objects.filter(ativo=True)
        
        # Se for um plano provincial, tornar o plano_pai obrigatório se necessário
        # Ou logica JS no template para filtrar sub-atividades later
        
        if 'responsavel_principal' in self.fields:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['responsavel_principal'].queryset = User.objects.filter(is_active=True)


# ========== MÓDULO 2: FORMAÇÕES ==========

class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ['plano', 'objetivo_institucional', 'nome', 'descricao', 
                  'referencia_nacional', 'data_inicio', 'data_fim', 
                  'status', 'orcamento_estimado', 'responsavel']
        widgets = {
            'plano': forms.Select(attrs={'class': 'form-select'}),
            'objetivo_institucional': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'referencia_nacional': forms.Select(attrs={'class': 'form-select'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'orcamento_estimado': forms.NumberInput(attrs={'class': 'form-control'}),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se um plano for passado, filtrar atividades nacionais de referência
        if 'plano' in self.fields:
            self.fields['plano'].queryset = PlanoAtividade.objects.filter(ativo=True)
        
        # Filtro de referências nacionais (atividades que pertencem a planos nacionais)
        self.fields['referencia_nacional'].queryset = Atividade.objects.filter(plano__nivel='CENTRAL')

class FormacaoForm(forms.ModelForm):
    class Meta:
        model = Formacao
        fields = ['atividade', 'nome', 'tipo_formacao', 'nivel', 'provincia', 
                  'local_realizacao', 'vagas_planeadas', 'status', 'responsavel_principal']
        widgets = {
            'atividade': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da formação'}),
            'tipo_formacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tipo de formação'}),
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'local_realizacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Local'}),
            'vagas_planeadas': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}, choices=[
                ('planejada', 'Planejada'),
                ('ativa', 'Ativa'),
                ('concluida', 'Concluída'),
                ('cancelada', 'Cancelada'),
            ]),
            'responsavel_principal': forms.Select(attrs={'class': 'form-select'}),
        }


class FormandoForm(forms.ModelForm):
    class Meta:
        model = Participante
        fields = ['nome_completo', 'categoria', 'bilhete_identidade', 'telefone',
                  'genero', 'provincia', 'distrito', 'data_nascimento']
        widgets = {
            'nome_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'bilhete_identidade': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'genero': forms.Select(attrs={'class': 'form-select'}),
            'provincia': forms.Select(attrs={'class': 'form-select'}),
            'distrito': forms.TextInput(attrs={'class': 'form-control'}),
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = ['nome', 'formacao', 'formador_principal', 'data_inicio', 'data_fim']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'formacao': forms.Select(attrs={'class': 'form-control'}),
            'formador_principal': forms.Select(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }


class BrigadaForm(forms.ModelForm):
    class Meta:
        model = Brigada
        fields = ['codigo', 'formacao', 'provincia', 'distrito', 'localidade',
                  'supervisor', 'digitador', 'entrevistador']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'formacao': forms.Select(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'distrito': forms.TextInput(attrs={'class': 'form-control'}),
            'localidade': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor': forms.Select(attrs={'class': 'form-control'}),
            'digitador': forms.Select(attrs={'class': 'form-control'}),
            'entrevistador': forms.Select(attrs={'class': 'form-control'}),
        }


# ========== MÓDULO 3: ANÁLISE ELEITORAL ==========

class ImportarDadosForm(forms.Form):
    TIPO_ARQUIVO_CHOICES = [
        ('csv', 'CSV (Excel)'),
        ('excel', 'Excel (XLSX)'),
        ('json', 'JSON'),
    ]

    arquivo_dados = forms.FileField(
        label='Arquivo de Dados',
        help_text='Selecione o arquivo com os resultados eleitorais'
    )

    tipo_arquivo = forms.ChoiceField(
        choices=TIPO_ARQUIVO_CHOICES,
        initial='csv',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    eleicao = forms.ModelChoiceField(
        queryset=Eleicao.objects.all(),  # CORRIGIDO: Eleicao em vez de ResultadoEleicao
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AnaliseRegiaoForm(forms.Form):
    TIPO_ANALISE_CHOICES = [
        ('participacao', 'Análise de Participação'),
        ('tendencia', 'Análise de Tendência'),
        ('comparativa', 'Análise Comparativa'),
        ('geral', 'Análise Geral'),
    ]

    regiao = forms.ChoiceField(
        choices=[('provincial', 'Provincial'), ('distrital', 'Distrital')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    eleicao = forms.ModelChoiceField(
        queryset=Eleicao.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    tipo_analise = forms.ChoiceField(
        choices=TIPO_ANALISE_CHOICES,
        initial='participacao',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# ========== MÓDULO 5: MANUAIS ==========

class ManualForm(forms.ModelForm):
    class Meta:
        model = Manual  # Modelo SIMPLES do manual.py
        fields = [
            'titulo', 'codigo', 'descricao', 'tipo', 'versao',
            'status', 'formato_papel', 'ficha_tecnica', 'publicado', 'grupos_permitidos'
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Descrição do manual...'
            }),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'versao': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'formato_papel': forms.Select(attrs={'class': 'form-control'}),
            'ficha_tecnica': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Informações técnicas (Editora, ISBN, etc)'}),
            'publicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grupos_permitidos': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'size': '6'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar grupos por nome
        self.fields['grupos_permitidos'].queryset = Group.objects.order_by('name')

        # Se for edição, mostrar código como readonly
        if self.instance and self.instance.pk:
            self.fields['codigo'].widget.attrs['readonly'] = True

    def clean_codigo(self):
        codigo = self.cleaned_data['codigo']

        if not codigo:
            raise ValidationError("O código é obrigatório.")

        # Verificar se código já existe (exceto para esta instância)
        manual_id = self.instance.id if self.instance else None
        existe = Manual.objects.filter(codigo=codigo).exclude(id=manual_id).exists()

        if existe:
            raise ValidationError(f"Já existe um manual com o código '{codigo}'.")

        return codigo.upper()




class CapituloForm(forms.ModelForm):
    class Meta:
        model = CapituloSimples  # Ou CapituloManual, dependendo do que você está usando
        fields = ['titulo', 'numero', 'ordem', 'conteudo']
        labels = {
            'titulo': 'Título do Capítulo',
            'numero': 'Número do Capítulo',
            'ordem': 'Posição (Index)',
            'conteudo': 'Conteúdo do Capítulo',
        }
        help_texts = {
            'numero': 'Ex: 1, 2 (O n.º que aparece no título)',
            'ordem': 'Ordem na lista (1º, 2º...)',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Manual do Brigadista'
            }),
            'numero': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0'
            }),
            'ordem': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1'
            }),
            'conteudo': forms.Textarea(attrs={
                'rows': 20,
                'class': 'form-control',
                'id': 'id_conteudo',  # IMPORTANTE: ID para o TinyMCE
                'placeholder': 'Digite o conteúdo do capítulo aqui...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adicionar classes CSS aos campos
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'


class ComentarioForm(forms.ModelForm):
    class Meta:
        model = ComentarioManual  # Modelo do manual.py
        fields = ['texto']
        widgets = {
            'texto': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Digite seu comentário aqui...'
            }),
        }

    def clean_texto(self):
        texto = self.cleaned_data['texto']

        if not texto.strip():
            raise ValidationError("O comentário não pode estar vazio.")

        if len(texto) < 10:
            raise ValidationError("O comentário deve ter pelo menos 10 caracteres.")

        return texto.strip()


class UploadImagemForm(forms.ModelForm):
    class Meta:
        model = ImagemManual  # Modelo do manual.py
        fields = ['titulo', 'descricao', 'imagem']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Título da imagem...'
            }),
            'descricao': forms.Textarea(attrs={
                'rows': 2,
                'class': 'form-control',
                'placeholder': 'Descrição da imagem...'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

    def clean_imagem(self):
        imagem = self.cleaned_data.get('imagem')

        if not imagem:
            raise ValidationError("Selecione uma imagem para upload.")

        # Validar tamanho (máximo 5MB)
        tamanho_maximo = 5 * 1024 * 1024  # 5MB em bytes
        if imagem.size > tamanho_maximo:
            raise ValidationError("A imagem não pode ter mais de 5MB.")

        # Validar formato
        formatos_permitidos = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
        formato = imagem.name.split('.')[-1].lower()

        if formato not in formatos_permitidos:
            raise ValidationError(
                f"Formato '{formato}' não permitido. Use: {', '.join(formatos_permitidos)}"
            )

        return imagem


# ========== FORMULÁRIOS ADICIONAIS ==========

class PesquisaManualForm(forms.Form):
    termo = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pesquisar manuais...'
        })
    )

    tipo = forms.ChoiceField(
        choices=[('', 'Todos os tipos')] + list(Manual.TIPO_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos os status')] + list(Manual.STATUS_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class FiltroFormandosForm(forms.Form):
    turma = forms.ModelChoiceField(
        queryset=Turma.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    genero = forms.ChoiceField(
        choices=[('', 'Todos'), ('M', 'Masculino'), ('F', 'Feminino'), ('O', 'Outro')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        formacao_id = kwargs.pop('formacao_id', None)
        super().__init__(*args, **kwargs)

        if formacao_id:
            self.fields['turma'].queryset = Turma.objects.filter(formacao_id=formacao_id)


class ConfiguracaoExportacaoForm(forms.Form):
    FORMATO_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('word', 'Word (DOCX)'),
    ]

    formato = forms.ChoiceField(
        choices=FORMATO_CHOICES,
        initial='pdf',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )

    incluir_cabecalho = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    incluir_rodape = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    qualidade_imagens = forms.ChoiceField(
        choices=[
            ('baixa', 'Baixa (mais rápida)'),
            ('media', 'Média'),
            ('alta', 'Alta (melhor qualidade)'),
        ],
        initial='media',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


# ========== FORMULÁRIOS PARA MANUAL COMPLETO ==========

class ManualCompletoForm(forms.ModelForm):
    class Meta:
        model = ManualCompleto
        fields = ['titulo', 'codigo', 'tipo', 'versao', 'status',
                  'formato', 'autor_principal', 'publico_alvo',
                  'objetivos', 'restrito', 'grupos_permitidos']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'versao': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'formato': forms.Select(attrs={'class': 'form-control'}),
            'autor_principal': forms.Select(attrs={'class': 'form-control'}),
            'publico_alvo': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'objetivos': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'restrito': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'grupos_permitidos': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '6'}),
        }


class CapituloManualForm(forms.ModelForm):
    class Meta:
        model = CapituloManual
        fields = ['titulo', 'numero', 'conteudo_texto', 'ordem']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'conteudo_texto': forms.Textarea(attrs={'rows': 20, 'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control'}),
        }

# No final do dfec/forms.py, adiciona:

class ImpressaoForm(forms.Form):
    """Formulário para solicitar impressão"""
    quantidade = forms.IntegerField(
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Observações para a impressão...'
        })
    )


class ImagemForm(forms.ModelForm):
    """Formulário para upload de imagens"""
    class Meta:
        model = ImagemManual  # OU ImagemManualSimples se usares o modelo simples
        fields = ['titulo', 'descricao', 'imagem', 'tags', 'manual']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
            'manual': forms.Select(attrs={'class': 'form-control'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }
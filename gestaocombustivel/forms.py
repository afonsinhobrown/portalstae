from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import (Viatura, PedidoCombustivel, ManutencaoViatura,
                     SeguroViatura, RotaTransporte, PontoRota, RegistroDiarioRota,
                     FornecedorCombustivel, TIPO_MANUTENCAO_CHOICES)
from recursoshumanos.models import Funcionario


class ViaturaForm(forms.ModelForm):
    class Meta:
        model = Viatura
        fields = [
            'matricula', 'marca', 'modelo', 'ano_fabrico', 'cor',
            'tipo_combustivel', 'tipo_viatura', 'cilindrada', 'capacidade_tanque',
            'kilometragem_actual', 'estado', 'activa', 'disponivel', 'funcionario_afecto',
            'motoristas_autorizados', 'numero_chassi', 'numero_motor',
            'data_ultimo_seguro', 'data_proximo_seguro',
            'data_ultima_inspecao', 'data_proxima_inspecao',
            'proxima_manutencao_km', 'observacoes'
        ]
        widgets = {
            'matricula': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: AB-12-CD'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'ano_fabrico': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900'}),
            'cor': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_combustivel': forms.Select(attrs={'class': 'form-control'}),
            'tipo_viatura': forms.Select(attrs={'class': 'form-control'}),
            'cilindrada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2000cc'}),
            'capacidade_tanque': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'kilometragem_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'disponivel': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'funcionario_afecto': forms.Select(attrs={'class': 'form-control'}),
            'numero_chassi': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': '17 caracteres (opcional)'}),
            'numero_motor': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'data_ultimo_seguro': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proximo_seguro': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'proxima_manutencao_km': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar funcionários activos
        self.fields['funcionario_afecto'].queryset = Funcionario.objects.filter(ativo=True)
        self.fields['motoristas_autorizados'].queryset = Funcionario.objects.filter(ativo=True)

        # Configurar campo motoristas_autorizados
        self.fields['motoristas_autorizados'].widget.attrs.update({'class': 'form-control'})

        # Tornar campos opcionais mais claros
        optional_fields = ['ano_fabrico', 'numero_chassi', 'numero_motor', 'data_ultimo_seguro',
                           'data_proximo_seguro', 'data_ultima_inspecao', 'data_proxima_inspecao',
                           'proxima_manutencao_km', 'cilindrada', 'capacidade_tanque', 'kilometragem_actual']

        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
                self.fields[field].widget.attrs['placeholder'] = 'Opcional'

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')
        if matricula:
            # Verificar formato básico (pelo menos 3 caracteres)
            if len(matricula) < 3:
                raise ValidationError("Matrícula muito curta.")

            # Verificar se já existe (exceto para esta instância)
            if self.instance.pk:
                if Viatura.objects.filter(matricula=matricula).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Já existe uma viatura com esta matrícula.")
            else:
                if Viatura.objects.filter(matricula=matricula).exists():
                    raise ValidationError("Já existe uma viatura com esta matrícula.")
        return matricula

    def clean_numero_chassi(self):
        numero_chassi = self.cleaned_data.get('numero_chassi')
        if numero_chassi and numero_chassi.strip():  # Só valida se não estiver vazio
            if len(numero_chassi) != 17:
                raise ValidationError("Número do chassi deve ter 17 caracteres.")

            # Verificar se já existe (exceto para esta instância)
            if self.instance.pk:
                if Viatura.objects.filter(numero_chassi=numero_chassi).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Já existe uma viatura com este número de chassi.")
            else:
                if Viatura.objects.filter(numero_chassi=numero_chassi).exists():
                    raise ValidationError("Já existe uma viatura com este número de chassi.")
        return numero_chassi  # Pode ser None ou string vazia

    def clean_ano_fabrico(self):
        ano_fabrico = self.cleaned_data.get('ano_fabrico')
        if ano_fabrico:  # Só valida se foi preenchido
            ano_atual = date.today().year
            if ano_fabrico < 1900 or ano_fabrico > ano_atual + 1:
                raise ValidationError(f"Ano de fabrico inválido (1900-{ano_atual + 1})")
        return ano_fabrico  # Pode ser None

    def clean_capacidade_tanque(self):
        capacidade = self.cleaned_data.get('capacidade_tanque')
        if capacidade is not None:  # Só valida se não for None
            if capacidade <= 0:
                raise ValidationError("Capacidade do tanque deve ser positiva")
        return capacidade  # Pode ser None

    def clean_kilometragem_actual(self):
        kilometragem = self.cleaned_data.get('kilometragem_actual')
        if kilometragem is not None:  # Só valida se não for None
            if kilometragem < 0:
                raise ValidationError("Quilometragem não pode ser negativa")
        return kilometragem  # Pode ser None (não força para 0!)

    def clean_data_ultimo_seguro(self):
        data = self.cleaned_data.get('data_ultimo_seguro')
        if data and data > date.today():
            raise ValidationError("Data do último seguro não pode ser no futuro")
        return data

    def clean_data_proximo_seguro(self):
        data = self.cleaned_data.get('data_proximo_seguro')
        data_ultimo = self.cleaned_data.get('data_ultimo_seguro')

        if data:
            if data > date.today() + timedelta(days=365 * 10):  # 10 anos no futuro
                raise ValidationError("Data do próximo seguro inválida")

            if data_ultimo and data <= data_ultimo:
                raise ValidationError("Data do próximo seguro deve ser após data do último seguro")

        return data


class PedidoCombustivelForm(forms.ModelForm):
    # Adicionar campo solicitante explícito
    solicitante = forms.ModelChoiceField(
        queryset=Funcionario.objects.none(),  # Será configurado no __init__
        widget=forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
        label="Solicitante *",
        empty_label="Selecione o solicitante..."
    )

    class Meta:
        model = PedidoCombustivel
        fields = [
            'solicitante', 'viatura', 'fornecedor', 'tipo_pedido', 'data_abastecimento',
            'quantidade_litros', 'kilometragem_actual',
            'destino', 'descricao_missao', 'funcionarios_envolvidos', 'observacoes',
            'preco_por_litro'
        ]
        widgets = {
            'preco_por_litro': forms.HiddenInput(),
            'viatura': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'fornecedor': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'tipo_pedido': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'data_abastecimento': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'quantidade_litros': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'required': 'required'}),

            'kilometragem_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'destino': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Maputo - Matola'}),
            'descricao_missao': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Descreva a missão ou motivo...'}),
            'funcionarios_envolvidos': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '4'}),
            'observacoes': forms.Textarea(
                attrs={'rows': 2, 'class': 'form-control', 'placeholder': 'Observações adicionais...'}),
        }
        # Remover 'solicitante' dos widgets pois já definimos acima

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurar queryset para o campo solicitante (todos funcionários ativos)
        self.fields['solicitante'].queryset = Funcionario.objects.filter(ativo=True)

        # Mostrar TODAS as viaturas
        self.fields['viatura'].queryset = Viatura.objects.all()

        # Filtrar fornecedores activos
        from .models import FornecedorCombustivel
        self.fields['fornecedor'].queryset = FornecedorCombustivel.objects.filter(activo=True)

        # Filtrar funcionários activos para funcionarios_envolvidos
        funcionarios_qs = Funcionario.objects.filter(ativo=True)
        self.fields['funcionarios_envolvidos'].queryset = funcionarios_qs

        # Configurar data padrão para hoje
        self.fields['data_abastecimento'].initial = date.today()

        # Ordenar o campo solicitante por nome
        self.fields['solicitante'].queryset = self.fields['solicitante'].queryset.order_by('nome_completo')

    def clean(self):
        """Validações cruzadas"""
        cleaned_data = super().clean()
        solicitante = cleaned_data.get('solicitante')
        funcionarios_envolvidos = cleaned_data.get('funcionarios_envolvidos')

        # Verificar se o solicitante está na lista de funcionários envolvidos
        if solicitante and funcionarios_envolvidos:
            if solicitante in funcionarios_envolvidos:
                self.add_error('funcionarios_envolvidos',
                               'O solicitante não deve estar na lista de funcionários envolvidos')

        # Lógica de Contrato e Preço
        fornecedor = cleaned_data.get('fornecedor')
        viatura = cleaned_data.get('viatura')
        
        if fornecedor and viatura:
            from .models import ContratoCombustivel
            
            # Tentar encontrar contrato ativo
            contrato = ContratoCombustivel.objects.filter(
                fornecedor=fornecedor,
                tipo_combustivel=viatura.tipo_combustivel,
                activo=True,
                data_inicio__lte=date.today(),
                data_fim__gte=date.today()
            ).first()
            
            if contrato:
                self.instance.contrato = contrato
                self.instance.preco_por_litro = contrato.preco_unitario
                cleaned_data['preco_por_litro'] = contrato.preco_unitario
            elif cleaned_data.get('preco_por_litro'):
                # Já veio da UGEA pela View, não precisa de contrato legado
                pass
            else:
                self.add_error('fornecedor', 
                             f"Não há contrato ativo com {fornecedor.nome} para {viatura.get_tipo_combustivel_display()}")

        return cleaned_data

    # Manter os outros clean methods como estão...
    def clean_data_abastecimento(self):
        data_abastecimento = self.cleaned_data.get('data_abastecimento')
        if data_abastecimento:
            if data_abastecimento > date.today():
                raise ValidationError("Data de abastecimento não pode ser no futuro")
        return data_abastecimento

    def clean_quantidade_litros(self):
        quantidade = self.cleaned_data.get('quantidade_litros')
        if quantidade is not None:
            if quantidade <= 0:
                raise ValidationError("Quantidade deve ser positiva")
        return quantidade



    def clean_kilometragem_actual(self):
        kilometragem = self.cleaned_data.get('kilometragem_actual')
        viatura = self.cleaned_data.get('viatura')

        if kilometragem is not None and viatura:
            if viatura.kilometragem_actual is not None and kilometragem < viatura.kilometragem_actual:
                raise ValidationError(
                    f"Quilometragem não pode ser menor que a atual da viatura ({viatura.kilometragem_actual})"
                )
        return kilometragem or 0

class ManutencaoViaturaForm(forms.ModelForm):
    # Campo para selecionar Contrato da UGEA (Centralizado)
    contrato_ugea = forms.ModelChoiceField(
        queryset=None, # Definido no __init__
        label="Contrato de Manutenção (UGEA)",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = ManutencaoViatura
        fields = [
            'viatura', 'tipo_manutencao', 'contrato_ugea', 'descricao', 'data_agendada',
            'kilometragem_actual', 'prioridade', 'observacoes'
        ]
        # Excluimos 'fornecedor' e 'contrato' legado da lista de fields explícitos para o user
        # Mas mantemos no model
        widgets = {
            'viatura': forms.Select(attrs={'class': 'form-select'}),
            'tipo_manutencao': forms.Select(attrs={'class': 'form-select'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'data_agendada': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'kilometragem_actual': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from ugea.models import Contrato, ItemContrato
        
        # Filtra viaturas e Contratos UGEA
        self.fields['viatura'].queryset = Viatura.objects.filter(activa=True)
        
        # Busca CONTRATOS DA UGEA de Manutenção ativos
        contratos_ugea = Contrato.objects.filter(ativo=True).distinct()
        self.fields['contrato_ugea'].queryset = contratos_ugea
        
        # Pegar todos os itens de todos os contratos ativos para servir de sugestão
        itens_contratos = ItemContrato.objects.filter(contrato__in=contratos_ugea).values_list('descricao', 'descricao').distinct()
        
        # Combinar escolhas padrao com itens do contrato
        base_choices = [('', '---------')] + list(TIPO_MANUTENCAO_CHOICES)
        contract_choices = list(itens_contratos)
        
        # Remover duplicados mantendo a ordem (padrao primeiro)
        seen = set()
        final_choices = []
        for val, lbl in base_choices + contract_choices:
            if val not in seen:
                final_choices.append((val, lbl))
                seen.add(val)
        
        self.fields['tipo_manutencao'].choices = final_choices

    def clean_data_agendada(self):
        data_agendada = self.cleaned_data.get('data_agendada')
        if data_agendada:
            if data_agendada < date.today():
                raise ValidationError("Data agendada não pode ser no passado")
        return data_agendada

    def clean_kilometragem_actual(self):
        kilometragem = self.cleaned_data.get('kilometragem_actual')
        viatura = self.cleaned_data.get('viatura')

        if kilometragem is not None and viatura:
            if viatura.kilometragem_actual is not None and kilometragem < viatura.kilometragem_actual:
                raise ValidationError(
                    f"Quilometragem não pode ser menor que a atual da viatura ({viatura.kilometragem_actual})"
                )
        return kilometragem or 0


class SeguroViaturaForm(forms.ModelForm):
    class Meta:
        model = SeguroViatura
        fields = [
            'viatura', 'tipo_seguro', 'companhia_seguros', 'numero_apolice',
            'agente_seguros', 'contacto_agente', 'data_inicio', 'data_fim',
            'premio_seguro', 'franquia', 'valor_segurado', 'coberturas',
            'restricoes', 'condicoes_especiais', 'contacto_seguros',
            'renovacao_automatica'
        ]
        widgets = {
            'viatura': forms.Select(attrs={'class': 'form-control'}),
            'tipo_seguro': forms.Select(attrs={'class': 'form-control'}),
            'companhia_seguros': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_apolice': forms.TextInput(attrs={'class': 'form-control'}),
            'agente_seguros': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_agente': forms.TextInput(attrs={'class': 'form-control'}),
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_fim': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'premio_seguro': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'franquia': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'valor_segurado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'coberturas': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'restricoes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'condicoes_especiais': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'contacto_seguros': forms.TextInput(attrs={'class': 'form-control'}),
            'renovacao_automatica': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar viaturas activas
        self.fields['viatura'].queryset = Viatura.objects.filter(activa=True)

    def clean_data_fim(self):
        data_inicio = self.cleaned_data.get('data_inicio')
        data_fim = self.cleaned_data.get('data_fim')

        if data_inicio and data_fim:
            if data_fim <= data_inicio:
                raise ValidationError("Data de fim deve ser após data de início")
        return data_fim

    def clean_premio_seguro(self):
        premio = self.cleaned_data.get('premio_seguro')
        if premio is not None:
            if premio <= 0:
                raise ValidationError("Prêmio do seguro deve ser positivo")
        return premio or 0


# gestaocombustivel/forms.py - Corrija a classe RotaTransporteForm

class RotaTransporteForm(forms.ModelForm):
    class Meta:
        model = RotaTransporte
        fields = [
            'nome_rota', 'viatura', 'motorista', 'descricao',
            'hora_partida', 'hora_chegada', 'dias_semana',
            'distancia_total', 'combustivel_estimado'
        ]
        widgets = {
            'nome_rota': forms.TextInput(attrs={'class': 'form-control'}),
            'viatura': forms.Select(attrs={'class': 'form-control'}),
            'motorista': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'hora_partida': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_chegada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'dias_semana': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Seg-Sex'}),
            'distancia_total': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'combustivel_estimado': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # IMPORTANTE: Importe aqui para evitar circular imports
        from .models import Viatura
        from recursoshumanos.models import Funcionario

        # Filtrar viaturas ACTIVAS e DISPONÍVEIS
        self.fields['viatura'].queryset = Viatura.objects.filter(
            activa=True,
            disponivel=True
        ).order_by('matricula')

        # Filtrar funcionários que são motoristas e ACTIVOS
        # VERIFIQUE O NOME EXATO DO CAMPO - pode ser 'funcao', 'cargo', 'profissao', etc.
        self.fields['motorista'].queryset = Funcionario.objects.filter(
            ativo=True  # Verifique se o campo é 'ativo' ou 'activo'
        ).filter(
            # Opção 1: Se tiver campo específico para motorista
            funcao='motorista'  # ← Mude para o nome correto do campo
        ).order_by('nome_completo')

        # Se não funcionar, use este código alternativo:
        """
        # ALTERNATIVA - Mostrar todos funcionários ativos com uma nota
        funcionarios_ativos = Funcionario.objects.filter(ativo=True).order_by('nome_completo')
        self.fields['motorista'].queryset = funcionarios_ativos
        self.fields['motorista'].help_text = "Selecione um funcionário ativo"
        """

        # Se quiser mostrar apenas funcionários com categoria de condução
        """
        # ALTERNATIVA 2 - Filtrar por categoria de condução
        self.fields['motorista'].queryset = Funcionario.objects.filter(
            ativo=True,
            categoria_conducao__isnull=False  # Se tiver este campo
        ).order_by('nome_completo')
        """

    def clean_distancia_total(self):
        distancia = self.cleaned_data.get('distancia_total')
        if distancia is not None and distancia < 0:
            raise ValidationError("Distância não pode ser negativa")
        return distancia or 0

    def clean_combustivel_estimado(self):
        combustivel = self.cleaned_data.get('combustivel_estimado')
        if combustivel is not None and combustivel < 0:
            raise ValidationError("Combustível estimado não pode ser negativo")
        return combustivel or 0

class PontoRotaForm(forms.ModelForm):
    class Meta:
        model = PontoRota
        fields = ['rota', 'nome_ponto', 'localizacao', 'ordem', 'hora_estimada', 'tipo_ponto', 'observacoes']
        widgets = {
            'rota': forms.Select(attrs={'class': 'form-control'}),
            'nome_ponto': forms.TextInput(attrs={'class': 'form-control'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'ordem': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'hora_estimada': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'tipo_ponto': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar rotas activas
        self.fields['rota'].queryset = RotaTransporte.objects.filter(activa=True)

    def clean_ordem(self):
        ordem = self.cleaned_data.get('ordem')
        rota = self.cleaned_data.get('rota')

        if ordem and rota:
            if ordem < 1:
                raise ValidationError("Ordem deve ser maior que 0")

            # Verificar se já existe ponto com esta ordem nesta rota
            if self.instance.pk:
                if PontoRota.objects.filter(rota=rota, ordem=ordem).exclude(pk=self.instance.pk).exists():
                    raise ValidationError("Já existe um ponto com esta ordem nesta rota")
            else:
                if PontoRota.objects.filter(rota=rota, ordem=ordem).exists():
                    raise ValidationError("Já existe um ponto com esta ordem nesta rota")

        return ordem


class RegistroDiarioRotaForm(forms.ModelForm):
    class Meta:
        model = RegistroDiarioRota
        fields = [
            'rota', 'data', 'motorista', 'hora_partida_real',
            'hora_chegada_real', 'kilometragem_inicial', 'kilometragem_final',
            'condicoes_climaticas', 'temperatura', 'incidentes',
            'numero_passageiros', 'observacoes'
        ]
        widgets = {
            'rota': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motorista': forms.Select(attrs={'class': 'form-control'}),
            'hora_partida_real': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_chegada_real': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'kilometragem_inicial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'kilometragem_final': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'condicoes_climaticas': forms.TextInput(attrs={'class': 'form-control'}),
            'temperatura': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'incidentes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'numero_passageiros': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'observacoes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar rotas activas
        self.fields['rota'].queryset = RotaTransporte.objects.filter(activa=True)

        # Filtrar apenas motoristas activos
        self.fields['motorista'].queryset = Funcionario.objects.filter(
            funcao='motorista',
            ativo=True
        ).exclude(funcao__isnull=True)

    def clean_kilometragem_final(self):
        km_inicial = self.cleaned_data.get('kilometragem_inicial')
        km_final = self.cleaned_data.get('kilometragem_final')

        if km_inicial is not None and km_final is not None:
            if km_final < km_inicial:
                raise ValidationError("Quilometragem final não pode ser menor que a inicial")

        return km_final

    def clean_temperatura(self):
        temperatura = self.cleaned_data.get('temperatura')
        if temperatura is not None:
            if temperatura < -50 or temperatura > 60:
                raise ValidationError("Temperatura inválida")
        return temperatura

    def clean_numero_passageiros(self):
        passageiros = self.cleaned_data.get('numero_passageiros')
        if passageiros is not None and passageiros < 0:
            raise ValidationError("Número de passageiros não pode ser negativo")
        return passageiros or 0


class FornecedorCombustivelForm(forms.ModelForm):
    class Meta:
        model = FornecedorCombustivel
        fields = ['nome', 'nuit', 'contacto', 'email', 'endereco', 'activo', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo da empresa'}),
            'nuit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '999999999'}),
            'contacto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone/Telemóvel'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@empresa.com'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações adicionais...'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_nuit(self):
        nuit = self.cleaned_data.get('nuit')
        if not nuit or not nuit.isdigit() or len(nuit) != 9:
            raise ValidationError("O NUIT deve conter exatamente 9 dígitos numéricos.")
        # Check uniqueness manually if needed, but unique=True in model handles it (though form validation is nicer)
        return nuit


from django.db import models
from partidos.models import Partido
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral
from dfec.models.election_analytics import Provincia

class InscricaoPartidoEleicao(models.Model):
    """Registo de um partido para participar numa eleição específica com escopo geográfico"""
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='inscricoes_eleitorais')
    eleicao = models.ForeignKey(Eleicao, on_delete=models.CASCADE, related_name='partidos_inscritos')
    
    # Escopo de Inscrição (Contexto Moçambique)
    scope_provincia = models.ForeignKey(Provincia, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Província (Gerais/Legislativas)")
    scope_circulo = models.ForeignKey(CirculoEleitoral, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Círculo (Autárquicas)")
    
    status = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente'),
        ('inscrito', 'Inscrito/Aprovado'),
        ('rejeitado', 'Rejeitado'),
    ], default='pendente')
    
    posicao_boletim = models.IntegerField(null=True, blank=True, verbose_name="Posição no Boletim/Sorteio")
    data_inscricao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inscrição de Partido em Eleição"
        verbose_name_plural = "Inscrições de Partidos"

    def __str__(self):
        scope = self.scope_provincia or self.scope_circulo or "Nacional"
        return f"{self.partido.sigla} - {self.eleicao.nome} ({scope})"
        
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.eleicao.tipo == 'autarquica' and not self.scope_circulo:
            raise ValidationError("Nas eleições autárquicas, a inscrição do partido deve ser associada obrigatoriamente a um Círculo Eleitoral (Município/Vila).")
        if self.eleicao.tipo in ['legislativa', 'provincial'] and not self.scope_provincia:
            # Para legislativas nacionais em Moçambique, o âmbito é muitas vezes a Província que serve de Círculo
            # mas vamos permitir passar se for uma regra específica de 'geral'
            if self.eleicao.tipo != 'geral':
                raise ValidationError("Para estas eleições, o partido deve selecionar o âmbito provincial de atuação.")

class ListaCandidatura(models.Model):
    """Lista oficial de candidatos de um partido num círculo específico"""
    inscricao = models.ForeignKey(InscricaoPartidoEleicao, on_delete=models.CASCADE, related_name='listas')
    circulo = models.ForeignKey(CirculoEleitoral, on_delete=models.CASCADE, related_name='listas_candidatos')
    
    cargo_disputado = models.CharField(max_length=100, help_text="Ex: Assembleia da República, Assembleia Provincial")
    validada = models.BooleanField(default=False)
    submetido_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Submetido por")
    data_submissao = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['inscricao', 'circulo']
        verbose_name = "Lista de Candidaturas"
        verbose_name_plural = "Listas de Candidaturas"

    def __str__(self):
        return f"Lista {self.inscricao.partido.sigla} - {self.circulo.nome}"

    def verificar_conformidade(self):
        """Valida se a lista cumpre os requisitos de mandatos e suplentes, integridade RS e exclusividade"""
        candidatos_lista = self.candidatos.all()
        efetivos = candidatos_lista.filter(tipo='efetivo').order_by('posicao')
        suplentes = candidatos_lista.filter(tipo='suplente').count()
        mandatos_necessarios = self.circulo.num_mandatos
        
        erros = []
        alertas = []

        # 1. Validação de Quantitativos
        if efetivos.count() != mandatos_necessarios:
            erros.append(f"Número de efetivos ({efetivos.count()}) difere dos mandatos do círculo ({mandatos_necessarios}).")
        if suplentes < 3:
            erros.append(f"Número de suplentes ({suplentes}) é inferior ao mínimo legal (3).")
            
        # 2. Validação de Integridade RS (Voter Registry)
        from rs.models import Eleitor
        for cand in candidatos_lista:
            # Tentar localizar por Cartão de Eleitor ou BI (mocking logic if NUIT/BI is same as card in some cases)
            eleitor_existe = Eleitor.objects.filter(
                models.Q(numero_cartao=cand.numero_eleitor) | 
                models.Q(nuit=cand.bi_numero)
            ).exists()
            
            if not eleitor_existe:
                alertas.append(f"Candidato {cand.nome_completo} não localizado no Recenseamento (RS).")
                cand.status_eleitor = 'irregular'
            else:
                cand.status_eleitor = 'confirmado'
            
            # 3. Verificação de Exclusividade (Cruzar com outras listas da mesma eleição)
            outros = Candidato.objects.filter(
                models.Q(bi_numero=cand.bi_numero) | models.Q(numero_eleitor=cand.numero_eleitor)
            ).exclude(id=cand.id).filter(lista__inscricao__eleicao=self.inscricao.eleicao)
            
            if outros.exists():
                outra_lista = outros.first().lista
                if outra_lista.inscricao.partido != self.inscricao.partido:
                    erros.append(f"Fraude Detectada: {cand.nome_completo} consta também na lista do {outra_lista.inscricao.partido.sigla} em {outra_lista.circulo.nome}.")
                    cand.duplicado = True
            
            # cand.save() # REMOVIDO para performance: o STAE deve chamar save() ou bulk_update externamente se precisar persistir
        
        # Otimização: Só atualizamos o status se houver alterações reais no futuro (versão assíncrona)

        return {
            'conforme': len(erros) == 0,
            'erros': erros,
            'alertas': alertas,
            'efetivos': efetivos.count(),
            'suplentes': suplentes,
            'mandatos': mandatos_necessarios,
            'candidatos_data': efetivos # Para o simulador de boletim
        }

class Candidato(models.Model):
    """Candidato individual numa lista ou presidencial"""
    lista = models.ForeignKey(ListaCandidatura, on_delete=models.CASCADE, related_name='candidatos', null=True, blank=True)
    # Novo: Ligação directa para Presidenciais (Nacional)
    inscricao_direta = models.ForeignKey(InscricaoPartidoEleicao, on_delete=models.CASCADE, related_name='candidatos_diretos', null=True, blank=True)
    
    nome_completo = models.CharField(max_length=200)
    bi_numero = models.CharField(max_length=20)
    numero_eleitor = models.CharField(max_length=20, blank=True, null=True)
    
    # Identificação e Dados Demográficos
    posicao = models.IntegerField(verbose_name="Posição na Lista", help_text="Para candidatos presidenciais, use 1")
    tipo = models.CharField(max_length=20, choices=[
        ('efetivo', 'Efetivo'),
        ('suplente', 'Suplente'),
    ], default='efetivo')
    
    categoria = models.CharField(max_length=20, choices=[
        ('presidencial', 'Candidatura Presidencial'),
        ('legislativo', 'Assembleia da República'),
        ('provincial', 'Assembleia Provincial'),
        ('governador', 'Governador de Província'),
        ('autarquico', 'Assembleia Municipal / Autárquica'),
    ], default='legislativo')

    genero = models.CharField(max_length=1, choices=[('M', 'Masculino'), ('F', 'Feminino')], default='M', verbose_name="Género")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    foto = models.ImageField(upload_to='candidaturas/fotos/', null=True, blank=True)
    
    # Status de Verificação
    status_eleitor = models.CharField(max_length=20, choices=[
        ('pendente', 'Pendente Verificação'),
        ('confirmado', 'Eleitor Confirmado'),
        ('irregular', 'Irregular / Não Localizado'),
    ], default='pendente')
    
    duplicado = models.BooleanField(default=False, help_text="Candidato encontrado em mais de uma lista (Fraude?)")
    motivo_irregularidade = models.TextField(blank=True)
    
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['tipo', 'posicao']
        verbose_name = "Candidato"
        verbose_name_plural = "Candidatos"

    def __str__(self):
        sigla = self.lista.inscricao.partido.sigla if self.lista else self.inscricao_direta.partido.sigla
        return f"{self.posicao}º {self.nome_completo} ({sigla})"

    def clean(self):
        from django.core.exceptions import ValidationError
        from datetime import date
        
        # Validação de Idade (Geral)
        if self.data_nascimento:
            hoje = date.today()
            idade = hoje.year - self.data_nascimento.year - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
            
            if self.categoria == 'presidencial' and idade < 35:
                raise ValidationError("Candidato Presidential deve ter no mínimo 35 anos (Artigo 147 da Constituição).")
            if idade < 18:
                raise ValidationError("O candidato deve ser maior de idade.")

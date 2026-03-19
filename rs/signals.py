from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from eleicao.models import Eleicao
from circuloseleitorais.models import CirculoEleitoral
from candidaturas.models import ListaCandidatura, InscricaoPartidoEleicao
from .logic import sync_plano_logistico

@receiver(post_save, sender=CirculoEleitoral)
@receiver(post_delete, sender=CirculoEleitoral)
def trigger_sync_logistica_circulo(sender, instance, **kwargs):
    """Sincroniza logística quando alteramos dados geográficos ou mesas"""
    if instance.eleicao:
        sync_plano_logistico(instance.eleicao)

@receiver(post_save, sender=Eleicao)
def trigger_sync_logistica_eleicao(sender, instance, **kwargs):
    """Sincroniza logística quando uma eleição é criada ou alterada"""
    if instance.ativo:
        sync_plano_logistico(instance)

@receiver(post_save, sender=ListaCandidatura)
@receiver(post_delete, sender=ListaCandidatura)
def trigger_sync_logistica_lista(sender, instance, **kwargs):
    """Sincroniza logística quando listas são submetidas (afecta credenciais/coletes)"""
    if instance.inscricao and instance.inscricao.eleicao:
        sync_plano_logistico(instance.inscricao.eleicao)

@receiver(post_save, sender=InscricaoPartidoEleicao)
def trigger_sync_logistica_inscricao(sender, instance, **kwargs):
    """Sincroniza logística quando partidos se inscrevem"""
    if instance.eleicao:
        sync_plano_logistico(instance.eleicao)

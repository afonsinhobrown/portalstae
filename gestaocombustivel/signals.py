# gestaocombustivel/signals.py - NOVO ARQUIVO
from django.apps import AppConfig
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import PedidoCombustivel, SeguroViatura
from .notifications import enviar_alerta_seguro


@receiver(post_save, sender=PedidoCombustivel)
def actualizar_kilometragem_apos_abastecimento(sender, instance, **kwargs):
    """Actualiza kilometragem da viatura após abastecimento"""
    if instance.status == 'abastecido' and instance.kilometragem_actual:
        instance.viatura.kilometragem_actual = instance.kilometragem_actual
        instance.viatura.save()


@receiver(post_save, sender=SeguroViatura)
def verificar_vencimento_seguro(sender, instance, **kwargs):
    """Verifica se seguro está próximo do vencimento"""
    dias_para_vencer = (instance.data_fim - timezone.now().date()).days
    if 0 <= dias_para_vencer <= 7:  # Últimos 7 dias
        enviar_alerta_seguro()


# No apps.py da app
class GestaocombustivelConfig(AppConfig):
    name = 'gestaocombustivel'

    def ready(self):
        import gestaocombustivel.signals
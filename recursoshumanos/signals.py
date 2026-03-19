# recursoshumanos/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Funcionario, SaldoFerias, ConfiguracaoNotificacao



@receiver(post_save, sender=User)
def criar_configuracao_notificacoes(sender, instance, created, **kwargs):
    """Criar configuração de notificações para novo usuário"""
    if created:
        ConfiguracaoNotificacao.objects.get_or_create(usuario=instance)


@receiver(post_save, sender=Funcionario)
def criar_saldo_ferias(sender, instance, created, **kwargs):
    """Criar saldo de férias para novo funcionário"""
    if created:
        ano_atual = instance.data_admissao.year
        SaldoFerias.objects.get_or_create(
            funcionario=instance,
            ano=ano_atual,
            defaults={'dias_disponiveis': 0, 'dias_saldo': 0}  # Sem férias no ano de admissão
        )

        # Criar saldo para ano seguinte
        SaldoFerias.objects.get_or_create(
            funcionario=instance,
            ano=ano_atual + 1,
            defaults={'dias_disponiveis': 22, 'dias_saldo': 22}
        )


@receiver(pre_save, sender=Funcionario)
def atualizar_qr_code(sender, instance, **kwargs):
    """Atualizar QR code se número de identificação mudar"""
    if instance.pk:
        try:
            antigo = Funcionario.objects.get(pk=instance.pk)
            if antigo.numero_identificacao != instance.numero_identificacao:
                # Número mudou, gerar novo QR code
                instance.gerar_qr_code()
        except Funcionario.DoesNotExist:
            pass
    else:
        # Novo funcionário, gerar QR code
        instance.gerar_qr_code()


@receiver(post_save, sender=Funcionario)
def criar_usuario_automatico(sender, instance, created, **kwargs):
    """Criar usuário Django automaticamente para novo funcionário"""
    if created and not instance.user:
        try:
            # Criar username único (usar número de identificação)
            base_username = instance.numero_identificacao.lower().replace(' ', '_')
            username = base_username

            # Se username já existe, adicionar sufixo
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            # Criar email (usar pessoal se existir, senão gerar)
            if instance.email_pessoal:
                email = instance.email_pessoal
            else:
                email = f"{username}@stae.gov.mz"

            # Criar usuário com senha temporária
            user = User.objects.create_user(
                username=username,
                email=email,
                password='TempPass123!',  # Senha temporária
                first_name=instance.nome_completo.split()[0] if instance.nome_completo else '',
                last_name=' '.join(instance.nome_completo.split()[1:]) if len(
                    instance.nome_completo.split()) > 1 else '',
                is_active=True
            )

            # Associar ao funcionário
            instance.user = user
            instance.save(update_fields=['user'])

            # Adicionar ao grupo padrão se existir
            try:
                grupo_funcionario = Group.objects.get(name='Funcionários')
                user.groups.add(grupo_funcionario)
            except Group.DoesNotExist:
                pass

        except Exception as e:
            # Log do erro sem interromper o processo
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao criar usuário para funcionário {instance.id}: {str(e)}")


# recursoshumanos/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Funcionario

@receiver(post_save, sender=Funcionario)
def garantir_qr_code(sender, instance, created, **kwargs):
    """Garante que todo funcionário tenha QR Code"""
    if not instance.qr_code or not instance.qr_code_hash:
        instance.gerar_qr_code()
        instance.save(update_fields=['qr_code', 'qr_code_hash', 'qr_code_data'])
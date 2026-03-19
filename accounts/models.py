# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class PerfilUsuario(models.Model):
    TIPOS_USUARIO = (
        ('publico', 'Público Geral'),
        ('funcionario_stae', 'Funcionário STAE'),
        ('tecnico', 'Técnico'),
        ('gestor', 'Gestor'),
        ('admin', 'Administrador'),
        ('superadmin', 'Super Administrador'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=20, choices=TIPOS_USUARIO, default='publico')
    departamento = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)
    foto = models.ImageField(upload_to='perfis/', blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    # Permissões específicas
    pode_acessar_rh = models.BooleanField(default=False)
    pode_acessar_equipamentos = models.BooleanField(default=False)
    pode_acessar_combustivel = models.BooleanField(default=False)
    pode_acessar_admin = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'

    def __str__(self):
        return f"{self.user.username} - {self.get_tipo_display()}"

    def is_funcionario_stae(self):
        return self.tipo in ['funcionario_stae', 'tecnico', 'gestor', 'admin', 'superadmin']

    def is_administrador(self):
        return self.tipo in ['admin', 'superadmin']

    def get_login_url(self):
        """Retorna URL de login apropriada para este perfil"""
        if self.is_administrador():
            return '/portal-admin/login/'
        elif self.is_funcionario_stae():
            return '/stae/login/'
        else:
            return '/accounts/login/'


@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil(sender, instance, created, **kwargs):
    """Cria perfil automaticamente quando usuário é criado"""
    if created:
        PerfilUsuario.objects.create(user=instance)
    else:
        # Atualiza perfil se existir
        if hasattr(instance, 'perfil'):
            instance.perfil.save()


@receiver(post_save, sender=User)
def atribuir_grupos_iniciais(sender, instance, created, **kwargs):
    """Atribui grupos baseados no tipo de perfil"""
    if created and hasattr(instance, 'perfil'):
        from django.contrib.auth.models import Group

        grupos_map = {
            'funcionario_stae': 'STAE',
            'tecnico': ['STAE', 'TECNICOS'],
            'gestor': ['STAE', 'GESTORES'],
            'admin': ['STAE', 'ADMINISTRADORES'],
            'superadmin': ['STAE', 'ADMINISTRADORES', 'SUPERADMIN'],
        }

        grupos_nomes = grupos_map.get(instance.perfil.tipo, [])
        if isinstance(grupos_nomes, str):
            grupos_nomes = [grupos_nomes]

        for grupo_nome in grupos_nomes:
            grupo, _ = Group.objects.get_or_create(name=grupo_nome)
            instance.groups.add(grupo)
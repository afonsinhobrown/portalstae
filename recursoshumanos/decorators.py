# recursoshumanos/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from .models import Funcionario


def chefe_required(view_func):
    """Decorator que verifica se o usuário é chefe"""

    def check_chefe(user):
        if not user.is_authenticated:
            return False

        # RH tem acesso a tudo
        if user.is_staff or user.groups.filter(name='rh_staff').exists():
            return True

        # Verificar se é funcionário com função de chefe
        try:
            funcionario = Funcionario.objects.get(user=user)
            return funcionario.funcao in ['chefe', 'coordenador', 'director']
        except Funcionario.DoesNotExist:
            return False

    return user_passes_test(check_chefe, login_url='recursoshumanos:dashboard')(view_func)


def director_required(view_func):
    """Decorator que verifica se o usuário é diretor"""

    def check_director(user):
        if not user.is_authenticated:
            return False

        # RH tem acesso a tudo
        if user.is_staff or user.groups.filter(name='rh_staff').exists():
            return True

        # Verificar se é diretor
        try:
            funcionario = Funcionario.objects.get(user=user)
            return funcionario.funcao == 'director'
        except Funcionario.DoesNotExist:
            return False

    return user_passes_test(check_director, login_url='recursoshumanos:dashboard')(view_func)


def rh_required(view_func):
    """Decorator que verifica se o usuário tem acesso RH"""

    def check_rh(user):
        if not user.is_authenticated:
            return False

        # Staff ou grupo rh_staff
        return user.is_staff or user.groups.filter(name='rh_staff').exists()

    return user_passes_test(check_rh, login_url='recursoshumanos:dashboard')(view_func)


def funcionario_required(view_func):
    """Decorator que verifica se o usuário é funcionário"""

    def check_funcionario(user):
        if not user.is_authenticated:
            return False

        # Todos os usuários autenticados devem ser funcionários
        # Exceto superusuários/admin que podem não ter funcionário associado
        if user.is_superuser or user.is_staff:
            return True

        return Funcionario.objects.filter(user=user).exists()

    return user_passes_test(check_funcionario, login_url='login')(view_func)
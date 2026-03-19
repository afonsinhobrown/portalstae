# recursoshumanos/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RHRequiredMixin(LoginRequiredMixin):
    """Mixin para views que requerem permissão RH"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name='rh_staff').exists() and not request.user.is_staff:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class ChefeRequiredMixin(LoginRequiredMixin):
    """Mixin para views de chefes"""

    def dispatch(self, request, *args, **kwargs):
        try:
            funcionario = request.user.funcionario
            if funcionario.funcao not in ['chefe', 'coordenador', 'director']:
                raise PermissionDenied
        except:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
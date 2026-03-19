from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.utils import timezone

@receiver(user_logged_in)
def clear_multiple_sessions(sender, user, request, **kwargs):
    # Encontrar todas as sessões ativas do utilizador e apagá-las (menos a atual)
    # Nota: No momento do sinal, a sessão atual ainda pode não estar persistida com o UserID.
    # Por isso, apagamos TODAS as sessões antigas que tenham este User ID nos dados codificados.
    
    current_session_key = request.session.session_key
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    
    for s in sessions:
        decoded = s.get_decoded()
        if decoded.get('_auth_user_id') == str(user.id):
            if s.session_key != current_session_key:
                s.delete()

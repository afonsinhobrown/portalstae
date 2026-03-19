from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.views.decorators.csrf import csrf_exempt

# View de login SIMPLES - sem CSRF
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login


@csrf_exempt
def login_simples(request):
    """Login mais simples possível"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next', '/')
            return redirect(next_url)
        else:
            return render(request, 'login_simples.html', {
                'error': 'Usuário ou senha incorretos'
            })

    return render(request, 'login_simples.html')


urlpatterns = [
    # Página inicial
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    # Admin Django
    path('admin/', admin.site.urls),

    # ✅ LOGIN SIMPLES - SEM CSRF
    path('accounts/login/', login_simples, name='login_publico'),

    # Logout
    path('accounts/logout/',
         auth_views.LogoutView.as_view(next_page='/'),
         name='logout_publico'),

    path('logout/',
         auth_views.LogoutView.as_view(next_page='/'),
         name='logout'),

    # Apps
    path('rh/', include('recursoshumanos.urls')),
    path('portal-admin/', include('admin_portal.urls')),
   path('equipamentos/', include('gestaoequipamentos.urls')),
    path('combustivel/', include('gestaocombustivel.urls')),
    path('dfec/', include('dfec.urls')),
    path('credenciais/', include('credenciais.urls')),
    path('site/', include('pagina_stae.urls')),
    path('chat/', include('chatbot.urls')),
    
    # NOVAS APPS - SISTEMA ELEITORAL
    path('ugea/', include('ugea.urls')),  # 1. Procurement
    path('partidos/', include('partidos.urls')),  # 2. Partidos
    path('circulos/', include('circuloseleitorais.urls')),  # 3. Círculos
    path('eleicao/', include('eleicao.urls')),  # 4. Eleição
    path('candidaturas/', include('candidaturas.urls')),  # 5. Candidaturas
    path('rs/', include('rs.urls')),  # 6. Recenseamento/Logística
    path('apuramento/', include('apuramento.urls')),  # 7. Apuramento
]

# Media em dev
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
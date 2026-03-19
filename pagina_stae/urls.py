# pagina_stae/urls.py - VERSÃO COMPLETA
from django.urls import path
from . import views

app_name = 'pagina_stae'

urlpatterns = [
    # ========== PÁGINAS PRINCIPAIS ==========
    path('', views.HomeView.as_view(), name='home'),
    path('sobre/', views.SobreView.as_view(), name='sobre'),
    path('servicos/', views.ServicosView.as_view(), name='servicos'),
    path('contactos/', views.ContactosView.as_view(), name='contactos'),
    path('faq/', views.FAQListView.as_view(), name='faq'),
    path('busca/', views.BuscaView.as_view(), name='busca'),

    # ========== NOTÍCIAS ==========
    path('noticias/', views.NoticiasListView.as_view(), name='noticias'),
    path('noticias/<slug:slug>/', views.NoticiaDetailView.as_view(), name='noticia_detalhe'),

    # ========== GALERIAS ==========
    path('galerias/', views.GaleriasListView.as_view(), name='galerias'),
    path('galerias/<slug:slug>/', views.GaleriaDetailView.as_view(), name='galeria_detalhe'),

    # ========== VÍDEOS ==========
    path('videos/', views.VideosListView.as_view(), name='videos'),

    # ========== DOCUMENTOS ==========
    path('documentos/', views.DocumentosListView.as_view(), name='documentos'),

    # ========== PÁGINAS ESTÁTICAS ==========
    path('pagina/<slug:slug>/', views.PaginaDetailView.as_view(), name='pagina_detalhe'),

    # ========== ELEIÇÕES ==========
    path('eleicoes/resultados/', views.ResultadosView.as_view(), name='resultados'),
    path('eleicoes/candidatos/', views.CandidatosView.as_view(), name='candidatos'),
    path('eleicoes/mapa/', views.MapaView.as_view(), name='mapa'),

    # ========== APIs ==========
    path('api/dados-abertos/', views.api_dados_abertos, name='api_dados_abertos'),
    path('api/streaming/', views.streaming_resultados, name='streaming_resultados'),
]
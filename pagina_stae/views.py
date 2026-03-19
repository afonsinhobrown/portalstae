# pagina_stae/views.py - VERSÃO COMPLETA
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.http import JsonResponse
from django.db.models import Q
from .models import *


# ========== PÁGINAS PRINCIPAIS ==========
# pagina_stae/views.py - ATUALIZAR HomeView
class HomeView(TemplateView):
    template_name = 'pagina_stae/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # NOTÍCIAS - CORRIGIR os filtros
        noticias_destaque = Noticia.objects.filter(
            publicado=True,
            destaque=True
        ).order_by('-data_publicacao')[:6]  # ← ADD order_by

        noticias_recentes = Noticia.objects.filter(
            publicado=True
        ).exclude(destaque=True).order_by('-data_publicacao')[:6]  # ← ADD order_by

        context.update({
            'noticias_destaque': noticias_destaque,
            'noticias_recentes': noticias_recentes,
            'galerias_recentes': Galeria.objects.filter(publica=True)[:4],
            'videos_destaque': Video.objects.filter(destaque=True)[:3],
            'departamentos': Departamento.objects.filter(ativo=True)[:6],
        })
        return context
    
class SobreView(TemplateView):
    template_name = 'pagina_stae/sobre.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departamentos'] = Departamento.objects.filter(ativo=True)
        return context


class ServicosView(TemplateView):
    template_name = 'pagina_stae/servicos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departamentos'] = Departamento.objects.filter(ativo=True)
        return context


class ContactosView(TemplateView):
    template_name = 'pagina_stae/contactos.html'


class FAQListView(ListView):
    model = FAQ
    template_name = 'pagina_stae/faq.html'

    def get_queryset(self):
        return FAQ.objects.filter(ativo=True)


class BuscaView(TemplateView):
    template_name = 'pagina_stae/busca.html'


# ========== NOTÍCIAS ==========
# pagina_stae/views.py - VERIFICAR NoticiasListView
class NoticiasListView(ListView):
    model = Noticia
    template_name = 'pagina_stae/noticias/lista.html'
    paginate_by = 9
    context_object_name = 'noticias'  # ← IMPORTANTE: Este nome deve bater com o template

    def get_queryset(self):
        return Noticia.objects.filter(publicado=True).order_by('-data_publicacao')
    
    

class NoticiaDetailView(DetailView):
    model = Noticia
    template_name = 'pagina_stae/noticias/detalhe.html'


# ========== GALERIAS ==========
class GaleriasListView(ListView):
    model = Galeria
    template_name = 'pagina_stae/galerias/lista.html'
    paginate_by = 12

    def get_queryset(self):
        return Galeria.objects.filter(publica=True)


class GaleriaDetailView(DetailView):
    model = Galeria
    template_name = 'pagina_stae/galerias/detalhe.html'


# ========== VÍDEOS ==========
class VideosListView(ListView):
    model = Video
    template_name = 'pagina_stae/videos/lista.html'
    paginate_by = 12


# ========== DOCUMENTOS ==========
class DocumentosListView(ListView):
    model = Documento
    template_name = 'pagina_stae/documentos/lista.html'
    paginate_by = 20

    def get_queryset(self):
        return Documento.objects.filter(publico=True)


# ========== PÁGINAS ESTÁTICAS ==========
class PaginaDetailView(DetailView):
    model = Pagina
    template_name = 'pagina_stae/paginas/detalhe.html'

    def get_queryset(self):
        return Pagina.objects.filter(ativa=True)


# ========== ELEIÇÕES ==========
class ResultadosView(TemplateView):
    template_name = 'pagina_stae/eleicoes/resultados.html'


class CandidatosView(ListView):
    model = Candidato
    template_name = 'pagina_stae/eleicoes/candidatos.html'

    def get_queryset(self):
        eleicao_ativa = Eleicao.objects.filter(ativa=True).first()
        if eleicao_ativa:
            return Candidato.objects.filter(eleicao=eleicao_ativa)
        return Candidato.objects.none()


class MapaView(TemplateView):
    template_name = 'pagina_stae/eleicoes/mapa.html'


# ========== APIs ==========
def api_dados_abertos(request):
    return JsonResponse({
        'status': 'API em desenvolvimento',
        'portal': 'STAE Moçambique'
    })


def streaming_resultados(request):
    return JsonResponse({
        'status': 'Streaming em desenvolvimento'
    })
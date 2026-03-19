from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'gestaoequipamentos'

urlpatterns = [
    # ✅ URLs DE AUTENTICAÇÃO
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='recursoshumanos/login_rh.html',
        redirect_authenticated_user=True
    ), name='login_equipamentos'),

    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout_equipamentos'),

    # ===== DASHBOARD =====
    path('', views.dashboard_equipamentos, name='dashboard_equipamentos'),

    # ===== EQUIPAMENTOS =====
    path('equipamentos/', views.lista_equipamentos, name='lista_equipamentos'),
    path('equipamentos/novo/', views.novo_equipamento, name='novo_equipamento'),
    path('equipamentos/<int:equipamento_id>/', views.detalhe_equipamento, name='detalhe_equipamento'),
    path('equipamentos/<int:equipamento_id>/editar/', views.editar_equipamento, name='editar_equipamento'),
    path('equipamentos/<int:equipamento_id>/excluir/', views.excluir_equipamento, name='excluir_equipamento'),
    path('equipamentos/<int:equipamento_id>/movimentar/', views.movimentar_equipamento, name='movimentar_equipamento'),

    # ===== MOVIMENTAÇÕES =====
    path('movimentacoes/', views.lista_movimentacoes, name='lista_movimentacoes'),
    path('movimentacoes/<int:movimentacao_id>/aprovar/', views.aprovar_movimentacao, name='aprovar_movimentacao'),
    path('movimentacoes/<int:movimentacao_id>/concluir/', views.concluir_movimentacao, name='concluir_movimentacao'),

    # ===== CATEGORIAS =====
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/nova/', views.nova_categoria, name='nova_categoria'),

    # ===== ARMAZÉNS =====
    path('armazens/', views.lista_armazens, name='lista_armazens'),
    path('armazens/novo/', views.novo_armazem, name='novo_armazem'),

    # ===== PATRIMÓNIO GLOBAL =====
    path('patrimonio-global/', views.patrimonio_global, name='patrimonio_global'),
]
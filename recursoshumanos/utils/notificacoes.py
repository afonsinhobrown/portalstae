# recursoshumanos/utils/notificacoes.py
from django.db.models import Q
from django.contrib.auth.models import User
from ..models import NotificacaoSistema, ConfiguracaoNotificacao
import logging

logger = logging.getLogger(__name__)


class Notificador:
    """Sistema centralizado de notificações internas"""

    @staticmethod
    def criar_notificacao(usuario, tipo, titulo, mensagem, link_url='', link_texto=''):
        """Cria uma notificação no sistema"""
        try:
            notificacao = NotificacaoSistema.objects.create(
                usuario=usuario,
                tipo=tipo,
                titulo=titulo,
                mensagem=mensagem,
                url_link=link_url,
                prioridade='media'
            )
            logger.info(f"Notificação criada para {usuario.username}: {titulo}")
            return notificacao
        except Exception as e:
            logger.error(f"Erro ao criar notificação: {str(e)}")
            return None

    @staticmethod
    def _filtrar_por_configuracao(usuario, tipo):
        """Filtra notificações baseado na configuração do usuário"""
        try:
            config, created = ConfiguracaoNotificacao.objects.get_or_create(
                usuario=usuario,
                defaults={
                    'mostrar_licencas': True,
                    'mostrar_avaliacoes': True,
                    'mostrar_documentos': True,
                    'mostrar_mensagens': True,
                    'mostrar_sistema': True,
                    'som_notificacoes': True,
                }
            )

            # Verificar se deve mostrar este tipo de notificação
            if 'licenca' in tipo and not config.mostrar_licencas:
                return False
            elif 'avaliacao' in tipo and not config.mostrar_avaliacoes:
                return False
            elif 'documento' in tipo and not config.mostrar_documentos:
                return False
            elif 'mensagem' in tipo and not config.mostrar_mensagens:
                return False
            elif 'sistema' in tipo and not config.mostrar_sistema:
                return False

            return True

        except Exception as e:
            logger.error(f"Erro ao verificar configuração: {str(e)}")
            return True

    # ========== MÉTODOS ESPECÍFICOS POR EVENTO ==========

    @staticmethod
    def licenca_submetida(licenca):
        """Notificar RH e chefe sobre nova licença"""
        from django.contrib.auth.models import User

        # Notificar RH/staff
        rh_users = User.objects.filter(
            Q(is_staff=True) | Q(groups__name='rh_staff')
        ).distinct()

        for user in rh_users:
            if Notificador._filtrar_por_configuracao(user, 'licenca'):
                Notificador.criar_notificacao(
                    usuario=user,
                    tipo='licenca_submetida',
                    titulo='Nova Licença Submetida',
                    mensagem=f'{licenca.funcionario.nome_completo} submeteu uma licença de {licenca.dias_utilizados} dias.',
                    link_url=f'/rh/licencas/{licenca.id}/',
                    link_texto='Ver Licença'
                )

        # Notificar chefe do funcionário
        try:
            chefe = licenca.funcionario.get_chefe_imediato()
            if chefe and chefe.user:
                if Notificador._filtrar_por_configuracao(chefe.user, 'licenca'):
                    Notificador.criar_notificacao(
                        usuario=chefe.user,
                        tipo='licenca_submetida',
                        titulo='Licença do Subordinado Aguardando Parecer',
                        mensagem=f'{licenca.funcionario.nome_completo} submeteu uma licença que requer seu parecer.',
                        link_url=f'/rh/licenca/{licenca.id}/dar-parecer/',
                        link_texto='Dar Parecer'
                    )
        except Exception as e:
            logger.error(f"Erro ao notificar chefe: {str(e)}")

    @staticmethod
    def licenca_parecer_chefe(licenca):
        """Notificar funcionário sobre parecer do chefe"""
        if licenca.chefe_aprovador and licenca.funcionario.user:
            status_text = 'favorável' if licenca.status_chefia == 'favoravel' else 'desfavorável'

            if Notificador._filtrar_por_configuracao(licenca.funcionario.user, 'licenca'):
                Notificador.criar_notificacao(
                    usuario=licenca.funcionario.user,
                    tipo='licenca_parecer_chefe',
                    titulo='Parecer do Chefe na Sua Licença',
                    mensagem=f'Seu chefe {licenca.chefe_aprovador.get_full_name()} emitiu parecer {status_text} sobre sua licença.',
                    link_url=f'/rh/licencas/minhas/',
                    link_texto='Ver Licença'
                )

        # Notificar diretor se parecer foi favorável
        if licenca.status_chefia in ['favoravel', 'com_reservas']:
            diretores = User.objects.filter(
                funcionario__funcao='director',
                funcionario__sector__direcao=licenca.funcionario.sector.direcao
            )

            for diretor in diretores:
                if Notificador._filtrar_por_configuracao(diretor, 'licenca'):
                    Notificador.criar_notificacao(
                        usuario=diretor,
                        tipo='licenca_parecer_chefe',
                        titulo='Licença Aguardando Autorização',
                        mensagem=f'Licença de {licenca.funcionario.nome_completo} com parecer {licenca.get_status_chefia_display()} aguarda sua autorização.',
                        link_url=f'/rh/licenca/{licenca.id}/autorizar/',
                        link_texto='Autorizar/Reprovar'
                    )

    @staticmethod
    def licenca_autorizada(licenca):
        """Notificar funcionário sobre licença autorizada"""
        if licenca.funcionario.user and Notificador._filtrar_por_configuracao(licenca.funcionario.user, 'licenca'):
            Notificador.criar_notificacao(
                usuario=licenca.funcionario.user,
                tipo='licenca_autorizada',
                titulo='Licença Autorizada!',
                mensagem=f'Sua licença de {licenca.dias_utilizados} dias foi autorizada.',
                link_url=f'/rh/licencas/minhas/',
                link_texto='Ver Detalhes'
            )

        # Notificar RH
        rh_users = User.objects.filter(
            Q(is_staff=True) | Q(groups__name='rh_staff')
        ).distinct()

        for user in rh_users:
            if Notificador._filtrar_por_configuracao(user, 'licenca'):
                Notificador.criar_notificacao(
                    usuario=user,
                    tipo='licenca_autorizada',
                    titulo='Licença Autorizada',
                    mensagem=f'Licença de {licenca.funcionario.nome_completo} foi autorizada.',
                    link_url=f'/rh/licencas/{licenca.id}/',
                    link_texto='Ver Licença'
                )

    @staticmethod
    def licenca_rejeitada(licenca):
        """Notificar funcionário sobre licença rejeitada"""
        if licenca.funcionario.user and Notificador._filtrar_por_configuracao(licenca.funcionario.user, 'licenca'):
            Notificador.criar_notificacao(
                usuario=licenca.funcionario.user,
                tipo='licenca_rejeitada',
                titulo='Licença Rejeitada',
                mensagem=f'Sua licença foi rejeitada.',
                link_url=f'/rh/licencas/minhas/',
                link_texto='Ver Detalhes'
            )

    @staticmethod
    def avaliacao_realizada(avaliacao):
        """Notificar funcionário sobre nova avaliação"""
        if avaliacao.funcionario.user and Notificador._filtrar_por_configuracao(avaliacao.funcionario.user,
                                                                                'avaliacao'):
            Notificador.criar_notificacao(
                usuario=avaliacao.funcionario.user,
                tipo='avaliacao_realizada',
                titulo='Nova Avaliação de Desempenho',
                mensagem=f'Você foi avaliado por {avaliacao.avaliado_por.get_full_name()} com classificação {avaliacao.classificacao_final}.',
                link_url=f'/rh/avaliacoes/minhas/',
                link_texto='Ver Avaliação'
            )

    @staticmethod
    def documento_compartilhado(documento, usuarios):
        """Notificar usuários sobre documento compartilhado"""
        for usuario in usuarios:
            if Notificador._filtrar_por_configuracao(usuario, 'documento'):
                Notificador.criar_notificacao(
                    usuario=usuario,
                    tipo='documento_compartilhado',
                    titulo='Novo Documento Compartilhado',
                    mensagem=f'Documento "{documento.titulo}" foi compartilhado com você.',
                    link_url=f'/rh/comunicacao/documentos/{documento.id}/',
                    link_texto='Ver Documento'
                )

    @staticmethod
    def mensagem_recebida(mensagem, destinatarios):
        """Notificar destinatários sobre nova mensagem"""
        for usuario in destinatarios:
            if usuario != mensagem.remetente and Notificador._filtrar_por_configuracao(usuario, 'mensagem'):
                Notificador.criar_notificacao(
                    usuario=usuario,
                    tipo='mensagem_recebida',
                    titulo=f'Nova Mensagem em {mensagem.canal.nome}',
                    mensagem=f'{mensagem.remetente.get_full_name()} enviou uma mensagem no canal {mensagem.canal.nome}.',
                    link_url=f'/rh/comunicacao/canal/{mensagem.canal.id}/',
                    link_texto='Ver Mensagem'
                )

    @staticmethod
    def promocao_concedida(promocao):
        """Notificar funcionário sobre promoção"""
        if promocao.funcionario.user and Notificador._filtrar_por_configuracao(promocao.funcionario.user, 'sistema'):
            Notificador.criar_notificacao(
                usuario=promocao.funcionario.user,
                tipo='promocao_concedida',
                titulo='Parabéns! Promoção Concedida',
                mensagem=f'Você foi promovido para {promocao.cargo_atual}. Parabéns pela conquista!',
                link_url=f'/rh/promocoes/',
                link_texto='Ver Detalhes'
            )

    @staticmethod
    def lembrete_ferias(funcionario, dias_vencendo):
        """Notificar sobre férias prestes a vencer"""
        if funcionario.user and Notificador._filtrar_por_configuracao(funcionario.user, 'sistema'):
            Notificador.criar_notificacao(
                usuario=funcionario.user,
                tipo='lembrete_ferias',
                titulo='Lembrete de Férias',
                mensagem=f'Você tem {dias_vencendo} dias de férias prestes a vencer.',
                link_url=f'/rh/licencas/solicitar/',
                link_texto='Marcar Férias'
            )

    @staticmethod
    def sistema_manutencao(usuarios, mensagem):
        """Notificar sobre manutenção do sistema"""
        for usuario in usuarios:
            if Notificador._filtrar_por_configuracao(usuario, 'sistema'):
                Notificador.criar_notificacao(
                    usuario=usuario,
                    tipo='sistema',
                    titulo='Manutenção do Sistema',
                    mensagem=mensagem,
                    link_url='/rh/dashboard/',
                    link_texto='Ir para Dashboard'
                )
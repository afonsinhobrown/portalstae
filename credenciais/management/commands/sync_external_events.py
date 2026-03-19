from django.core.management.base import BaseCommand
from django.utils import timezone
from credenciais.models import Evento
# Tentar importar modelos externos. 
# Usamos try/except para evitar crash se a app DFEC não estiver instalada/configurada corretamente
try:
    from dfec.models.completo import Formacao, Eleicao
    DFEC_AVAILABLE = True
except ImportError:
    DFEC_AVAILABLE = False
    print("Aviso: App DFEC não encontrada ou erro de importação.")

class Command(BaseCommand):
    help = 'Sincroniza eventos de apps externas (DFEC, etc) para a tabela de Eventos de Credenciais'

    def handle(self, *args, **kwargs):
        if not DFEC_AVAILABLE:
            self.stdout.write(self.style.WARNING("DFEC não disponível. Pulando."))
            return

        count = 0
        updated = 0
        
        # 1. Importar FORMAÇÕES
        self.stdout.write("Sincronizando Formações do DFEC...")
        
        # Mapeamento de status DFEC -> Ativo
        # 'planejada', 'ativa' -> True
        # 'concluida', 'cancelada' -> False (ou True se quisermos emitir certificados pos-evento? Melhor True se concluida)
        
        for f in Formacao.objects.all():
            try:
                # Construir dados
                nome_evt = f.nome
                if not nome_evt and f.atividade:
                    nome_evt = f.atividade.nome
                
                if not nome_evt:
                    nome_evt = f"Formação DFEC #{f.id}"

                # Prefixo para identificar visualmente
                if f.tipo_formacao:
                     nome_final = f"[DFEC] {f.tipo_formacao}: {nome_evt}"
                else:
                     nome_final = f"[DFEC] {nome_evt}"
                
                # Datas (via Atividade)
                d_ini = timezone.now().date()
                d_fim = timezone.now().date()
                
                if hasattr(f, 'atividade') and f.atividade:
                    d_ini = f.atividade.data_inicio or d_ini
                    d_fim = f.atividade.data_fim or d_fim
                
                # Status
                eh_ativo = True
                if f.status == 'cancelada':
                    eh_ativo = False
                
                # Abrangencia e Provincia
                # Normalizar values para coincidir com choices do Evento
                # choices=[('nacional',...), ('provincial',...), ('distrital',...), ('estrangeiro',...)]
                abrangencia = 'nacional'
                if f.nivel:
                    if 'provincia' in str(f.nivel).lower(): abrangencia = 'provincial'
                    elif 'distrit' in str(f.nivel).lower(): abrangencia = 'distrital'
                    elif 'central' in str(f.nivel).lower(): abrangencia = 'nacional'
                
                provincia = None
                if f.provincia:
                    # Tenta pegar valor da escolha ou string
                    provincia = str(f.provincia)

                defaults = {
                    'categoria': 'formacao',
                    'data_inicio': d_ini,
                    'data_fim': d_fim,
                    'local': f.local_realizacao or 'N/D',
                    'provincia': provincia or 'Maputo', # Default safe
                    'abrangencia': abrangencia,
                    'ativo': eh_ativo,
                    'descricao': f"Importado automaticamente do DFEC. Status original: {f.status}"
                }

                # Get or Create
                # Usamos o nome como chave única. Se mudou nome lá, cria novo aqui.
                obj, created = Evento.objects.get_or_create(
                    nome=nome_final,
                    defaults=defaults
                )

                if created:
                    count += 1
                else:
                    # Update se necessário (opcional, mas bom manter sync)
                    changed = False
                    if obj.ativo != eh_ativo:
                        obj.ativo = eh_ativo
                        changed = True
                    # Não sobrescrevemos tudo para não perder edições manuais locais
                    if changed:
                        obj.save()
                        updated += 1
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erro ao processar Formacao ID {f.id}: {e}"))

        # 2. Importar ELEIÇÕES (Se houver)
        self.stdout.write("Sincronizando Eleições...")
        try:
             for e in Eleicao.objects.all():
                 nome_eleicao = f"[Eleição] {e.nome}"
                 Evento.objects.get_or_create(
                     nome=nome_eleicao,
                     defaults={
                         'categoria': 'oficial',
                         'data_inicio': e.data_eleicao, # Supondo campo data_eleicao
                         'data_fim': e.data_eleicao,
                         'ativo': e.ativa, # Supondo campo ativa
                         'descricao': f"Eleição oficial importada do DFEC."
                     }
                 )
        except Exception as e:
             # Pode falhar se campos forem diferentes, ignorar silenciosamente ou logar
             # print(f"Info: Eleicoes sync skip: {e}")
             pass

        self.stdout.write(self.style.SUCCESS(f"Sincronização Finalizada: {count} criados, {updated} atualizados."))

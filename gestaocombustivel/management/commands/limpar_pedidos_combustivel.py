from django.core.management.base import BaseCommand
from gestaocombustivel.models import PedidoCombustivel, FornecedorCombustivel, ContratoCombustivel

class Command(BaseCommand):
    help = 'Limpa pedidos de combustível antigos e dados inconsistentes para reiniciar o sistema com contratos.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando limpeza de dados de combustível...")

        # 1. Apagar todos os pedidos de combustível existentes
        count_pedidos = PedidoCombustivel.objects.count()
        if count_pedidos > 0:
            PedidoCombustivel.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Removidos {count_pedidos} pedidos de combustível antigos.'))
        else:
            self.stdout.write('Nenhum pedido de combustível para remover.')

        # 2. Resetar consumo dos contratos (se houver algum criado manulamente e sujo)
        for contrato in ContratoCombustivel.objects.all():
            contrato.litros_consumidos = 0
            contrato.valor_pago = 0
            contrato.save()
            
        self.stdout.write(self.style.SUCCESS('Consumo dos contratos resetado para 0.'))

        # 3. Listar fornecedores para lembrar o usuário de criar contratos
        fornecedores = FornecedorCombustivel.objects.filter(activo=True)
        self.stdout.write('\nFornecedores Ativos:')
        for f in fornecedores:
            contratos = f.contratos.count()
            status = "COM CONTRATO" if contratos > 0 else "SEM CONTRATO"
            color = self.style.SUCCESS if contratos > 0 else self.style.WARNING
            self.stdout.write(color(f'- {f.nome} (NUIT: {f.nuit}) -> {status}'))

        self.stdout.write(self.style.SUCCESS('\nLimpeza concluída! O sistema está pronto para novos contratos e pedidos.'))

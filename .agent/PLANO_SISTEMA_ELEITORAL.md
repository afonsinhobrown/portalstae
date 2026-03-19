# PLANO DE IMPLEMENTAÇÃO - SISTEMA ELEITORAL COMPLETO
# =======================================================
# Data: 2025-12-29
# Status: Em Desenvolvimento

## APPS CRIADAS (7 Total)

### 1. UGEA - Gestão de Concursos Públicos ✓ (App criada)
**Objetivo:** Gerir todo processo de procurement/licitações da instituição

**Models Necessários:**
- `Concurso` - Anúncios, especificações, datas, tipo
- `CadernoEncargos` - Especificações técnicas, requisitos
- `Proposta` - Propostas submetidas por fornecedores
- `AvaliacaoProposta` - Avaliação técnica e financeira
- `JuriConcurso` - Membros do júri de avaliação
- `ContratoResultante` - Contratos adjudicados
- `AcompanhamentoExecucao` - Follow-up da execução

### 2. PARTIDOS - Gestão de Partidos Políticos ✅ (MODELS CRIADOS)
**Objetivo:** Cadastro completo de partidos

**Models Criados:**
- `Partido` - Dados básicos, símbolo, cores, contactos
- `LiderancaPartido` - Histórico de liderança

### 3. CIRCULOSELEITORAIS - Gestão de Círculos Eleitorais ✓ (App criada)
**Objetivo:** Gestão de círculos por eleição

**Models Necessários:**
- `CirculoEleitoral` - Vinculado a uma Eleição específica
- `PostoVotacao` - Postos dentro do círculo
- `MesaVotacao` - Mesas dentro dos postos
- `EstatisticasCirculo` - Nº eleitores, nº mesas, etc.

### 4. ELEICOES - Gestão de Eleições ✓ (App JÁ EXISTIA - precisa expansão)
**Objetivo:** Configuração e dados de eleições

**Models a Adicionar/Verificar:**
- `Eleicao` - Tipo, data, configurações
- `TipoEleicao` - Presidencial, Legislativa, Autárquica, etc.
- `ConfiguracaoEleicao` - Parâmetros específicos

### 5. CANDIDATURAS - Gestão de Candidaturas ✓ (App criada)
**Objetivo:** Inscrições de partidos e listas

**Models Necessários:**
- `InscricaoPartido` - Inscrição do partido na eleição
- `ListaCandidatos` - Lista por círculo eleitoral
- `Candidato` - Candidato individual (Titular/Suplente)
- `DocumentacaoCandidatura` - Docs submetidos
- `AvaliacaoCandidatura` - Validação técnica
- `RelatorioEstatistico` - Faixas etárias, género, etc.

### 6. RS - Recenseamento & Logística ✓ (App criada)
**Objetivo:** Planejamento completo do processo eleitoral

**Models Necessários:**
**Recenseamento:**
- `DadosRecenseamento` - Importação de dados
- `EstatisticasRecenseamento` - Por círculo/posto

**Planejamento:**
- `PlanoLogistico` - Plano geral (Recenseamento ou Votação)
- `Atividade` - Atividades específicas
- `OrcamentoEleitoral` - Orçamentos detalhados
- `ItemOrcamento` - Itens específicos

**Documentos Eleitorais:**
- `TipoDocumento` - Tipos (Cartão Eleitor, Boletim Voto, etc.)
- `ModeloDocumento` - Templates editáveis
- `DocumentoGerado` - Documentos produzidos
- `ConfiguracaoImpressao` - Parâmetros de impressão

### 7. APURAMENTO - Apuramento de Resultados ✓ (App criada)
**Objetivo:** Gestão de resultados e publicação

**Models Necessários:**
- `ResultadoMesa` - Resultado por mesa de votação
- `ResultadoDistrito` - Resumo distrital
- `ResultadoCirculo` - Resumo por círculo
- `ResultadoNacional` - Resumo nacional
- `AtaApuramento` - Atas de apuramento
- `PublicacaoResultado` - Histórico de publicações

## PRIORIDADE DE IMPLEMENTAÇÃO

### FASE 1 (URGENTE):
1. ✅ PARTIDOS - Models criados
2. CIRCULOSELEITORAIS - Models (próximo)
3. ELEICOES - Verificar/expandir models existentes

### FASE 2 (IMPORTANTE):
4. CANDIDATURAS - Models + lógica de validação
5. RS - Início com DadosRecenseamento + PlanoLogistico

### FASE 3 (SEQUENCIAL):
6. APURAMENTO - Após eleições/candidaturas
7. UGEA - Pode ser paralelo

## INTER-RELACIONAMENTO DAS APPS

```
PARTIDOS ──┐
           ├──> CANDIDATURAS ──> APURAMENTO
ELEICOES ──┤         │
           │         │
CIRCULOSELEITORAIS ──┘         │
           │                   │
           ├──> RS ─────────────┘
           │
UGEA (independente, suporta procurement de materiais eleitorais)
```

## PRÓXIMOS PASSOS IMEDIATOS

1. Criar models para CIRCULOSELEITORAIS
2. Verificar app ELEICOES existente
3. Criar models para CANDIDATURAS
4. Fazer migrations
5. Testar integridade referencial

## NOTAS TÉCNICAS

- Todas as apps devem ter admin.py configurado
- Criar views básicas (listar, detalhe, criar, editar)
- Templates seguindo padrão do portal
- Permissões específicas por app
- Logs de auditoria para alterações críticas

## STATUS ATUAL
- Apps Django: 7/7 criadas ✓
- Settings.py: Registradas ✓
- Models: 1/7 completo (PARTIDOS)
- Próximo: CIRCULOSELEITORAIS models

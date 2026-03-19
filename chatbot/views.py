from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
import json
from datetime import datetime


# REMOVA estas linhas:
# from .models import FAQEntry, ConversationLog, KnowledgeGap
# from .advanced_engine import AdvancedChatbotEngine
# from .memory import ConversationMemory
# from .learning import LearningSystem

# REMOVA estas linhas também:
# chatbot_engine = AdvancedChatbotEngine()
# learning_system = LearningSystem()


def get_chatbot_engine():
    """Lazy loading para chatbot engine"""
    from .advanced_engine import AdvancedChatbotEngine
    return AdvancedChatbotEngine()


def get_learning_system():
    """Lazy loading para learning system"""
    from .learning import LearningSystem
    return LearningSystem()


def chat_interface(request):
    """Interface principal do chatbot"""
    return render(request, 'chatbot/interface.html')


@csrf_exempt
def advanced_chat_api(request):
    """API do chatbot avançado"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()

            if not user_message:
                return JsonResponse({'response': 'Por favor, digite uma mensagem.'})

            # Obtém ou cria session ID
            if not request.session.session_key:
                request.session.create()
            session_id = request.session.session_key

            # Processa a mensagem (com lazy loading)
            chatbot_engine = get_chatbot_engine()
            response = chatbot_engine.process_message_advanced(user_message, session_id)

            # Log da conversa (com try-except)
            try:
                from .models import ConversationLog
                ConversationLog.objects.create(
                    user_message=user_message,
                    bot_response=response,
                    intent_detected=chatbot_engine._analyze_intent(user_message),
                    confidence=0.8,  # Estimativa
                    session_id=session_id
                )
            except Exception as e:
                print(f"Aviso: Não foi possível criar log da conversa: {e}")

            return JsonResponse({
                'response': response,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            return JsonResponse({
                'response': 'Desculpe, ocorreu um erro. Tente novamente.',
                'error': str(e)
            }, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


def chat_widget(request):
    """Widget para embed"""
    return render(request, 'chatbot/widget.html')


@login_required
@permission_required('chatbot.add_faqentry')
def contribuicao_painel(request):
    """Painel para contribuição de conhecimento"""
    try:
        from .models import ConversationLog, KnowledgeGap, FAQEntry
        from django.db import models

        frequent_questions = ConversationLog.objects.values('user_message').annotate(
            count=models.Count('id')
        ).order_by('-count')[:10]

        knowledge_gaps = KnowledgeGap.objects.filter(resolvido=False)[:10]

        if request.method == 'POST':
            pergunta = request.POST.get('pergunta')
            resposta = request.POST.get('resposta')
            tags = [tag.strip() for tag in request.POST.get('tags', '').split(',')]

            FAQEntry.objects.create(
                pergunta=pergunta,
                resposta=resposta,
                tags=tags,
                fonte=f"Contribuição: {request.user.username}",
                confianca=0.9
            )

            # Marca gaps relacionados como resolvidos
            related_gaps = KnowledgeGap.objects.filter(
                pergunta_nao_respondida__icontains=pergunta[:20]
            )
            related_gaps.update(resolvido=True)

            return render(request, 'chatbot/contribuicao_painel.html', {
                'frequent_questions': frequent_questions,
                'knowledge_gaps': knowledge_gaps,
                'success': True
            })

        return render(request, 'chatbot/contribuicao_painel.html', {
            'frequent_questions': frequent_questions,
            'knowledge_gaps': knowledge_gaps,
            'success': False
        })

    except Exception as e:
        print(f"Aviso: Erro no painel de contribuição: {e}")
        return render(request, 'chatbot/contribuicao_painel.html', {
            'frequent_questions': [],
            'knowledge_gaps': [],
            'success': False,
            'error': 'Sistema temporariamente indisponível'
        })


@login_required
def estatisticas_painel(request):
    """Painel de estatísticas"""
    try:
        from .models import ConversationLog, FAQEntry
        learning_system = get_learning_system()
        learning_system.detect_knowledge_gaps()
        suggestions = learning_system.get_improvement_suggestions()

        stats = {
            'total_conversas': ConversationLog.objects.count(),
            'total_faqs': FAQEntry.objects.count(),
            'lacunas_nao_resolvidas': suggestions.get('total_gaps', 0),
            'perguntas_frequentes': suggestions.get('most_frequent', [])
        }

        return render(request, 'chatbot/estatisticas_painel.html', {
            'stats': stats,
            'suggestions': suggestions
        })

    except Exception as e:
        print(f"Aviso: Erro no painel de estatísticas: {e}")
        return render(request, 'chatbot/estatisticas_painel.html', {
            'stats': {
                'total_conversas': 0,
                'total_faqs': 0,
                'lacunas_nao_resolvidas': 0,
                'perguntas_frequentes': []
            },
            'suggestions': {},
            'error': 'Sistema temporariamente indisponível'
        })
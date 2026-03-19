from django.db import models
from .models import KnowledgeGap, ConversationLog


class LearningSystem:
    def __init__(self):
        self.feedback_threshold = 3

    def detect_knowledge_gaps(self):
        """Detecta lacunas no conhecimento"""
        low_confidence_logs = ConversationLog.objects.filter(
            confidence__lt=0.5
        )[:10]

        for log in low_confidence_logs:
            gap, created = KnowledgeGap.objects.get_or_create(
                pergunta_nao_respondida=log.user_message,
                defaults={
                    'contexto': log.bot_response,
                    'frequencia': 1
                }
            )

            if not created:
                gap.frequencia += 1
                gap.save()

    def get_improvement_suggestions(self):
        """Sugestões de melhoria baseadas em logs"""
        gaps = KnowledgeGap.objects.filter(resolvido=False)
        return {
            'total_gaps': gaps.count(),
            'most_frequent': gaps.order_by('-frequencia')[:5],
            'recent_gaps': gaps.order_by('-data_deteccao')[:5]
        }
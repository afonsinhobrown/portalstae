from django import forms
from .models import TemplateImportacao, ImportacaoLog, ConfiguracaoSistema  # ← Importe do models.py


class TemplateImportacaoForm(forms.ModelForm):
    class Meta:
        model = TemplateImportacao
        fields = ['nome', 'app_destino', 'modelo_destino', 'ficheiro_template', 'mapeamento_campos', 'activo']
        widgets = {
            'mapeamento_campos': forms.Textarea(
                attrs={'rows': 4, 'placeholder': '{"coluna_excel": "campo_model", ...}'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'app_destino': forms.Select(attrs={'class': 'form-control'}),
            'modelo_destino': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_mapeamento_campos(self):
        mapeamento = self.cleaned_data.get('mapeamento_campos')
        try:
            import json
            if isinstance(mapeamento, str):
                mapeamento = json.loads(mapeamento)
            return mapeamento
        except json.JSONDecodeError:
            raise forms.ValidationError("Formato JSON inválido para mapeamento de campos")


class ImportacaoForm(forms.ModelForm):
    template = forms.ModelChoiceField(
        queryset=TemplateImportacao.objects.filter(activo=True),
        empty_label="Selecione um template...",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    ficheiro_importado = forms.FileField(
        label="Ficheiro para Importar",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls,.csv'})
    )

    class Meta:
        model = ImportacaoLog
        fields = ['template', 'ficheiro_importado']


class ConfiguracaoSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracaoSistema  # ← Agora vem do models.py
        fields = ['chave', 'valor', 'descricao']
        widgets = {
            'chave': forms.TextInput(attrs={'class': 'form-control'}),
            'valor': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

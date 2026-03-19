# fix_models.py
import sys

path = r'c:\Users\Acer\Documents\tecnologias\portalstae\dfec\models\completo.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('data_criacao = models.DateTimeField(auto_now_add=True)', 'data_criacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)')
content = content.replace('data_atualizacao = models.DateTimeField(auto_now=True)', 'data_atualizacao = models.DateTimeField(auto_now=True, null=True, blank=True)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("File fixed.")

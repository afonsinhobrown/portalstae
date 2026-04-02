import os
import glob

rs_templates_dir = "templates/rs"

def update_templates():
    files = glob.glob(os.path.join(rs_templates_dir, "*.html"))
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% block menu_items %}" in content:
            # Check if it already has the new menu item
            if "Divisão Eleição" not in content and "Divisão por Eleição" not in content:
                # Add the generic entry for Divisao Eleicao
                # Insert right after Ciclos Eleitorais
                old_str = '<a href="{% url \'rs:lista_eleicoes\' %}" class="menu-item active"><i class="fas fa-vote-yea"></i> <span>Ciclos Eleitorais</span></a>'
                old_str2 = '<a href="{% url \'rs:lista_eleicoes\' %}" class="menu-item"><i class="fas fa-vote-yea"></i> <span>Ciclos Eleitorais</span></a>'
                
                new_str = '<a href="{% url \'rs:divisao_eleicao_index\' %}" class="menu-item {% if \'divisao-eleicao\' in request.path %}active{% endif %}"><i class="fas fa-sitemap"></i> <span>Divisão Eleição</span></a>'
                
                content = content.replace(old_str, old_str + '\n' + new_str)
                content = content.replace(old_str2, old_str2 + '\n' + new_str)
                
                with open(file, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == "__main__":
    update_templates()

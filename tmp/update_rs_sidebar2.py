import os
import glob

rs_templates_dir = "templates/rs"

def update_templates():
    files = glob.glob(os.path.join(rs_templates_dir, "*.html"))
    modified_count = 0
    for file in files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "{% block menu_items %}" in content:
            if "rs:divisao_eleicao_index" not in content:
                # Localize and inject after Ciclos Eleitorais
                match_str = "<span>Ciclos Eleitorais</span></a>"
                if match_str in content:
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if match_str in line:
                            new_lines.append(line.split('<a ')[0] + '<a href="{% url \'rs:divisao_eleicao_index\' %}" class="menu-item {% if \'divisao-eleicao\' in request.path %}active{% endif %}"><i class="fas fa-sitemap"></i> <span>Divisão Eleição</span></a>')
                    
                    with open(file, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(new_lines))
                    modified_count += 1
                    print(f"Modified: {file}")
    print(f"Total modified: {modified_count}")

if __name__ == "__main__":
    update_templates()

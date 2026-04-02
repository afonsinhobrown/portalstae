import os
import glob
import traceback

def fix_menus():
    files = glob.glob('templates/rs/*.html')
    count = 0
    for filepath in files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            s1 = '<a href="{vw_url}" class="menu-item"><i class="fas fa-vote-yea"></i> <span>Ciclos Eleitorais</span></a>'.replace('{vw_url}', "{% url 'rs:lista_eleicoes' %}")
            s2 = '<a href="{vw_url}" class="menu-item active"><i class="fas fa-vote-yea"></i> <span>Ciclos Eleitorais</span></a>'.replace('{vw_url}', "{% url 'rs:lista_eleicoes' %}")
            
            new_item = '\n<a href="{vw_url}" class="menu-item"><i class="fas fa-sitemap"></i> <span>Divisão Eleição</span></a>'.replace('{vw_url}', "{% url 'rs:divisao_eleicao_index' %}")
            
            if 'rs:divisao_eleicao_index' not in content:
                if s1 in content:
                    content = content.replace(s1, s1 + new_item)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed {filepath} via s1")
                    count += 1
                elif s2 in content:
                    content = content.replace(s2, s2 + new_item)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Fixed {filepath} via s2")
                    count += 1
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            traceback.print_exc()

    print(f"Total files fixed: {count}")

if __name__ == '__main__':
    fix_menus()

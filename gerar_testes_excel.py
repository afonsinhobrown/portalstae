import pandas as pd
import io
import os

def gerar_excel(filename, partido_sigla, circulo_nome, num_mandatos):
    # 1. Cabecalho (Simulando o que o sistema espera)
    # Procuramos por palabras-chave na coluna A e valor na coluna B
    # O sistema procura "CIRCULO" ou "PARTIDO" na coluna A
    
    # 2. Dados dos Candidatos
    rows = []
    # Efetivos
    for i in range(1, num_mandatos + 1):
        rows.append([
            f"Candidato Efetivo {i} {partido_sigla}",
            f"100{partido_sigla}{i}",
            f"888{i}",
            "1990-01-01",
            "M" if i % 2 == 0 else "F",
            "Efetivo",
            i
        ])
    # Suplentes (Mínimo 3)
    for i in range(1, 4):
        rows.append([
            f"Candidato Suplente {i} {partido_sigla}",
            f"200{partido_sigla}{i}",
            f"999{i}",
            "1995-06-15",
            "F" if i % 2 == 0 else "M",
            "Suplente",
            i
        ])
        
    df = pd.DataFrame(rows, columns=["Nome Completo", "BI", "Cartão Eleitor", "Data Nascimento (AAAA-MM-DD)", "Género (M/F)", "Tipo (Efetivo/Suplente)", "Posição"])
    
    # Salvar com cabeçalho nas primeiras linhas
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Lista_Candidatos', startrow=5)
        ws = writer.sheets['Lista_Candidatos']
        
        # Cabeçalho para o motor de busca do código
        ws.cell(row=1, column=1, value="PARTIDO:")
        ws.cell(row=1, column=2, value=partido_sigla)
        
        ws.cell(row=3, column=1, value="CÍRCULO:")
        ws.cell(row=3, column=2, value=circulo_nome)
        
        ws.cell(row=5, column=1, value="SECRETARIADO TÉCNICO DE ADMINISTRAÇÃO ELEITORAL - MOÇAMBIQUE")

    print(f"Ficheiro {filename} gerado para {partido_sigla} em {circulo_nome} ({num_mandatos} mandatos).")

if __name__ == "__main__":
    # Pedido: P1 Maputo, P2 Maputo, P2 Xai-Xai
    gerar_excel('Candidaturas_P1_Maputo.xlsx', 'P1', 'MAPUTO CIDADE', 40)
    gerar_excel('Candidaturas_P2_Maputo.xlsx', 'P2', 'MAPUTO CIDADE', 40)
    gerar_excel('Candidaturas_P2_XaiXai.xlsx', 'P2', 'CIDADE DE XAI-XAI', 50)

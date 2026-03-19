# create_excel_models.py
import pandas as pd
import os

def create_model(filename, count, start_id):
    data = []
    categorias = ['BRIGADISTA', 'MMV', 'AGENTE_EC', 'TECNICO']
    provincias = ['GAZA', 'MAPUTO_CIDADE', 'SOFALA', 'NAMPULA']
    
    for i in range(count):
        idx = start_id + i
        genero = 'M' if i % 2 == 0 else 'F'
        data.append({
            "nome_completo": f"Participante Importado {idx}",
            "categoria": categorias[i % len(categorias)],
            "bilhete_identidade": f"9900{idx:05d}",
            "telefone": f"82{idx:07d}",
            "genero(M/F)": genero,
            "data_nascimento(AAAA-MM-DD)": f"19{80 + (i%20)}-01-01",
            "provincia": provincias[i % len(provincias)],
            "distrito": "Distrito Teste"
        })
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"Ficheiro {filename} criado com {count} registos.")

if __name__ == "__main__":
    create_model("modelo1.xlsx", 30, 1000)
    create_model("modelo2.xlsx", 50, 2000)

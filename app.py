import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="Gestão de Projetos PPCI", layout="centered")
st.title("📁 Ferramenta de Projetos PPCI")

# Função para gerar nome do arquivo
def gerar_nome_arquivo(nome_projeto, nome_arquivo_entrada=None):
    if nome_arquivo_entrada:
        match = re.search(r"-R(\d+)", nome_arquivo_entrada)
        if match:
            numero = int(match.group(1)) + 1
        else:
            numero = 1
        novo_nome = re.sub(r"-R\d+", f"-R{numero:02}", nome_arquivo_entrada)
    else:
        novo_nome = f"checklistINC_{nome_projeto}-R00.xlsx"
    return novo_nome

# Escolha do modo
modo = st.radio("Como deseja começar?", ["📄 Revisar projeto existente", "🆕 Criar novo projeto"])

# Inicializa o DataFrame
df = pd.DataFrame()
arquivo = None
nome_arquivo_entrada = None

if modo == "📄 Revisar projeto existente":
    arquivo = st.file_uploader("Anexe a planilha do projeto (.xlsx)", type=["xlsx"])
    if arquivo:
        nome_arquivo_entrada = arquivo.name
        try:
            df = pd.read_excel(arquivo)
            st.success("Planilha carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

elif modo == "🆕 Criar novo projeto":
    df = pd.DataFrame([{
        "NomeProjeto": "",
        "Ocupacao": "A-1",
        "Area": 100.0,
        "Altura": 3.0,
        "UltimoUsuario": "",
        "UltimaModificacao": datetime.now().strftime('%d/%m/%Y %H:%M')
    }])
    st.info("Novo projeto iniciado. Preencha os dados abaixo.")

# Se o DataFrame estiver disponível, mostra os campos para edição
if not df.empty:
    st.subheader("📝 Dados do Projeto")

    df.loc[0, "NomeProjeto"] = st.text_input("Nome do Projeto", value=df.loc[0, "NomeProjeto"])
    df.loc[0, "Ocupacao"] = st.selectbox("Ocupação", ["A-1", "B-2", "C-3"], index=["A-1", "B-2", "C-3"].index(df.loc[0, "Ocupacao"]))
    df.loc[0, "Area"] = st.number_input("Área (m²)", value=float(df.loc[0, "Area"]))
    df.loc[0, "Altura"] = st.number_input("Altura (m)", value=float(df.loc[0, "Altura"]))
    df.loc[0, "UltimoUsuario"] = st.text_input("Seu nome", value=df.loc[0, "UltimoUsuario"])
    df.loc[0, "UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    st.write("📊 Visualização dos dados:")
    st.dataframe(df)

    # Gera nome do arquivo de saída
    nome_projeto = df.loc[0, "NomeProjeto"]
    nome_arquivo_saida = gerar_nome_arquivo(nome_projeto, nome_arquivo_entrada)

    # Prepara arquivo para download
    output = io.BytesIO()
    df.to_excel(output, index=False)

    st.download_button(
        "📥 Baixar planilha atualizada",
        data=output.getvalue(),
        file_name=nome_arquivo_saida
    )

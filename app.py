import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Gestão de Projetos PPCI", layout="centered")
st.title("📁 Ferramenta de Projetos PPCI")

# Escolha do modo
modo = st.radio("Como deseja começar?", ["📄 Revisar projeto existente", "🆕 Criar novo projeto"])

# Inicializa o DataFrame
df = pd.DataFrame()

if modo == "📄 Revisar projeto existente":
    arquivo = st.file_uploader("Anexe a planilha do projeto (.xlsx)", type=["xlsx"])
    if arquivo:
        try:
            df = pd.read_excel(arquivo)
            st.success("Planilha carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

elif modo == "🆕 Criar novo projeto":
    # Cria estrutura básica
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

    # Botão para baixar a planilha atualizada
    output = io.BytesIO()
    df.to_excel(output, index=False)
    st.download_button("📥 Baixar planilha atualizada", data=output.getvalue(), file_name="projeto_ppci_atualizado.xlsx")

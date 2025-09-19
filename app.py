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

# Inicializa variáveis
df = pd.DataFrame()
arquivo = None
nome_arquivo_entrada = None
linha_selecionada = None

if modo == "📄 Revisar projeto existente":
    arquivo = st.file_uploader("Anexe a planilha do projeto (.xlsx)", type=["xlsx"])
    if arquivo:
        nome_arquivo_entrada = arquivo.name
        try:
            df = pd.read_excel(arquivo)
            st.success("Planilha carregada com sucesso!")

            # Verifica se há múltiplas revisões
            if len(df) > 1:
                opcoes = [f"{i} - {df.loc[i, 'NomeProjeto']} (Rev: {df.loc[i, 'UltimaModificacao']})" for i in df.index]
                idx = st.selectbox("Selecione a revisão base para editar", options=df.index, format_func=lambda i: opcoes[i])
                linha_selecionada = df.loc[idx].copy()
            else:
                linha_selecionada = df.loc[0].copy()

        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

elif modo == "🆕 Criar novo projeto":
    linha_selecionada = pd.Series({
        "NomeProjeto": "",
        "Ocupacao": "A-1",
        "Area": 100.0,
        "Altura": 3.0,
        "UltimoUsuario": "",
        "UltimaModificacao": datetime.now().strftime('%d/%m/%Y %H:%M')
    })
    st.info("Novo projeto iniciado. Preencha os dados abaixo.")

# 🔻 Separação visual entre modo e edição
st.markdown("---")
st.markdown("### ✏️ Informações do Projeto")

# Se houver dados para edição
if linha_selecionada is not None:
    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada["NomeProjeto"])
    linha_selecionada["Ocupacao"] = st.selectbox("Ocupação", ["A-1", "B-2", "C-3"], index=["A-1", "B-2", "C-3"].index(linha_selecionada["Ocupacao"]))
    linha_selecionada["Area"] = st.number_input("Área (m²)", value=float(linha_selecionada["Area"]))
    linha_selecionada["Altura"] = st.number_input("Altura (m)", value=float(linha_selecionada["Altura"]))
    linha_selecionada["UltimoUsuario"] = st.text_input("Seu nome", value=linha_selecionada["UltimoUsuario"])
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    st.write("📊 Visualização da nova linha:")
    st.dataframe(pd.DataFrame([linha_selecionada]))

    # Adiciona nova linha ao histórico
    df_novo = pd.DataFrame([linha_selecionada])
    if modo == "📄 Revisar projeto existente" and arquivo:
        df = pd.concat([df, df_novo], ignore_index=True)
    else:
        df = df_novo.copy()

    # Gera nome do arquivo de saída
    nome_projeto = linha_selecionada["NomeProjeto"]
    nome_arquivo_saida = gerar_nome_arquivo(nome_projeto, nome_arquivo_entrada)

    # Prepara arquivo para download
    output = io.BytesIO()
    df.to_excel(output, index=False)

    st.download_button(
        "📥 Baixar planilha atualizada",
        data=output.getvalue(),
        file_name=nome_arquivo_saida
    )

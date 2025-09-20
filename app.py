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
        "Ocupacao": "A-2",
        "Area": 100.0,
        "Altura": 3.0,
        "UltimoUsuario": "",
        "UltimaModificacao": datetime.now().strftime('%d/%m/%Y %H:%M'),
        "Anexo1": "",
        "Anexo2": "",
        "Anexo3": "",
        "Anexo4": "",
        "Anexo5": "",
        "SubsoloTecnico": "",
        "SubsoloComOcupacao": "",
        "SubsoloMenor50m2": "",
        "DuplexUltimoPavimento": "",
        "AticoOuCasaMaquinas": ""
    })
    st.info("Novo projeto iniciado. Preencha os dados abaixo.")

# 🔝 Informações gerais da versão
if linha_selecionada is not None:
    st.markdown("### 🧾 Versão do Projeto")

    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada["NomeProjeto"])
    
    nome_usuario = st.text_input("Seu nome", value="Vitor")
    linha_selecionada["UltimoUsuario"] = f"{nome_usuario} + Copilot"
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    st.markdown("### 📎 Anexos do Projeto")
    adicionar_anexos = st.radio("Adicionar anexos?", ["Não", "Sim"])
    if adicionar_anexos == "Sim":
        qtd_anexos = st.number_input("Selecione a quantidade de anexos", min_value=1, max_value=5, step=1)
        for i in range(1, 6):
            if i <= qtd_anexos:
                linha_selecionada[f"Anexo{i}"] = st.text_input(f"Insira o nome do anexo {i}")
            else:
                linha_selecionada[f"Anexo{i}"] = ""

# 🔻 Separação visual entre versão e dados técnicos
st.markdown("---")
st.markdown("### 🧱 Área da edificação A-2")
linha_selecionada["Area"] = st.number_input("Área da edificação A-2 (m²)", value=float(linha_selecionada["Area"]))

st.markdown("### 🏗️ Altura da edificação")

linha_selecionada["SubsoloTecnico"] = st.radio("Existe subsolo de estacionamento, área técnica ou sem ocupação de pessoas?", ["Não", "Sim"])
if linha_selecionada["SubsoloTecnico"] == "Sim":
    st.markdown("<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento ou sua laje de teto estiver acima, em pelo menos, 1,2m do perfil natural em pelo menos um lado, não é subsolo e deve ser considerado na altura</span>", unsafe_allow_html=True)
    linha_selecionada["SubsoloComOcupacao"] = st.radio("Um dos dois primeiros subsolos abaixo do térreo possui ocupação secundária?", ["Não", "Sim"])
    if linha_selecionada["SubsoloComOcupacao"] == "Sim":
        linha_selecionada["SubsoloMenor50m2"] = st.radio("Essa ocupação secundária tem no máximo 50m² em cada subsolo?", ["Não", "Sim"])

linha_selecionada["DuplexUltimoPavimento"] = st.radio("Existe duplex no último pavimento?", ["Não", "Sim"])
linha_selecionada["AticoOuCasaMaquinas"] = st.radio("Há pavimento de ático/casa de máquinas/casa de bombas acima do último pavimento?", ["Não", "Sim"])

linha_selecionada["Altura"] = st.number_input("Altura da edificação (m)", value=float(linha_selecionada["Altura"]))

# 🧠 Frase explicativa da altura
explicacao = ""
s1 = linha_selecionada["SubsoloTecnico"]
s2 = linha_selecionada.get("SubsoloComOcupacao", "Não")
s3 = linha_selecionada.get("SubsoloMenor50m2", "Não")
duplex = linha_selecionada["DuplexUltimoPavimento"]

if s1 == "Não" and s2 == "Não":
    explicacao = "Altura da edificação é: Cota de piso do último pavimento habitado - cota de piso do pavimento mais baixo, exceto subsolos"
elif s1 == "Não" and duplex == "Sim":
    explicacao = "Altura da edificação é: Cota de piso do primeiro pavimento duplex - cota de piso do pavimento mais baixo, exceto subsolos"
elif s1 == "Sim" and s2 == "Não":
    explicacao = "Altura da edificação é: Cota de piso do último pavimento habitado - cota de piso do pavimento mais baixo, exceto subsolos"
elif s1 == "Sim" and s2 == "Sim" and s3 == "Sim":
    explicacao = "Altura da edificação é: Cota de piso do último pavimento habitado - cota de piso do pavimento mais baixo, exceto subsolos"
elif s1 == "Sim" and s2 == "Sim" and s3 == "Não":
    explicacao = "Altura da edificação é: Cota de piso do último pavimento habitado - cota de piso do subsolo em que a ocupação secundária ultrapassa 50m²"

if explicacao:
    st.markdown(f"💡 **{explicacao}**")

# Finalização
df_novo = pd.DataFrame([linha_selecionada])
if modo == "📄 Revisar projeto existente" and arquivo is not None:
    df = pd.concat([df, df_novo], ignore_index=True)
else:
    df = df_novo.copy()

nome_projeto = linha_selecionada["NomeProjeto"]
nome_arquivo_saida = gerar_nome_arquivo(nome_projeto, nome_arquivo_entrada)

output = io.BytesIO()
df.to_excel(output, index=False)

st.download_button(
    "📥 Baixar planilha atualizada",
    data=output.getvalue(),
    file_name=nome_arquivo_saida
)

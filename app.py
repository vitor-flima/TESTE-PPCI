import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="Gestão de Projetos PPCI", layout="centered")
st.title("📁 Ferramenta de Projetos PPCI")

# Funções auxiliares
def gerar_nome_arquivo(nome_projeto, nome_arquivo_entrada=None):
    if nome_arquivo_entrada:
        match = re.search(r"-R(\d+)", nome_arquivo_entrada)
        numero = int(match.group(1)) + 1 if match else 1
        novo_nome = re.sub(r"-R\d+", f"-R{numero:02}", nome_arquivo_entrada)
    else:
        novo_nome = f"checklistINC_{nome_projeto}-R00.xlsx"
    return novo_nome

def faixa_altura(h):
    if h == 0:
        return "Térrea"
    elif h < 6:
        return "H < 6 m"
    elif h < 12:
        return "6 ≤ H < 12 m"
    elif h < 23:
        return "12 ≤ H < 23 m"
    elif h < 30:
        return "23 ≤ H < 30 m"
    else:
        return "Acima de 30 m"

def medidas_por_faixa(faixa):
    tabela = {
        "Acesso de Viatura na Edificação": ["X"] * 6,
        "Segurança Estrutural contra Incêndio": ["X"] * 6,
        "Compartimentação Horizontal ou de Área": ["X⁴"] * 6,
        "Compartimentação de Verticais": ["", "", "", "X²", "X²", "X²"],
        "Controle de Materiais de Acabamento": ["", "", "", "X", "X", "X"],
        "Saídas de Emergência": ["X", "X", "X", "X", "X", "X¹"],
        "Brigada de Incêndio": ["X"] * 6,
        "Iluminação de Emergência": ["X"] * 6,
        "Alarme de Incêndio": ["X³", "X³", "X³", "X³", "X³", "X"],
        "Sinalização de Emergência": ["X"] * 6,
        "Extintores": ["X"] * 6,
        "Hidrantes e Mangotinhos": ["X"] * 6
    }
    faixas = ["Térrea", "H < 6 m", "6 ≤ H < 12 m", "12 ≤ H < 23 m", "23 ≤ H < 30 m", "Acima de 30 m"]
    idx = faixas.index(faixa)
    return {medida: tabela[medida][idx] for medida in tabela}

def notas_relevantes(resumo, altura):
    notas = []
    if altura >= 80:
        notas.append("1 – Deve haver Elevador de Emergência para altura maior que 80 m")
    if any("X²" in v for v in resumo.values()):
        notas.append("2 – Pode ser substituída por sistema de controle de fumaça somente nos átrios")
    if any("X³" in v for v in resumo.values()):
        notas.append("3 – O sistema de alarme pode ser setorizado na central junto à portaria, desde que tenha vigilância 24 horas")
    if any("X⁴" in v for v in resumo.values()):
        notas.append("4 – Devem ser atendidas somente as regras específicas de compartimentação entre unidades autônomas")
    return notas

# Interface principal
modo = st.radio("Como deseja começar?", ["📄 Revisar projeto existente", "🆕 Criar novo projeto"])
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
            if isinstance(linha_selecionada, pd.DataFrame):
                linha_selecionada = linha_selecionada.iloc[0]
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
        "Anexo1": "", "Anexo2": "", "Anexo3": "", "Anexo4": "", "Anexo5": "",
        "SubsoloTecnico": "", "SubsoloComOcupacao": "", "SubsoloMenor50m2": "",
        "DuplexUltimoPavimento": "", "ÁticoOuCasaMaquinas": "",
        "ComentarioAltura": ""
    })
    st.info("Novo projeto iniciado. Preencha os dados abaixo.")

if linha_selecionada is not None:
    st.markdown("### 🧾 Versão do Projeto")
    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada["NomeProjeto"])
    nome_usuario = st.text_input("Seu nome", value="Vitor")
    linha_selecionada["UltimoUsuario"] = f"{nome_usuario} + Copilot"
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    st.markdown("### 📎 Anexos do Projeto")
    if st.radio("Adicionar anexos?", ["Não", "Sim"]) == "Sim":
        qtd_anexos = st.number_input("Selecione a quantidade de anexos", min_value=1, max_value=5, step=1)
        for i in range(1, 6):
            linha_selecionada[f"Anexo{i}"] = st.text_input(f"Insira o nome do anexo {i}") if i <= qtd_anexos else ""

    st.markdown("### 🧱 Enquadramento da edificação A-2")
    linha_selecionada["Area"] = st.number_input("Área da edificação A-2 (m²)", value=float(linha_selecionada["Area"]))

    st.markdown("### 🏗️ Altura da edificação")
    linha_selecionada["SubsoloTecnico"] = st.radio("Existe subsolo de estacionamento, área técnica ou sem ocupação de pessoas?", ["Não", "Sim"])
    if linha_selecionada["SubsoloTecnico"] == "Sim":
        st.markdown("<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento ou sua laje de teto estiver acima, em pelo menos, 1,2m do perfil natural em pelo menos um lado, não é subsolo e deve ser considerado na altura</span>", unsafe_allow_html=True)
        linha_selecionada["SubsoloComOcupacao"] = st.radio("Um dos dois primeiros subsolos abaixo do térreo possui ocupação secundária?", ["Não", "Sim"])
        if linha_selecionada["SubsoloComOcupacao"] == "Sim":
            linha_selecionada["SubsoloMenor50m2"] = st.radio("Essa ocupação secundária tem no máximo 50m² em cada subsolo?", ["Não", "Sim"])

    linha_selecionada["DuplexUltimoPavimento"] = st.radio("Existe duplex no último pavimento?", ["Não", "Sim"])
    linha_selecionada["ÁticoOuCasaMaquinas"] = st.radio("Há pavimento de ático/casa de máquinas/casa de bombas acima do último pavimento?", ["Não", "Sim"])

    # 💡 Explicação da altura (antes do campo de entrada)
    s1 = linha_selecionada["SubsoloTecnico"]
    s2 = linha_selecionada.get("SubsoloComOcupacao", "Não")
    s3 = linha_selecionada.get("SubsoloMenor50m2", "

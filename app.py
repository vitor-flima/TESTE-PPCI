# 📦 Importações
import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# ⚙️ Configuração da página
st.set_page_config(page_title="Gestão de Projetos PPCI", layout="centered")
st.title("📁 Ferramenta de Projetos PPCI")

# 🧠 Funções auxiliares
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

# 🧭 Interface principal
modo = st.radio("Como deseja começar?", ["📄 Revisar projeto existente", "🆕 Criar novo projeto"])
df = pd.DataFrame()
arquivo = None
nome_arquivo_entrada = None
linha_selecionada = None
mostrar_campos = False

if modo == "📄 Revisar projeto existente":
    arquivo = st.file_uploader("Anexe a planilha do projeto (.xlsx)", type=["xlsx"])
    if not arquivo:
        st.warning("⚠️ Para revisar um projeto, anexe a planilha primeiro.")
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
            mostrar_campos = True
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
        "ComentarioAltura": ""
    })
    st.success("Novo projeto iniciado. Preencha os dados abaixo.")
    mostrar_campos = True

# 🏗️ Levantamento das edificações
if mostrar_campos:
    st.markdown("### 🧾 Versão do Projeto")
    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada.get("NomeProjeto", ""))
    nome_usuario = st.text_input("Seu nome", value="Vitor")
    linha_selecionada["UltimoUsuario"] = f"{nome_usuario} + Copilot"
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    # 🔻 Separação visual destacada
    st.markdown("---")
    st.markdown("<div style='border-top: 6px solid #555; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)

    # 🏢 Novo título atualizado
    st.markdown("### 🏢 Levantamento das Edificações do Empreendimento para Distâncias de Isolamento")
    st.markdown("As medidas de segurança podem ser determinadas individualmente para cada edificação, desde que estejam isoladas. Caso contrário, são consideradas como um único edifício.")

    # Torres residenciais
    num_torres = st.number_input("Quantidade de torres/edificações residenciais", min_value=0, step=1)
    torres = []
    
    for i in range(int(num_torres)):
        st.markdown(f"**Edificação Residencial {i+1}**")
        nome = st.text_input(f"Nome da edificação {i+1}", key=f"nome_torre_{i}")
        area = st.number_input(f"Área da edificação {i+1} (m²)", min_value=0.0, step=1.0, key=f"area_torre_{i}")
        terrea = st.radio(f"A edificação {i+1} é térrea?", ["Sim", "Não"], key=f"terrea_torre_{i}")
    
        if terrea == "Não":
            um_ap_por_pav = st.radio(f"A edificação {i+1} é de um apartamento por pavimento?", ["Sim", "Não"], key=f"ap_por_pav_{i}")
    
            subsolo_tecnico = st.radio(
                f"Existe subsolo na edificação {i+1}?",
                ["Não", "Sim"], key=f"subsolo_tecnico_{i}"
            )
    
            if subsolo_tecnico == "Sim":
                st.markdown(
                    "<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento ou sua laje de teto estiver acima, em pelo menos, 1,2m do perfil natural em pelo menos um lado, não é subsolo e deve ser considerado na altura</span>",
                    unsafe_allow_html=True
                )
    
                numero_subsolos = st.radio(
                    f"Quantidade de subsolos na edificação {i+1}",
                    ["1", "Mais de 1"], key=f"numero_subsolos_{i}"
                )
    
                if numero_subsolos == "1":
                    area_subsolo = st.selectbox(
                        f"Área do subsolo da edificação {i+1}",
                        ["Menor que 500m²", "Maior que 500m²"], key=f"area_subsolo_{i}"
                    )
                else:
                    area_subsolo = "Maior que 500m²"
    
                subsolo_ocupado = st.radio(
                    f"Algum dos dois primeiros subsolos possui ocupação secundária?",
                    ["Não", "Sim"], key=f"subsolo_ocupado_{i}"
                )
    
                if subsolo_ocupado == "Sim":
                    subsolo_menor_50 = st.radio(
                        f"A ocupação secundária tem no máximo 50m² em cada subsolo?",
                        ["Não", "Sim"], key=f"subsolo_menor_50_{i}"
                    )
                else:
                    subsolo_menor_50 = "Não"
            else:
                numero_subsolos = "0"
                area_subsolo = "Menor que 500m²"
                subsolo_ocupado = "Não"
                subsolo_menor_50 = "Não"
    
            duplex = st.radio(
                f"Existe duplex no último pavimento da edificação {i+1}?",
                ["Não", "Sim"], key=f"duplex_{i}"
            )
    
            atico = st.radio(
                f"Há pavimento de ático/casa de máquinas acima do último pavimento?",

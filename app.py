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
    st.success("Novo projeto iniciado. Preencha os dados abaixo.")

if linha_selecionada is not None:
    # 🧾 Versão do Projeto
    st.markdown("### 🧾 Versão do Projeto")
    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada.get("NomeProjeto", ""))
    nome_usuario = st.text_input("Seu nome", value="Vitor")
    linha_selecionada["UltimoUsuario"] = f"{nome_usuario} + Copilot"
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')

    # 📎 Anexos do Projeto
    st.markdown("### 📎 Anexos do Projeto")
    if st.radio("Adicionar anexos?", ["Não", "Sim"]) == "Sim":
        qtd_anexos = st.number_input("Selecione a quantidade de anexos", min_value=1, max_value=5, step=1)
        for i in range(1, 6):
            linha_selecionada[f"Anexo{i}"] = st.text_input(f"Insira o nome do anexo {i}") if i <= qtd_anexos else ""

    # 🧱 Enquadramento da edificação A-2
st.markdown("### 🧱 Enquadramento da edificação A-2")

# ✅ Garantir que linha_selecionada está inicializada corretamente
if linha_selecionada is None or not isinstance(linha_selecionada, (dict, pd.Series)):
    linha_selecionada = {}

linha_selecionada["Area"] = st.number_input(
    "Área da edificação A-2 (m²)",
    value=float(linha_selecionada.get("Area", 100.0))


# ✅ Novo campo: edificação térrea
linha_selecionada["EdificacaoTerrea"] = st.radio(
    "A edificação é térrea?",
    ["Não", "Sim"],
    index=0
)

st.markdown("### 🏗️ Altura da edificação")

# Subsolo — só aparece se NÃO for térrea
if linha_selecionada["EdificacaoTerrea"] == "Não":
    linha_selecionada["SubsoloTecnico"] = st.radio(
        "Existe subsolo de estacionamento, área técnica ou sem ocupação de pessoas?",
        ["Não", "Sim"]
    )

    if linha_selecionada["SubsoloTecnico"] == "Sim":
        st.markdown(
            "<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento ou sua laje de teto estiver acima, em pelo menos, 1,2m do perfil natural em pelo menos um lado, não é subsolo e deve ser considerado na altura</span>",
            unsafe_allow_html=True
        )

        linha_selecionada["NumeroSubsolos"] = st.radio(
            "Qual a quantidade de subsolo?",
            ["1", "Mais de 1"]
        )

        if linha_selecionada["NumeroSubsolos"] == "1":
            linha_selecionada["AreaSubsolo"] = st.selectbox(
                "Área do subsolo:",
                ["Menor que 500m²", "Maior que 500m²"]
            )

        linha_selecionada["SubsoloComOcupacao"] = st.radio(
            "Um dos dois primeiros subsolos abaixo do térreo possui ocupação secundária?",
            ["Não", "Sim"]
        )
        if linha_selecionada["SubsoloComOcupacao"] == "Sim":
            linha_selecionada["SubsoloMenor50m2"] = st.radio(
                "Essa ocupação secundária tem no máximo 50m² em cada subsolo?",
                ["Não", "Sim"]
            )

# ✅ Campos sempre visíveis — fora do bloco de subsolo
if linha_selecionada is not None and isinstance(linha_selecionada, (dict, pd.Series)):
    if linha_selecionada["EdificacaoTerrea"] == "Não":
        linha_selecionada["DuplexUltimoPavimento"] = st.radio(
            "Existe duplex no último pavimento?",
            ["Não", "Sim"]
        )

        if "AticoOuCasaMaquinas" not in linha_selecionada:
            linha_selecionada["AticoOuCasaMaquinas"] = ""

        linha_selecionada["ÁticoOuCasaMaquinas"] = st.radio(
            "Há pavimento de ático/casa de máquinas/casa de bombas acima do último pavimento?",
            ["Não", "Sim"]
        )

# 💡 Explicação da altura (antes do campo de entrada)
if linha_selecionada is not None and isinstance(linha_selecionada, (dict, pd.Series)):
    # Garantir que todos os campos existem
    for campo in ["SubsoloTecnico", "SubsoloComOcupacao", "SubsoloMenor50m2", "DuplexUltimoPavimento"]:
        if campo not in linha_selecionada:
            linha_selecionada[campo] = "Não"

    # Definir variáveis seguras
    s1 = linha_selecionada["SubsoloTecnico"]
    s2 = linha_selecionada["SubsoloComOcupacao"]
    s3 = linha_selecionada["SubsoloMenor50m2"]
    duplex = linha_selecionada["DuplexUltimoPavimento"]

    # Lógica de altura
    if duplex == "Sim":
        parte_superior = "Cota do primeiro pavimento do duplex"
    else:
        parte_superior = "Cota de piso do último pavimento habitado"

    if s1 == "Não" and s2 == "Não":
        parte_inferior = "cota de piso do pavimento mais baixo, exceto subsolos"
    elif s1 == "Sim" and s2 == "Sim" and s3 == "Não":
        parte_inferior = "cota de piso do subsolo em que a ocupação secundária ultrapassa 50m²"
    else:
        parte_inferior = "cota de piso do pavimento mais baixo, exceto subsolos"

    explicacao = f"💡 Altura da edificação é: {parte_superior} - {parte_inferior}"
    st.markdown(explicacao)

    # Campo de entrada da altura
    if "Altura" not in linha_selecionada:
        linha_selecionada["Altura"] = 3.0
    linha_selecionada["Altura"] = st.number_input(
        "Altura da edificação (m)",
        value=float(linha_selecionada["Altura"])
    )


    # 🧯 Tabela resumo de medidas de segurança
    faixa = faixa_altura(linha_selecionada["Altura"])
    resumo = medidas_por_faixa(faixa)
    notas = notas_relevantes(resumo, linha_selecionada["Altura"])

    st.markdown("### 🔍 Medidas de Segurança Aplicáveis")
    df_resumo = pd.DataFrame.from_dict(resumo, orient='index', columns=["Aplicação"])
    st.table(df_resumo)

    # 📌 Notas específicas
    if notas:
        st.markdown("### 📌 Notas Específicas")
        for nota in notas:
            st.markdown(f"- {nota}")

    # 🗒️ Comentários do projetista
    st.markdown("### 🗒️ Comentários sobre este tópico")
    linha_selecionada["ComentarioAltura"] = st.text_area(
        "Observações, justificativas ou dúvidas sobre altura e medidas aplicáveis",
        value=linha_selecionada.get("ComentarioAltura", "")
    )

    # 🔍 Detalhamento por medida de segurança
st.markdown("## 🧯 Detalhamento por medida de segurança")

if linha_selecionada is not None and isinstance(linha_selecionada, (dict, pd.Series)):
    altura_valor = linha_selecionada.get("Altura", 0)
    faixa = faixa_altura(altura_valor)
    resumo = medidas_por_faixa(faixa)

    for medida, aplicacao in resumo.items():
        if "X" in aplicacao:
            # 🔹 Tópico específico: Acesso de Viatura na Edificação
            if medida == "Acesso de Viatura na Edificação":
                with st.expander(f"🔹 {medida}"):
                    st.markdown("**Será previsto hidrante de recalque a não mais que 20m do limite da edificação?**")
                    hidrante_recalque = st.radio("Resposta:", ["Sim", "Não"], key="hidrante_recalque")
                    st.markdown(
                        "<span style='color:red'>⚠️ O hidrante de recalque a menos de 20m anula as exigências a respeito do acesso de viaturas na edificação.</span>",
                        unsafe_allow_html=True
                    )
                    st.markdown("✅ O portão de acesso deve ter, no mínimo, **4m de largura** e **4,5m de altura**.")
                    if hidrante_recalque == "Não":
                        st.markdown("✅ As vias devem ter, no mínimo, **6m de largura** e **4,5m de altura**, além de suportar viaturas de **25 toneladas em dois eixos**.")

            # 🔹 Tópico específico: Segurança Estrutural contra Incêndio
            elif medida == "Segurança Estrutural contra Incêndio":
                with st.expander(f"🔹 {medida}"):
                    # ✅ Regra 1: Edificação térrea
                    if linha_selecionada.get("EdificacaoTerrea") == "Sim":
                        st.markdown("✅ A edificação está isenta de comprovação de TRRF para elementos estruturais.")
            
                    # ✅ Regras 2 a 5: Edificação não térrea
                    else:
                        altura = linha_selecionada.get("Altura", 0)
                        area = linha_selecionada.get("Area", 0)
                        subsolo_tecnico = linha_selecionada.get("SubsoloTecnico", "Não")
                        numero_subsolos = linha_selecionada.get("NumeroSubsolos", "0")
                        area_subsolo = linha_selecionada.get("AreaSubsolo", "Menor que 500m²")
            
                        # Normalizar valores
                        altura_menor_igual_12 = altura <= 12
                        area_menor_1500 = area < 1500
                        area_maior_igual_1500 = area >= 1500
                        subsolo_simples = numero_subsolos == "1" and area_subsolo == "Menor que 500m²"
                        subsolo_complexo = numero_subsolos != "1" or area_subsolo == "Maior que 500m²"
                        sem_subsolo = subsolo_tecnico == "Não"
            
                        # ✅ Regra 2
                        if altura_menor_igual_12 and area_menor_1500 and (sem_subsolo or subsolo_simples):
                            st.markdown("✅ A edificação está isenta de comprovação de TRRF para elementos estruturais.")
            
                        # ✅ Regra 3
                        elif altura_menor_igual_12 and area_menor_1500 and subsolo_complexo:
                            st.markdown("⚠️ Apenas o(s) subsolo(s) deverão apresentar comprovação de TRRF para elementos estruturais.")
            
                        # ✅ Regra 4
                        elif (altura > 12 or area_maior_igual_1500) and (sem_subsolo or subsolo_simples):
                            st.markdown("⚠️ Cada pavimento deverá apresentar comprovação de TRRF para elementos estruturais. Cada pavimento tem seu TRRF determino de acordo com seu uso e nunca inferior ao do pavimento superior (o subsolo absorve o TRRF do pavimento superior).")
            
                        # ✅ Regra 5
                        elif (altura > 12 or area_maior_igual_1500) and subsolo_complexo:
                            st.markdown("⚠️ Cada pavimento deverá apresentar comprovação de TRRF para elementos estruturais. Cada pavimento tem seu TRRF determino de acordo com seu uso e nunca inferior ao do pavimento superior.")
            
                    # Campo opcional para observações
                    linha_selecionada["ComentarioEstrutural"] = st.text_area(
                        "Observações sobre segurança estrutural",
                        value=linha_selecionada.get("ComentarioEstrutural", "")
                    )

            # 🔹 Outros tópicos genéricos
            else:
                with st.expander(f"🔹 {medida}"):
                    st.markdown(f"Conteúdo técnico sobre **{medida.lower()}**...")
                    if "¹" in aplicacao:
                        st.markdown("📌 Observação especial: ver nota 1")
                    elif "²" in aplicacao:
                        st.markdown("📌 Observação especial: ver nota 2")
                    elif "³" in aplicacao:
                        st.markdown("📌 Observação especial: ver nota 3")
                    elif "⁴" in aplicacao:
                        st.markdown("📌 Observação especial: ver nota 4")

# 📥 Exportação final
st.markdown("## 📥 Exportar planilha atualizada")

if linha_selecionada is not None:
    nova_linha_df = pd.DataFrame([linha_selecionada])

    if arquivo and not df.empty:
        df_atualizado = pd.concat([df, nova_linha_df], ignore_index=True)
    else:
        df_atualizado = nova_linha_df

    nome_arquivo_saida = gerar_nome_arquivo(linha_selecionada["NomeProjeto"], nome_arquivo_entrada)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_atualizado.to_excel(writer, index=False, sheet_name='Projetos')
    output.seek(0)

    st.download_button(
        label="📥 Baixar Planilha Atualizada",
        data=output.getvalue(),
        file_name=nome_arquivo_saida,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_button_planilha_final"  # ✅ chave única
    )

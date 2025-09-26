# 📦 Importações
import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# ⚙️ Configuração da página
st.set_page_config(page_title="Gestão de Projetos PPCI", layout="centered")
st.title("📁 Ferramenta de Projetos PPCI")

# Inicializa o estado da sessão
if 'comparisons' not in st.session_state:
    st.session_state.comparisons = []
if 'comparacoes_extra' not in st.session_state:
    st.session_state.comparacoes_extra = [] # Lista para gerenciar as comparações dinâmicas
if 'bombeiros' not in st.session_state:
    st.session_state.bombeiros = "Sim"
if 'edificacoes_finais' not in st.session_state:
    st.session_state.edificacoes_finais = []
if 'processamento_concluido' not in st.session_state:
    st.session_state.processamento_concluido = False


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

def medidas_tabela_completa(faixa):
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

def medidas_tabela_simplificada(num_pavimentos):
    iluminacao_aplicavel = "X" if num_pavimentos > 2 else "-"

    tabela = {
        "Acesso de Viatura na Edificação": ["X"], 
        "Segurança Estrutural contra Incêndio": ["X"], 
        "Compartimentação Horizontal ou de Área": ["X⁴"],
        "Compartimentação de Verticais": ["-"],
        "Controle de Materiais de Acabamento": ["-"],
        "Saídas de Emergência": ["X"],
        "Brigada de Incêndio": ["-"],
        "Iluminação de Emergência": [iluminacao_aplicavel],
        "Alarme de Incêndio": ["X³"],
        "Sinalização de Emergência": ["X"],
        "Extintores": ["X"],
        "Hidrantes e Mangotinhos": ["-"]
    }
    return {medida: tabela[medida][0] for medida in tabela}

def medidas_por_enquadramento(area_consolidada, altura, num_pavimentos):
    """Determina o conjunto de medidas de segurança com base na área e altura."""
    
    if area_consolidada > 750 or altura > 12:
        faixa = faixa_altura(altura)
        return medidas_tabela_completa(faixa)
    else:
        return medidas_tabela_simplificada(num_pavimentos)


def notas_relevantes(resumo, altura, num_pavimentos, is_tabela_simplificada):
    notas = []
    
    if not is_tabela_simplificada:
        if altura >= 80:
            notas.append("1 – Deve haver Elevador de Emergência para altura maior que 80 m")
        if any("X²" in v for v in resumo.values()):
            notas.append("2 – Pode ser substituída por sistema de controle de fumaça somente nos átrios")
        if any("X³" in v for v in resumo.values()):
            notas.append("3 – O sistema de alarme pode ser setorizado na central junto à portaria, desde que tenha vigilância 24 horas")
        if any("X⁴" in v for v in resumo.values()):
            notas.append("4 – Devem ser atendidas somente as regras específicas de compartimentação entre unidades autônomas")

    if is_tabela_simplificada and resumo.get("Iluminação de Emergência") == "X":
        notas.append("5 – Iluminação de Emergência: Somente para as edificações com mais de dois pavimentos (regra simplificada).")
        
    return notas

def fachada_edificacao(edf):
    if "um_ap_por_pav" in edf and edf["um_ap_por_pav"] == "Sim":
        return "toda a fachada do pavimento"
    elif "terrea" in edf and edf["terrea"] == "Sim":
        return "toda a fachada do edifício"
    elif "altura" in edf and "area" in edf:
        if edf["area"] <= 750 and edf["altura"] < 12:
            return "toda a área da fachada"
        elif edf["area"] > 750 and edf["altura"] < 12:
            return "fachada da área do maior compartimento"
        elif edf["area"] > 750 and edf["altura"] >= 12:
            return "fachada da área do maior compartimento"
        else:
            return "toda a área da fachada"
    else:
        return "toda a fachada do edifício"

def buscar_valor_tabela_simplificada(porcentagem, num_pavimentos):
    tabela = {
        1: {10: 4, 20: 5, 30: 6, 40: 7, 50: 8, 70: 9, 100: 10},
        2: {10: 6, 20: 7, 30: 8, 40: 9, 50: 10, 70: 11, 100: 12},
        3: {10: 8, 20: 9, 30: 10, 40: 11, 50: 12, 70: 13, 100: 14}
    }
    if num_pavimentos >= 3:
        num_pavimentos_lookup = 3
    else:
        num_pavimentos_lookup = num_pavimentos

    porcentagens_lookup = sorted(tabela[num_pavimentos_lookup].keys())
    porcentagem_mais_proxima = next((p for p in porcentagens_lookup if porcentagem <= p), porcentagens_lookup[-1])
    return tabela[num_pavimentos_lookup][porcentagem_mais_proxima]

def buscar_valor_tabela(porcentagem, fator_x):
    tabela = {
        20: [0.4, 0.4, 0.44, 0.46, 0.48, 0.49, 0.5, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51, 0.51],
        30: [0.6, 0.66, 0.73, 0.79, 0.84, 0.88, 0.9, 0.92, 0.93, 0.94, 0.94, 0.95, 0.95, 0.95, 0.95, 0.95, 0.95],
        40: [0.8, 0.8, 0.94, 1.02, 1.1, 1.17, 1.23, 1.27, 1.3, 1.32, 1.33, 1.33, 1.34, 1.34, 1.34, 1.34, 1.34, 1.34],
        50: [0.9, 1.0, 1.11, 1.22, 1.33, 1.42, 1.51, 1.58, 1.63, 1.66, 1.69, 1.7, 1.71, 1.71, 1.71, 1.71, 1.71, 1.71],
        60: [1.0, 1.14, 1.26, 1.39, 1.52, 1.64, 1.76, 1.85, 1.93, 1.99, 2.03, 2.05, 2.07, 2.08, 2.08, 2.08, 2.08, 2.08],
        80: [1.2, 1.37, 1.52, 1.68, 1.85, 2.02, 2.18, 2.34, 2.48, 2.59, 2.67, 2.73, 2.77, 2.79, 2.8, 2.81, 2.81],
        100: [1.4, 1.56, 1.74, 1.93, 2.13, 2.34, 2.55, 2.76, 2.95, 3.12, 3.26, 3.36, 3.43, 3.48, 3.51, 3.52, 3.53]
    }
    valores_x = [1.0, 1.3, 1.6, 2.0, 2.5, 3.2, 4.0, 5.0, 6.0, 8.0, 10.0, 13.0, 16.0, 20.0, 25.0, 32.0, 40.0]
    porcentagem_mais_proxima = min(tabela.keys(), key=lambda p: abs(p - porcentagem))
    indice_x = min(range(len(valores_x)), key=lambda i: abs(valores_x[i] - fator_x))
    return tabela[porcentagem_mais_proxima][indice_x]

def consolidar_edificacoes(edificacoes_atuais):
    edificacoes_consolidadas = []
    nomes_ja_consolidados = set()
    
    todas_edificacoes_copia = [e.copy() for e in edificacoes_atuais] 

    for edificacao in todas_edificacoes_copia:
        if edificacao["nome"] in nomes_ja_consolidados:
            continue
        
        is_principal_ou_independente = edificacao.get("tratamento") != "Conjunta" or \
                                      edificacao.get("nome") == edificacao.get("edificacao_conjunta")
        
        if is_principal_ou_independente:
            edificacao_combinada = edificacao.copy()
            edificacao_combinada['area_original'] = edificacao['area']
            edificacao_combinada['areas_combinadas_com'] = [edificacao["nome"]]
            
            area_total_combinada = edificacao['area']
            
            for outra_edificacao in todas_edificacoes_copia:
                if outra_edificacao["nome"] != edificacao["nome"] and \
                   outra_edificacao.get("tratamento") == "Conjunta" and \
                   outra_edificacao.get("edificacao_conjunta") == edificacao["nome"]:
                       
                       area_total_combinada += outra_edificacao['area']
                       edificacao_combinada['areas_combinadas_com'].append(outra_edificacao['nome'])
                       
            edificacao_combinada['area'] = area_total_combinada
            
            edificacoes_consolidadas.append(edificacao_combinada)
            nomes_ja_consolidados.add(edificacao["nome"])
        
    return edificacoes_consolidadas


# --- FUNÇÕES PARA GESTÃO DE COMPARAÇÕES DE ISOLAMENTO DE RISCO ---
def add_comparison():
    """Adiciona uma nova comparação à lista no session_state."""
    if 'comparacoes_extra' not in st.session_state:
        st.session_state.comparacoes_extra = []
        
    st.session_state.comparacoes_extra.append({
        'edf1_nome': None, 
        'edf2_nome': None, 
        'largura1': 5.0, 
        'altura1': 10.0, 
        'abertura1': 2.0
    })
    pass 

def remove_comparison(index):
    """Remove a comparação pelo índice."""
    if index < len(st.session_state.comparacoes_extra):
        st.session_state.comparacoes_extra.pop(index)
        # CORREÇÃO FINAL: Retirado o st.experimental_rerun() daqui
    pass
# --- FIM FUNÇÕES GESTÃO DE COMPARAÇÕES ---


# 🧭 Interface principal
modo = st.radio("Como deseja começar?", ["📄 Revisar projeto existente", "🆕 Criar novo projeto"])
df = pd.DataFrame()
arquivo = None
linha_selecionada = None
mostrar_campos = False
todas_edificacoes = [] 

if modo == "📄 Revisar projeto existente":
    arquivo = st.file_uploader("Anexe a planilha do projeto (.xlsx)", type=["xlsx"])
    if not arquivo:
        st.warning("⚠️ Para revisar um projeto, anexe a planilha primeiro.")
    if arquivo:
        nome_arquivo_entrada = arquivo.name
        try:
            df = pd.read_excel(arquivo)
            st.success("Planilha carregada com sucesso!")
            if not df.empty:
                st.session_state.processamento_concluido = True 
            mostrar_campos = True
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

elif modo == "🆕 Criar novo projeto":
    linha_selecionada = pd.Series({"NomeProjeto": ""})
    st.success("Novo projeto iniciado. Preencha os dados abaixo.")
    mostrar_campos = True

# 🏗️ Levantamento das edificações
if mostrar_campos:
    st.markdown("### 🧾 Versão do Projeto")
    linha_selecionada["NomeProjeto"] = st.text_input("Nome do Projeto", value=linha_selecionada.get("NomeProjeto", ""))
    nome_usuario = st.text_input("Seu nome", value="Vitor")
    linha_selecionada["UltimoUsuario"] = f"{nome_usuario} + Copilot"
    linha_selecionada["UltimaModificacao"] = datetime.now().strftime('%d/%m/%Y %H:%M')
    st.markdown("<div style='border-top: 6px solid #555; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>🏢 Levantamento das Edificações e Anexos</h3>", unsafe_allow_html=True)
    
    col_qtd_edificacoes, col_qtd_anexos = st.columns(2)
    with col_qtd_edificacoes:
        num_torres = st.number_input("Quantidade de torres/edificações residenciais", min_value=0, step=1, value=1, key='num_torres')
    with col_qtd_anexos:
        num_anexos = st.number_input("Quantidade de anexos", min_value=0, step=1, value=1, key='num_anexos', help="Edificações térreas com permanência de pessoas e de uso não residencial.")

    torres = []
    st.markdown("### 🏢 Edificações Residenciais")
    if num_torres > 0:
        for i in range(int(num_torres)):
            st.markdown(f"**Edificação Residencial {i+1}**")
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input(f"Nome da edificação {i+1}", key=f"nome_torre_{i}", value=f"Edificação {chr(97+i)}")
            with col2:
                area = st.number_input(f"Área da edificação {i+1} (m²)", min_value=0.0, step=1.0, key=f"area_torre_{i}", value=750.0)
            terrea = st.radio(f"A edificação {i+1} é térrea?", ["Sim", "Não"], key=f"terrea_torre_{i}")
            
            num_pavimentos, um_ap_por_pav, subsolo_tecnico, numero_subsolos, area_subsolo, subsolo_ocupado, subsolo_menor_50, duplex, atico, altura = (1, None, "Não", "0", "Menor que 500m²", "Não", "Não", "Não", "Não", 0.0)

            if terrea == "Não":
                num_pavimentos = st.number_input(f"Número de pavimentos da edificação {i+1}", min_value=2, step=1, key=f"num_pavimentos_torre_{i}", value=4)
                um_ap_por_pav = st.radio(f"A edificação {i+1} é de um apartamento por pavimento?", ["Sim", "Não"], key=f"ap_por_pav_{i}")
                subsolo_tecnico = st.radio(f"Existe subsolo na edificação {i+1}?", ["Não", "Sim"], key=f"subsolo_tecnico_{i}")
                if subsolo_tecnico == "Sim":
                    st.markdown("<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento...</span>", unsafe_allow_html=True)
                    numero_subsolos = st.radio(f"Quantidade de subsolos na edificação {i+1}?", ["1", "Mais de 1"], key=f"numero_subsolos_{i}")
                    if numero_subsolos == "1":
                        area_subsolo = st.selectbox(f"Área do subsolo da edificação {i+1}", ["Menor que 500m²", "Maior que 500m²"], key=f"area_subsolo_{i}")
                    else:
                        area_subsolo = "Maior que 500m²"
                    subsolo_ocupado = st.radio(f"Algum dos dois primeiros subsolos possui ocupação secundária?", ["Não", "Sim"], key=f"subsolo_ocupado_{i}")
                    if subsolo_ocupado == "Sim":
                        subsolo_menor_50 = st.radio(f"A ocupação secundária tem no máximo 50m² em cada subsolo?", ["Não", "Sim"], key=f"subsolo_menor_50_{i}")
                duplex = st.radio(f"Existe duplex no último pavimento da edificação {i+1}?", ["Não", "Sim"], key=f"duplex_{i}")
                atico = st.radio(f"Há pavimento de ático/casa de máquinas acima do último pavimento?", ["Não", "Sim"], key=f"atico_{i}")
                
                parte_superior = "Cota do primeiro pavimento do duplex" if duplex == "Sim" else "Cota de piso do último pavimento habitado"
                if subsolo_tecnico == "Não" and subsolo_ocupado == "Não":
                    parte_inferior = "cota de piso do pavimento mais baixo, exceto subsolos"
                elif subsolo_tecnico == "Sim" and subsolo_ocupado == "Sim" and subsolo_menor_50 == "Não":
                    parte_inferior = "cota de piso do subsolo em que a ocupação secundária ultrapassa 50m²"
                else:
                    parte_inferior = "cota de piso do pavimento mais baixo, exceto subsolos"
                st.markdown(f"💡 Altura da edificação {i+1} é: **{parte_superior} - {parte_inferior}**")
                altura = st.number_input(f"Informe a altura da edificação {i+1} (m)", min_value=0.0, step=0.1, key=f"altura_torre_{i}", value=8.0)
            
            torres.append({
                "nome": nome, "area": area, "altura": altura, "terrea": terrea,
                "num_pavimentos": num_pavimentos, "um_ap_por_pav": um_ap_por_pav,
                "subsolo_tecnico": subsolo_tecnico, "numero_subsolos": numero_subsolos,
                "area_subsolo": area_subsolo, "subsolo_ocupado": subsolo_ocupado,
                "subsolo_menor_50": subsolo_menor_50, "duplex": duplex, "atico": atico,
            })

    anexos = []
    st.markdown("### 📎 Anexos do Projeto")
    if num_anexos > 0:
        opcoes_uso_anexo = ["C-1", "F-6", "F-8", "G-1", "G-2", "J-2"]
        opcoes_carga_incendio = ["300 MJ/m²", "600 MJ/m²"]
        for i in range(int(num_anexos)):
            st.markdown(f"**Anexo {i+1}**")
            col_anexo_1, col_anexo_2 = st.columns(2)
            with col_anexo_1:
                nome = st.text_input(f"Nome do anexo {i+1}", key=f"nome_anexo_{i}", value=f"Anexo {chr(97+i)}")
            with col_anexo_2:
                area = st.number_input(f"Área do anexo {i+1} (m²)", min_value=0.0, step=1.0, key=f"area_anexo_{i}", value=50.0)
            col_anexo_3, col_anexo_4 = st.columns(2)
            with col_anexo_3:
                uso = st.selectbox(f"Uso/Ocupação do anexo {i+1}", options=opcoes_uso_anexo, key=f"uso_anexo_{i}")
            with col_anexo_4:
                carga = st.selectbox(f"Carga de incêndio do anexo {i+1}", options=opcoes_carga_incendio, key=f"carga_anexo_{i}")
            anexos.append({
                "nome": nome, "area": area, "uso": uso, "carga_incendio": carga,
                "terrea": "Sim", "num_pavimentos": 1, "um_ap_por_pav": None, "altura": 0.0
            })
    
    # Juntar todas as edificações
    todas_edificacoes = torres + anexos

    # --- INÍCIO LÓGICA DE DECISÃO E CONSOLIDAÇÃO ---
    if len(todas_edificacoes) >= 1:
        
        # 1. Definição de Tratamento (Aparece se houver ANEXOS OU MAIS DE UMA TORRE)
        if len(torres) > 1 or len(anexos) > 0:
            st.markdown("<div style='border-top: 6px solid #555; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)
            st.markdown("### 🔀 Definição de Tratamento por Edificação")
            
            nomes_torres = [t['nome'] for t in torres if t['nome']]

            for i, edificacao in enumerate(todas_edificacoes):
                if edificacao["nome"]:
                    tratamento_key = f"tratamento_{edificacao['nome']}_{i}"
                    conjunta_key = f"conjunta_com_{edificacao['nome']}_{i}"
                    
                    is_torre = edificacao in torres
                    
                    # --- FLUXO CONDICIONAL DE EXIBIÇÃO ---
                    # 1. Se é a ÚNICA torre, define como Independente e informa
                    if is_torre and len(torres) == 1:
                        edificacao['tratamento'] = "Independente"
                        edificacao['edificacao_conjunta'] = None
                        st.markdown(f"✅ Edificação **{edificacao['nome']}** (Torre Única) será tratada como **Independente**.")
                        continue
                    
                    # 2. Para anexos ou múltiplas torres, exibe o radio button
                    pergunta = f"A edificação **{edificacao['nome']}** será tratada independente ou conjunta com outra?"
                    if not is_torre:
                        pergunta = f"O anexo **{edificacao['nome']}** será tratado independente ou será anexado como área de outra?"
                        
                    tratamento = st.radio(
                        pergunta,
                        ["Independente", "Conjunta"],
                        key=tratamento_key
                    )
                    edificacao['tratamento'] = tratamento
                    
                    if tratamento == "Conjunta":
                        if not nomes_torres:
                            st.warning("⚠️ Necessário cadastrar uma torre para anexar a área.")
                            edificacao['edificacao_conjunta'] = None
                        else:
                            edificacao['edificacao_conjunta'] = st.selectbox(
                                f"Qual edificação **irá absorver** a área de **{edificacao['nome']}**?",
                                options=nomes_torres,
                                key=conjunta_key
                            )
                    else:
                        edificacao['edificacao_conjunta'] = None
        else:
            # Caso haja apenas 1 edificação e 0 anexos, define como Independente
            if todas_edificacoes:
                todas_edificacoes[0]['tratamento'] = "Independente"
                todas_edificacoes[0]['edificacao_conjunta'] = None
        
        # 2. Consolidação da Área (Executada após o loop de tratamento)
        edificacoes_consolidadas = consolidar_edificacoes(todas_edificacoes)
        
        st.session_state.edificacoes_finais = edificacoes_consolidadas
        st.session_state.processamento_concluido = True 
        
    # --- FIM LÓGICA DE DECISÃO E CONSOLIDAÇÃO ---

    # 🔀 Bloco de Isolamento entre Edificações (OPCIONAL)
    # A exibição é baseada no número de edificações iniciais
    if len(todas_edificacoes) > 1:
        if st.checkbox("Deseja rodar a análise detalhada de Isolamento de Risco (Fachada/Abertura)?", key='check_isolamento'):
            
            # --- PREPARAÇÃO DA LISTA DE OPÇÕES ---
            nomes_edificacoes_finais = [e["nome"] for e in st.session_state.edificacoes_finais if e["nome"]]
            
            st.markdown("<div style='border-top: 6px solid #555; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)
            st.markdown("### Isolamento entre Edificações (Análise de Fachada)")
            
            st.radio("Há corpo de bombeiros com viatura de combate a incêndio na cidade?", ["Sim", "Não"], key="bombeiros")

            # --- GESTÃO DINÂMICA DE COMPARAÇÕES ---
            if st.button("➕ Adicionar Comparação de Isolamento de Risco", on_click=add_comparison):
                pass 
            
            if len(nomes_edificacoes_finais) < 2:
                st.warning("É necessário que hajam pelo menos duas edificações ou grupos consolidados (Independentes) para fazer uma comparação de isolamento de risco.")
            
            # Loop sobre as comparações dinâmicas
            for i, comp in enumerate(st.session_state.comparacoes_extra):
                
                opcoes_edf = nomes_edificacoes_finais
                
                if not opcoes_edf:
                    break
                    
                # 1. TRATAMENTO DE VALOR INICIAL PARA SELEÇÃO
                if comp['edf1_nome'] is None or comp['edf1_nome'] not in opcoes_edf:
                    comp['edf1_nome'] = opcoes_edf[0] if opcoes_edf else None
                    
                # 2. TRATAMENTO DE VALOR INICIAL PARA EDIFICAÇÃO 2
                opcoes_edf2 = [n for n in opcoes_edf if n != comp['edf1_nome']]
                if not opcoes_edf2:
                     comp['edf2_nome'] = None
                elif comp['edf2_nome'] is None or comp['edf2_nome'] not in opcoes_edf2:
                    comp['edf2_nome'] = opcoes_edf2[0]
                
                st.markdown(f"#### Comparação {i+1}: Risco entre {comp.get('edf1_nome', '...')} e {comp.get('edf2_nome', '...')}")
                
                col_init = st.columns(3)
                
                # Edificação 1
                with col_init[0]:
                    index_edf1 = opcoes_edf.index(comp['edf1_nome']) if comp['edf1_nome'] in opcoes_edf else 0
                    
                    comp['edf1_nome'] = st.selectbox(
                        "Edificação 1:", 
                        opcoes_edf, 
                        key=f"comparacao_edf1_{i}",
                        index=index_edf1
                    )
                
                # Edificação 2
                with col_init[1]:
                    # Recalcula as opções após a seleção da Edificação 1
                    opcoes_edf2 = [n for n in opcoes_edf if n != comp['edf1_nome']]
                    
                    # Garantir que o índice seja 0 se houver opções, ou 0 se estiver vazia (para evitar crash)
                    index_edf2 = opcoes_edf2.index(comp['edf2_nome']) if comp['edf2_nome'] in opcoes_edf2 else (0 if opcoes_edf2 else 0)
                    
                    comp['edf2_nome'] = st.selectbox(
                        "Edificação 2:", 
                        opcoes_edf2, 
                        key=f"comparacao_edf2_{i}",
                        index=index_edf2
                    )

                # Botão de Remover
                with col_init[2]:
                    st.write("") 
                    if st.button(f"➖ Remover", key=f"remove_comp_{i}", on_click=remove_comparison, args=(i,)):
                        pass 

                # Os dados para cálculo devem vir da lista CONSOLIDADA
                edf1_data = next((e for e in st.session_state.edificacoes_finais if e["nome"] == comp['edf1_nome']), None)
                edf2_data = next((e for e in st.session_state.edificacoes_finais if e["nome"] == comp['edf2_nome']), None)

                # Só exibe os campos de input de cálculo se houver 2 edificações válidas para comparação
                if edf1_data and edf2_data and edf1_data['nome'] != edf2_data['nome']:
                    acrescimo = 1.5 if st.session_state.bombeiros == "Sim" else 3.0
                    
                    st.markdown(f"**Fachada a usar na comparação (Edificação 1 - {edf1_data['nome']}):** {fachada_edificacao(edf1_data)}")
                    
                    col_calc = st.columns(4)
                    with col_calc[0]:
                        comp['largura1'] = st.number_input(f"Largura Fachada {edf1_data['nome']} (m)", min_value=0.0, step=0.1, key=f"largura1_{i}", value=comp.get('largura1', 5.0))
                    with col_calc[1]:
                        comp['altura1'] = st.number_input(f"Altura Fachada {edf1_data['nome']} (m)", min_value=0.0, step=0.1, key=f"altura1_{i}", value=comp.get('altura1', 10.0))
                    with col_calc[2]:
                        area1 = comp['largura1'] * comp['altura1']
                        st.metric(label=f"Área Fachada {edf1_data['nome']} (m²)", value=f"{area1:.2f}")
                    with col_calc[3]:
                        comp['abertura1'] = st.number_input(f"Área Abertura {edf1_data['nome']} (m²)", min_value=0.0, step=0.1, key=f"abertura1_{i}", value=comp.get('abertura1', 2.0))
                    
                    st.metric(label=f"Distância de isolamento (Edificação 1)", value=f"N/A m")
                    st.metric(label=f"Distância de isolamento (Edificação 2)", value=f"N/A m")
                
                st.markdown("<div style='border-top: 2px solid #ddd; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)
                
            # --- COMENTÁRIO FIXO EM VERMELHO ADICIONADO AQUI ---
            st.markdown(
                "<span style='color:red'>⚠️ Ao terminar as análises, volte e revise as considerações de **independência** de cada edificação/anexo.</span>", 
                unsafe_allow_html=True
            )
            
            st.markdown("### 📝 Comentários sobre Isolamento de Risco")
            st.text_area("Observações sobre distanciamento e isolamento de risco.", key="comentario_isolamento_geral")
    
    # 🧯 Tabela resumo de medidas de segurança e Detalhamento por medida de segurança
    if st.session_state.processamento_concluido:
        st.markdown("<div style='border-top: 6px solid #555; margin-top: 20px; margin-bottom: 20px'></div>", unsafe_allow_html=True)
        st.markdown("## 🔍 Medidas de Segurança por Edificação")
        
        for i, edificacao in enumerate(st.session_state.edificacoes_finais):
            nome_edificacao = edificacao.get("nome", f"Edificação {i+1}")
            st.markdown(f"### 🏢 {nome_edificacao}")

            area_consolidada = edificacao.get("area", 0) 
            altura_valor = edificacao.get("altura", 0)
            num_pavimentos = edificacao.get("num_pavimentos", 1)
            
            is_tabela_simplificada = area_consolidada <= 750 and altura_valor <= 12

            resumo = medidas_por_enquadramento(area_consolidada, altura_valor, num_pavimentos)
            
            notas = notas_relevantes(resumo, altura_valor, num_pavimentos, is_tabela_simplificada)
            
            st.markdown("### Tabela de Medidas de Segurança Aplicáveis")
            st.info(f"Área Consolidada utilizada para Enquadramento: **{area_consolidada:.2f} m²**") 
            df_resumo = pd.DataFrame.from_dict(resumo, orient='index', columns=["Aplicação"])
            st.table(df_resumo)

            if notas:
                st.markdown("### Notas Específicas")
                for nota in notas:
                    st.markdown(f"- {nota}")
            
            st.markdown("### Detalhamento")
            
            # Detalhamento para "Acesso de Viatura"
            if "X" in resumo.get("Acesso de Viatura na Edificação", ""):
                with st.expander(f"🔹 Acesso de Viatura na Edificação - {nome_edificacao}"):
                    st.markdown("**Será previsto hidrante de recalque a não mais que 20m do limite da edificação?**")
                    hidrante_recalque = st.radio("Resposta:", ["Sim", "Não"], key=f"hidrante_recalque_{i}")
                    st.markdown("<span style='color:red'>⚠️ O hidrante de recalque a menos de 20m anula as exigências a respeito do acesso de viaturas na edificação.</span>", unsafe_allow_html=True)
                    st.markdown("✅ O portão de acesso deve ter, no mínimo, **4m de largura** e **4,5m de altura**.")
                    if hidrante_recalque == "Não":
                        st.markdown("✅ As vias devem ter, no mínimo, **6m de largura** e **4,5m de altura**, além de suportar viaturas de **25 toneladas em dois eixos**.")
            
            # Detalhamento para "Segurança Estrutural"
            if "X" in resumo.get("Segurança Estrutural contra Incêndio", ""):
                with st.expander(f"🔹 Segurança Estrutural contra Incêndio - {nome_edificacao}"):
                    resposta_trrf = ""
                    mostrar_trrf_adotado = False
                    
                    if edificacao.get("terrea") == "Sim":
                        resposta_estrutura_terrea = st.radio(
                            "Há algum elemento estrutural que seu colapso comprometa a estabilidade de elementos de compartimentação ou isolamento?",
                            ["Não", "Sim"], key=f"estrutura_terrea_{i}")
                        if resposta_estrutura_terrea == "Sim":
                            resposta_trrf = "⚠️ A edificação deve comprovar TRRF de 30min para elementos estruturais."
                            st.markdown(f"<span style='color:red'>{resposta_trrf}</span>", unsafe_allow_html=True)
                            mostrar_trrf_adotado = True
                        else:
                            resposta_trrf = "✅ A edificação está isenta de comprovação de TRRF para elementos estruturais."
                            st.markdown(resposta_trrf)
                    else:
                        area = area_consolidada
                        subsolo_tecnico = edificacao.get("subsolo_tecnico", "Não")
                        numero_subsolos = edificacao.get("numero_subsolos", "0")
                        area_subsolo = edificacao.get("area_subsolo", "Menor que 500m²")
                        
                        altura_menor_igual_12 = altura_valor <= 12
                        area_menor_1500 = area < 1500
                        area_maior_igual_1500 = area >= 1500
                        subsolo_simples = numero_subsolos == "1" and area_subsolo == "Menor que 500m²"
                        subsolo_complexo = numero_subsolos != "1" or area_subsolo == "Maior que 500m²"
                        sem_subsolo = subsolo_tecnico == "Não"
                        
                        if altura_menor_igual_12 and area_menor_1500 and (sem_subsolo or subsolo_simples):
                            resposta_trrf = "✅ A edificação está isenta de comprovação de TRRF para elementos estruturais."
                        elif altura_menor_igual_12 and area_menor_1500 and subsolo_complexo:
                            resposta_trrf = "⚠️ Apenas o(s) subsolo(s) deverão apresentar comprovação de TRRF para elementos estruturais."
                            mostrar_trrf_adotado = True
                        elif (altura_valor > 12 or area_maior_igual_1500) and (sem_subsolo or subsolo_simples):
                            resposta_trrf = "⚠️ Cada pavimento deverá apresentar comprovação de TRRF para elementos estruturais. Cada pavimento tem seu TRRF determinado de acordo com seu uso e nunca inferior ao do pavimento superior (o subsolo absorve o TRRF do pavimento superior)."
                            mostrar_trrf_adotado = True
                        elif (altura_valor > 12 or area_maior_igual_1500) and subsolo_complexo:
                            resposta_trrf = "⚠️ Cada pavimento deverá apresentar comprovação de TRRF para elementos estruturais. Cada pavimento tem seu TRRF determinado de acordo com seu uso e nunca inferior ao do pavimento superior."
                            mostrar_trrf_adotado = True
                        st.markdown(resposta_trrf)
                        
                        if "Cada pavimento deverá apresentar comprovação de TRRF" in resposta_trrf:
                            cobertura_check = st.radio("Algum dos seguintes itens é verdadeiro:\n\nI. A cobertura tem permanência de pessoas ou estoque de algum material?\nII. Faz parte de alguma rota de fuga?\nIII. Seu colapso estrutural compromete a estrutura principal ou paredes externas?", ["Não", "Sim"], index=0, key=f"cobertura_trrf_{i}")
                            if cobertura_check == "Sim":
                                st.markdown("⚠️ A cobertura deve ter o mesmo TRRF da estrutura principal.")
                            else:
                                st.markdown("✅ A cobertura está isenta de comprovação de TRRF para os elementos estruturais.")
                        
                    if mostrar_trrf_adotado:
                        if "Cada pavimento deverá apresentar comprovação de TRRF" in resposta_trrf or "subsolo(s) deverão apresentar comprovação de TRRF" in resposta_trrf:
                            st.markdown("*(Referência: Imagem da tabela de Tempos requeridos de resistência ao fogo)*")
                        st.text_area("TRRF adotado:", value="", key=f"trrf_adotado_{i}")
                    st.text_area("Observações sobre segurança estrutural", value="", key=f"comentario_estrutural_{i}")

            # Detalhamento para outras medidas
            for medida, aplicacao in resumo.items():
                if aplicacao != "-" and medida not in ["Acesso de Viatura na Edificação", "Segurança Estrutural contra Incêndio"]:
                    with st.expander(f"🔹 {medida} - {nome_edificacao}"):
                        st.markdown(f"Conteúdo técnico sobre **{medida.lower()}**...")
                        if "¹" in aplicacao: st.markdown("📌 Observação especial: ver nota 1")
                        elif "²" in aplicacao: st.markdown("📌 Observação especial: ver nota 2")
                        elif "³" in aplicacao: st.markdown("📌 Observação especial: ver nota 3")
                        elif "⁴" in aplicacao: st.markdown("📌 Observação especial: ver nota 4")
    else:
        st.warning("Cadastre as edificações para ver as medidas de segurança aplicáveis.")


    # 📥 Exportação final (Adaptado para múltiplas edificações)
    st.markdown("## 📥 Exportar planilha atualizada")
    if st.session_state.processamento_concluido and st.session_state.edificacoes_finais:
        df_completo = pd.DataFrame(st.session_state.edificacoes_finais)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_completo.to_excel(writer, index=False, sheet_name='Edificações')
        output.seek(0)
        
        nome_projeto = linha_selecionada.get("NomeProjeto", "ProjetoSemNome")
        nome_arquivo_saida = gerar_nome_arquivo(nome_projeto, arquivo.name if arquivo else None)
        
        st.download_button(
            label="📥 Baixar Planilha Atualizada",
            data=output.getvalue(),
            file_name=nome_arquivo_saida,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_button_planilha_final"
        )
    else:
        if len(todas_edificacoes) > 0 and not st.session_state.processamento_concluido:
            st.warning("Defina o agrupamento das edificações para liberar a exportação.")
        elif not todas_edificacoes:
            st.warning("Cadastre as edificações para exportar.")

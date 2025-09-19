# app.py - Versão Final e Corrigida

import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA E ESTADO INICIAL ---
st.set_page_config(layout="wide", page_title="Ferramenta de Projetos Colaborativa")

# Inicializa o estado da sessão
if 'screen' not in st.session_state:
    st.session_state.screen = 'lobby'
if 'current_project_data' not in st.session_state:
    st.session_state.current_project_data = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# --- CONEXÃO COM O GOOGLE SHEETS ---
try:
    conn = st.connection("gcs", type="streamlit_gsheets.GSheetsConnection")
except Exception as e:
    st.error("Erro ao conectar com o Google Sheets. Verifique a configuração em .streamlit/secrets.toml e o compartilhamento da planilha.")
    st.exception(e)
    st.stop()

# --- FUNÇÃO AUXILIAR ---
def get_all_projects():
    """Lê todos os projetos da planilha e retorna como um DataFrame."""
    try:
        df = conn.read(worksheet="Projetos", usecols=list(range(6)), ttl=5)
        df.dropna(how="all", inplace=True)
        return df
    except Exception as e:
        if "WorksheetNotFound" in str(e):
            return pd.DataFrame(columns=['NomeProjeto', 'Ocupacao', 'Area', 'Altura', 'UltimoUsuario', 'UltimaModificacao'])
        else:
            st.error(f"Ocorreu um erro ao ler a planilha: {e}")
            return None

# --- TELAS DA APLICAÇÃO ---

def show_lobby():
    """Exibe a tela inicial para selecionar ou criar um projeto."""
    st.title("Lobby de Projetos PPCI")
    st.write("Selecione um projeto existente para continuar ou crie um novo.")

    df_projetos = get_all_projects()
    
    if df_projetos is None:
        st.stop()

    st.header("1. Continuar um Projeto")
    if not df_projetos.empty:
        opcoes = [f"{row.NomeProjeto} (Editado por: {row.UltimoUsuario})" for _, row in df_projetos.iterrows()]
        projeto_selecionado_str = st.selectbox("Selecione um projeto:", options=opcoes, index=None, placeholder="Escolha um projeto...")

        if st.button("Carregar Projeto"):
            if projeto_selecionado_str:
                nome_real_projeto = projeto_selecionado_str.split(" (Editado por:")[0]
                dados_do_projeto = df_projetos[df_projetos['NomeProjeto'] == nome_real_projeto].iloc[0]
                st.session_state.current_project_data = dados_do_projeto
                st.session_state.screen = 'workspace'
                st.rerun()
            else:
                st.warning("Por favor, selecione um projeto para carregar.")
    else:
        st.info("Nenhum projeto encontrado. Crie o primeiro abaixo!")

    st.header("2. Criar um Novo Projeto")
    with st.form("form_novo_projeto"):
        novo_nome_projeto = st.text_input("Nome do Novo Projeto:")
        submitted = st.form_submit_button("Criar e Começar")

        if submitted:
            if novo_nome_projeto:
                if 'NomeProjeto' in df_projetos.columns and novo_nome_projeto in df_projetos['NomeProjeto'].values:
                    st.error("Já existe um projeto com este nome.")
                else:
                    novo_projeto_data = {
                        'NomeProjeto': novo_nome_projeto, 'Ocupacao': 'A-1',
                        'Area': 100.0, 'Altura': 3.0, 'UltimoUsuario': st.session_state.user_name or 'N/A',
                        'UltimaModificacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    try:
                        worksheet = conn._instance.worksheet("Projetos")
                        nova_linha = [
                            novo_projeto_data['NomeProjeto'], novo_projeto_data['Ocupacao'],
                            novo_projeto_data['Area'], novo_projeto_data['Altura'],
                            novo_projeto_data['UltimoUsuario'], novo_projeto_data['UltimaModificacao']
                        ]
                        worksheet.append_row(nova_linha)
                        
                        st.session_state.current_project_data = pd.Series(novo_projeto_data)
                        st.session_state.screen = 'workspace'
                        st.success(f"Projeto '{novo_nome_projeto}' criado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não foi possível adicionar o projeto à planilha. Erro: {e}")

            else:
                st.warning("Por favor, digite um nome para o novo projeto.")

def show_workspace():
    """Exibe a área de trabalho para editar o projeto carregado."""
    dados_projeto = st.session_state.current_project_data
    nome_projeto = dados_projeto['NomeProjeto']
    
    st.title(f"Editando Projeto: ✨ {nome_projeto} ✨")
    
    if st.button("← Voltar ao Lobby (sem salvar)"):
        st.session_state.screen = 'lobby'
        st.session_state.current_project_data = None
        st.rerun()
        
    st.sidebar.header("Sua Identificação")
    st.session_state.user_name = st.sidebar.text_input("Seu nome (obrigatório para salvar):", value=st.session_state.user_name)
    st.sidebar.info(f"Última alteração por: **{dados_projeto['UltimoUsuario']}**")

    st.header("Dados do Projeto")
    
    ocupacao_opts = ['A-1', 'B-2', 'C-3', 'F-6']
    try:
        current_ocup_index = ocupacao_opts.index(dados_projeto.get('Ocupacao', 'A-1'))
    except (ValueError, TypeError):
        current_ocup_index = 0

    ocupacao = st.selectbox("Tipo de Ocupação:", options=ocupacao_opts, index=current_ocup_index)
    area = st.number_input("Área Construída (m²):", min_value=1.0, value=float(dados_projeto.get('Area', 100.0)))
    altura = st.number_input("Altura da Edificação (m):", min_value=1.0, value=float(dados_projeto.get('Altura', 3.0)))

    if st.button("Salvar Alterações no Projeto", type="primary"):
        if st.session_state.user_name:
            try:
                worksheet = conn._instance.worksheet("Projetos")
                cell = worksheet.find(nome_projeto)
                
                if cell:
                    linha_para_atualizar = cell.row
                    novos_valores = [
                        nome_projeto, ocupacao, area, altura,
                        st.session_state.user_name, datetime.now().strftime('%d/%m/%Y %H:%M')
                    ]
                    worksheet.update(f'A{linha_para_atualizar}:F{linha_para_atualizar}', [novos_valores])
                    
                    df_headers = worksheet.row_values(1)
                    st.session_state.current_project_data = pd.Series(dict(zip(df_headers, novos_valores)))
                    
                    st.success(f"Projeto '{nome_projeto}' atualizado com sucesso!")
                    st.balloons()
                else:
                    st.error("Erro: Projeto não encontrado na planilha para atualização.")
            except Exception as e:
                st.error(f"Não foi possível salvar as alterações. Erro: {e}")
        else:
            st.warning("Por favor, insira seu nome na barra lateral para salvar.")

# --- CONTROLE PRINCIPAL DO FLUXO ---
if st.session_state.screen == 'lobby':
    show_lobby()
elif st.session_state.screen == 'workspace':
    show_workspace()
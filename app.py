# app.py - Versão Supabase

import streamlit as st
import pandas as pd
from datetime import datetime
from st_supabase_connection import SupabaseConnection

# --- CONFIGURAÇÃO DA PÁGINA E ESTADO INICIAL ---
st.set_page_config(layout="wide", page_title="Ferramenta de Projetos Colaborativa")

if 'screen' not in st.session_state:
    st.session_state.screen = 'lobby'
if 'current_project_data' not in st.session_state:
    st.session_state.current_project_data = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

# --- CONEXÃO COM O SUPABASE ---
try:
   conn = st.connection(
    "supabase",
    type=SupabaseConnection,
    url="https://cohrnyrtazrcgemiakqr.supabase.co"
)
except Exception as e:
    st.error("Erro ao conectar com o Supabase. Verifique a configuração em .streamlit/secrets.toml.")
    st.exception(e)
    st.stop()

# --- FUNÇÕES AUXILIARES ---
def get_all_projects():
    """Lê todos os projetos do Supabase e retorna como um DataFrame."""
    try:
        response = conn.query("*", table="projetos", ttl="10m").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler os projetos: {e}")
        return pd.DataFrame()

# --- TELAS DA APLICAÇÃO ---

def show_lobby():
    """Exibe a tela inicial para selecionar ou criar um projeto."""
    st.title("Lobby de Projetos PPCI")
    st.write("Selecione um projeto existente para continuar ou crie um novo.")

    df_projetos = get_all_projects()

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
                        'Area': 100.0, 'Altura': 3.0, 'UltimoUsuario': 'N/A',
                        'UltimaModificacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    try:
                        conn.insert("projetos", [novo_projeto_data]).execute()
                        st.session_state.current_project_data = pd.Series(novo_projeto_data)
                        st.session_state.screen = 'workspace'
                        st.success(f"Projeto '{novo_nome_projeto}' criado!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Não foi possível criar o projeto. Erro: {e}")

def show_workspace():
    """Exibe a área de trabalho para editar o projeto carregado."""
    dados_projeto = st.session_state.current_project_data
    nome_projeto = dados_projeto['NomeProjeto']
    
    st.title(f"Editando Projeto: ✨ {nome_projeto} ✨")
    
    if st.button("← Voltar ao Lobby"):
        st.session_state.screen = 'lobby'
        st.rerun()
        
    st.sidebar.header("Sua Identificação")
    st.session_state.user_name = st.sidebar.text_input("Seu nome:", value=st.session_state.user_name)

    st.header("Dados do Projeto")
    ocupacao = st.selectbox("Ocupação:", ['A-1', 'B-2', 'C-3'], index=0)
    area = st.number_input("Área (m²):", value=float(dados_projeto.get('Area', 100.0)))
    altura = st.number_input("Altura (m):", value=float(dados_projeto.get('Altura', 3.0)))

    if st.button("Salvar Alterações", type="primary"):
        if st.session_state.user_name:
            novos_dados = {
                'Ocupacao': ocupacao, 'Area': area, 'Altura': altura,
                'UltimoUsuario': st.session_state.user_name,
                'UltimaModificacao': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            try:
                conn.update("projetos", novos_dados).eq("NomeProjeto", nome_projeto).execute()
                st.success(f"Projeto '{nome_projeto}' atualizado!")
                st.balloons()
            except Exception as e:
                st.error(f"Não foi possível salvar as alterações. Erro: {e}")

# --- CONTROLE PRINCIPAL DO FLUXO ---
if st.session_state.screen == 'lobby':
    show_lobby()
elif st.session_state.screen == 'workspace':
    show_workspace()

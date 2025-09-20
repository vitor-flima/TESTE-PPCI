# ... [cabeçalho e funções anteriores mantidos]

# 🔝 Informações gerais da versão
if linha_selecionada is not None and isinstance(linha_selecionada, pd.Series):
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

# Perguntas condicionais
linha_selecionada["SubsoloTecnico"] = st.radio("Existe subsolo de estacionamento, área técnica ou sem ocupação de pessoas?", ["Não", "Sim"])
if linha_selecionada["SubsoloTecnico"] == "Sim":
    st.markdown("<span style='color:red'>⚠️ Se tiver mais de 0,006m² por m³ do pavimento ou sua laje de teto estiver acima, em pelo menos, 1,2m do perfil natural em pelo menos um lado, não é subsolo e deve ser considerado na altura</span>", unsafe_allow_html=True)
    linha_selecionada["SubsoloComOcupacao"] = st.radio("Um dos dois primeiros subsolos abaixo do térreo possui ocupação secundária?", ["Não", "Sim"])
    if linha_selecionada["SubsoloComOcupacao"] == "Sim":
        linha_selecionada["SubsoloMenor50m2"] = st.radio("Essa ocupação secundária tem no máximo 50m² em cada subsolo?", ["Não", "Sim"])

linha_selecionada["DuplexUltimoPavimento"] = st.radio("Existe duplex no último pavimento?", ["Não", "Sim"])
linha_selecionada["AticoOuCasaMaquinas"] = st.radio("Há pavimento de ático/casa de máquinas/casa de bombas acima do último pavimento?", ["Não", "Sim"])

# Campo de altura
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

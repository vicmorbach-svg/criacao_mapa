import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io # Necessário para gerar o arquivo de download em memória

# Configuração inicial da página
st.set_page_config(page_title="Mapa de Diretorias - RS", layout="wide")

st.title("🗺️ Mapa de Reestruturação - Diretorias do RS")
st.markdown("Faça o upload da sua planilha, personalize as cores e baixe os mapas em alta resolução.")

@st.cache_data
def load_map_data():
    return gpd.read_file("rs_municipios.geojson")

with st.spinner("Carregando mapa local..."):
    rs_map = load_map_data()

# Função auxiliar para desenhar os mapas (evita repetição de código)
def criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores, diretoria_especifica=None):
    fig, ax = plt.subplots(figsize=(12, 10))

    # Fundo cinza (todas as cidades)
    rs_map.plot(ax=ax, color='#e0e0e0', edgecolor='white', linewidth=0.5)
    itens_legenda = []

    if diretoria_especifica is None:
        # Modo: MAPA GERAL
        for diretoria, cor in dicionario_cores.items():
            subset = cidades_destaque[cidades_destaque['DIRETORIA'] == diretoria]
            if not subset.empty:
                subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.8)
                itens_legenda.append(mpatches.Patch(color=cor, label=diretoria))

        ax.legend(handles=itens_legenda, title='Diretorias Regionais', loc='lower right')
        plt.title("Distribuição Geral das Diretorias no RS", fontsize=16, fontweight='bold')

    else:
        # Modo: MAPA INDIVIDUAL
        cor = dicionario_cores[diretoria_especifica]
        subset = cidades_destaque[cidades_destaque['DIRETORIA'] == diretoria_especifica]

        if not subset.empty:
            subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.8)
            itens_legenda.append(mpatches.Patch(color=cor, label=diretoria_especifica))

        ax.legend(handles=itens_legenda, title='Diretoria', loc='lower right')
        plt.title(f"Diretoria Regional: {diretoria_especifica}", fontsize=16, fontweight='bold')

    plt.axis('off')
    plt.tight_layout()
    return fig

# Função para converter a figura em um arquivo baixável de alta qualidade
def gerar_buffer_download(fig):
    buf = io.BytesIO()
    # dpi=300 garante a alta qualidade da imagem
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
    buf.seek(0)
    return buf

# ==========================================
# LÓGICA PRINCIPAL DO APP
# ==========================================
uploaded_file = st.file_uploader("Selecione a planilha Excel", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    if 'CIDADE' in df.columns and 'DIRETORIA' in df.columns:
        df['CIDADE'] = df['CIDADE'].astype(str).str.upper().str.strip()
        rs_map['name_muni'] = rs_map['name_muni'].astype(str).str.upper().str.strip()

        mapa_diretorias = rs_map.merge(df, how="left", left_on="name_muni", right_on="CIDADE")
        cidades_destaque = mapa_diretorias.dropna(subset=['DIRETORIA'])

        # --- BARRA LATERAL (CORES) ---
        st.sidebar.header("🎨 Personalizar Cores")
        diretorias_unicas = sorted(df['DIRETORIA'].dropna().unique())
        cores_iniciais = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99', '#C2C2F0', '#FFB3E6']

        dicionario_cores = {}
        for i, diretoria in enumerate(diretorias_unicas):
            cor_padrao = cores_iniciais[i % len(cores_iniciais)]
            dicionario_cores[diretoria] = st.sidebar.color_picker(f"{diretoria}", cor_padrao)

        # --- CRIAÇÃO DAS ABAS (TABS) ---
        nomes_abas = ["Visão Geral"] + diretorias_unicas
        abas = st.tabs(nomes_abas)

        # Aba 1: Visão Geral
        with abas[0]:
            with st.spinner("Gerando mapa geral..."):
                fig_geral = criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores)
                st.pyplot(fig_geral)

                st.download_button(
                    label="📥 Baixar Mapa Geral em Alta Qualidade (PNG)",
                    data=gerar_buffer_download(fig_geral),
                    file_name="mapa_geral_rs.png",
                    mime="image/png",
                    use_container_width=True
                )

        # Abas Seguintes: Mapas Individuais
        for i, diretoria in enumerate(diretorias_unicas):
            with abas[i + 1]: # +1 porque a aba 0 é a Visão Geral
                with st.spinner(f"Gerando mapa da regional {diretoria}..."):
                    fig_ind = criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores, diretoria_especifica=diretoria)
                    st.pyplot(fig_ind)

                    st.download_button(
                        label=f"📥 Baixar Mapa {diretoria} em Alta Qualidade (PNG)",
                        data=gerar_buffer_download(fig_ind),
                        file_name=f"mapa_{diretoria.lower()}.png",
                        mime="image/png",
                        use_container_width=True
                    )

    else:
        st.error("Erro: A planilha precisa conter as colunas 'CIDADE' e 'DIRETORIA'.")

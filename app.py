import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Mapa de Diretorias - RS", layout="wide")

st.title("🗺️ Mapa de Reestruturação - Diretorias do RS")
st.markdown("Faça o upload da sua planilha para visualizar a distribuição das cidades.")

# Agora a função lê o arquivo local instantaneamente, sem precisar de internet
@st.cache_data
def load_map_data():
    return gpd.read_file("rs_municipios.geojson")

with st.spinner("Carregando mapa local..."):
    rs_map = load_map_data()

uploaded_file = st.file_uploader("Selecione a planilha Excel", type=["xlsx"])

if uploaded_file is not None:
    with st.spinner("Processando dados e desenhando o mapa..."):
        df = pd.read_excel(uploaded_file)

        if 'CIDADE' in df.columns and 'DIRETORIA' in df.columns:
            df['CIDADE'] = df['CIDADE'].astype(str).str.upper().str.strip()
            rs_map['name_muni'] = rs_map['name_muni'].astype(str).str.upper().str.strip()

            mapa_diretorias = rs_map.merge(df, how="left", left_on="name_muni", right_on="CIDADE")

            fig, ax = plt.subplots(figsize=(12, 10))

            # Fundo cinza
            rs_map.plot(ax=ax, color='#e0e0e0', edgecolor='white', linewidth=0.5)

            cidades_destaque = mapa_diretorias.dropna(subset=['DIRETORIA'])

            if not cidades_destaque.empty:
                cidades_destaque.plot(
                    ax=ax,
                    column='DIRETORIA',
                    cmap='Set2',
                    legend=True,
                    edgecolor='black',
                    linewidth=0.8,
                    legend_kwds={'title': 'Diretorias Regionais', 'loc': 'lower right'}
                )

            plt.title("Distribuição das Diretorias no Rio Grande do Sul", fontsize=16, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()

            st.pyplot(fig)

        else:
            st.error("Erro: A planilha precisa conter as colunas 'CIDADE' e 'DIRETORIA'.")

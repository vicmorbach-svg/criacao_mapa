import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from geobr import read_municipality

# Configuração inicial da página
st.set_page_config(page_title="Mapa de Diretorias - RS", layout="wide")

st.title("🗺️ Mapa de Reestruturação - Diretorias do RS")
st.markdown("Faça o upload da sua planilha para visualizar a distribuição das cidades por diretoria no mapa do Rio Grande do Sul.")

# Função com cache para baixar o mapa do IBGE apenas na primeira vez
@st.cache_data
def load_map_data():
    return read_municipality(code_muni="RS", year=2020)

# Carrega a malha municipal
with st.spinner("Carregando malha municipal do IBGE (isso pode levar alguns segundos na primeira vez)..."):
    rs_map = load_map_data()

# Componente para upload do arquivo Excel
uploaded_file = st.file_uploader("Selecione a planilha Excel (ex: Reestruturaao_Oficial_1.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    with st.spinner("Processando dados e desenhando o mapa..."):
        # Lendo a planilha carregada
        df = pd.read_excel(uploaded_file)

        # Verificando se as colunas corretas existem
        if 'CIDADE' in df.columns and 'DIRETORIA' in df.columns:

            # Padronizando os nomes para maiúsculas para garantir o cruzamento exato
            df['CIDADE'] = df['CIDADE'].astype(str).str.upper().str.strip()
            rs_map['name_muni'] = rs_map['name_muni'].astype(str).str.upper().str.strip()

            # Cruzando os dados do mapa com a planilha
            mapa_diretorias = rs_map.merge(df, how="left", left_on="name_muni", right_on="CIDADE")

            # Configurando a figura do mapa
            fig, ax = plt.subplots(figsize=(12, 10))

            # Desenhando o fundo (todas as cidades do RS em cinza claro)
            rs_map.plot(ax=ax, color='#e0e0e0', edgecolor='white', linewidth=0.5)

            # Filtrando apenas as cidades que estão na planilha
            cidades_destaque = mapa_diretorias.dropna(subset=['DIRETORIA'])

            # Desenhando as cidades coloridas por diretoria
            if not cidades_destaque.empty:
                cidades_destaque.plot(
                    ax=ax,
                    column='DIRETORIA',
                    cmap='Set2',          # Paleta de cores
                    legend=True,
                    edgecolor='black',    # Limites das cidades em destaque
                    linewidth=0.8,
                    legend_kwds={'title': 'Diretorias Regionais', 'loc': 'lower right'}
                )

            # Ajustes visuais finais
            plt.title("Distribuição das Diretorias no Rio Grande do Sul", fontsize=16, fontweight='bold')
            plt.axis('off') # Esconde os eixos X e Y
            plt.tight_layout()

            # Exibindo o mapa no Streamlit
            st.pyplot(fig)

            # Opção para visualizar os dados brutos
            with st.expander("Visualizar dados da planilha"):
                st.dataframe(df)

        else:
            st.error("Erro: A planilha precisa conter as colunas exatas 'CIDADE' e 'DIRETORIA'.")
else:
    st.info("Aguardando o upload do arquivo para gerar a visualização.")

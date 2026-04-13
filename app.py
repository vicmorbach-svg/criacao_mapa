import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import io

st.set_page_config(page_title="Mapa Corsan", layout="wide")

st.title("🗺️ Mapa das regionais Corsan")
st.markdown("Explore o mapa interativo das cidades atendidas pela Corsan.")

@st.cache_data
def load_data():
    mapa = gpd.read_file("rs_municipios.geojson").to_crs(epsg=4326)
    planilha = pd.read_excel("Reestruturaao_Oficial_1.xlsx")
    return mapa, planilha

with st.spinner("Carregando base de dados e mapas..."):
    try:
        rs_map, df = load_data()
    except FileNotFoundError:
        st.error("⚠️ Arquivo não encontrado! Verifique os nomes dos arquivos na pasta.")
        st.stop()

df['CIDADE'] = df['CIDADE'].astype(str).str.upper().str.strip()
rs_map['name_muni'] = rs_map['name_muni'].astype(str).str.upper().str.strip()

mapa_diretorias = rs_map.merge(df, how="left", left_on="name_muni", right_on="CIDADE")
mapa_diretorias['DIRETORIA'] = mapa_diretorias['DIRETORIA'].fillna('Sem Diretoria')
cidades_destaque = mapa_diretorias[mapa_diretorias['DIRETORIA'] != 'Sem Diretoria']

# CORES FIXAS DAS REGIONAIS
# ==========================================
# Altere os códigos hexadecimais abaixo se desejar mudar as cores no futuro
dicionario_cores = {
    'CENTRAL': '#F8DC00', # Amarelo Pequi
    'LESTE': '#17E3CB',   # Turquesa Rio
    'NORTE': '#FE952B',   # Laranja-da-Baía
    'OESTE': '#0027BD',   # Azul Mar
    'SUL': '#A11FFF'      # Roxo Açai
}
diretorias_unicas = sorted(df['DIRETORIA'].dropna().unique())


nomes_abas = ["📍 Mapa Interativo", "Visão Geral (Download)"] + diretorias_unicas
abas = st.tabs(nomes_abas)

# ==========================================
# ABA 0: MAPA INTERATIVO (PLOTLY)
# ==========================================
with abas[0]:
    st.subheader("Busca e Exploração Interativa")

    lista_cidades = sorted(cidades_destaque['name_muni'].unique())

    # 1. Inicializa variáveis de estado (incluindo a chave de reset do mapa)
    if 'cidade_selecionada' not in st.session_state:
        st.session_state.cidade_selecionada = None
    if 'map_key' not in st.session_state:
        st.session_state.map_key = 0

    # Descobre a posição da cidade na lista
    index_selecionado = None
    if st.session_state.cidade_selecionada in lista_cidades:
        index_selecionado = lista_cidades.index(st.session_state.cidade_selecionada)

    # 2. Interface de busca e botão de limpar lado a lado
    col1, col2 = st.columns([4, 1])

    with col1:
        nova_selecao = st.selectbox(
            "🔍 Digite, selecione ou clique no mapa para destacar uma cidade:", 
            lista_cidades, 
            index=index_selecionado,
            placeholder="Escolha uma cidade..."
        )

    with col2:
        st.write("") # Espaçamento para alinhar os botões
        st.write("")
        if st.button("🗑️ Limpar Seleção", use_container_width=True):
            nova_selecao = None # Força a limpeza se o botão for clicado

    # 3. Lógica de atualização: Se a seleção mudou (pela caixa ou pelo botão)
    if nova_selecao != st.session_state.cidade_selecionada:
        st.session_state.cidade_selecionada = nova_selecao
        # A MÁGICA: Se a seleção ficou vazia, muda a chave do mapa para forçar ele a esquecer o clique anterior
        if nova_selecao is None:
            st.session_state.map_key += 1
        st.rerun()

    cidade_atual = st.session_state.cidade_selecionada

    mapa_interativo = mapa_diretorias.copy()

    # Variáveis padrão de câmera
    mapa_zoom = 5.5
    mapa_centro = {"lat": -30.0, "lon": -53.5}

    if cidade_atual is None:
        mapa_interativo['Status_Cor'] = mapa_interativo['DIRETORIA']
        cores_plotly = dicionario_cores.copy()
        cores_plotly['Sem Diretoria'] = '#E0E0E0'
    else:
        regional_alvo = mapa_interativo[mapa_interativo['name_muni'] == cidade_atual]['DIRETORIA'].values[0]

        def definir_destaque(row):
            if row['name_muni'] == cidade_atual:
                return '📍 Cidade Selecionada'
            elif row['DIRETORIA'] == regional_alvo:
                return f'Regional: {regional_alvo}'
            else:
                return 'Outras Regiões'

        mapa_interativo['Status_Cor'] = mapa_interativo.apply(definir_destaque, axis=1)

        cores_plotly = {
            '📍 Cidade Selecionada': '#FF0000', 
            f'Regional: {regional_alvo}': dicionario_cores[regional_alvo],
            'Outras Regiões': '#F0F0F0'
        }

        # Lógica de zoom automático
        geometria_cidade = mapa_interativo[mapa_interativo['name_muni'] == cidade_atual].geometry.iloc[0]
        centroide = geometria_cidade.centroid
        mapa_centro = {"lat": centroide.y, "lon": centroide.x}
        mapa_zoom = 8.0

    mapa_interativo = mapa_interativo.set_index('name_muni')

    fig_interativa = px.choropleth_mapbox(
        mapa_interativo,
        geojson=mapa_interativo.geometry,
        locations=mapa_interativo.index,
        color='Status_Cor',
        color_discrete_map=cores_plotly,
        mapbox_style="carto-positron",
        zoom=mapa_zoom,
        center=mapa_centro,
        opacity=0.8,
        hover_name=mapa_interativo.index,
        hover_data={'DIRETORIA': True, 'Status_Cor': False},
        height=750
    )

    fig_interativa.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # 4. Renderiza o mapa usando a chave dinâmica
    evento_mapa = st.plotly_chart(
        fig_interativa, 
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        config={'scrollZoom': True},
        key=f"mapa_interativo_{st.session_state.map_key}" # Chave que reseta a memória do mapa
    )

    # 5. Lógica de clique no mapa
    if evento_mapa and len(evento_mapa.selection["points"]) > 0:
        cidade_clicada = evento_mapa.selection["points"][0]["location"]
        if cidade_clicada != st.session_state.cidade_selecionada:
            st.session_state.cidade_selecionada = cidade_clicada
            st.rerun()

# ==========================================
# FUNÇÕES E ABAS DE DOWNLOAD (MATPLOTLIB)
# ==========================================
def criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores, diretoria_especifica=None):
    fig, ax = plt.subplots(figsize=(12, 10))
    rs_map.plot(ax=ax, color='#e0e0e0', edgecolor='white', linewidth=0.5)
    itens_legenda = []

    if diretoria_especifica is None:
        for diretoria, cor in dicionario_cores.items():
            subset = cidades_destaque[cidades_destaque['DIRETORIA'] == diretoria]
            if not subset.empty:
                subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.8)
                itens_legenda.append(mpatches.Patch(color=cor, label=diretoria))
        ax.legend(handles=itens_legenda, title='Diretorias Regionais', loc='lower right')
        plt.title("Distribuição regionais Corsan", fontsize=16, fontweight='bold')
    else:
        cor = dicionario_cores[diretoria_especifica]
        subset = cidades_destaque[cidades_destaque['DIRETORIA'] == diretoria_especifica]
        if not subset.empty:
            subset.plot(ax=ax, color=cor, edgecolor='black', linewidth=0.8)
            itens_legenda.append(mpatches.Patch(color=cor, label=diretoria_especifica))
        ax.legend(handles=itens_legenda, title='Diretoria', loc='lower right')
        plt.title(f"Regional: {diretoria_especifica}", fontsize=16, fontweight='bold')

    plt.axis('off')
    plt.tight_layout()
    return fig

def gerar_buffer_download(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches='tight', transparent=True)
    buf.seek(0)
    return buf

with abas[1]:
    with st.spinner("Gerando mapa geral para download..."):
        fig_geral = criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores)
        st.pyplot(fig_geral)
        st.download_button("📥 Baixar Mapa Geral (PNG)", data=gerar_buffer_download(fig_geral), file_name="mapa_geral.png", mime="image/png")

for i, diretoria in enumerate(diretorias_unicas):
    with abas[i + 2]:
        with st.spinner(f"Gerando mapa da regional {diretoria}..."):
            fig_ind = criar_figura_mapa(rs_map, cidades_destaque, dicionario_cores, diretoria_especifica=diretoria)
            st.pyplot(fig_ind)
            st.download_button(f"📥 Baixar Mapa {diretoria} (PNG)", data=gerar_buffer_download(fig_ind), file_name=f"mapa_{diretoria.lower()}.png", mime="image/png")

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 1. Configuração da Página
st.set_page_config(page_title="Radar de Dividendos B3", layout="wide", page_icon="🎯")

# 2. Design Customizado Fintech Premium
st.markdown("""
<style>
    /* Fundo principal escuro e elegante */
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
    }
    
    /* Sidebar refinada */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Estilização dos Tags do Multiselect na Sidebar (de Vermelho para Azul Neon) */
    span[data-baseweb="tag"] {
        background-color: #1f293d !important;
        border: 1px solid #38bdf8 !important;
        color: #38bdf8 !important;
        border-radius: 6px !important;
    }
    
    /* Botão Adicionar Ação */
    div.stButton > button {
        background: linear-gradient(90deg, #0284c7 0%, #2563eb 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #0369a1 0%, #1d4ed8 100%);
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.4);
    }

    /* Cards de métricas (KPIs) com efeito Glassmorphism */
    div[data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
    
    div[data-testid="stMetricLabel"] {
        color: #8b949e !important;
        font-size: 0.85rem !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-size: 2rem !important;
        font-weight: 800;
    }

    /* Ajustes das Caixas de Texto e Sliders */
    .stTextInput input {
        background-color: #0d1117 !important;
        border: 1px solid #30363d !important;
        color: #e6edf3 !important;
        border-radius: 8px !important;
    }
    .stTextInput input:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 1px #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Título e Cabeçalho
st.markdown("<h1 style='color: #f0f6fc; font-weight: 800;'>🎯 Radar de Dividendos B3</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #8b949e;'>Monitore ativos em tempo real, calculando o <b>Dividend Yield acumulado (12M)</b> e o preço vs. <b>média móvel anual</b>.</p>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 4. Configuração da Barra Lateral (Sidebar)
LISTA_PADRAO = ["VIVT3.SA", "KLBN11.SA", "CPFE3.SA", "SANB11.SA", "MGLU3.SA", "VALE3.SA", "PETR4.SA", "BBAS3.SA", "ITSA4.SA", "BPAC11.SA"]

st.sidebar.title("⚙️ Configurações")

if "novos_tickers" not in st.session_state:
    st.session_state["novos_tickers"] = []

novo_ticker = st.sidebar.text_input("Adicionar Ticker (ex: ITUB4):").upper().strip()
if st.sidebar.button("➕ Adicionar Ação"):
    if novo_ticker:
        if not novo_ticker.endswith(".SA"):
            novo_ticker += ".SA"
        if novo_ticker not in st.session_state["novos_tickers"]:
            st.session_state["novos_tickers"].append(novo_ticker)
            st.rerun()

todas_opcoes = list(set(LISTA_PADRAO + st.session_state["novos_tickers"]))

lista_acoes = st.sidebar.multiselect(
    "Ações Monitoradas:",
    options=todas_opcoes,
    default=todas_opcoes
)

st.sidebar.divider()
st.sidebar.subheader("🎯 Filtros de Oportunidade")
min_dy = st.sidebar.slider("DY Mínimo nos últimos 12M (%)", 0.0, 15.0, 0.0, 0.5)
max_p_media = st.sidebar.slider(
    "Máx. Preço / Média 1A", 0.70, 1.50, 1.30, 0.01, 
    help="Valores abaixo de 1.00 indicam que a ação está descontada em relação à sua média de 1 ano."
)

# 5. Processamento dos Dados
@st.cache_data(ttl=1800)
def processar_radar(tickers):
    if not tickers:
        return pd.DataFrame(), {}
    
    df_raw = yf.download(tickers, period="1y", actions=True, progress=False)
    dados_tabela = []
    historicos_grafico = {}
    
    multi_index = isinstance(df_raw.columns, pd.MultiIndex)
    
    for ticker in tickers:
        try:
            if multi_index:
                prices = df_raw['Close'][ticker].dropna()
                dividends = df_raw['Dividends'][ticker].dropna()
            else:
                prices = df_raw['Close'].dropna()
                dividends = df_raw['Dividends'].dropna()
                
            if not prices.empty:
                preco_atual = float(prices.iloc[-1])
                media_1a = float(prices.mean())
                minima_1a = float(prices.min())
                
                div_acumulado = float(dividends.sum()) if not dividends.empty else 0.0
                dy_calculado = (div_acumulado / preco_atual) * 100 if preco_atual > 0 else 0.0
                razao_p_media = preco_atual / media_1a
                ticker_limpo = ticker.replace(".SA", "")
                
                historicos_grafico[ticker_limpo] = pd.DataFrame({'Preco': prices, 'Media_1A': media_1a})
                
                dados_tabela.append({
                    "Ativo": ticker_limpo,
                    "Preço Atual (R$)": round(preco_atual, 2),
                    "Média 1A (R$)": round(media_1a, 2),
                    "Mínima 52S (R$)": round(minima_1a, 2),
                    "Div. 12M (R$)": round(div_acumulado, 2),
                    "DY Real (%)": round(dy_calculado, 2),
                    "Preço / Média": round(razao_p_media, 2)
                })
        except Exception:
            continue
            
    return pd.DataFrame(dados_tabela), historicos_grafico

with st.spinner("Buscando cotações em tempo real..."):
    df_resultado, historicos = processar_radar(lista_acoes)

# 6. Filtros e Métricas
if not df_resultado.empty:
    df_filtrado = df_resultado[
        (df_resultado["DY Real (%)"] >= min_dy) & 
        (df_resultado["Preço / Média"] <= max_p_media)
    ].sort_values(by="Preço / Média")
else:
    df_filtrado = pd.DataFrame()

col1, col2, col3 = st.columns(3)
col1.metric("Ações Analisadas", len(lista_acoes))
col2.metric("Oportunidades Filtradas", len(df_filtrado))
col3.metric("Filtro DY Mínimo", f"{min_dy}%")

st.markdown("<br>", unsafe_allow_html=True)

# 7. Tabela e Gráfico
col_tabela, col_grafico = st.columns([1.3, 1])

with col_tabela:
    st.subheader("📋 Oportunidades Selecionadas")
    if not df_filtrado.empty:
        st.dataframe(
            df_filtrado,
            column_config={
                "Preço Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Média 1A (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Mínima 52S (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Div. 12M (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "DY Real (%)": st.column_config.NumberColumn(format="%.2f %%"),
                "Preço / Média": st.column_config.NumberColumn(format="%.2f"),
            },
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.warning("Nenhuma ação com os filtros atuais.")

with col_grafico:
    st.subheader("📈 Raio-X da Ação")
    if not df_filtrado.empty:
        acao_sel = st.selectbox("Selecione para analisar:", df_filtrado["Ativo"])
        
        if acao_sel in historicos:
            hist = historicos[acao_sel]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Preco'], mode='lines', name='Preço Diário', line=dict(color='#38bdf8', width=2)))
            fig.add_trace(go.Scatter(x=hist.index, y=hist['Media_1A'], mode='lines', name='Média 1 Ano', line=dict(color='#f59e0b', dash='dash', width=2)))
            
            fig.update_layout(
                xaxis_title="",
                yaxis_title="R$",
                height=350,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8b949e'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='#21262d')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#21262d')
            
            st.plotly_chart(fig, use_container_width=True)

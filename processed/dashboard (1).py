import streamlit as st
import pandas as pd
import plotly.express as px
import json

# 1. OLDAL BEÁLLÍTÁSAI

st.set_page_config(page_title="Magyarországi Bér-Dashboard", layout="wide", page_icon="📈")

st.title("Interaktív Vármegyei Gazdasági Dashboard (2018-2025)")
st.markdown("Elemzés a KSH STADAT adatbázisa alapján. Válassz a bal oldali menüből!")

# 2. ADATOK BETÖLTÉSE (Cache-elve a gyorsaságért)
@st.cache_data
def load_data():
    # Ezt a tisztított fájlt generáltuk az előző lépésekben
    df = pd.read_csv("KSH_Final_MachineLearning_Panel.csv")
    df['Dátum'] = pd.to_datetime(df['Dátum'])
    return df

df = load_data()

# 3. OLDALSÁV (SIDEBAR) - VEZÉRLŐK
st.sidebar.header("Szűrőfeltételek")

# Évválasztó csúszka a térképhez
min_ev = int(df['Dátum'].dt.year.min())
max_ev = int(df['Dátum'].dt.year.max())
kivalasztott_ev = st.sidebar.slider("Válaszd ki az évet (Térképhez):", min_ev, max_ev, 2024)

# Vármegye kiválasztó a grafikonokhoz
megyek = sorted(df['Területi egység neve'].unique())
alap_index = megyek.index('Hajdú-Bihar') if 'Hajdú-Bihar' in megyek else 0
kivalasztott_megye = st.sidebar.selectbox("Válaszd ki a vármegyét (Idősorhoz):", megyek, index=alap_index)

st.sidebar.markdown("---")
st.sidebar.info("A Dashboard a szakdolgozati kutatás vizuális bemutatására szolgál.")


# 4. FŐ TARTALOM (KÉT OSZLOPOS ELRENDEZÉS)
col1, col2 = st.columns((1.2, 1)) # A térkép oszlopa picit szélesebb

with col1:
    st.subheader(f"Bruttó Átlagkereset Eloszlása ({kivalasztott_ev})")
    
    # Adatok szűrése az adott évre és átlagolás vármegyénként
    df_terkep = df[df['Dátum'].dt.year == kivalasztott_ev].groupby('Területi egység neve')['Bruttó_átlagkereset_HUF'].mean().reset_index()
    
    try:
        # Térkép generálása (Ha megvan a GeoJSON fájl)
        with open('gadm41_HUN_1.json', encoding='utf-8') as response:
            counties = json.load(response)
        
        fig_map = px.choropleth(
            df_terkep,
            geojson=counties,
            featureidkey='properties.name', # GeoJSON-tól függ!
            locations='Területi egység neve',
            color='Bruttó_átlagkereset_HUF',
            color_continuous_scale="Viridis",
            labels={'Bruttó_átlagkereset_HUF': 'Átlagbér (Ft)'}
        )
        fig_map.update_geos(fitbounds="locations", visible=False)
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
        
    except FileNotFoundError:
        # Ha nincs GeoJSON, egy vízszintes sávdiagramot mutatunk a térkép helyett
        st.warning("A hőtérképhez hiányzik a 'gadm41_HUN_1.json' fájl. Helyette a régiók rangsorát látod:")
        fig_bar = px.bar(
            df_terkep.sort_values('Bruttó_átlagkereset_HUF'), 
            x='Bruttó_átlagkereset_HUF', 
            y='Területi egység neve', 
            orientation='h', 
            color='Bruttó_átlagkereset_HUF', 
            color_continuous_scale="Viridis",
            labels={'Bruttó_átlagkereset_HUF': 'Átlagbér (Ft)', 'Területi egység neve': ''}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    st.subheader(f" {kivalasztott_megye} - Idősoros Elemzés")
    
    # Adatok szűrése a kiválasztott megyére
    df_megye = df[df['Területi egység neve'] == kivalasztott_megye].sort_values('Dátum')
    
    # 1. Grafikon: Abszolút bérnövekedés
    fig_line = px.line(
        df_megye, x='Dátum', y='Bruttó_átlagkereset_HUF', 
        markers=True, 
        line_shape='spline',
        labels={'Bruttó_átlagkereset_HUF': 'Bruttó Bér (Ft)', 'Dátum': 'Időszak'}
    )
    fig_line.update_traces(line_color='#e74c3c', line_width=3, marker=dict(size=8))
    st.plotly_chart(fig_line, use_container_width=True)
    
    # 2. Grafikon: Munkanélküliségi ráta alakulása
    fig_unemp = px.area(
        df_megye, x='Dátum', y='Munkanélküliségi_ráta_%',
        labels={'Munkanélküliségi_ráta_%': 'Munkanélküliség (%)', 'Dátum': 'Időszak'}
    )
    fig_unemp.update_traces(line_color='#3498db', fillcolor='rgba(52, 152, 219, 0.3)')
    st.plotly_chart(fig_unemp, use_container_width=True)


# 5. NYERS ADATOK TÁBLÁZATA

st.markdown("---")
st.subheader("Nyers Adathalmaz Böngészése")
st.dataframe(df.sort_values(by='Dátum', ascending=False).head(500), use_container_width=True)
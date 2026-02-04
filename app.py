# ==================================================
# IMPORTS
# ==================================================
import streamlit as st
import pandas as pd
import pydeck as pdk
from datetime import datetime
from pathlib import Path
import base64

# ==================================================
# CHEMINS
# ==================================================
BASE_DIR = Path(__file__).parent
ICON_PATH = BASE_DIR / "icon.png"

# ==================================================
# FONCTION BASE64 POUR ICÔNE
# ==================================================
def get_icon_base64(path):
    with open(path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    return f"data:image/png;base64,{encoded}"

ICON_BASE64 = get_icon_base64(ICON_PATH)

# ==================================================
# CONFIGURATION PAGE
# ==================================================
st.set_page_config(
    page_title="Pharmacies de garde – Ouagadougou",
    page_icon=str(ICON_PATH),
    layout="wide"
)

# ==================================================
# STYLE CSS
# ==================================================
st.markdown("""
<style>
    .main { background-color: #f4f7fb; }
    h1, h2, h3 { color: #145a32; }
    .stDataFrame { border-radius: 12px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# EN-TÊTE
# ==================================================
st.image(str(ICON_PATH), width=90)
st.markdown("## Pharmacies de garde à **Ouagadougou**")
st.caption("Plateforme officielle de recherche des pharmacies de garde")

# ==================================================
# CHARGEMENT DES DONNÉES
# ==================================================
@st.cache_data
def load_data():
    pharmacies = pd.read_csv("x.csv", sep=";", encoding="utf-8-sig")
    calendrier = pd.read_csv("TourGarde.csv", sep=";", encoding="utf-8-sig")

    pharmacies.columns = pharmacies.columns.str.strip().str.lower()
    calendrier.columns = calendrier.columns.str.strip().str.lower()

    calendrier["debut"] = pd.to_datetime(calendrier["debut"], dayfirst=True, errors="coerce")
    calendrier["fin"] = pd.to_datetime(calendrier["fin"], dayfirst=True, errors="coerce")

    pharmacies["groupe"] = pd.to_numeric(pharmacies["groupe"], errors="coerce").fillna(0).astype(int)
    calendrier["groupe"] = pd.to_numeric(calendrier["groupe"], errors="coerce").fillna(0).astype(int)

    pharmacies["latitude"] = pd.to_numeric(pharmacies["latitude"], errors="coerce")
    pharmacies["longitude"] = pd.to_numeric(pharmacies["longitude"], errors="coerce")

    return pharmacies, calendrier

df_pharmacies, df_calendrier = load_data()

# ==================================================
# SIDEBAR
# ==================================================
with st.sidebar:
    st.image(str(ICON_PATH), width=110)
    date_recherche = st.date_input("Date", datetime.now())
    search = st.text_input("Nom ou quartier")

date_recherche = pd.to_datetime(date_recherche)

# ==================================================
# GROUPE DE GARDE
# ==================================================
garde = df_calendrier[
    (date_recherche >= df_calendrier["debut"]) &
    (date_recherche <= df_calendrier["fin"])
]

if garde.empty:
    st.warning("Aucune pharmacie de garde pour cette date.")
    st.stop()

num_groupe = int(garde.iloc[0]["groupe"])
st.success(f"Groupe de garde actif : {num_groupe}")

# ==================================================
# FILTRAGE
# ==================================================
resultats = df_pharmacies[df_pharmacies["groupe"] == num_groupe]

if search:
    resultats = resultats[
        resultats["nom"].str.contains(search, case=False, na=False) |
        resultats["localisation"].str.contains(search, case=False, na=False)
    ]

# ==================================================
# TABLEAU
# ==================================================
st.dataframe(
    resultats[["nom", "localisation", "telephone"]],
    use_container_width=True,
    hide_index=True
)

# ==================================================
# CARTE – ICÔNES PHARMACIE (FIX DÉFINITIF)
# ==================================================
st.markdown("### Carte interactive")

df_map = resultats.dropna(subset=["latitude", "longitude"]).copy()

icon_data = {
    "url": ICON_BASE64,
    "width": 48,
    "height": 48,
    "anchorY": 48
}

df_map["icon"] = [icon_data] * len(df_map)

layer = pdk.Layer(
    "IconLayer",
    data=df_map,
    get_icon="icon",
    get_position="[longitude, latitude]",
    size_scale=12,
    get_size=4,
    pickable=True
)

view_state = pdk.ViewState(
    latitude=df_map["latitude"].mean(),
    longitude=df_map["longitude"].mean(),
    zoom=12.5
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={
            "html": "<b>{nom}</b><br/>{localisation}<br/>📞 {telephone}",
            "style": {
                "backgroundColor": "rgba(0,0,0,0.85)",
                "color": "white"
            }
        }
    )
)

# ==================================================
# ITINÉRAIRE
# ==================================================
st.markdown("### Itinéraire")

if not df_map.empty:
    pharmacie = st.selectbox("Choisissez une pharmacie", df_map["nom"].tolist())
    p = df_map[df_map["nom"] == pharmacie].iloc[0]
    url = f"https://www.google.com/maps/dir/?api=1&destination={p.latitude},{p.longitude}"

    st.markdown(
        f"""
        <a href="{url}" target="_blank">
            <button style="
                background:#198754;
                color:white;
                padding:12px 26px;
                border:none;
                border-radius:12px;
                font-size:16px;">
                Ouvrir l’itinéraire
            </button>
        </a>
        """,
        unsafe_allow_html=True
    )

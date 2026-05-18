import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="SmartRail", page_icon="🚆", layout="wide")

DATA_FILE = Path("smart_rail_data.xlsx")

@st.cache_data
def load_data():
    return pd.read_excel(DATA_FILE, sheet_name="SmartRail_Data")

def risk_color(risk):
    if risk == "Hög":
        return "🔴 Hög"
    if risk == "Medel":
        return "🟡 Medel"
    return "🟢 Låg"

def status_box(row):
    if row["Isrisk"] == "Hög" or row["Temperatur_C"] <= -3:
        return "⚠️ VARNING: Hög isrisk – växelvärme bör vara aktiverad"
    elif row["Isrisk"] == "Medel":
        return "🟡 Bevakas – risknivån är förhöjd"
    return "🟢 Normal status"

st.title("🚆 SmartRail")
st.subheader("Digitalt varningssystem för vinterunderhåll av spårväxlar")

if not DATA_FILE.exists():
    st.error("Filen smart_rail_data.xlsx saknas. Lägg Excel-filen i samma mapp som app.py.")
    st.stop()

data = load_data()

# Sidebar
st.sidebar.header("Filter")
selected_risk = st.sidebar.multiselect("Välj isrisk", sorted(data["Isrisk"].unique()), default=sorted(data["Isrisk"].unique()))
selected_status = st.sidebar.multiselect("Välj status", sorted(data["Status"].unique()), default=sorted(data["Status"].unique()))
selected_contractor = st.sidebar.multiselect("Välj entreprenör", sorted(data["Ansvarig_entreprenör"].unique()), default=sorted(data["Ansvarig_entreprenör"].unique()))

filtered = data[
    data["Isrisk"].isin(selected_risk)
    & data["Status"].isin(selected_status)
    & data["Ansvarig_entreprenör"].isin(selected_contractor)
]

# Online/offline indicator (prototype mode)
st.info("Prototypen använder lokal Excel-data. Det betyder att appen kan visas även utan koppling till verkliga sensorer.")
st.write("Senast uppdaterad i appen:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# KPI cards
col1, col2, col3, col4 = st.columns(4)
col1.metric("Antal växlar", len(data))
col2.metric("Hög isrisk", len(data[data["Isrisk"] == "Hög"]))
col3.metric("Växelvärme aktiverad", len(data[data["Växelvärme"] == "Aktiverad"]))
col4.metric("Åtgärder pågår", len(data[data["Åtgärdsstatus"] == "Pågår"]))

st.header("Översikt för driftcentral och underhåll")
show_data = filtered.copy()
show_data["Riskvisning"] = show_data["Isrisk"].apply(risk_color)
st.dataframe(
    show_data[["Växel_ID", "Plats", "Temperatur_C", "Fuktighet_%", "Riskvisning", "Status", "Växelvärme", "Ansvarig_entreprenör", "Åtgärdsstatus"]],
    use_container_width=True
)

st.header("Varningar vid isrisk")
critical = data[(data["Isrisk"] == "Hög") | (data["Temperatur_C"] <= -3)]

if len(critical) > 0:
    for _, row in critical.iterrows():
        st.error(
            f"{row['Växel_ID']} – {row['Plats']} | Temperatur: {row['Temperatur_C']}°C | "
            f"Isrisk: {row['Isrisk']} | Växelvärme: {row['Växelvärme']} | Ansvarig: {row['Ansvarig_entreprenör']}"
        )
else:
    st.success("Inga kritiska isrisker just nu.")

st.header("Detaljvy och kontaktkedja")
selected_switch = st.selectbox("Välj spårväxel", data["Växel_ID"].tolist())
row = data[data["Växel_ID"] == selected_switch].iloc[0]

c1, c2 = st.columns(2)
with c1:
    st.subheader("Teknisk status")
    st.write("**Plats:**", row["Plats"])
    st.write("**Temperatur:**", f"{row['Temperatur_C']}°C")
    st.write("**Fuktighet:**", f"{row['Fuktighet_%']}%")
    st.write("**Isrisk:**", risk_color(row["Isrisk"]))
    st.write("**Växelvärme:**", row["Växelvärme"])
    st.warning(status_box(row))

with c2:
    st.subheader("Åtgärd och ansvar")
    st.write("**Ansvarig entreprenör:**", row["Ansvarig_entreprenör"])
    st.write("**Kontaktad först:**", row["Kontaktad_först"])
    st.write("**Kontakt tid:**", row["Kontakt_tid"] if pd.notna(row["Kontakt_tid"]) else "Ej kontaktad")
    st.write("**Åtgärdsstatus:**", row["Åtgärdsstatus"])
    st.write("**Åtgärdad tid:**", row["Åtgärdad_tid"] if pd.notna(row["Åtgärdad_tid"]) else "Inte klar")
    st.write("**Kommentar:**", row["Kommentar"])

st.header("Simulering av åtgärd")
st.write("Här visas hur systemet kan uppdateras när underhållspersonal markerar en växel som åtgärdad.")
if st.button("Markera vald växel som åtgärdad i simulering"):
    st.success(f"{selected_switch} är markerad som åtgärdad i simuleringen.")
    st.write("Ny åtgärdsstatus: Åtgärdad")
    st.write("Åtgärdad tid:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

st.header("Export")
csv = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button("Ladda ner aktuell vy som CSV", csv, "smartrail_export.csv", "text/csv")

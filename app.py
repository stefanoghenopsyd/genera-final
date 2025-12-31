import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import numpy as np
import json

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="GÉNERA | ISA-Q", layout="centered")
COLORS = {'primary': '#1A3A5F', 'secondary': '#5D8A78', 'bg': '#F4F4F4'}

# --- CONNESSIONE GOOGLE (Metodo "Blocco Testo") ---
def save_to_google_sheets(data_row):
    try:
        # 1. Recupera il blocco di testo JSON dai segreti
        json_text = st.secrets["gcp_json_text"]
        # 2. Lo trasforma in dizionario
        creds_dict = json.loads(json_text)
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(credentials)
        
        sh = gc.open_by_url(st.secrets["private_sheet_url"])
        sh.sheet1.append_row(data_row)
        return True
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return False

# --- GRAFICO ---
def create_radar_chart(scores):
    cats = list(scores.keys())
    vals = list(scores.values())
    vals += vals[:1]
    angles = np.linspace(0, 2*np.pi, len(cats), endpoint=False).tolist() + [0]
    
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    plt.xticks(angles[:-1], cats, color=COLORS['primary'], size=9)
    ax.set_rlabel_position(0)
    plt.ylim(0, 20)
    ax.plot(angles, vals, color=COLORS['primary'], linewidth=2)
    ax.fill(angles, vals, color=COLORS['secondary'], alpha=0.4)
    ax.spines['polar'].set_visible(False)
    return fig

# --- APP ---
def main():
    st.markdown(f"<h1 style='color:{COLORS['primary']}; text-align: center;'>GÉNERA</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Impact Self-Assessment</h3>", unsafe_allow_html=True)
    
    # 1. Anagrafica
    st.subheader("1. Chi sei")
    c1, c2 = st.columns(2)
    with c1:
        genere = st.selectbox("Genere", ["Seleziona...", "M", "F", "Non Binario", "Altro"])
        eta = st.selectbox("Età", ["Seleziona...", "<20", "21-30", "31-40", "41-50", "51-60", "61-70", ">70"])
    with c2:
        scolarita = st.selectbox("Studi", ["Seleziona...", "Media", "Diploma", "Laurea Triennale", "Laurea Magistrale", "Post Laurea"])

    # 2. Domande
    st.subheader("2. Test (1-6)")
    questions = [
        ("I miei valori riflettono il mio lavoro", False, "SDT"),
        ("Ho fiducia nella mia capacità", False, "SDT"),
        ("Lavoro solo perché imposto", True, "SDT"),
        ("Mi attivo su ciò che controllo", False, "Empowerment"),
        ("Influenzo le decisioni", False, "Empowerment"),
        ("La crescita dipende dal caso", True, "Empowerment"),
        ("Comprendo il quadro generale", False, "Salutogenesi"),
        ("Le sfide hanno senso", False, "Salutogenesi"),
        ("Richieste confuse/imprevedibili", True, "Salutogenesi"),
        ("Trasmetto conoscenze agli altri", False, "Generatività"),
        ("Il mio lavoro ha impatto futuro", False, "Generatività"),
        ("Focalizzato solo sui miei task", True, "Generatività"),
        ("Recupero equilibrio velocemente", False, "Resilienza"),
        ("Cambiamento come opportunità", False, "Resilienza"),
        ("Mi irrigidisco sotto stress", True, "Resilienza")
    ]
    
    responses = {}
    with st.form("isa"):
        for i, (q, rev, dim) in enumerate(questions):
            responses[i] = st.slider(q, 1, 6, 3, key=i)
        if st.form_submit_button("Calcola"):
            if "Seleziona..." in [genere, eta, scolarita]:
                st.error("Compila i dati anagrafici.")
            else:
                # Calcolo
                scores = {"SDT":0, "Empowerment":0, "Salutogenesi":0, "Generatività":0, "Resilienza":0}
                for i, (q, rev, dim) in enumerate(questions):
                    val = 7 - responses[i] if rev else responses[i]
                    scores[dim] += val
                
                tot = sum(scores.values())
                
                # Feedback
                if tot <= 45: msg, col = "IMPATTO LATENTE", "warning"
                elif tot <= 70: msg, col = "IMPATTO EMERGENTE", "info"
                else: msg, col = "IMPATTO GENERATIVO", "success"
                
                st.markdown("---")
                c_g, c_t = st.columns(2)
                with c_g: st.pyplot(create_radar_chart(scores))
                with c_t: 
                    st.metric("Totale", f"{tot}/90")
                    if col=="warning": st.warning(msg)
                    elif col=="info": st.info(msg)
                    else: st.success(msg)
                
                # Salvataggio
                row = [str(datetime.datetime.now()), genere, eta, scolarita, tot, scores["SDT"], scores["Empowerment"], scores["Salutogenesi"], scores["Generatività"], scores["Resilienza"]]
                if save_to_google_sheets(row): st.success("Dati Salvati!")
                else: st.error("Errore Salvataggio")

if __name__ == "__main__":
    main()

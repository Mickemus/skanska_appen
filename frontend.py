import base64 
from pathlib import Path
from datetime import date
import streamlit as st
import backend


st.set_page_config(
    page_title="Skånska Upplevelser",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ---------
# Session State
# ---------
if "user" not in st.session_state:
    st.session_state.user = None

if "valda_mal" not in st.session_state:
    st.session_state.valda_mal = []

if "valt_datum" not in st.session_state:
    st.session_state.valt_datum = date.today()

if "boknings_meddelande" not in st.session_state:
    st.session_state.boknings_meddelande = None

if "datum_varning" not in st.session_state:
    st.session_state.datum_varning = None


# ---------
# Registrera ny användare (Modal)
# ---------
@st.dialog("Registrera ny användare")
def visa_registrering_modal():
    st.caption(
        "Fyll i dina uppgifter nedan för att skapa ett konto hos Skånska Upplevelser."
    )

    kommuner = backend.hamta_kommuner()
    kommun_dict = {k["municipality_name"]: k["municipality_id"] for k in kommuner}

    with st.form("registrera_kund_form", border=False):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            first_name = st.text_input(
                "Förnamn *", max_chars=60, placeholder="T.ex. Anna"
            )
        with col_f2:
            last_name = st.text_input(
                "Efternamn *", max_chars=60, placeholder="T.ex. Andersson"
            )

        email = st.text_input(
            "E-postadress *", max_chars=150, placeholder="namn@exempel.com"
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            password = st.text_input(
                "Lösenord * (minst 7 tecken)", type="password", max_chars=255
            )
        with col_p2:
            password_confirm = st.text_input(
                "Bekräfta lösenord *", type="password", max_chars=255
            )

        phone = st.text_input(
            "Telefonnummer", max_chars=25, placeholder="070-1234567"
        )

        vald_kommun_namn = st.selectbox(
            "Hemkommun *",
            options=list(kommun_dict.keys()) if kommun_dict else ["Malmö"],
        )

        skicka = st.form_submit_button(
            "Skapa konto", type="primary", use_container_width=True
        )

        if skicka:
            fn = first_name.strip()
            ln = last_name.strip()
            em = email.strip()

            if not fn or not ln or not em or not password or not password_confirm:
                st.error("Vänligen fyll i alla obligatoriska fält (*).")
            elif "  " in fn or "  " in ln or "  " in em:
                st.error("Fälten får inte innehålla dubbla mellanslag.")
            elif fn != fn.capitalize() or ln != ln.capitalize():
                st.error(
                    "Förnamn och efternamn måste börja med stor bokstav följt av små bokstäver."
                )
            elif (
                "@" not in em
                or "." not in em.split("@")[-1]
                or len(em.split("@")[-1].split(".")[-1]) < 2
                or " " in em
            ):
                st.error("Ange en giltig e-postadress.")
            elif len(password) <= 6:
                st.error("Lösenordet måste vara längre än 6 tecken.")
            elif password != password_confirm:
                st.error("Lösenorden matchar inte!")
            else:
                kommun_id = kommun_dict.get(vald_kommun_namn, 17)
                lyckades, meddelande = backend.registrera_kund_i_db(
                    fn, ln, em, password, phone, kommun_id
                )
                if lyckades:
                    ny_user = backend.verifiera_inloggning(em, password)
                    st.session_state.user = ny_user
                    st.session_state.boknings_meddelande = meddelande
                    st.rerun()
                else:
                    st.error(meddelande)


# ---------
# Redigera betald resa (Modal)
# ---------
@st.dialog("Redigera betald resa", width="large")
def visa_redigera_resa_modal():
    user = st.session_state.user
    is_admin = user["customer_id"] == 1

    bokningar = backend.hamta_redigerbara_bokningar(
        user["customer_id"], is_admin=is_admin
    )

    if not bokningar:
        st.info("Det finns inga kommande resor som kan redigeras.")
        return

    boknings_val = {
        f"Bokning #{b['booking_id']} — {b['first_name']} {b['last_name']} | {b['travel_date']} ({b['total_price']:.0f} kr)": b
        for b in bokningar
    }

    vald_label = st.selectbox(
        "Välj bokning att redigera", options=list(boknings_val.keys())
    )
    aktuell_bokning = boknings_val[vald_label]
    b_id = aktuell_bokning["booking_id"]

    st.divider()

    rcol1, rcol2, rcol3 = st.columns(3)
    with rcol1:
        nytt_datum = st.date_input(
            "Nytt avresedatum",
            value=aktuell_bokning["travel_date"],
            min_value=date.today(),
            key=f"edit_date_{b_id}",
        )
    with rcol2:
        nya_vuxna = st.number_input(
            "Antal vuxna",
            min_value=1,
            value=int(aktuell_bokning["number_of_adults"]),
            key=f"edit_adults_{b_id}",
        )
    with rcol3:
        nya_barn = st.number_input(
            "Antal barn",
            min_value=0,
            value=int(aktuell_bokning["number_of_children"]),
            key=f"edit_children_{b_id}",
        )

    lediga_for_andring, _ = backend.hamta_lediga_platser(
        nytt_datum, exkludera_booking_id=b_id
    )

    st.markdown("##### Välj destinationer för resan")
    st.caption(
        "Kryssa i eller ur destinationer. Stängda mål för valt datum är inaktiverade."
    )

    alla_aktiviteter = backend.hamta_alla_aktiviteter()
    vald_veckodag = nytt_datum.isoweekday()

    kat_col1, kat_col2, kat_col3 = st.columns(3)
    nya_valda_mal = []

    for kat_col, kat_kod, kat_rubrik in [
        (kat_col1, "amusement", "Nöjen"),
        (kat_col2, "place", "Platser"),
        (kat_col3, "fika", "Fika"),
    ]:
        with kat_col:
            st.markdown(f"**{kat_rubrik}**")
            for akt in alla_aktiviteter:
                if akt["kategori"] == kat_kod:
                    nyckel = f"{akt['kategori']}_{akt['id']}"
                    dag_info = akt.get("oppettider", {}).get(vald_veckodag)
                    ar_oppet = dag_info["is_open"] if dag_info else True

                    forifyll = (
                        nyckel in aktuell_bokning["valda_nycklar"] and ar_oppet
                    )
                    pris_txt = (
                        f"{akt['pris']:.0f} kr" if akt["pris"] > 0 else "0 kr"
                    )
                    status_txt = (
                        f" ({dag_info['text']})"
                        if (dag_info and ar_oppet)
                        else " (Stängt)"
                    )

                    if st.checkbox(
                        f"{akt['plats_namn']} · {pris_txt}{status_txt}",
                        value=forifyll,
                        disabled=not ar_oppet,
                        key=f"edit_chk_{b_id}_{nyckel}_{nytt_datum}",
                    ):
                        nya_valda_mal.append(akt)

    st.divider()

    if len(nya_valda_mal) == 0:
        st.warning("Du måste ha minst en öppen destination vald i resan.")
        return

    nytt_totalpris, _, _, totalt_nya_resenarer = backend.berakna_respris(
        aktuell_bokning["kund_kommun_id"], nya_valda_mal, nya_vuxna, nya_barn
    )

    if totalt_nya_resenarer > lediga_for_andring:
        st.error(
            f"Det finns tyvärr bara **{lediga_for_andring} platser tillgängliga** på bussen den {nytt_datum} "
            f"(du har valt {totalt_nya_resenarer} resenärer)."
        )
        return

    gammalt_pris = float(aktuell_bokning["total_price"])
    mellanskillnad = round(nytt_totalpris - gammalt_pris, 2)

    pcol1, pcol2 = st.columns(2)
    with pcol1:
        st.write(f"**Tidigare betalt:** {gammalt_pris:.2f} kr")
        st.write(f"**Nytt totalpris:** {nytt_totalpris:.2f} kr")
        if mellanskillnad > 0:
            st.warning(f"**Att betala extra:** +{mellanskillnad:.2f} kr")
        elif mellanskillnad < 0:
            st.success(f"**Återbetalning:** {abs(mellanskillnad):.2f} kr")
        else:
            st.info("**Prisskillnad:** 0.00 kr")

    with pcol2:
        betal_metod = st.selectbox(
            "Betalsätt för tillägg / återbetalning",
            ["Swish", "Kort", "Klarna"],
            key=f"edit_pay_{b_id}",
        )

    knapp_text = (
        f"Betala mellanskillnad ({mellanskillnad:.2f} kr) & spara"
        if mellanskillnad > 0
        else (
            f"Spara ändring & återbetala {abs(mellanskillnad):.2f} kr"
            if mellanskillnad < 0
            else "Spara ändringar"
        )
    )

    if st.button(knapp_text, type="primary", use_container_width=True):
        ok, fel = backend.uppdatera_bokning_i_db(
            booking_id=b_id,
            package_id=aktuell_bokning["package_id"],
            route_id=aktuell_bokning["route_id"],
            nya_mal=nya_valda_mal,
            nytt_datum=nytt_datum,
            adults=nya_vuxna,
            children=nya_barn,
            nytt_totalpris=nytt_totalpris,
            mellanskillnad=mellanskillnad,
            payment_method=betal_metod,
        )
        if ok:
            if mellanskillnad > 0:
                st.session_state.boknings_meddelande = (
                    f"Bokning #{b_id} har uppdaterats! Mellanskillnaden på {mellanskillnad:.2f} kr har betalats med {betal_metod}."
                )
            elif mellanskillnad < 0:
                st.session_state.boknings_meddelande = (
                    f"Bokning #{b_id} har uppdaterats! En återbetalning på {abs(mellanskillnad):.2f} kr via {betal_metod} är registrerad."
                )
            else:
                st.session_state.boknings_meddelande = (
                    f"Bokning #{b_id} har uppdaterats utan prisskillnad!"
                )
            st.rerun()
        else:
            st.error(f"Kunde inte uppdatera bokningen: {fel}")


# ---------
# Betalningshistorik och kvitton (Modal)
# ---------
@st.dialog("Betalningshistorik & Kvitton", width="large")
def visa_kvitto_modal():
    user = st.session_state.user
    is_admin = user["customer_id"] == 1

    if is_admin:
        st.caption(
            "Adminvy: Visar samtliga registrerade betalningar och kvitton i systemet."
        )
    else:
        st.caption(
            f"Visar betalningar och kvitton för {user['first_name']} {user['last_name']} (Kund-ID #{user['customer_id']})."
        )

    kvitton = backend.hamta_betalningshistorik(
        user["customer_id"], is_admin=is_admin
    )

    if not kvitton:
        st.info("Det finns inga tidigare betalningar eller kvitton registrerade.")
        return

    for k in kvitton:
        betal_status = k["payment_status"] if k["payment_status"] else "Paid"
        betal_metod = (
            k["payment_method"] if k["payment_method"] else "Direktbetalning"
        )
        belopp = (
            float(k["amount"])
            if k["amount"] is not None
            else float(k["total_price"])
        )
        datum_tid = k["payment_date"] if k["payment_date"] else k["booking_date"]
        datum_str = (
            datum_tid.strftime("%Y-%m-%d %H:%M")
            if hasattr(datum_tid, "strftime")
            else str(datum_tid)
        )
        kvitto_nr = k["payment_id"] if k["payment_id"] else k["booking_id"]

        typ_etikett = (
            f"Återbetalning: {belopp:.2f} kr"
            if belopp < 0
            else f"{belopp:.2f} kr"
        )
        kund_info = (
            f" · {k['first_name']} {k['last_name']}" if is_admin else ""
        )

        rubrik = f"Kvitto #{kvitto_nr} · {typ_etikett} ({betal_metod}) · Avresa {k['travel_date']}{kund_info}"

        with st.expander(rubrik, expanded=False):
            kcol1, kcol2 = st.columns(2)
            with kcol1:
                st.markdown("**Resedetaljer**")
                st.write(f"Bokningsnummer: `#{k['booking_id']}`")
                if is_admin:
                    st.write(
                        f"Kund: {k['first_name']} {k['last_name']} (`#{k['customer_id']}`)"
                    )
                st.write(f"Paket: {k['package_name']}")
                st.write(f"Besöksmål: {k['resmal'] or 'Ej angivet'}")
                st.write(f"Rutt: {k['start_kommun']} → {k['slut_kommun']}")
                st.write(f"Avresedatum: {k['travel_date']}")
                st.write(
                    f"Resenärer: {k['number_of_adults']} vuxna, {k['number_of_children']} barn"
                )

            with kcol2:
                st.markdown("**Betalningsspecifikation**")
                st.write(f"Kvittonummer: `#{kvitto_nr}`")
                st.write(f"Transaktionsdatum: {datum_str}")
                st.write(f"Betalsätt: {betal_metod}")
                st.write(f"Betalningsstatus: {betal_status}")
                st.write(f"Bokningsstatus: {k['booking_status']}")
                st.write(f"Bokningens totalpris: {k['total_price']:.2f} kr")


# ---------
# Bakgrund & Modern 2026 CSS (Utan skuggor, smal & mobilanpassad)
# ---------
BASE_DIR = Path(__file__).parent

def get_base64_image(image_name):
    try:
        with open(BASE_DIR / image_name, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

bg_img = get_base64_image("bakgrund.jpg")
bg_css = (
    f'background-image: linear-gradient(rgba(15, 23, 42, 0.5), rgba(15, 23, 42, 0.5)), url("data:image/jpeg;base64,{bg_img}");'
    if bg_img
    else "background-color: #0F172A;"
)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}

    /* Nollställ alla skuggor globalt */
    *, *::before, *::after {{
        box-shadow: none !important;
        text-shadow: none !important;
    }}

    /* Bakgrund */
    .stApp {{
        {bg_css}
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    header[data-testid="stHeader"] {{
        background: transparent !important;
    }}

    /* Smal, centrerad och mobilanpassad behållare */
    .block-container {{
        max-width: 680px !important;
        padding-top: 1.4rem !important;
        padding-bottom: 4rem !important;
        padding-left: 0.85rem !important;
        padding-right: 0.85rem !important;
        margin: 0 auto !important;
    }}

    /* Rubrik i kolumn 1+2 direkt på bakgrunden */
    .hero-title {{
        color: #FFFFFF !important;
        font-size: clamp(1.35rem, 4vw, 1.75rem) !important;
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        margin: 0 !important;
        line-height: 1.15 !important;
    }}
    .hero-meta {{
        color: rgba(255, 255, 255, 0.88) !important;
        font-size: 0.8rem !important;
        font-weight: 500 !important;
        margin-top: 0.25rem !important;
    }}

    /* Kompakt styling för datumväljare (kolumn 3) och login-popover (kolumn 4) */
    div[data-testid="stDateInput"] div[data-baseweb="input"] {{
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
    }}
    div[data-testid="stDateInput"] input {{
        color: #0F172A !important;
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        padding: 0.4rem 0.6rem !important;
    }}
    div[data-testid="stPopover"] > button {{
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        min-height: 40px !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        padding: 0.4rem 0.75rem !important;
    }}
    div[data-testid="stPopover"] > button p {{
        color: #0F172A !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
    }}

    /* Sökfält */
    div[data-testid="stTextInput"] input {{
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.8rem !important;
    }}

    




   /* Hela fliksektionen nederdelen bakom kort och bilder */
    div[data-testid="stTabs"] {{
        background-color: #c2b9ac !important;    
        border: 1px solid rgba(255, 255, 255, 1.0) !important;
        border-radius: 10px !important;
        padding: 1.0rem !important;
    }}

    /* Flikraden (Nöjen, Platser, Fika, Bokning) */
    div[data-baseweb="tab-list"] {{
        background-color: #F0E2C3 !important;
        border: 1px solid rgba(255, 255, 255, 1.0) !important;
        border-radius: 12px !important;
        padding: 0.3rem !important;
        gap: 0.25rem !important;
        overflow-x: auto !important;
        overflow-y: hidden !important;
        flex-wrap: nowrap !important;
        scrollbar-width: none !important;
        margin-bottom: 0.85rem !important;
    }}
    div[data-baseweb="tab-list"]::-webkit-scrollbar {{
        display: none !important;
    }}

    div[data-baseweb="tab-highlight"],
    div[data-baseweb="tab-border"] {{
        display: none !important;
    }}

    button[data-baseweb="tab"] {{
        flex: 1 0 auto !important;
        white-space: nowrap !important;
        background-color: transparent !important;
        border: none !important;
        border-radius: 9px !important;
        padding: 0.5rem 0.9rem !important;
        margin: 0 !important;
        transition: background-color 0.15s ease !important;
    }}

    button[data-baseweb="tab"] p {{
        color: #F0E2C3 !important;
        font-size: 0.88rem !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }}

    /* Aktiv flik */
    button[data-baseweb="tab"][aria-selected="true"] {{
        background-color: #F0E2C3 !important;
    }}

    button[data-baseweb="tab"][aria-selected="true"] p {{
        color: #000000 !important;
        font-weight: 600 !important;
    }}


    div[data-testid="stVerticalBlockBorderWrapper"] p,
    div[data-testid="stVerticalBlockBorderWrapper"] span,
    div[data-testid="stVerticalBlockBorderWrapper"] label,
    div[data-testid="stVerticalBlockBorderWrapper"] h1,
    div[data-testid="stVerticalBlockBorderWrapper"] h2,
    div[data-testid="stVerticalBlockBorderWrapper"] h3,
    div[data-testid="stVerticalBlockBorderWrapper"] h4 {{
        color: #000000 !important;
    }}

    /* Bild-styling i kort */
    .card-img {{
        width: 100%;
        height: 190px;
        object-fit: cover;
        border-radius: 10px;
      
        margin-bottom: 0.65rem;
        display: block;
    }}
    .card-img-closed {{
        width: 100%;
        height: 190px;
        object-fit: cover;
        border-radius: 10px;
        filter: grayscale(100%);
        opacity: 0.55;
        margin-bottom: 0.65rem;
        display: block;
    }}

    /* Status- och informationsmärken (Badges) */
    .badge-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        align-items: center;
        margin: 0.35rem 0 0.6rem 0;
    }}
    .badge {{
        display: inline-flex;
        align-items: center;
        padding: 0.22rem 0.6rem;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
        line-height: 1.2;
    }}
    .badge-neutral {{
        background-color: #3B281F;
        color: #F3E9E4 !important;
        border: 1px solid #543A2E;
    }}
    .badge-price {{
        background-color: #FFFFFF;
        color: #1E40AF !important;
        border: 1px solid #000000;
    }}
    .badge-open {{
        background-color: #BAFFC9;   
        color: #065F46 !important;
        border: 1px solid #000000;
    }}
    .badge-closed {{
        background-color: #FAA0A0;  
        color: #C4B2A9 !important;
        border: 1px solid #000000;
    }}

    .card-title {{
        font-size: 1.0rem;
        font-weight: 400;
        color: #000000 !important;
        margin: 0;
        letter-spacing: -0.01em;
    }}
    .card-desc {{
        font-size: 0.9rem;
        color: #000000 !important;
        line-height: 1.5;
        margin-bottom: 0.65rem;
    }}

    /* Kompakta expanders för öppettider */
    div[data-testid="stExpander"] {{
        background-color: #c9c1b5 !important;
        border: 1px solid #000000 !important;
        border-radius: 10px !important;
        margin-top: 0.4rem !important;
    }}
    div[data-testid="stExpander"] summary {{
        background-color: transparent !important;
        padding: 0.45rem 0.75rem !important;
    }}
    div[data-testid="stExpander"] summary p {{
        color: #000000 !important;
        font-size: 0.84rem !important;
        font-weight: 600 !important;
    }}

    /* Knappar utan skuggor */
    button[kind="primary"] {{
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
    }}
    button[kind="secondary"] {{
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 10px !important;
        font-weight: 500 !important;
    }}

    /* Mobilanpassning för små skärmar */
    @media (max-width: 600px) {{
        .block-container {{
            padding-left: 0.55rem !important;
            padding-right: 0.55rem !important;
            padding-top: 0.8rem !important;
        }}
        .card-img, .card-img-closed {{
            height: 160px;
        }}
        button[data-baseweb="tab"] {{
            padding: 0.45rem 0.7rem !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------
# Huvudrad i 4-kolumners struktur: [Kolumn 1+2: Rubrik] [Kolumn 3: Datum] [Kolumn 4: Login]
# ---------
col_rubrik, col_datum, col_login = st.columns(
    [2, 1, 1], vertical_alignment="center"
)

with col_datum:
    nytt_datum = st.date_input(
        "Avresedatum",
        value=st.session_state.valt_datum,
        min_value=date.today(),
        label_visibility="collapsed",
        key="header_date_picker",
    )
    if nytt_datum != st.session_state.valt_datum:
        st.session_state.valt_datum = nytt_datum
        st.session_state.boknings_meddelande = None

        ny_veckodag = nytt_datum.isoweekday()
        kvarvarande_mal = []
        borttagna_namn = []
        for m in st.session_state.valda_mal:
            dag_status = m.get("oppettider", {}).get(ny_veckodag)
            if dag_status and not dag_status["is_open"]:
                borttagna_namn.append(m["namn"])
            else:
                kvarvarande_mal.append(m)

        st.session_state.valda_mal = kvarvarande_mal
        if borttagna_namn:
            st.session_state.datum_varning = (
                f"{', '.join(borttagna_namn)} togs bort från din bokning eftersom "
                f"det är stängt på {backend.VECKODAGAR[ny_veckodag].lower()}ar ({nytt_datum})."
            )
        else:
            st.session_state.datum_varning = None
        st.rerun()

lediga_platser, _ = backend.hamta_lediga_platser(st.session_state.valt_datum)
veckodag_nu = st.session_state.valt_datum.isoweekday()
veckodag_namn = backend.VECKODAGAR[veckodag_nu]

with col_rubrik:
    plats_text = (
        f"{veckodag_namn} · {lediga_platser} av {backend.MAX_BUSS_PLATSER} bussplatser kvar"
        if lediga_platser > 0
        else f"{veckodag_namn} · Bussen är fullbokad"
    )
    st.markdown(
        f"""
        <div>
            <h1 class="hero-title">Skånska Upplevelser</h1>
            <div class="hero-meta">{plats_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_login:
    if st.session_state.user is None:
        with st.popover("Logga in", use_container_width=True):
            st.markdown("**Kundinloggning**")
            email_input = st.text_input(
                "E-post", placeholder="dinmail@exempel.se"
            )
            pass_input = st.text_input("Lösenord", type="password")

            if st.button("Logga in", type="primary", use_container_width=True):
                user_data = backend.verifiera_inloggning(
                    email_input, pass_input
                )
                if user_data:
                    st.session_state.user = user_data
                    st.session_state.boknings_meddelande = None
                    st.rerun()
                else:
                    st.error("Fel e-post eller lösenord!")

            st.divider()
            if st.button("Skapa nytt konto", use_container_width=True):
                visa_registrering_modal()
    else:
        ar_admin = st.session_state.user["customer_id"] == 1
        etikett = (
            f"Admin · {st.session_state.user['first_name']}"
            if ar_admin
            else st.session_state.user["first_name"]
        )
        with st.popover(etikett, use_container_width=True):
            st.write(
                f"**{st.session_state.user['first_name']} {st.session_state.user['last_name']}**"
            )
            st.caption(
                f"Hemkommun: {st.session_state.user['municipality_name']}"
            )
            st.divider()

            if st.button("Redigera betald resa", use_container_width=True):
                visa_redigera_resa_modal()

            if st.button("Betalningshistorik & kvitton", use_container_width=True):
                visa_kvitto_modal()

            if st.button("Logga ut", use_container_width=True):
                st.session_state.user = None
                st.session_state.valda_mal = []
                st.session_state.boknings_meddelande = None
                st.rerun()


# ---------
# Meddelanden & Sökfält direkt på bakgrunden
# ---------
if st.session_state.datum_varning:
    st.warning(st.session_state.datum_varning)
    st.session_state.datum_varning = None

if st.session_state.boknings_meddelande:
    st.success(st.session_state.boknings_meddelande)

sok_fras = st.text_input(
    "Sök",
    placeholder="Sök bland nöjen, platser eller fika...",
    label_visibility="collapsed",
)


# ---------
# Kortkomponent för ett besöksmål (Platt 2026-kort)
# ---------
def rendera_besoksmal_kort(item):
    plats_namn = item["plats_namn"]
    kommun_namn = item["municipality_name"]
    bild_url = item["bild_url"]
    lang_text = item["lang_text"]
    kategori = item["kategori"]
    item_id = item["id"]
    municipality_id = item["municipality_id"]
    pris = item["pris"]
    oppettider = item.get("oppettider", {})

    dag_status = oppettider.get(veckodag_nu) if oppettider else None
    ar_oppet = dag_status["is_open"] if dag_status else True

    pris_etikett = f"{pris:.0f} kr / person" if pris > 0 else "Fri entré"
    if dag_status:
        if ar_oppet:
            tid_badge = f'<span class="badge badge-open">Öppet {dag_status["dag_namn"].lower()}: {dag_status["text"]}</span>'
        else:
            tid_badge = f'<span class="badge badge-closed">Stängt på {dag_status["dag_namn"].lower()}ar</span>'
    else:
        tid_badge = ""

    img_klass = "card-img" if ar_oppet else "card-img-closed"

    with st.container(border=True):
        st.markdown(
            f"""
            <img src="{bild_url}" class="{img_klass}" alt="{plats_namn}" />
            <div class="card-title">{plats_namn}</div>
            <div class="badge-row">
                <span class="badge badge-neutral">{kommun_namn}</span>
                <span class="badge badge-price">{pris_etikett}</span>
                {tid_badge}
            </div>
            <div class="card-desc">{lang_text}</div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.user is not None:
            unik_nyckel = f"{kategori}_{item_id}"
            redan_vald = any(
                m["nyckel"] == unik_nyckel for m in st.session_state.valda_mal
            )

            if lediga_platser <= 0:
                st.caption("Bussen är fullsatt på valt datum.")
            else:
                etikett = (
                    f"Välj {plats_namn}"
                    if ar_oppet
                    else f"{plats_namn} är stängt valt datum"
                )
                vald = st.checkbox(
                    etikett,
                    value=redan_vald and ar_oppet,
                    disabled=not ar_oppet,
                    key=f"chk_{unik_nyckel}_{st.session_state.valt_datum}",
                )

                if vald and not redan_vald and ar_oppet:
                    st.session_state.valda_mal.append(
                        {
                            "nyckel": unik_nyckel,
                            "kategori": kategori,
                            "id": item_id,
                            "namn": plats_namn,
                            "municipality_id": municipality_id,
                            "pris": pris,
                            "oppettider": oppettider,
                        }
                    )
                    st.rerun()
                elif not vald and redan_vald:
                    st.session_state.valda_mal = [
                        m
                        for m in st.session_state.valda_mal
                        if m["nyckel"] != unik_nyckel
                    ]
                    st.rerun()
        else:
            st.caption("Logga in högst upp för att lägga till i din resa.")

        with st.expander("Visa öppettider (Mån–Sön)", expanded=False):
            if oppettider:
                for veckodag_nr in range(1, 8):
                    rad = oppettider.get(veckodag_nr)
                    if rad:
                        markering = "• " if veckodag_nr == veckodag_nu else ""
                        vikt = "**" if veckodag_nr == veckodag_nu else ""
                        status_str = rad["text"] if rad["is_open"] else "Stängt"
                        st.write(
                            f"{markering}{vikt}{rad['dag_namn']}:{vikt} {status_str}"
                        )
            else:
                st.caption("Inga öppettider registrerade.")


# ---------
# Huvudflikar direkt på bakgrunden
# ---------
antal_valda = len(st.session_state.valda_mal)
boknings_flik_titel = (
    f"Bokning ({antal_valda})" if antal_valda > 0 else "Bokning"
)

flik_titlar = ["Nöjen", "Platser", "Fika", boknings_flik_titel]
ar_admin_inloggad = (
    st.session_state.user is not None
    and st.session_state.user["customer_id"] == 1
)
if ar_admin_inloggad:
    flik_titlar.append("Admin")

flikar = st.tabs(flik_titlar)

# 1–3. Kategoriflikar (Nöjen, Platser, Fika)
for flik, (titel, kat_kod) in zip(
    flikar[:3],
    [("Nöjen", "amusement"), ("Platser", "place"), ("Fika", "fika")],
):
    with flik:
        items = backend.filtrera_aktiviteter(kat_kod, sok_fras)
        if not items:
            with st.container(border=True):
                st.write(f"Inga besöksmål under **{titel}** matchade din sökning.")
        else:
            for item in items:
                rendera_besoksmal_kort(item)

# 4. Bokningsflik direkt på bakgrunden
with flikar[3]:
    with st.container(border=True):
        if st.session_state.user is None:
            st.markdown("#### Min bokning")
            st.write(
                "Logga in via knappen längst upp till höger för att välja resmål och slutföra din bokning."
            )
        else:
            st.markdown(
                f"#### Boka resa för {st.session_state.user['first_name']}"
            )
            st.caption(
                f"Avresa från {st.session_state.user['municipality_name']} · {st.session_state.valt_datum} ({veckodag_namn})"
            )

            if lediga_platser <= 0:
                st.warning(
                    "Bussen är fullbokad på detta datum. Byt datum högst upp för att boka."
                )
            elif antal_valda == 0:
                st.info(
                    "Du har inte valt några besöksmål än. Kryssa i dina favoriter under flikarna Nöjen, Platser eller Fika."
                )
            else:
                st.markdown("**Valda resmål i ditt paket**")
                for mal in st.session_state.valda_mal:
                    dag_info = mal.get("oppettider", {}).get(veckodag_nu)
                    tid_etikett = (
                        f" · {dag_info['text']}" if dag_info else ""
                    )
                    st.write(
                        f"- **{mal['namn']}** ({mal['pris']:.0f} kr){tid_etikett}"
                    )

                st.divider()

                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    adults = st.number_input("Vuxna", min_value=1, value=1)
                with bcol2:
                    children = st.number_input("Barn", min_value=0, value=0)
                with bcol3:
                    payment_method = st.selectbox(
                        "Betalsätt", ["Swish", "Kort", "Klarna"]
                    )

                total_price, buss_avgift, antal_kommuner, antal_resenarer = (
                    backend.berakna_respris(
                        st.session_state.user["municipality_id"],
                        st.session_state.valda_mal,
                        adults,
                        children,
                    )
                )

                st.write(
                    f"Bussavgift ({antal_kommuner} kommuner × 45 kr): **{buss_avgift:.2f} kr**"
                )
                st.markdown(f"### Totalpris: {total_price:.2f} kr")

                for_manga_resenarer = antal_resenarer > lediga_platser
                if for_manga_resenarer:
                    st.warning(
                        f"Du har valt {antal_resenarer} resenärer men det finns endast {lediga_platser} platser kvar."
                    )

                if st.button(
                    "Slutför bokning & betala",
                    type="primary",
                    disabled=for_manga_resenarer,
                    use_container_width=True,
                ):
                    booking_id, fel = backend.spara_bokning_i_db(
                        user=st.session_state.user,
                        valda_mal=st.session_state.valda_mal,
                        travel_date=st.session_state.valt_datum,
                        adults=adults,
                        children=children,
                        total_price=total_price,
                        payment_method=payment_method,
                    )
                    if booking_id:
                        st.session_state.boknings_meddelande = (
                            f"Betalning genomförd med {payment_method}! Bokningsnummer #{booking_id}. "
                            f"Kvitto finns under Betalningshistorik i kontomenyn."
                        )
                        st.session_state.valda_mal = []
                        st.rerun()
                    else:
                        st.error(f"Kunde inte spara bokningen: {fel}")

# 5. Adminflik (Visas endast för Kund-ID #1)
if ar_admin_inloggad:
    with flikar[4]:
        with st.container(border=True):
            st.markdown("#### Administratörsvy (Kund-ID #1)")
            st.caption(
                "Alla kunders bokningar och kvitton nås även via kontomenyn längst upp till höger."
            )
            alla_kunder = backend.hamta_alla_kunder()
            st.dataframe(alla_kunder, use_container_width=True, hide_index=True)
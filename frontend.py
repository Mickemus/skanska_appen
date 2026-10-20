import base64
from datetime import date
import streamlit as st
import backend

st.set_page_config(page_title="Skånska Upplevelser", layout="wide")


# ---------
# Registrera ny användare
# ---------

@st.dialog("Registrera ny användare")
def visa_registrering_modal():
    st.write("Fyll i dina uppgifter nedan för att skapa ett konto hos Skånska Upplevelser.")

    kommuner = backend.hamta_kommuner()
    kommun_dict = {k["municipality_name"]: k["municipality_id"] for k in kommuner}

    with st.form("registrera_kund_form"):
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

        skicka = st.form_submit_button("Skapa konto", use_container_width=True)

        if skicka:
            fn = first_name.strip()
            ln = last_name.strip()
            em = email.strip()

            # 1. Kontrollera att obligatoriska fält är ifyllda
            if not fn or not ln or not em or not password or not password_confirm:
                st.error("Vänligen fyll i alla obligatoriska fält (*).")

            # 2. Kontrollera dubbla mellanslag
            elif "  " in fn or "  " in ln or "  " in em:
                st.error("Fälten får inte innehålla dubbla mellanslag.")

            # 3. Kontrollera namnformat: Stor första bokstav, resten små
            elif fn != fn.capitalize() or ln != ln.capitalize():
                st.error(
                    f""
                )

            # 4. Kontrollera e-post (@ och domän som .com/.se)
            elif (
                "@" not in em
                or "." not in em.split("@")[-1]
                or len(em.split("@")[-1].split(".")[-1]) < 2
                or " " in em
            ):
                st.error(
                    "Ange en giltig e-postadress."
                )

            # 5. Kontrollera lösenordslängd (> 6 tecken, alltså minst 7)
            elif len(password) <= 6:
                st.error("Lösenordet måste vara längre än 6 tecken.")

            # 6. Kontrollera att båda lösenordsfälten matchar
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
# redigera betald resa
# ---------

@st.dialog("Redigera betald resa", width="large")
def visa_redigera_resa_modal():
    user = st.session_state.user
    is_admin = user["customer_id"] == 1

    bokningar = backend.hamta_redigerbara_bokningar(user["customer_id"], is_admin=is_admin)

    if not bokningar:
        st.info("Det finns inga resor som kan redigeras.")
        return

    boknings_val = {
        f"Bokning #{b['booking_id']} — {b['first_name']} {b['last_name']} | Avresa: {b['travel_date']} ({b['total_price']:.2f} kr)": b
        for b in bokningar
    }

    vald_label = st.selectbox("Välj bokning att redigera", options=list(boknings_val.keys()))
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

    st.markdown("#### Välj destinationer för resan")
    st.caption("Kryssa i eller ur destinationer. Priset räknas om automatiskt nedan.")

    kat_col1, kat_col2, kat_col3 = st.columns(3)
    nya_valda_mal = []

    for kat_col, kat_kod, kat_rubrik in [
        (kat_col1, "amusement", "Nöjen"),
        (kat_col2, "place", "Platser"),
        (kat_col3, "fika", "Fika"),
    ]:
        with kat_col:
            st.markdown(f"**{kat_rubrik}**")
            for akt in backend.ALLA_AKTIVITETER:
                if akt["kategori"] == kat_kod:
                    nyckel = f"{akt['kategori']}_{akt['id']}"
                    forifyll = nyckel in aktuell_bokning["valda_nycklar"]
                    pris_txt = f"{akt['pris']:.0f} kr" if akt["pris"] > 0 else "0 kr"
                    if st.checkbox(
                        f"{akt['plats_namn']} ({pris_txt})",
                        value=forifyll,
                        key=f"edit_chk_{b_id}_{nyckel}",
                    ):
                        nya_valda_mal.append(akt)

    st.divider()

    if len(nya_valda_mal) == 0:
        st.warning("Du måste ha minst en destination vald i resan.")
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
        st.write(f"**Tidigare betalt totalpris:** {gammalt_pris:.2f} kr")
        st.write(f"**Nytt beräknat totalpris:** {nytt_totalpris:.2f} kr")
        if mellanskillnad > 0:
            st.warning(f"**Att betala extra:** +{mellanskillnad:.2f} kr")
        elif mellanskillnad < 0:
            st.success(f"**Att få tillbaka (Återbetalning):** {abs(mellanskillnad):.2f} kr")
        else:
            st.info("**Prisskillnad:** 0.00 kr (Ingen extra kostnad)")

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

    if st.button(knapp_text, use_container_width=True):
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
# Betalningshistorik och kvitton
# ---------

@st.dialog("Betalningshistorik & Kvitton", width="large")
def visa_kvitto_modal():
    user = st.session_state.user
    is_admin = user["customer_id"] == 1

    if is_admin:
        st.write(
            "**Adminvy:** Visar samtliga registrerade betalningar och kvitton i systemet (nyaste överst)."
        )
    else:
        st.write(
            f"Visar alla registrerade betalningar och bokningskvitton för **{user['first_name']} {user['last_name']}** "
            f"(Kund-ID: `#{user['customer_id']}`)."
        )
    st.divider()

    kvitton = backend.hamta_betalningshistorik(user["customer_id"], is_admin=is_admin)

    if not kvitton:
        st.info("Det finns inga tidigare betalningar eller kvitton registrerade ännu.")
        return

    for k in kvitton:
        betal_status = k["payment_status"] if k["payment_status"] else "Paid"
        betal_metod = k["payment_method"] if k["payment_method"] else "Direktbetalning"
        belopp = float(k["amount"]) if k["amount"] is not None else float(k["total_price"])
        datum_tid = k["payment_date"] if k["payment_date"] else k["booking_date"]
        datum_str = (
            datum_tid.strftime("%Y-%m-%d %H:%M:%S")
            if hasattr(datum_tid, "strftime")
            else str(datum_tid)
        )
        kvitto_nr = k["payment_id"] if k["payment_id"] else k["booking_id"]

        if belopp < 0:
            typ_etikett = f"Återbetalning: {belopp:.2f} kr"
        else:
            typ_etikett = f"Betalning: {belopp:.2f} kr"

        kund_info = f" | Kund: {k['first_name']} {k['last_name']}" if is_admin else ""

        rubrik = (
            f"Kvitto #{kvitto_nr} | {datum_str} | "
            f"{typ_etikett} ({betal_metod}) — Avresa: {k['travel_date']}{kund_info}"
        )

        with st.expander(rubrik, expanded=False):
            kcol1, kcol2 = st.columns(2)

            with kcol1:
                st.markdown("### Resedetaljer")
                st.write(f"**Bokningsnummer:** #{k['booking_id']}")
                if is_admin:
                    st.write(f"**Kund:** {k['first_name']} {k['last_name']} (ID #{k['customer_id']})")
                st.write(f"**Paket:** {k['package_name']}")
                st.write(f"**Valda besöksmål:** {k['resmal'] or 'Inga specifika mål angivna'}")
                st.write(f"**Rutt:** {k['start_kommun']} ➔ {k['slut_kommun']}")
                st.write(f"**Avresedatum:** {k['travel_date']}")
                st.write(
                    f"**Resenärer:** {k['number_of_adults']} vuxna, {k['number_of_children']} barn"
                )

            with kcol2:
                st.markdown("### Betalningsspecifikation")
                st.write(f"**Kvittonummer:** #{kvitto_nr}")
                st.write(f"**Transaktionsdatum:** {datum_str}")
                st.write(f"**Betalsätt:** {betal_metod}")
                st.write(f"**Betalningsstatus:** {betal_status}")
                st.write(f"**Bokningsstatus:** {k['booking_status']}")
                st.write(f"**Bokningens nuvarande totalpris:** {k['total_price']:.2f} kr")
                if belopp < 0:
                    st.markdown(f"#### Återbetalt belopp: {abs(belopp):.2f} kr")
                else:
                    st.markdown(f"#### Transaktionsbelopp: {belopp:.2f} kr")


# ---------
# Session
# ---------

if "user" not in st.session_state:
    st.session_state.user = None

if "valda_mal" not in st.session_state:
    st.session_state.valda_mal = []

if "valt_datum" not in st.session_state:
    st.session_state.valt_datum = date.today()

if "boknings_meddelande" not in st.session_state:
    st.session_state.boknings_meddelande = None

lediga_platser, totalt_bokade = backend.hamta_lediga_platser(st.session_state.valt_datum)


# ---------
# bg och css
# ---------
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""


bg_img = get_base64_image("bakgrund.jpg")

st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url("data:image/jpeg;base64,{bg_img}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    h1 {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 1px #000000D2 !important;
    }}

    div[data-testid="stExpander"] {{
        background-color: #F3E2C3;
        border-radius: 10px;
    }}

    div[data-testid="stExpander"] summary {{
        background-color: #ECCF9D !important;
        border-radius: 10px;
    }}
    
    div[data-testid="stExpander"] summary p {{
        color: #FFFFFF !important;
        text-shadow: 1px 1px 1px #000000D2 !important;
        font-size: 1.4rem;
    }}

    div[data-testid="stExpanderDetails"] p, 
    div[data-testid="stExpanderDetails"] span,
    button[data-baseweb="tab"] p {{
        color: #000000 !important; 
    }}

    div[data-testid="stDialog"] div[role="dialog"] {{
        width: 92vw !important;
        max-width: 92vw !important;
        min-height: 75vh !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------
# rubrik, inloggning o registrering
# ---------
top_left, top_center, top_right = st.columns([1, 5, 1])

with top_center:
    st.markdown(
        "<h1 style='text-align: center;'>Skånska Upplevelser</h1>",
        unsafe_allow_html=True,
    )

with top_right:
    st.write("")
    if st.session_state.user is None:
        with st.popover("Logga in", use_container_width=True):
            st.subheader("Kundinloggning")
            email_input = st.text_input("E-post", placeholder="dinmail@exempel.se")
            pass_input = st.text_input("Lösenord", type="password")

            if st.button("Logga in", use_container_width=True):
                user_data = backend.verifiera_inloggning(email_input, pass_input)
                if user_data:
                    st.session_state.user = user_data
                    st.session_state.boknings_meddelande = None
                    st.rerun()
                else:
                    st.error("Fel e-post eller lösenord!")

            st.divider()
            st.caption("Ny hos oss?")
            if st.button("Registrera ny kund", use_container_width=True):
                visa_registrering_modal()
    else:
        ar_admin = st.session_state.user["customer_id"] == 1
        ikon = "👑" if ar_admin else "👤"
        with st.popover(
            f"{ikon} {st.session_state.user['first_name']}",
            use_container_width=True,
        ):
            st.write(
                f"**Inloggad som:** {st.session_state.user['first_name']} {st.session_state.user['last_name']}"
            )
            if ar_admin:
                st.caption("Roll: **Administratör (ID #1)**")
            st.write(
                f"**Hemkommun:** {st.session_state.user['municipality_name']}"
            )
            st.divider()

            if st.button("Redigera betald resa", use_container_width=True):
                visa_redigera_resa_modal()

            if st.button("Betalningshistorik", use_container_width=True):
                visa_kvitto_modal()

            if st.button("Logga ut", use_container_width=True):
                st.session_state.user = None
                st.session_state.valda_mal = []
                st.session_state.boknings_meddelande = None
                st.rerun()

st.write("")


# ---------
# UI-komponenter för aktivitetsflikar
# ---------
def visa_plats(
    plats_namn,
    kort_info,
    bild_url,
    lang_text,
    kategori,
    item_id,
    municipality_id,
    pris=0.0,
):
    st.write(kort_info)

    with st.container(height=380, border=False):
        st.subheader(plats_namn)
        if pris > 0:
            st.write(f"**Biljettpris:** {pris:.0f} kr / person")
        else:
            st.write("**Pris:** Kostnadsfritt besöksmål (eller egen fika)")

        if st.session_state.user is not None:
            unik_nyckel = f"{kategori}_{item_id}"
            redan_vald = any(
                m["nyckel"] == unik_nyckel for m in st.session_state.valda_mal
            )

            if lediga_platser <= 0:
                st.error(
                    f"**Fullsatt** ({st.session_state.valt_datum}) — Alla {backend.MAX_BUSS_PLATSER} platser på bussen är bokade."
                )
            else:
                vald = st.checkbox(
                    f"Lägg till {plats_namn} i min bokning",
                    value=redan_vald,
                    key=f"chk_{unik_nyckel}",
                )

                if vald and not redan_vald:
                    st.session_state.valda_mal.append(
                        {
                            "nyckel": unik_nyckel,
                            "kategori": kategori,
                            "id": item_id,
                            "namn": plats_namn,
                            "municipality_id": municipality_id,
                            "pris": pris,
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
            st.info("Logga in för att kunna boka.")

        st.image(bild_url, use_container_width=True)
        st.write(lang_text)
        st.write(
            "Här kan du fylla på med grejsimojs Emil. Kartor också? Kanske adress"
        )


def rendera_kategori_expander(titel, kategori_kod, sok_ord):
    """Renderar en expander med flikar baserat på filtrerad data från backend."""
    items = backend.filtrera_aktiviteter(kategori_kod, sok_ord)
    auto_expand = bool(sok_ord.strip() and len(items) > 0)

    with st.expander(titel, expanded=auto_expand):
        if not items:
            st.info(f"Inga aktiviteter under '{titel}' matchade din sökning.")
        else:
            flikar = st.tabs([item["plats_namn"] for item in items])
            for flik, item in zip(flikar, items):
                with flik:
                    visa_plats(
                        plats_namn=item["plats_namn"],
                        kort_info=item["kort_info"],
                        bild_url=item["bild_url"],
                        lang_text=item["lang_text"],
                        kategori=item["kategori"],
                        item_id=item["id"],
                        municipality_id=item["municipality_id"],
                        pris=item["pris"],
                    )


# ---------
# Sökfält, Flikar, Bokning & Adminpanel
# ---------
col1, col2, col3 = st.columns([1, 5, 1])

with col2:
    sok_fras = st.text_input(
        "",
        placeholder="Sök...",
    )

    rendera_kategori_expander("Nöjen", "amusement", sok_fras)
    rendera_kategori_expander("Platser", "place", sok_fras)
    rendera_kategori_expander("Fika", "fika", sok_fras)

    if st.session_state.user is not None:
        with st.expander("Min Bokning", expanded=True):
            st.subheader(
                f"Boka resa för {st.session_state.user['first_name']} från {st.session_state.user['municipality_name']}"
            )

            if st.session_state.boknings_meddelande:
                st.success(st.session_state.boknings_meddelande)

            dcol1, dcol2 = st.columns([1, 2])
            with dcol1:
                nytt_datum = st.date_input(
                    "Välj avresedatum",
                    value=st.session_state.valt_datum,
                    min_value=date.today(),
                )
                if nytt_datum != st.session_state.valt_datum:
                    st.session_state.valt_datum = nytt_datum
                    st.session_state.boknings_meddelande = None
                    st.rerun()

            with dcol2:
                st.write("")
                if lediga_platser > 0:
                    st.info(
                        f"**Superduperbussen ({st.session_state.valt_datum}):** "
                        f"{totalt_bokade}/{backend.MAX_BUSS_PLATSER} platser bokade — **{lediga_platser} platser kvar**."
                    )
                else:
                    st.error(
                        f"**Superduperbussen ({st.session_state.valt_datum}):** "
                        f"Fullsatt ({backend.MAX_BUSS_PLATSER}/{backend.MAX_BUSS_PLATSER} platser bokade). Välj ett annat datum!"
                    )

            if lediga_platser <= 0:
                st.warning(
                    "Bussen är fullbokad på detta datum. Byt datum ovan för att kunna kryssa i resmål."
                )
            elif len(st.session_state.valda_mal) == 0:
                st.write(
                    "Du har inte valt några resmål än. Öppna flikarna ovan och kryssa i ett eller flera mål!"
                )
            else:
                st.write("**Valda resmål i ditt paket:**")
                for mal in st.session_state.valda_mal:
                    st.write(f"- {mal['namn']} ({mal['pris']:.0f} kr)")

                bcol1, bcol2, bcol3 = st.columns(3)
                with bcol1:
                    adults = st.number_input("Antal vuxna", min_value=1, value=1)
                with bcol2:
                    children = st.number_input("Antal barn", min_value=0, value=0)
                with bcol3:
                    payment_method = st.selectbox(
                        "Välj betalsätt", ["Swish", "Kort", "Klarna"]
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
                    f"**Bussavgift ({antal_kommuner} kommuner x 45 kr):** {buss_avgift:.2f} kr"
                )
                st.subheader(f"Totalpris: {total_price:.2f} kr")

                for_manga_resenarer = antal_resenarer > lediga_platser

                if for_manga_resenarer:
                    st.warning(
                        f"Det går inte att boka {antal_resenarer} resenärer ({adults} vuxna, {children} barn)! "
                        f"Det finns bara **{lediga_platser} platser kvar** på bussen den {st.session_state.valt_datum}."
                    )

                if st.button(
                    "Slutför bokning & betala", disabled=for_manga_resenarer
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
                            f"Betalning genomförd med {payment_method}! Ditt bokningsnummer är #{booking_id}. "
                            f"Du hittar ditt kvitto under 'Betalningshistorik'."
                        )
                        st.session_state.valda_mal = []
                        st.rerun()
                    else:
                        st.error(f"Kunde inte spara bokningen: {fel}")
# ---------
# "Admin panel" visas endast när customer_id 1 är inloggad
# ---------
        if st.session_state.user["customer_id"] == 1:
            with st.expander("Adminpanel — Systemöversikt", expanded=False):
                st.subheader("Administratörsvy (Kund-ID #1)")
                st.write(
                    "Som admin kan du även redigera alla kunders kommande bokningar under **Redigera betald resa** "
                    "och se alla transaktioner under **Betalningshistorik** uppe till höger."
                )
                alla_kunder = backend.hamta_alla_kunder()
                st.markdown("#### Registrerade användare")
                st.dataframe(alla_kunder, use_container_width=True)
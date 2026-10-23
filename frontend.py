import base64  # Lånar in en verktygslåda som kan översätta bilder till långa bokstavskoder (så webbläsaren fattar dem)
from pathlib import Path  # Hämtar en digital spejare som är expert på att hitta filer och mappar på datorn
from datetime import date, timedelta  # Hämtar en kalender-assistent så att datorn vet vilket datum det är idag och imorgon
import streamlit as st  # Hämtar vår superhjälte "Streamlit" (och ger den smeknamnet "st") som bygger hemsidor utan att vi behöver gråta
import backend  # Kopplar in vår egen fil "backend.py" – maskinrummet som sköter allt det tunga jobbet bakom kulisserna


st.set_page_config(  # Säger åt Streamlit att vi vill ställa in grundreglerna för hela webbsidan
    page_title="Skånska Upplevelser",  # Bestämmer vad som ska stå högst upp på fliken i webbläsaren
    layout="centered",  # Säger att innehållet ska ligga prydligt i mitten istället för att flyta ut som en pannkaka
    initial_sidebar_state="collapsed",  # Gömmer sidomenyn från start så sidan ser ren och snygg ut
)  # Stänger inställningsrutan – nu är grunden lagd!


# ---------  # En visuell avdelare (bara för att vi människor ska se att ett nytt kapitel börjar)
# Session State  # Här räddar vi appen från guldfiskminne! "Session State" är hemsidans korttidsminne.
# ---------  # Ännu ett prydligt staket i koden
if "user" not in st.session_state:  # Kollar i minnet: "Har vi glömt att notera vem som är inloggad?"
    st.session_state.user = None  # Om ja: Sätt inloggad person till "Ingen alls" (None) så länge

if "valda_mal" not in st.session_state:  # Kollar i minnet: "Saknar vi en kundvagn för valda utflyktsmål?"
    st.session_state.valda_mal = []  # Om ja: Skapa en helt tom inköpslista (hakparenteser betyder lista!)

if "valt_datum" not in st.session_state:  # Kollar i minnet: "Har besökaren inte valt avresedatum än?"
    st.session_state.valt_datum = date.today()  # Om ja: Föreslå dagens datum som startvärde (default på dagens datum)

if "boknings_meddelande" not in st.session_state:  # Kollar i minnet: "Finns det något grönt glatt bekräftelsemeddelande?"
    st.session_state.boknings_meddelande = None  # Om ja: Sätt det till tomt från början (vi har ju inte bokat än!)

if "datum_varning" not in st.session_state:  # Kollar i minnet: "Finns det någon varning om stängda resmål?"
    st.session_state.datum_varning = None  # Sätt varningen till tom tills någon faktiskt väljer en stängd dag


def uppdatera_valt_datum(nytt_datum):  # Hjälpfunktion som synkar datumbyten mellan sidhuvudet och kassan i Bokning-fliken
    st.session_state.valt_datum = nytt_datum  # Uppdatera korttidsminnet med det nya datumet
    st.session_state.boknings_meddelande = None  # Städa bort eventuella gamla kvittomeddelanden

    ny_veckodag = nytt_datum.isoweekday()  # Kolla vilken veckodag (1-7) det nya datumet är
    kvarvarande_mal = []  # En lista för utflyktsmål som har öppet på den nya dagen
    borttagna_namn = []  # En lista för utflyktsmål som tyvärr har stängt på den nya dagen
    for m in st.session_state.valda_mal:  # Kolla igenom alla resmål som användaren redan hade kryssat i:
        dag_status = m.get("oppettider", {}).get(ny_veckodag)  # Slå upp öppettiden för den nya veckodagen
        ar_oppet_ny, _, _ = backend.utvardera_oppetstatus(dag_status, nytt_datum)  # Kolla om stället är öppet (inkl. stängningstid)
        if not ar_oppet_ny:  # Om stället är stängt den dagen...
            borttagna_namn.append(m["namn"])  # ...skriv upp namnet på "borttaget"-listan
        else:  # Annars, om stället har öppet som vanligt...
            kvarvarande_mal.append(m)  # ...låt det ligga kvar i kundvagnen!

    st.session_state.valda_mal = kvarvarande_mal  # Uppdatera kundvagnen så bara öppna resmål är kvar
    if borttagna_namn:  # Om vi var tvungna att plocka bort något stängt resmål:
        st.session_state.datum_varning = (  # Skapa ett varningsmeddelande i minnet:
            f"{', '.join(borttagna_namn)} togs bort från din bokning eftersom "  # Räknar upp vilka mål som togs bort
            f"det är stängt på {backend.VECKODAGAR[ny_veckodag].lower()}ar ({nytt_datum})."  # Förklarar vilken veckodag det är stängt
        )  # Varningstext klar
    else:  # Om alla valda mål hade öppet även på nya datumet:
        st.session_state.datum_varning = None  # Ingen varning behövs!
    st.rerun()  # Ladda om sidan direkt så alla öppettider och bussplatser uppdateras för det nya datumet!


# ---------  # Nytt kapitel på gång!
# Registrera ny användare (Modal)  # En "Modal" är fint programmerarspråk för en popup-ruta mitt på skärmen
# ---------  # Sista staketet innan popup-koden
@st.dialog("Registrera ny användare")  # Trollformel som förvandlar funktionen nedanför till en snygg popup-ruta med rubrik
def visa_registrering_modal():  # Skapar ett recept (en "funktion") som ritar upp registreringsrutan när någon klickar
    st.caption(  # Ber Streamlit skriva ut en liten, diskret hjälptext
        "Fyll i dina uppgifter nedan för att skapa ett konto hos Skånska Upplevelser."  # Själva texten som välkomnar nya kunder
    )  # Stänger hjälptexten

    kommuner = backend.hamta_kommuner()  # Ropar ner till maskinrummet (backend): "Ge mig alla skånska kommuner från databasen!"
    kommun_dict = {k["municipality_name"]: k["municipality_id"] for k in kommuner}  # Bygger en telefonbok där kommunens namn pekar på dess hemliga ID-nummer

    with st.form("registrera_kund_form", border=False):  # Öppnar ett digitalt pappersformulär utan synlig ram runt
        col_f1, col_f2 = st.columns(2)  # Delar in raden i två lika stora kolumner (vänster och höger)
        with col_f1:  # Kliver in i vänstra kolumnen
            first_name = st.text_input(  # Ritar en textruta där användaren kan skriva sitt förnamn
                "Förnamn *", max_chars=60, placeholder="T.ex. Anna"  # Sätter rubrik, max 60 bokstäver och en blek exempeltext
            )  # Klar med förnamnsrutan
        with col_f2:  # Kliver in i högra kolumnen
            last_name = st.text_input(  # Ritar en textruta för efternamn
                "Efternamn *", max_chars=60, placeholder="T.ex. Andersson"  # Rubrik, max 60 tecken och exempeltext
            )  # Klar med efternamnsrutan

        email = st.text_input(  # Ritar en textruta på full bredd för e-postadressen
            "E-postadress *", max_chars=150, placeholder="namn@exempel.com"  # Max 150 tecken (för folk med väldigt långa mejladresser)
        )  # Klar med e-postrutan

        col_p1, col_p2 = st.columns(2)  # Delar in nästa rad i två nya kolumner för lösenordet
        with col_p1:  # Vänstra lösenordskolumnen
            password = st.text_input(  # Ritar en textruta för lösenordet
                "Lösenord * (minst 7 tecken)", type="password", max_chars=255  # "type=password" byter ut bokstäverna mot hemliga prickar!
            )  # Klar med första lösenordsrutan
        with col_p2:  # Högra lösenordskolumnen
            password_confirm = st.text_input(  # Ritar en ruta till så användaren inte råkar slinta på tangenterna
                "Bekräfta lösenord *", type="password", max_chars=255  # Också hemliga prickar och max 255 tecken
            )  # Klar med bekräftelserutan

        phone = st.text_input(  # Ritar en textruta för telefonnummer (ingen stjärna = frivilligt!)
            "Telefonnummer", max_chars=25, placeholder="070-1234567"  # Max 25 tecken och ett skånskt mobilnummer-exempel
        )  # Klar med telefonrutan

        vald_kommun_namn = st.selectbox(  # Ritar en rullgardinsmeny (dropdown) där man väljer sin hemkommun
            "Hemkommun *",  # Rubriken ovanför rullgardinen
            options=list(kommun_dict.keys()) if kommun_dict else ["Malmö"],  # Fyller listan med kommunnamn (eller bara "Malmö" om databasen tar kaffepaus)
        )  # Klar med rullgardinsmenyn

        skicka = st.form_submit_button(  # Ritar den stora knappen längst ner i formuläret
            "Skapa konto", type="primary", use_container_width=True  # "primary" gör knappen extra snygg och "use_container_width" gör den bred
        )  # Klar med knappen

        if skicka:  # Om någon faktiskt tryckte på "Skapa konto"-knappen händer allt nedanför:
            fn = first_name.strip()  # Tvättar bort råkade mellanslag före och efter förnamnet
            ln = last_name.strip()  # Tvättar bort onödiga mellanslag runt efternamnet också
            em = email.strip()  # Och städar bort mellanslag runt mejladressen

            if not fn or not ln or not em or not password or not password_confirm:  # Om något av de tvingande fälten lämnades helt tomt...
                st.error("Vänligen fyll i alla obligatoriska fält (*).")  # ...visa en röd skäll-ruta!
            elif "  " in fn or "  " in ln or "  " in em:  # Annars, om någon somnat på mellanslagstangenten (dubbla mellanslag)...
                st.error("Fälten får inte innehålla dubbla mellanslag.")  # ...stoppa dem vänligt men bestämt!
            elif fn != fn.capitalize() or ln != ln.capitalize():  # Kollar så namnen börjar med STOR bokstav följt av små (Anna, inte aNNA)
                st.error(  # Förbereder röd felruta om bokstäverna är kaos
                    "Förnamn och efternamn måste börja med stor bokstav följt av små bokstäver."  # Förklarar regeln för användaren
                )  # Stänger felrutan
            elif (  # Påbörjar en rejäl detektivkontroll av e-postadressen:
                "@" not in em  # Saknas snabel-a?
                or "." not in em.split("@")[-1]  # Saknas punkt efter snabel-a?
                or len(em.split("@")[-1].split(".")[-1]) < 2  # Är slutet efter sista punkten (t.ex. ".se") kortare än 2 bokstäver?
                or " " in em  # Eller har det smugit sig in ett mellanslag mitt i mejlen?
            ):  # Om något av ovanstående mejl-fusk hittas...
                st.error("Ange en giltig e-postadress.")  # ...skrik till i en röd ruta!
            elif len(password) <= 6:  # Kollar om lösenordet är 6 tecken eller kortare (vi krävde ju minst 7!)
                st.error("Lösenordet måste vara längre än 6 tecken.")  # Ber användaren hitta på något längre
            elif password != password_confirm:  # Kollar om de två lösenordsrutorna inte matchar varandra
                st.error("Lösenorden matchar inte!")  # Röd ruta: "Nu skrev du olika!"
            else:  # HURRA! Alla kontroller godkända – nu sparar vi kunden:
                kommun_id = kommun_dict.get(vald_kommun_namn, 17)  # Slår upp kommunens ID-nummer i vår telefonbok (eller gissar på 17 om något är skumt)
                lyckades, meddelande = backend.registrera_kund_i_db(  # Skickar ner alla uppgifter till maskinrummet (backend) för lagring i databasen
                    fn, ln, em, password, phone, kommun_id  # Här är paketet med kunduppgifter vi skickar med
                )  # Backend svarar med två saker: om det gick bra (lyckades) och en text (meddelande)
                if lyckades:  # Om databasen gav tummen upp:
                    ny_user = backend.verifiera_inloggning(em, password)  # Loggar in den nyblivna kunden direkt på studs
                    st.session_state.user = ny_user  # Sparar kunden i appens korttidsminnet så de förblir inloggade
                    st.session_state.boknings_meddelande = meddelande  # Lägger välkomstmeddelandet i minnet så det syns på startsidan
                    st.rerun()  # Ladda om sidan direkt så popup-rutan stängs och kunden ser sitt nya konto!
                else:  # Om databasen sa nej (t.ex. att mejlen redan fanns):
                    st.error(meddelande)  # Visa databasens felmeddelande i en röd ruta


# ---------  # Ny avdelare i koden
# Redigera betald resa (Modal)  # Här kommer popup-rutan för folk som ångrat sig och vill ändra sin resa
# ---------  # Staket klart
@st.dialog("Redigera betald resa", width="large")  # Gör en extra bred ("large") popup-ruta med rubriken "Redigera betald resa"
def visa_redigera_resa_modal():  # Startar receptet för omboknings-popupen
    user = st.session_state.user  # Hämtar den inloggade personen ur korttidsminnet
    is_admin = user["customer_id"] == 1  # Kollar om kunden har ID nummer 1 – i så fall är personen vår allsmäktiga Administratör!

    bokningar = backend.hamta_redigerbara_bokningar(  # Ber maskinrummet hämta alla framtida resor som går att ändra
        user["customer_id"], is_admin=is_admin  # Skickar med kundens ID (och om det är chefen som tittar, för chefen får se ALLAS resor)
    )  # Nu har vi en lista med bokningar

    if not bokningar:  # Om listan med bokningar är helt ekande tom:
        st.info("Det finns inga kommande resor som kan redigeras.")  # Visa en snäll blå infoskylt
        return  # Avbryt funktionen här – det finns ju inget mer att rita ut!

    boknings_val = {  # Bygger en uppslagsbok där en snygg beskrivande text kopplas till respektive bokning
        f"Bokning #{b['booking_id']} — {b['first_name']} {b['last_name']} | {b['travel_date']} ({b['total_price']:.0f} kr)": b  # Snygg etikett med bokningsnr, namn, datum och pris
        for b in bokningar  # Gör detta för varje bokning ("b") som vi fick från databasen
    }  # Uppslagsboken är klar!

    vald_label = st.selectbox(  # Ritar en rullgardinsmeny där användaren väljer vilken bokning som ska ändras
        "Välj bokning att redigera", options=list(boknings_val.keys())  # Stoppar in våra snygga etiketter som val i menyn
    )  # Användaren har valt en bokning
    aktuell_bokning = boknings_val[vald_label]  # Plockar fram hela bokningspaketet bakom den valda etiketten
    b_id = aktuell_bokning["booking_id"]  # Plockar ut själva bokningsnumret så vi slipper skriva så långt varje gång

    st.divider()  # Ritar ett tunnt vågrätt streck för att dela av rutan snyggt

    tidigaste_bokningsdag = date.today() + timedelta(days=1)  # Bussen kan tidigast bokas/ombokas till dagen därpå
    rcol1, rcol2, rcol3 = st.columns(3)  # Delar upp raden i tre lika stora kolumner
    with rcol1:  # I första kolumnen:
        nytt_datum = st.date_input(  # Ritar en kalenderväljare för nytt avresedatum
            "Nytt avresedatum",  # Rubrik ovanför kalendern
            value=max(aktuell_bokning["travel_date"], tidigaste_bokningsdag),  # Förifyller det datum resan har just nu (minst imorgon)
            min_value=tidigaste_bokningsdag,  # Tidigast dagen därpå kan bokningar göras!
            key=f"edit_date_{b_id}",  # Ger kalendern en unik namnlapp så Streamlit inte blandar ihop olika bokningar
        )  # Kalender klar
    with rcol2:  # I andra kolumnen:
        nya_vuxna = st.number_input(  # Ritar en sifferväljare med plus- och minusknappar för antal vuxna
            "Antal vuxna",  # Rubrik
            min_value=1,  # Minst 1 vuxen måste åka med (annars blir busschauffören barnvakt)
            value=int(aktuell_bokning["number_of_adults"]),  # Förifyller nuvarande antal vuxna på bokningen
            key=f"edit_adults_{b_id}",  # Unik namnlapp för denna sifferruta
        )  # Vuxenräknare klar
    with rcol3:  # I tredje kolumnen:
        nya_barn = st.number_input(  # Ritar en sifferväljare för antal barn
            "Antal barn",  # Rubrik
            min_value=0,  # Man får ha 0 barn med sig
            value=int(aktuell_bokning["number_of_children"]),  # Förifyller nuvarande antal barn
            key=f"edit_children_{b_id}",  # Unik namnlapp för barnräknaren
        )  # Barnräknare klar

    lediga_for_andring, _ = backend.hamta_lediga_platser(  # Frågar maskinrummet hur många bussplatser som är lediga på det nya datumet
        nytt_datum, exkludera_booking_id=b_id  # Ber den räkna bort vår egen bokning så vi inte tävlar mot våra egna säten!
    )  # Nu vet vi exakt hur många säten som finns kvar

    st.markdown("##### Välj destinationer för resan")  # Skriver ut en liten underrubrik (fem brädgårdar = lagom liten rubrik)
    st.caption(  # Skriver en liten förklarande hjälptext under rubriken
        "Kryssa i eller ur destinationer. Stängda mål för valt datum är inaktiverade."  # Berättar hur kryssrutorna fungerar
    )  # Hjälptext klar

    alla_aktiviteter = backend.hamta_alla_aktiviteter()  # Hämtar precis alla utflyktsmål som existerar i hela Skåne-databasen
    vald_veckodag = nytt_datum.isoweekday()  # Kollar vilken veckodag det nya datumet är (1 = Måndag ... 7 = Söndag)

    kat_col1, kat_col2, kat_col3 = st.columns(3)  # Gör tre kolumner: en för Nöjen, en för Platser och en för Fika
    nya_valda_mal = []  # Gör en tom korg där vi ska lägga alla resmål som är ikryssade

    for kat_col, kat_kod, kat_rubrik in [  # Startar en snurra (loop) som går igenom våra tre kategorier en i taget
        (kat_col1, "amusement", "Nöjen"),  # Varv 1: Kolumn 1, databas-kod "amusement", visas som "Nöjen"
        (kat_col2, "place", "Platser"),  # Varv 2: Kolumn 2, databas-kod "place", visas som "Platser"
        (kat_col3, "fika", "Fika"),  # Varv 3: Kolumn 3, databas-kod "fika", visas som "Fika" (viktigaste kategorin!)
    ]:  # Nu kör vi snurran!
        with kat_col:  # Kliver in i rätt kolumn för detta varv
            st.markdown(f"**{kat_rubrik}**")  # Skriver ut kategorins namn i fetstil (dubbla stjärnor = fetstil)
            for akt in alla_aktiviteter:  # Går igenom alla skånska utflyktsmål ett efter ett
                if akt["kategori"] == kat_kod:  # Om utflyktsmålet tillhör just den här kolumnens kategori:
                    nyckel = f"{akt['kategori']}_{akt['id']}"  # Skapar ett unikt ID-kort, t.ex. "fika_1"
                    dag_info = akt.get("oppettider", {}).get(vald_veckodag)  # Kikar i tidtabellen vad som gäller på just denna veckodag
                    ar_oppet, _, tid_visnings_txt = backend.utvardera_oppetstatus(dag_info, nytt_datum)  # Kollar om stället har öppet

                    forifyll = (  # Räknar ut om kryssrutan ska vara ikryssad från start:
                        nyckel in aktuell_bokning["valda_nycklar"] and ar_oppet  # Bara om kunden hade valt den förut OCH stället är öppet!
                    )  # Klar med förifyllnings-logiken
                    pris_txt = (  # Formaterar prislappen snyggt:
                        f"{akt['pris']:.0f} kr" if akt["pris"] > 0 else "0 kr"  # Visar t.ex. "250 kr" eller "0 kr" utan tråkiga ören
                    )  # Prislapp klar
                    status_txt = (  # Skapar en liten text med dagens öppettider:
                        f" ({tid_visnings_txt})"  # Visar t.ex. " (10:00–18:00)"
                        if (dag_info and ar_oppet)  # ...om stället faktiskt är öppet
                        else " (Stängt)"  # ...annars skriver vi kort och gott " (Stängt)"
                    )  # Öppettidstext klar

                    if st.checkbox(  # Ritar själva kryssrutan och kollar samtidigt om den är ikryssad:
                        f"{akt['plats_namn']} · {pris_txt}{status_txt}",  # Texten bredvid kryssrutan (Namn · Pris (Öppettid))
                        value=forifyll,  # Sätter om rutan ska vara ikryssad från start
                        disabled=not ar_oppet,  # Låser rutan (gråmarkerar) om stället är stängt denna dag!
                        key=f"edit_chk_{b_id}_{nyckel}_{nytt_datum}",  # Unik namnlapp så Streamlit håller isär alla kryssrutor
                    ):  # Om rutan är ikryssad...
                        nya_valda_mal.append(akt)  # ...lägg ner utflyktsmålet i vår korg med nya valda mål!

    st.divider()  # Ritar ett vågrätt streck under alla kryssrutor

    gammalt_pris = float(aktuell_bokning["total_price"])  # Hämtar vad kunden betalade förra gången (som decimaltal)
    if len(nya_valda_mal) > 0:  # Om minst ett resmål är valt räknar vi ut det nya priset:
        nytt_totalpris, _, _, totalt_nya_resenarer = backend.berakna_respris(  # Ber maskinrummet räkna ut vad den ändrade resan kostar
            aktuell_bokning["kund_kommun_id"], nya_valda_mal, nya_vuxna, nya_barn  # Skickar med hemkommun, nya mål och antal vuxna/barn
        )  # Vi får tillbaka nya totalpriset och totala antalet resenärer
    else:  # Om inga mål är ikryssade just nu:
        nytt_totalpris = 0.0  # Sätt nytt pris till 0 så länge
        totalt_nya_resenarer = nya_vuxna + nya_barn  # Räkna ihop antal valda resenärer

    mellanskillnad = round(nytt_totalpris - gammalt_pris, 2)  # Räknar ut skillnaden mellan nytt och gammalt pris, avrundat till ören

    pcol1, pcol2 = st.columns(2)  # Gör två kolumner längst ner för prisjämförelse, betalsätt och avbokningsknapp
    with pcol1:  # I vänstra priskolumnen:
        st.write(f"**Tidigare betalt:** {gammalt_pris:.2f} kr")  # Visar vad som redan är betalt med två decimaler
        st.write(f"**Nytt totalpris:** {nytt_totalpris:.2f} kr")  # Visar vad den nya resan kostar totalt
        if mellanskillnad > 0:  # Om resan har blivit dyrare:
            st.warning(f"**Att betala extra:** +{mellanskillnad:.2f} kr")  # Visa gul ruta med hur mycket extra som ska betalas
        elif mellanskillnad < 0:  # Om resan har blivit billigare:
            st.success(f"**Återbetalning:** {abs(mellanskillnad):.2f} kr")  # Visa grön glädjeruta med hur mycket pengar kunden får tillbaka!
        else:  # Om det kostar exakt lika mycket som förut:
            st.info("**Prisskillnad:** 0.00 kr")  # Visa blå ruta: jämt skägg!

    with pcol2:  # I högra kolumnen:
        betal_metod = st.selectbox(  # Ritar en rullgardinsmeny för hur man vill betala (eller få tillbaka pengar)
            "Betalsätt för tillägg / återbetalning",  # Rubrik på menyn
            ["Swish", "Kort", "Klarna"],  # De tre betalningsalternativen
            key=f"edit_pay_{b_id}",  # Unik namnlapp för menyn
        )  # Betalsätt valt

        if st.button(  # Ritar avbokningsknappen under "Betalsätt" och till höger om "Prisskillnad":
            "Avboka resa",  # Text på avbokningsknappen
            type="secondary",  # Sekundärknapp med tydlig kant
            use_container_width=True,  # Lika bred som betalsättsmenyn ovanför
            key=f"cancel_btn_{b_id}",  # Unikt ID för knappen
        ):  # Om kunden klickar på "Avboka resa":
            ok_avbok, fel_avbok = backend.avboka_bokning_i_db(  # Skickar avbokningen till maskinrummet (backend)
                booking_id=b_id,  # Bokningsnumret som ska avbokas
                aterbetalning_belopp=gammalt_pris,  # Hela det betalda beloppet återbetalas
                payment_method=betal_metod,  # Sker via det betalsätt som är valt ovanför
            )  # Backend svarar med om avbokningen gick igenom
            if ok_avbok:  # Om avbokningen lyckades:
                st.session_state.boknings_meddelande = (  # Spara ett bekräftelsemeddelande i korttidsminnet
                    f"Bokning #{b_id} har avbokats! En återbetalning på {gammalt_pris:.2f} kr via {betal_metod} är registrerad."  # Texten som visas
                )  # Meddelande klart
                st.rerun()  # Ladda om sidan så popup-rutan stängs och meddelandet visas!
            else:  # Om något gick fel:
                st.error(f"Kunde inte avboka resan: {fel_avbok}")  # Visa felmeddelande

    if len(nya_valda_mal) == 0:  # Om kunden har kryssat ur rubbet så korgen är helt tom:
        st.warning("Du måste ha minst en öppen destination vald för att spara ändringar i resan.")  # Visa en gul varningsruta
        return  # Stoppa spara-knappen tills kunden kryssar i minst ett mål

    if totalt_nya_resenarer > lediga_for_andring:  # Om kunden försöker klämma in fler personer än det finns säten på bussen:
        st.error(  # Visa en röd stopp-ruta!
            f"Det finns tyvärr bara **{lediga_for_andring} platser tillgängliga** på bussen den {nytt_datum} "  # Berättar hur många platser som finns
            f"(du har valt {totalt_nya_resenarer} resenärer)."  # Och hur många kunden försökte boka
        )  # Stänger felrutan
        return  # Avbryter så man inte kan råka överboka bussen

    knapp_text = (  # Bestämmer vad det ska stå på spara-knappen beroende på priset:
        f"Betala mellanskillnad ({mellanskillnad:.2f} kr) & spara"  # Text om kunden ska betala mer
        if mellanskillnad > 0  # (gäller när mellanskillnaden är över noll)
        else (  # Annars kollar vi...
            f"Spara ändring & återbetala {abs(mellanskillnad):.2f} kr"  # Text om kunden ska få pengar tillbaka
            if mellanskillnad < 0  # (gäller när mellanskillnaden är under noll)
            else "Spara ändringar"  # Text om priset är oförändrat
        )  # Klar med den inre kontrollen
    )  # Knapptexten är färdigsnickrad!

    if st.button(knapp_text, type="primary", use_container_width=True):  # Ritar den stora spara-knappen och kollar om kunden klickar:
        ok, fel = backend.uppdatera_bokning_i_db(  # Skickar alla nya uppgifter till maskinrummet för att skriva över i databasen
            booking_id=b_id,  # Vilket bokningsnummer som ändras
            package_id=aktuell_bokning["package_id"],  # Vilket resepaket som ska uppdateras
            route_id=aktuell_bokning["route_id"],  # Vilken bussrutt som ska uppdateras
            nya_mal=nya_valda_mal,  # De nya utflyktsmålen
            nytt_datum=nytt_datum,  # Det nya avresedatumet
            adults=nya_vuxna,  # Nytt antal vuxna
            children=nya_barn,  # Nytt antal barn
            nytt_totalpris=nytt_totalpris,  # Det nya totalpriset
            mellanskillnad=mellanskillnad,  # Hur mycket som ska dras eller betalas tillbaka
            payment_method=betal_metod,  # Valda betalsättet (Swish, Kort eller Klarna)
        )  # Maskinrummet svarar med "ok" (True/False) och eventuellt "fel"
        if ok:  # Om uppdateringen i databasen gick som en dans:
            if mellanskillnad > 0:  # Om kunden betalade extra:
                st.session_state.boknings_meddelande = (  # Spara ett kvittomeddelande i korttidsminnet
                    f"Bokning #{b_id} har uppdaterats! Mellanskillnaden på {mellanskillnad:.2f} kr har betalats med {betal_metod}."  # Texten som ska visas
                )  # Meddelande klart
            elif mellanskillnad < 0:  # Om kunden fick pengar tillbaka:
                st.session_state.boknings_meddelande = (  # Spara återbetalningsmeddelande i minnet
                    f"Bokning #{b_id} har uppdaterats! En återbetalning på {abs(mellanskillnad):.2f} kr via {betal_metod} är registrerad."  # Texten som ska visas
                )  # Meddelande klart
            else:  # Om det inte kostade något extra:
                st.session_state.boknings_meddelande = (  # Spara ett vanligt uppdateringsmeddelande
                    f"Bokning #{b_id} har uppdaterats utan prisskillnad!"  # Texten som ska visas
                )  # Meddelande klart
            st.rerun()  # Ladda om sidan så popup-rutan försvinner och det gröna meddelandet visas!
        else:  # Om databasen satte kaffet i vrångstrupen:
            st.error(f"Kunde inte uppdatera bokningen: {fel}")  # Visa vad som gick snett i en röd ruta


# ---------  # Nytt avsnitt!
# Betalningshistorik och kvitton (Modal)  # Popup-rutan där man kan beundra alla sina kvitton
# ---------  # Staket klart
@st.dialog("Betalningshistorik & Kvitton", width="large")  # Gör en bred popup-ruta för kvitton
def visa_kvitto_modal():  # Startar receptet för kvitto-fönstret
    user = st.session_state.user  # Kollar i minnet vem som är inloggad
    is_admin = user["customer_id"] == 1  # Kollar om det är chefen (Kund #1) som är inloggad

    if is_admin:  # Om det är administratören:
        st.caption(  # Skriv ut en liten upplysningstext högst upp
            "Adminvy: Visar samtliga registrerade betalningar och kvitton i systemet."  # Förklarar att admin ser precis allt
        )  # Text klar
    else:  # Om det är en helt vanlig dödlig kund:
        st.caption(  # Skriv en personlig liten text
            f"Visar betalningar och kvitton för {user['first_name']} {user['last_name']} (Kund-ID #{user['customer_id']})."  # Visar kundens namn och ID
        )  # Text klar

    kvitton = backend.hamta_betalningshistorik(  # Ber maskinrummet hämta alla kvitton från databasen
        user["customer_id"], is_admin=is_admin  # Skickar med kund-ID och admin-status
    )  # Nu har vi listan med kvitton

    if not kvitton:  # Om kunden inte har köpt en enda resa än:
        st.info("Det finns inga tidigare betalningar eller kvitton registrerade.")  # Visa en blå ruta som berättar att kvittolådan är tom
        return  # Stanna här!

    for k in kvitton:  # Går igenom varje kvitto ("k") i listan, ett i taget:
        betal_status = k["payment_status"] if k["payment_status"] else "Paid"  # Hämtar betalstatus (eller gissar "Paid" om det saknas)
        betal_metod = (  # Kollar vilket betalsätt som användes:
            k["payment_method"] if k["payment_method"] else "Direktbetalning"  # Hämtar t.ex. Swish/Kort, eller skriver "Direktbetalning"
        )  # Betalmetod klar
        belopp = (  # Hämtar beloppet som betalades på just detta kvitto:
            float(k["amount"])  # Gör om beloppet till ett decimaltal
            if k["amount"] is not None  # ...om det finns ett belopp registrerat i betalningstabellen
            else float(k["total_price"])  # ...annars tar vi hela bokningens pris som reservplan
        )  # Belopp klart
        datum_tid = k["payment_date"] if k["payment_date"] else k["booking_date"]  # Tar betalningsdatumet (eller bokningsdatumet i nödfall)
        datum_str = (  # Gör om datumet till snygg läsbar text:
            datum_tid.strftime("%Y-%m-%d %H:%M")  # Formaterar som ÅÅÅÅ-MM-DD TT:MM
            if hasattr(datum_tid, "strftime")  # ...om det är ett riktigt datum-objekt
            else str(datum_tid)  # ...annars gör vi bara om det till vanlig text rakt av
        )  # Datumtext klar
        kvitto_nr = k["payment_id"] if k["payment_id"] else k["booking_id"]  # Använder betalnings-ID som kvittonummer (eller boknings-ID som reserv)

        typ_etikett = (  # Kollar om kvittot är en betalning eller en återbetalning:
            f"Återbetalning: {belopp:.2f} kr"  # Om beloppet är på minus skriver vi "Återbetalning"
            if belopp < 0  # (minusbelopp = pengar tillbaka till kunden)
            else f"{belopp:.2f} kr"  # Annars skriver vi bara summan i kronor
        )  # Typ-etikett klar
        kund_info = (  # Om man är admin vill man ju se vems kvitto det är:
            f" · {k['first_name']} {k['last_name']}" if is_admin else ""  # Lägger till kundens namn för admin, annars tomt
        )  # Kundinfo klar

        rubrik = f"Kvitto #{kvitto_nr} · {typ_etikett} ({betal_metod}) · Avresa {k['travel_date']}{kund_info}"  # Bygger ihop hela rubriken för dragspelsrutan

        with st.expander(rubrik, expanded=False):  # Skapar en utfällbar dragspelsruta (stängd från start så det inte blir rörigt)
            kcol1, kcol2 = st.columns(2)  # Delar insidan av dragspelet i två kolumner
            with kcol1:  # Vänstra kolumnen på kvittot:
                st.markdown("**Resedetaljer**")  # Fet rubrik
                st.write(f"Bokningsnummer: `#{k['booking_id']}`")  # Skriver ut bokningsnumret i en liten grå kod-ruta
                if is_admin:  # Om chefen tittar:
                    st.write(  # Skriv även ut vem kunden är och kundens ID-nummer
                        f"Kund: {k['first_name']} {k['last_name']} (`#{k['customer_id']}`)"  # Namn och ID
                    )  # Kundrad klar
                st.write(f"Paket: {k['package_name']}")  # Skriver ut vad resepaketet kallas
                st.write(f"Besöksmål: {k['resmal'] or 'Ej angivet'}")  # Skriver ut alla valda besöksmål i resan
                st.write(f"Rutt: {k['start_kommun']} → {k['slut_kommun']}")  # Visar startkommun, en snygg pil och slutkommun
                st.write(f"Avresedatum: {k['travel_date']}")  # Visar vilket datum bussen rullar
                st.write(  # Skriver ut hur många som ska åka med
                    f"Resenärer: {k['number_of_adults']} vuxna, {k['number_of_children']} barn"  # Antal vuxna och barn
                )  # Resenärsrad klar

            with kcol2:  # Högra kolumnen på kvittot:
                st.markdown("**Betalningsspecifikation**")  # Fet rubrik för pengadetaljerna
                st.write(f"Kvittonummer: `#{kvitto_nr}`")  # Skriver ut kvittonumret
                st.write(f"Transaktionsdatum: {datum_str}")  # När betalningen gjordes på minuten när
                st.write(f"Betalsätt: {betal_metod}")  # Swish, Kort eller Klarna
                st.write(f"Betalningsstatus: {betal_status}")  # Att det är betalt och klart ("Paid")
                st.write(f"Bokningsstatus: {k['booking_status']}")  # Att bokningen är bekräftad ("Confirmed")
                st.write(f"Bokningens totalpris: {k['total_price']:.2f} kr")  # Vad hela kalaset kostar totalt


# ---------  # Dags för smink och kläder!
# Bakgrund & Modern 2026 CSS (Utan skuggor, smal & mobilanpassad)  # CSS är språket som bestämmer färger, typsnitt och runda hörn
# ---------  # Staket klart
BASE_DIR = Path(__file__).parent  # Tar reda på exakt vilken mapp på datorn som den här filen bor i

def get_base64_image(image_name):  # Ett litet recept som letar upp bakgrundsbilden och gör om den till textkod
    bas_namn = Path(image_name).stem  # Plockar ut filnamnet utan punkt och ändelse (t.ex. "bakgrund" ur "bakgrund.jpg")
    filer_i_mappen = {f.name.lower(): f for f in BASE_DIR.iterdir() if f.is_file()}  # Gör en lista på alla filer i vår mapp (med små bokstäver så vi inte missar ".JPG")
    for namn in [image_name, f"{image_name}.jpg", f"{bas_namn}.jpg", f"{bas_namn}.jpeg", f"{bas_namn}.png", f"{bas_namn}.webp"]:  # Testar alla tänkbara bildformat
        matchad_fil = filer_i_mappen.get(namn.lower())  # Kollar om just den här stavningen finns i mappen
        if matchad_fil:  # Om vi fick napp och hittade bildfilen:
            return base64.b64encode(matchad_fil.read_bytes()).decode()  # Läser in bilden och förvandlar den till en lång Base64-textsträng
    print(f"[VARNING] Hittade inte bakgrundsbilden '{image_name}' i {BASE_DIR}")  # Om bilden är spårlöst försvunnen, skvallra i terminalen!
    return ""  # Skicka tillbaka tom text om ingen bild hittades

bg_img = get_base64_image("bakgrund.jpg")  # Kör receptet ovan för att hämta vår skånska bakgrundsbild
bg_css = (  # Förbereder CSS-regeln för bakgrunden:
    f'background-image: linear-gradient(rgba(15, 23, 42, 0.5), rgba(15, 23, 42, 0.5)), url("data:image/jpeg;base64,{bg_img}");'  # Lägger en halvmörk slöja över bilden så vit text syns bra
    if bg_img  # ...om vi faktiskt hittade bakgrundsbilden
    else "background-color: #0F172A;"  # ...annars målar vi bara bakgrunden mörkblå som reservplan!
)  # Bakgrundsregeln är klar

st.markdown(  # Nu sprutar vi in vår egen designkod (CSS) direkt i webbsidan:
    f"""
    <style> /* Öppnar stil-avdelningen där vi bestämmer hur allt ska se ut */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'); /* Hämtar det moderna typsnittet "Inter" från Google */

    html, body, [class*="css"] {{ /* Väljer precis all text på hela hemsidan */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; /* Tvingar allt att använda det snygga typsnittet Inter */
    }} /* Klar med typsnittet */

    /* Nollställ alla skuggor globalt */ /* Vi vill ha en helt platt och ren 2026-design utan luddiga skuggor */
    *, *::before, *::after {{ /* Väljer varenda liten pinal på hela webbsidan */
        box-shadow: none !important; /* Förbjuder skuggor runt rutor och knappar */
        text-shadow: none !important; /* Förbjuder skuggor bakom bokstäver */
    }} /* Alla skuggor är nu officiellt utrotade */

    /* Bakgrund */ /* Här stylar vi själva huvudfönstret */
    .stApp {{ /* Väljer hela Streamlit-appen */
        {bg_css} /* Klistrar in vår skånska bakgrundsbild (eller reservfärgen) */
        background-size: cover; /* Sträcker ut bilden så den täcker hela skärmen utan glipor */
        background-position: center; /* Centrerar bilden så det finaste syns i mitten */
        background-attachment: fixed; /* Spikar fast bakgrunden så den ligger still när man scrollar! */
    }} /* Bakgrunden är klar */

    header[data-testid="stHeader"] {{ /* Väljer Streamlits inbyggda toppmeny */
        background: transparent !important; /* Gör den genomskinlig så den inte täcker vår fina himmel i bakgrundsbilden */
    }} /* Topplist klar */

    /* Smal, centrerad och mobilanpassad behållare */ /* Gör så sidan ser ut som en modern app i mitten av skärmen */
    .block-container {{ /* Väljer huvudlådan där allt vårt innehåll ligger */
        max-width: 680px !important; /* Sätter maxbredd till 680 pixlar (lagom smalt och läsvänligt!) */
        padding-top: 1.4rem !important; /* Lite luft högst upp mot skärmkanten */
        padding-bottom: 4rem !important; /* Gott om luft längst ner så man kan scrolla klart */
        padding-left: 0.85rem !important; /* Lite luft till vänster */
        padding-right: 0.85rem !important; /* Lite luft till höger */
        margin: 0 auto !important; /* Centrerar hela lådan mitt på skärmen */
    }} /* Huvudlådan klar */

    /* Rubrik i kolumn 1+2 direkt på bakgrunden */ /* Stylar huvudrubriken "Skånska Upplevelser" */
    .hero-title {{ /* Väljer huvudrubriken */
        color: #FFFFFF !important; /* Kritvit färg så den lyser mot bakgrunden */
        font-size: clamp(1.35rem, 4vw, 1.75rem) !important; /* Smart textstorlek som krymper på mobilen och växer på datorn */
        font-weight: 700 !important; /* Rejält fetstilad */
        letter-spacing: -0.03em !important; /* Klämmer ihop bokstäverna pyttelite för en modern look */
        margin: 0 !important; /* Ingen onödig marginal runt rubriken */
        line-height: 1.15 !important; /* Lagom avstånd om rubriken bryts på två rader */
    }} /* Huvudrubrik klar */
    .hero-meta {{ /* Väljer raden under rubriken (den som visar hur många bussplatser som är kvar) */
        color: rgba(255, 255, 255, 1.0) !important; /* Nästan helt vit text (88% synlig) */
        font-size: 0.8rem !important; /* Lite mindre och nättare textstorlek */
        font-weight: 500 !important; /* Halvfet text så den är lättläst */
        margin-top: 0.25rem !important; /* En liten glipa upp till huvudrubriken */
    }} /* Bussplats-texten klar */

    /* Kompakt styling för datumväljare (kolumn 3) och login-popover (kolumn 4) */ /* Gör kalendern och logga-in-knappen snygga */
    div[data-testid="stDateInput"] div[data-baseweb="input"] {{ /* Väljer rutan runt datumväljaren */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        border: 1px solid #E2E8F0 !important; /* Tunn ljusgrå kantlinje */
        border-radius: 10px !important; /* Mjukt rundade hörn */
        min-height: 40px !important; /* Minst 40 pixlar hög så den matchar logga-in-knappen */
    }} /* Datumruta klar */
    div[data-testid="stDateInput"] input {{ /* Väljer själva datumtexten inuti kalenderrutan */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        color: #0F172A !important; /* Mörkblå/svart textfärg */
        font-size: 0.85rem !important; /* Lagom kompakt textstorlek */
        font-weight: 500 !important; /* Halvfet stil */
        padding: 0.4rem 0.6rem !important; /* Lite luft runt siffrorna inuti rutan */
    }} /* Datumtext klar */
    div[data-testid="stPopover"] > button {{ /* Väljer "Logga in"-knappen högst upp till höger */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        color: #0F172A !important; /* Mörk text */
        border: 1px solid #E2E8F0 !important; /* Ljusgrå ram */
        border-radius: 10px !important; /* Rundade hörn (10 pixlar) */
        min-height: 40px !important; /* Exakt samma höjd som datumväljaren bredvid! */
        font-size: 0.85rem !important; /* Samma textstorlek som datumet */
        font-weight: 600 !important; /* Lite extra fet text */
        padding: 0.4rem 0.75rem !important; /* Lagom med vaddering inuti knappen */
    }} /* Logga-in-knapp klar */
    div[data-testid="stPopover"] > button p {{ /* Väljer texten inuti Logga-in-knappen */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        color: #0F172A !important; /* Säkerställer att texten håller sig mörk */
        
        font-size: 0.85rem !important; /* Och behåller rätt storlek */
        font-weight: 600 !important; /* Och rätt fetstil */
    }} /* Knapptext klar */

    /* Sökfält */ /* Stylar sökrutan där man letar efter fika och nöjen */
    div[data-testid="stTextInput"] input {{ /* Väljer alla textrutor (inklusive sökfältet) */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        color: #0F172A !important; /* Mörk text när man skriver */
        border: 1px solid #E2E8F0 !important; /* Tunn grå ram */
        border-radius: 10px !important; /* Samma runda hörn som resten av appen */
        padding: 0.55rem 0.8rem !important; /* Skönt med utrymme runt texten man skriver */
    }} /* Sökfält klart */


   /* Hela fliksektionen nederdelen bakom kort och bilder */ /* Den stora sandfärgade lådan som håller i flikarna och korten */
    div[data-testid="stTabs"] {{ /* Väljer hela flik-området */
        background-color: #c2b9ac !important; /* Varm, jordnära beige/grå bakgrundsfärg */
        border: 1px solid rgba(0, 0, 0, 1.0) !important; /* En krispig vit ram runt hela boxen */
        border-radius: 10px !important; /* Rundade hörn */
        padding: 1.0rem !important; /* Luft mellan kanten och korten inuti */
    }} /* Flik-lådan klar */

    /* Flikraden (Nöjen, Platser, Fika, Bokning) */ /* Själva menyraden där man byter flik */
    div[data-baseweb="tab-list"] {{ /* Väljer raden med flik-knappar */
        background-color: #F0E2C3 !important; /* Ljus sand/vaniljfärgad bakgrund */
        border: 1px solid rgba(255, 255, 255, 1.0) !important; /* Vit kantlinje */
        border-radius: 12px !important; /* Runda fina hörn */
        padding: 0.3rem !important; /* Lite luft runt knapparna */
        gap: 0.25rem !important; /* Litet mellanrum mellan varje flik-knapp */
        overflow-x: auto !important; /* Tillåter att man sveper i sidled på små mobilskärmar */
        overflow-y: hidden !important; /* Förbjuder konstig scrollning på höjden i menyraden */
        flex-wrap: nowrap !important; /* Tvingar alla flikar att ligga på en och samma rad */
        scrollbar-width: none !important; /* Gömmer den fula rullningslisten i Firefox */
        margin-bottom: 0.85rem !important; /* Luft ner till första utflyktskortet */
    }} /* Flikraden klar */
    div[data-baseweb="tab-list"]::-webkit-scrollbar {{ /* Väljer rullningslisten i Chrome/Safari */
        display: none !important; /* Gömmer den där också! */
    }} /* Rullningslist borta */

    div[data-baseweb="tab-highlight"], /* Väljer Streamlits inbyggda röda streck under flikar */
    div[data-baseweb="tab-border"] {{ /* Och den inbyggda linjen under flikraden */
        display: none !important; /* Tar bort båda två så vår egen design får glänsa ostört */
    }} /* Gamla streck borta */

    button[data-baseweb="tab"] {{ /* Väljer varje enskild flik-knapp (Nöjen, Platser osv.) */
        flex: 1 0 auto !important; /* Låter knapparna dela broderligt på utrymmet */
        white-space: nowrap !important; /* Förbjuder texten på knappen från att brytas på två rader */
        background-color: transparent !important; /* Genomskinlig bakgrund när fliken inte är vald */
        border: none !important; /* Ingen kantlinje runt själva knappen */
        border-radius: 9px !important; /* Rundade hörn */
        padding: 0.5rem 0.9rem !important; /* Lagom klick-yta */
        margin: 0 !important; /* Ingen extra marginal */
        transition: background-color 0.15s ease !important; /* Mjuk övergång när man klickar */
    }} /* Flik-knapp klar */

    button[data-baseweb="tab"] p {{ /* Väljer texten på flik-knapparna */
        color: #F0E2C3 !important; /* Färgsätter fliktexten */
        font-size: 0.88rem !important; /* Lagom textstorlek */
        font-weight: 500 !important; /* Halvfet stil */
        margin: 0 !important; /* Ingen marginal */
    }} /* Fliktext klar */

    /* Aktiv flik */ /* Så här ser fliken ut när man har klickat på den */
    button[data-baseweb="tab"][aria-selected="true"] {{ /* Väljer just den flik som är aktiv just nu */
        background-color: #F0E2C3 !important; /* Får en ljus sandfärgad bakgrund */
    }} /* Aktiv flikbakgrund klar */

    button[data-baseweb="tab"][aria-selected="true"] p {{ /* Väljer texten på den aktiva fliken */
        color: #000000 !important; /* Kolsvart text så man tydligt ser vilken flik man är på */
        font-weight: 600 !important; /* Och lite fetare stil! */
    }} /* Aktiv fliktext klar */


    div[data-testid="stVerticalBlockBorderWrapper"] p, /* Väljer brödtext inuti våra inramade kort */
    div[data-testid="stVerticalBlockBorderWrapper"] span, /* Och små textsnuttar inuti korten */
    div[data-testid="stVerticalBlockBorderWrapper"] label, /* Och etiketter vid kryssrutor */
    div[data-testid="stVerticalBlockBorderWrapper"] h1, /* Och stora rubriker */
    div[data-testid="stVerticalBlockBorderWrapper"] h2, /* Och mellanstora rubriker */
    div[data-testid="stVerticalBlockBorderWrapper"] h3, /* Och mindre rubriker */
    div[data-testid="stVerticalBlockBorderWrapper"] h4 {{ /* Och småkort-rubriker */
        color: #000000 !important; /* Gör all denna text tydligt svart så den är superlätt att läsa! */
    }} /* Kort-texter klara */

    /* Bild-styling i kort */ /* Hur bilderna på t.ex. Ales Stenar och Tosselilla ska se ut */
    .card-img {{ /* Väljer bilden på ett öppet besöksmål */
        width: 100%; /* Täcker hela kortets bredd */
        height: 190px; /* Exakt 190 pixlar hög så alla kort blir lika prydliga */
        object-fit: cover; /* Beskär bilden smart så den inte ser ihoptryckt ut */
        border-radius: 10px; /* Runda fina hörn på bilden */
      /* En tom rad där koden tar ett djupt andetag */
        margin-bottom: 0.65rem; /* Lite luft ner till rubriken under bilden */
        display: block; /* Gör bilden till ett eget block */
    }} /* Öppen bild klar */
    .card-img-closed {{ /* Väljer bilden på ett besöksmål som har STÄNGT valt datum */
        width: 100%; /* Full bredd */
        height: 190px; /* Samma höjd (190 pixlar) */
        object-fit: cover; /* Smart beskärning */
        border-radius: 10px; /* Runda hörn */
        filter: grayscale(100%); /* Trolleri! Gör bilden helt svartvit för att visa att det är stängt */
        opacity: 0.55; /* Gör den dessutom lite blek/genomskinlig */
        margin-bottom: 0.65rem; /* Luft ner till rubriken */
        display: block; /* Eget block */
    }} /* Stängd bild klar */

    /* Status- och informationsmärken (Badges) */ /* De små färgglada etiketterna för kommun, pris och öppettider */
    .badge-row {{ /* Raden som håller i etiketterna */
        display: flex; /* Lägger etiketterna på rad bredvid varandra */
        flex-wrap: wrap; /* Tillåter dem att hoppa ner på ny rad om skärmen är smal */
        gap: 0.4rem; /* Litet mellanrum mellan varje etikett */
        align-items: center; /* Centrerar dem i höjdled */
        margin: 0.35rem 0 0.6rem 0; /* Luft över och under etikettraden */
    }} /* Etikettrad klar */
    .badge {{ /* Grundformen för alla små etiketter */
        display: inline-flex; /* Gör etiketten till en nätt liten ruta runt texten */
        align-items: center; /* Texten i mitten på höjden */
        padding: 0.22rem 0.6rem; /* Lagom med luft inuti etiketten */
        border-radius: 6px; /* Lite rundade hörn */
        font-size: 0.78rem; /* Lagom liten textstorlek */
        font-weight: 600; /* Halvfet text */
        line-height: 1.2; /* Kompakt radhöjd */
    }} /* Grund-etikett klar */
    .badge-neutral {{ /* Etiketten som visar kommunens namn (t.ex. "Ystad") */
        background-color: #3B281F; /* Mörk kaffebrun bakgrund */
        color: #F3E9E4 !important; /* Ljus gräddvit text */
        border: 1px solid #543A2E; /* Diskret brun ram */
    }} /* Kommun-etikett klar */
    .badge-price {{ /* Etiketten som visar priset (t.ex. "Fri entré") */
        background-color: #FFFFFF; /* Krispigt vit bakgrund */
        color: #1E40AF !important; /* Klarblå text */
        border: 1px solid #000000; /* Tydlig svart kantlinje */
    }} /* Pris-etikett klar */
    .badge-open {{ /* Etiketten som visar när stället är ÖPPET */
        background-color: #BAFFC9; /* Glad pastellgrön bakgrund */
        color: #065F46 !important; /* Mörkgrön text */
        border: 1px solid #000000; /* Svart kantlinje */
    }} /* Öppet-etikett klar */
    .badge-closing {{ /* Etiketten som visar substatus "Stänger inom kort" (2h före stängning) */
        background-color: #FEF08A; /* Varm gul/orange varningsbakgrund */
        color: #854D0E !important; /* Mörkbrun/gul text */
        border: 1px solid #000000; /* Svart kantlinje */
    }} /* Stänger-inom-kort-etikett klar */
    .badge-closed {{ /* Etiketten som varnar för att stället är STÄNGT */
        background-color: #FAA0A0; /* Rosa/röd varningsbakgrund */
        color: #000000; /* Svart text */
        border: 1px solid #000000; /* Svart kantlinje */
    }} /* Stängt-etikett klar */

    .card-title {{ /* Rubriken på varje besöksmål (t.ex. "Tosselilla") */
        font-size: 1.0rem; /* Tydlig storlek */
        font-weight: 400; /* Normal tjocklek */
        color: #000000 !important; /* Svart färg */
        margin: 0; /* Ingen extra marginal */
        letter-spacing: -0.01em; /* Lätt ihopdragna bokstäver */
    }} /* Kort-titel klar */
    .card-desc {{ /* Beskrivningstexten som berättar om utflyktsmålet */
        font-size: 0.9rem; /* Behaglig lässtorlek */
        color: #000000 !important; /* Svart text */
        line-height: 1.5; /* Luftigt mellan raderna så man inte blir vindögd */
        margin-bottom: 0.65rem; /* Lite luft ner till kryssrutan */
    }} /* Kort-beskrivning klar */

    /* Kompakta expanders för öppettider */ /* Dragspelsrutorna längst ner på varje kort */
    div[data-testid="stExpander"] {{ /* Väljer hela dragspelsrutan */
        background-color: #c9c1b5 !important; /* Matchande sandgrå bakgrundsfärg */
        border: 1px solid #000000 !important; /* Tunn svart ram */
        border-radius: 10px !important; /* Runda hörn */
        margin-top: 0.4rem !important; /* Lite luft upp till kryssrutan */
    }} /* Dragspelsruta klar */
    div[data-testid="stExpander"] summary {{ /* Väljer rubrikraden man klickar på för att fälla ut */
        background-color: transparent !important; /* Genomskinlig bakgrund */
        padding: 0.45rem 0.75rem !important; /* Lagom klick-utrymme */
    }} /* Dragspels-rubrikrad klar */
    div[data-testid="stExpander"] summary p {{ /* Väljer texten "Visa öppettider (Mån–Sön)" */
        color: #000000 !important; /* Svart text */
        font-size: 0.84rem !important; /* Kompakt storlek */
        font-weight: 600 !important; /* Halvfet stil */
    }} /* Dragspelstext klar */

    /* Knappar utan skuggor */ /* Stylar vanliga knappar i appen */
    button[kind="primary"] {{ /* Väljer huvudknappar (t.ex. "Slutför bokning & betala") */
        background-color: #0F172A !important; /* Mörk marinblå/svart bakgrund */
        color: #FFFFFFF !important; /* Vit text på knappen */
        border: 1px solid #0F172A !important; /* Mörk kantlinje */
        border-radius: 10px !important; /* Runda hörn */
        font-weight: 600 !important; /* Tydlig fet text */
    }} /* Huvudknappar klara */
    button[kind="secondary"] {{ /* Väljer vanliga sekundära knappar */
        background-color: #FFFFFF !important; /* Vit bakgrund */
        color: #0F172A !important; /* Mörk text */
        border: 1px solid #CBD5E1 !important; /* Ljusgrå kantlinje */
        border-radius: 10px !important; /* Runda hörn */
        font-weight: 500 !important; /* Halvfet text */
    }} /* Sekundärknappar klara */

    

   
    </style> <!-- Stänger stil-avdelningen -->
    """,  # Här tar vår stora design-text slut
    unsafe_allow_html=True,  # Ger Streamlit tillåtelse att tolka vår designkod som riktig webbkod (HTML/CSS)
)  # Nu är hela sidan stylad till tänderna!


# ---------  # Dags att bygga sidhuvudet högst upp!
# Huvudrad i 4-kolumners struktur: [Kolumn 1+2: Rubrik] [Kolumn 3: Datum] [Kolumn 4: Login]  # Ritningen för toppen av sidan
# ---------  # Staket klart
col_rubrik, col_datum, col_login = st.columns(  # Skapar tre block där första blocket är dubbelt så brett som de andra två ([2, 1, 1])
    [2, 1, 1], vertical_alignment="center"  # Ser till att rubrik, datum och logga-in-knapp hamnar i exakt samma vågräta linje
)  # Kolumnerna är redo!

with col_datum:  # Vi börjar med att lägga in datumväljaren i mitten-högra kolumnen:
    nytt_datum = st.date_input(  # Ritar kalenderrutan där man väljer när man vill åka
        "Avresedatum",  # Osynlig etikett (för skärmläsare)
        value=st.session_state.valt_datum,  # Visar datumet som ligger i korttidsminnet (default på dagens datum)
        min_value=date.today(),  # Kalendern kan stå på dagens datum som default
        label_visibility="collapsed",  # Gömmer texten "Avresedatum" ovanför rutan så det blir superkompakt
    )  # Kalender klar
    if nytt_datum != st.session_state.valt_datum:  # Om besökaren nyss bytte till ett nytt datum i kalendern:
        uppdatera_valt_datum(nytt_datum)  # Uppdatera valt datum och kontrollera valda resmåls öppettider

lediga_platser, _ = backend.hamta_lediga_platser(st.session_state.valt_datum)  # Frågar maskinrummet hur många bussplatser som är kvar valt datum
veckodag_nu = st.session_state.valt_datum.isoweekday()  # Tar fram veckodagens nummer (1-7) för valt datum
veckodag_namn = backend.VECKODAGAR[veckodag_nu]  # Översätter numret till svenska (t.ex. 6 -> "Lördag")
bussen_redan_ute = st.session_state.valt_datum <= date.today()  # På dagens datum är bussen redan ute och kör!

with col_rubrik:  # Kliver in i den breda vänstra kolumnen för att skriva ut titel och bussplatser:
    if bussen_redan_ute:  # Om kalendern står på dagens datum:
        plats_text = f"{veckodag_namn} · Bussen är ute och kör (bokas tidigast imorgon)"  # Berättar att bussen redan rullar idag
    elif lediga_platser > 0:  # Om det är ett framtida datum och det finns plats kvar:
        plats_text = f"{veckodag_namn} · {lediga_platser} av {backend.MAX_BUSS_PLATSER} bussplatser kvar"  # Exempel: "Lördag · 5 av 50 bussplatser kvar"
    else:  # Om bussen är fullbokad:
        plats_text = f"{veckodag_namn} · Bussen är fullbokad"  # Skriver att bussen är smockfull!

    st.markdown(  # Skriver ut rubriken och platstexten med vår snygga CSS-design:
        f"""
        <div> <!-- En osynlig hållare runt rubriken -->
            <h1 class="hero-title">Skånska Upplevelser</h1> <!-- Själva huvudrubriken i stor vit stil -->
            <div class="hero-meta">{plats_text}</div> <!-- Bussplats-infon precis under -->
        </div> <!-- Stänger hållaren -->
        """,  # HTML-blocket klart
        unsafe_allow_html=True,  # Tillåter vår HTML-kod att ritas ut
    )  # Rubrik-kolumnen är klar!

with col_login:  # Kliver in i kolumnen längst till höger (inloggning och kontomeny):
    if st.session_state.user is None:  # Om INGEN är inloggad just nu:
        with st.popover("Logga in", use_container_width=True):  # Ritar en knapp "Logga in" som fäller ut en liten meny när man klickar
            st.markdown("**Kundinloggning**")  # Fet rubrik inuti menyn
            email_input = st.text_input(  # Textruta där man skriver sin e-post
                "E-post", placeholder="dinmail@exempel.se"  # Etikett och exempeltext
            )  # E-postruta klar
            pass_input = st.text_input("Lösenord", type="password")  # Lösenordsruta (med hemliga prickar)

            if st.button("Logga in", type="primary", use_container_width=True):  # Om användaren trycker på Logga-in-knappen inuti menyn:
                user_data = backend.verifiera_inloggning(  # Fråga maskinrummet om e-post och lösenord stämmer i databasen
                    email_input, pass_input  # Skickar med det användaren skrev in
                )  # Får tillbaka kundens profil (eller None om det var fel lösenord)
                if user_data:  # Om vi fick napp (rätt lösenord!):
                    st.session_state.user = user_data  # Spara kunden som inloggad i korttidsminnet
                    st.session_state.boknings_meddelande = None  # Nollställ gamla meddelanden
                    st.rerun()  # Ladda om sidan så inloggningen slår igenom direkt!
                else:  # Om e-post eller lösenord var fel:
                    st.error("Fel e-post eller lösenord!")  # Visa röd ruta: "Försök igen!"

            st.divider()  # Ett tunt streck längst ner i logga-in-menyn
            if st.button("Skapa nytt konto", use_container_width=True):  # En knapp för nya besökare som inte har konto än
                visa_registrering_modal()  # Öppnar vår fina registrerings-popup som vi byggde högre upp!
    else:  # Annars (om någon ÄR inloggad):
        ar_admin = st.session_state.user["customer_id"] == 1  # Kollar om den inloggade är chefen (Kund #1)
        etikett = (  # Bestämmer vad det ska stå på kontoknappen högst upp till höger:
            f"Admin · {st.session_state.user['first_name']}"  # T.ex. "Admin · Anna" om man är admin
            if ar_admin  # (gäller bara för Kund #1)
            else st.session_state.user["first_name"]  # Annars står bara kundens förnamn, t.ex. "Anna"
        )  # Knapptext klar
        with st.popover(etikett, use_container_width=True):  # Ritar kontoknappen som fäller ut en personlig meny vid klick
            st.write(  # Skriver ut kundens hela namn i fetstil högst upp i menyn
                f"**{st.session_state.user['first_name']} {st.session_state.user['last_name']}**"  # Förnamn och efternamn
            )  # Namn klart
            st.caption(  # Skriver ut kundens hemkommun i liten grå text under namnet
                f"Hemkommun: {st.session_state.user['municipality_name']}"  # T.ex. "Hemkommun: Lund"
            )  # Kommuntext klar
            st.divider()  # Ett streck innan menyknapparna

            if st.button("Redigera betald resa", use_container_width=True):  # Knapp 1: Ändra en bokad resa
                visa_redigera_resa_modal()  # Öppnar omboknings-popupen!

            if st.button("Betalningshistorik & kvitton", use_container_width=True):  # Knapp 2: Se gamla kvitton
                visa_kvitto_modal()  # Öppnar kvitto-popupen!

            if st.button("Logga ut", use_container_width=True):  # Knapp 3: Logga ut
                st.session_state.user = None  # Glöm bort vem som var inloggad
                st.session_state.valda_mal = []  # Töm kundvagnen på valda utflyktsmål
                st.session_state.boknings_meddelande = None  # Ta bort gamla meddelanden
                st.rerun()  # Ladda om sidan så vi är tillbaka i utloggat läge!


# ---------  # Mellanlandning innan flikarna!
# Meddelanden & Sökfält direkt på bakgrunden  # Här dyker eventuella varningar, gröna hurrarop och sökrutan upp
# ---------  # Staket klart
if st.session_state.datum_varning:  # Om det ligger en varning i minnet (t.ex. att ett resmål var stängt när man bytte datum):
    st.warning(st.session_state.datum_varning)  # Visa en gul varningsruta med meddelandet
    st.session_state.datum_varning = None  # Radera varningen ur minnet så den inte ligger kvar för evigt

if st.session_state.boknings_meddelande:  # Om det ligger ett glatt besked i minnet (t.ex. "Betalning genomförd!"):
    st.success(st.session_state.boknings_meddelande)  # Visa en grön seger-ruta!

sok_fras = st.text_input(  # Ritar sökrutan som spänner över hela bredden ovanför flikarna
    "Sök",  # Osynlig etikett
    placeholder="Sök bland nöjen, platser eller fika...",  # Hjälpsam text som syns när rutan är tom
    label_visibility="collapsed",  # Gömmer etiketten ovanför rutan så det ser cleant ut
)  # Allt användaren skriver i rutan sparas nu i "sok_fras"


# ---------  # Nu bygger vi mallen för utflyktskorten!
# Kortkomponent för ett besöksmål (Platt 2026-kort)  # Ett recept som ritar upp ett snyggt kort med bild, text och kryssruta
# ---------  # Staket klart
def rendera_besoksmal_kort(item):  # Startar receptet som tar emot ett besöksmål ("item") och ritar ut det på skärmen
    plats_namn = item["plats_namn"]  # Plockar ut namnet på stället (t.ex. "Ebbas Fik")
    kommun_namn = item["municipality_name"]  # Plockar ut vilken kommun det ligger i (t.ex. "Helsingborg")
    bild_url = item["bild_url"]  # Plockar ut bilden på stället
    lang_text = item["lang_text"]  # Plockar ut den lockande beskrivningstexten
    kategori = item["kategori"]  # Plockar ut kategorin ("amusement", "place" eller "fika")
    item_id = item["id"]  # Plockar ut ställets ID-nummer i databasen
    municipality_id = item["municipality_id"]  # Plockar ut kommunens ID-nummer (behövs för att räkna ut busspriset!)
    pris = item["pris"]  # Plockar ut inträdespriset i kronor
    oppettider = item.get("oppettider", {})  # Plockar ut veckans öppettider för stället

    dag_status = oppettider.get(veckodag_nu) if oppettider else None  # Tittar på öppettiden för just den veckodag som är vald i kalendern
    ar_oppet, substatus, _ = backend.utvardera_oppetstatus(dag_status, st.session_state.valt_datum)  # Kontrollerar stängningstid & substatus ("Stänger inom kort")
    if dag_status:  # Spara även aktuell substatus på dag_status för framtida syfte:
        dag_status["substatus"] = substatus  # T.ex. "Stänger inom kort" vid 16:01 (2h innan stängning 18:00)

    pris_etikett = f"{pris:.0f} kr / person" if pris > 0 else "Fri entré"  # Skriver t.ex. "195 kr / person" eller "Fri entré" om det är gratis
    if dag_status:  # Om vi har öppettidsinformation för denna veckodag:
        if ar_oppet:  # Och stället har öppet:
            tid_badge = f'<span class="badge badge-open">Öppet {dag_status["dag_namn"].lower()}: {dag_status["text"]}</span>'  # Gör en grön skylt med dagens tider
            if substatus == "Stänger inom kort":  # Om det är <= 2h kvar till stängning (t.ex. 16:01 vid stängning 18:00):
                tid_badge += ' <span class="badge badge-closing">Stänger inom kort</span>'  # Visa substatus-skylt
        elif substatus == "Stängt för dagen":  # Om stället har stängt för dagen p.g.a. passerad stängningstid (t.ex. kl. 19:00):
            tid_badge = f'<span class="badge badge-closed">Stängt för dagen ({dag_status["text"]})</span>'  # Röd skylt som visar att stängningstiden passerats
        else:  # Om stället har stängt hela denna veckodag:
            tid_badge = f'<span class="badge badge-closed">Stängt på {dag_status["dag_namn"].lower()}ar</span>'  # Gör en röd skylt som varnar för stängt
    else:  # Om det inte fanns några öppettider alls i databasen:
        tid_badge = ""  # Ingen tidsskylt alls

    img_klass = "card-img" if ar_oppet else "card-img-closed"  # Väljer färggrann bild om det är öppet, eller svartvit bild om det är stängt!

    with st.container(border=True):  # Skapar en inramad kort-ruta för besöksmålet
        st.markdown(  # Ritar ut bilden, rubriken, etiketterna och beskrivningen inuti kortet:
            f"""
            <img src="{bild_url}" class="{img_klass}" alt="{plats_namn}" /> <!-- Själva fotografiet på besöksmålet -->
            <div class="card-title">{plats_namn}</div> <!-- Namnet på besöksmålet -->
            <div class="badge-row"> <!-- Raden med små infoskyltar: -->
                <span class="badge badge-neutral">{kommun_namn}</span> <!-- Bruna kommun-skylten -->
                <span class="badge badge-price">{pris_etikett}</span> <!-- Vita prislappen -->
                {tid_badge} <!-- Gröna, gula eller röda öppettidsskylten -->
            </div> <!-- Slut på skyltraden -->
            <div class="card-desc">{lang_text}</div> <!-- Beskrivningstexten om stället -->
            """,  # Slut på HTML-koden för kortet
            unsafe_allow_html=True,  # Tillåt Streamlit att visa HTML-koden
        )  # Övre delen av kortet är klar!

        if st.session_state.user is not None:  # Om besökaren är inloggad får man lov att kryssa i besöksmålet:
            unik_nyckel = f"{kategori}_{item_id}"  # Skapar en unik namnlapp, t.ex. "amusement_2"
            redan_vald = any(  # Kollar i kundvagnen:
                m["nyckel"] == unik_nyckel for m in st.session_state.valda_mal  # Ligger det här utflyktsmålet redan i vår kundvagn?
            )  # Svaret blir True (ja) eller False (nej)

            if not ar_oppet and redan_vald:  # Om stället har hunnit stänga för dagen medan det låg i kundvagnen:
                st.session_state.valda_mal = [  # Plocka bort det stängda målet ur kundvagnen
                    m for m in st.session_state.valda_mal if m["nyckel"] != unik_nyckel
                ]
                redan_vald = False

            if lediga_platser <= 0:  # Om bussen är proppfull (0 platser kvar):
                st.caption("Bussen kan inte bokas på valt datum.")  # Skriv en liten text istället för kryssruta
            else:  # Om det finns plats på bussen:
                if ar_oppet:  # Om aktiviteten har öppet:
                    etikett = f"Välj {plats_namn}"  # T.ex. "Välj Tosselilla"
                elif substatus == "Stängt för dagen":  # Om klockan passerat stängningstid idag (t.ex. kl. 19:00):
                    etikett = f"{plats_namn} har stängt för dagen"  # Tydlig text om att det stängt för dagen
                else:  # Om det är stängt hela veckodagen:
                    etikett = f"{plats_namn} är stängt valt datum"  # Annars står det att stället är stängt valt datum

                vald = st.checkbox(  # Ritar ut själva kryssrutan på kortet:
                    etikett,  # Texten bredvid rutan
                    value=redan_vald and ar_oppet,  # Är ikryssad om den låg i kundvagnen OCH stället är öppet
                    disabled=not ar_oppet,  # Låser kryssrutan om stället är stängt (eller efter stängningstid) så ingen kan boka!
                    key=f"chk_{unik_nyckel}_{st.session_state.valt_datum}",  # Unikt ID för just denna kryssruta på detta datum
                )  # Kryssruta klar

                if vald and not redan_vald and ar_oppet:  # Om användaren PRECIS kryssade i rutan:
                    st.session_state.valda_mal.append(  # Lägg ner utflyktsmålet i kundvagnen (session_state.valda_mal):
                        {  # Vi packar ner all viktig info om målet i ett litet paket:
                            "nyckel": unik_nyckel,  # Unika ID-koden
                            "kategori": kategori,  # Kategorin (nöje, plats eller fika)
                            "id": item_id,  # Numret i databasen
                            "namn": plats_namn,  # Namnet på stället
                            "municipality_id": municipality_id,  # Kommunens ID (för bussavgiften)
                            "pris": pris,  # Inträdespriset
                            "oppettider": oppettider,  # Öppettiderna (så vi kan kolla dem om kunden byter datum sen)
                            "substatus": substatus,  # Sparar substatus (t.ex. "Stänger inom kort")
                        }  # Paketet är färdigpackat
                    )  # Och nedlagt i kundvagnen!
                    st.rerun()  # Ladda om sidan snabbt så siffran på fliken "Bokning (1)" uppdateras direkt!
                elif not vald and redan_vald:  # Om användaren precis kryssade UR rutan:
                    st.session_state.valda_mal = [  # Gör om kundvagnen:
                        m  # Behåll alla utflyktsmål ("m")...
                        for m in st.session_state.valda_mal  # ...som redan låg i kundvagnen...
                        if m["nyckel"] != unik_nyckel  # ...förutom just det här målet som vi nyss kryssade ur!
                    ]  # Kundvagnen är nu uppdaterad
                    st.rerun()  # Ladda om sidan så räknaren på Boknings-fliken minskar!
        else:  # Om besökaren INTE är inloggad:
            st.caption("Logga in högst upp för att lägga till i din resa.")  # Visa en vänlig liten påminnelse om att logga in först

        with st.expander("Visa öppettider (Mån–Sön)", expanded=False):  # Ritar den lilla dragspelsrutan längst ner på kortet
            if oppettider:  # Om stället har öppettider registrerade:
                for veckodag_nr in range(1, 8):  # Gå igenom dagarna 1 till 7 (Måndag till Söndag):
                    rad = oppettider.get(veckodag_nr)  # Hämta tiderna för just den dagen
                    if rad:  # Om dagen fanns i listan:
                        markering = "• " if veckodag_nr == veckodag_nu else ""  # Sätt en liten prick framför den veckodag som är vald i kalendern!
                        vikt = "**" if veckodag_nr == veckodag_nu else ""  # Och gör dagens veckodag fetstilad så ögat hittar den direkt!
                        status_str = rad["text"] if rad["is_open"] else "Stängt"  # Skriv ut tiderna (t.ex. "10:00–16:00") eller "Stängt"
                        st.write(  # Skriv ut raden i dragspelet:
                            f"{markering}{vikt}{rad['dag_namn']}:{vikt} {status_str}"  # Exempel: "• **Lördag:** 10:00–16:00"
                        )  # Dag-rad klar
            else:  # Om öppettider saknas helt:
                st.caption("Inga öppettider registrerade.")  # Skriv att vi inte har några tider


# ---------  # Nu ritar vi upp själva flikarna på sidan!
# Huvudflikar direkt på bakgrunden  # Nöjen, Platser, Fika, Bokning (och en hemlig Admin-flik för chefen!)
# ---------  # Staket klart
antal_valda = len(st.session_state.valda_mal)  # Räknar efter hur många utflyktsmål som ligger i kundvagnen just nu
boknings_flik_titel = (  # Bestämmer vad det ska stå på den fjärde fliken:
    f"Bokning ({antal_valda})" if antal_valda > 0 else "Bokning"  # Visar t.ex. "Bokning (3)" om man valt 3 mål, annars bara "Bokning"
)  # Fliknamn klart

flik_titlar = ["Nöjen", "Platser", "Fika", boknings_flik_titel]  # Listan med våra fyra standardflikar
ar_admin_inloggad = (  # Kollar om den som sitter vid skärmen är vår administratör:
    st.session_state.user is not None  # Någon måste vara inloggad...
    and st.session_state.user["customer_id"] == 1  # ...och ha Kund-ID nummer 1!
)  # Nu vet vi om admin är inloggad (True eller False)
if ar_admin_inloggad:  # Om det är chefen som är inloggad:
    flik_titlar.append("Admin")  # Trolla fram en femte hemlig flik längst till höger som heter "Admin"!

flikar = st.tabs(flik_titlar)  # Ber Streamlit rita ut alla flikarna på skärmen

# 1–3. Kategoriflikar (Nöjen, Platser, Fika)  # Här fyller vi de tre första flikarna med utflyktskort
for flik, (titel, kat_kod) in zip(  # Parar ihop varje flik med rätt titel och rätt databaskod:
    flikar[:3],  # De tre första flikarna
    [("Nöjen", "amusement"), ("Platser", "place"), ("Fika", "fika")],  # Deras namn och databaskoder
):  # Snurrar igenom flik 1, 2 och 3:
    with flik:  # Kliver in i fliken
        items = backend.filtrera_aktiviteter(kat_kod, sok_fras)  # Ber maskinrummet hämta alla mål i kategorin som matchar det man skrivit i sökrutan
        if not items:  # Om sökningen inte gav några träffar alls under denna flik:
            with st.container(border=True):  # Rita en liten ruta
                st.write(f"Inga besöksmål under **{titel}** matchade din sökning.")  # Berätta vänligt att vi kammade noll
        else:  # Om vi hittade utflyktsmål:
            for item in items:  # Gå igenom dem ett efter ett...
                rendera_besoksmal_kort(item)  # ...och rita upp dem med vår snygga kort-mall!

# 4. Bokningsflik direkt på bakgrunden  # Här inne ligger kassan där man betalar och bokar sin resa
with flikar[3]:  # Kliver in i den fjärde fliken ("Bokning", som har plats nummer 3 eftersom datorer börjar räkna från 0!)
    with st.container(border=True):  # Skapar en snygg inramad ruta för kassan
        if st.session_state.user is None:  # Om besökaren inte har loggat in än:
            st.markdown("#### Min bokning")  # Visa en rubrik
            st.write(  # Och berätta hur man gör för att komma igång:
                "Logga in via knappen längst upp till höger för att välja resmål och slutföra din bokning."  # Vägledningstext
            )  # Klar med utloggad vy
        else:  # Om kunden är inloggad:
            st.markdown(  # Visa en personlig rubrik med kundens förnamn:
                f"#### Boka resa för {st.session_state.user['first_name']}"  # T.ex. "Boka resa för Anna"
            )  # Rubrik klar
            st.caption(  # Visa varifrån bussen utgår (kundens hemkommun) och valt datum:
                f"Avresa från {st.session_state.user['municipality_name']} · {st.session_state.valt_datum} ({veckodag_namn})"  # T.ex. "Avresa från Malmö · 2026-10-22 (Torsdag)"
            )  # Undertext klar

            if antal_valda == 0:  # Om kunden inte har kryssat i ett enda utflyktsmål än:
                st.info(  # Visa en blå tipsruta:
                    "Du har inte valt några besöksmål än. Kryssa i dina favoriter under flikarna Nöjen, Platser eller Fika."  # Förklarar hur man väljer mål
                )  # Tipsruta klar
            else:  # Om kunden har minst en "vara" (besöksmål) inlagd i kundvagnen:
                kassa_datum = st.date_input(  # Punkt 3: Datumväljare direkt efter "Avresa"-raden så man kan ändra datum vid kassan
                    "Ändra avresedatum",  # Tydlig etikett ovanför kalendern i kassan
                    value=st.session_state.valt_datum,  # Visar nuvarande valda datum
                    min_value=date.today(),  # Kalendern tillåter från dagens datum (men bokning kräver minst imorgon)
                )  # Kassa-kalender klar
                if kassa_datum != st.session_state.valt_datum:  # Om kunden byter datum här i kassan:
                    uppdatera_valt_datum(kassa_datum)  # Synka datumet med resten av appen och kolla öppettiderna!

                if bussen_redan_ute:  # Punkt 4: Om datumet står på idag är bussen redan ute och kör!
                    st.warning(  # Visa tydlig varning om att bussen tidigast kan bokas dagen därpå
                        "Bussen är redan ute och kör idag. Välj ett datum från och med imorgon ovan för att slutföra bokningen."
                    )  # Varning klar
                elif lediga_platser <= 0:  # Om bussen är helt slutsåld på valt framtida datum:
                    st.warning(  # Visa en gul varningsruta:
                        "Bussen är fullbokad på detta datum. Välj ett annat datum ovan för att boka."  # Ber kunden prova en annan dag
                    )  # Varning klar

                st.markdown("**Valda resmål i ditt paket**")  # Fet underrubrik
                for mal in st.session_state.valda_mal:  # Gå igenom varje valt resmål i kundvagnen:
                    dag_info = mal.get("oppettider", {}).get(veckodag_nu)  # Hämta dagens öppettid för målet
                    tid_etikett = (  # Om vi har en öppettid, lägg till den med en liten punkt före:
                        f" · {dag_info['text']}" if dag_info else ""  # T.ex. " · 10:00–17:00"
                    )  # Tid-etikett klar
                    st.write(  # Skriv ut en punkt på listan med namn, pris och öppettid:
                        f"- **{mal['namn']}** ({mal['pris']:.0f} kr){tid_etikett}"  # T.ex. "- **Ystad Djurpark** (260 kr) · 10:00–17:00"
                    )  # Punkt klar

                st.divider()  # Rita ett vågrätt streck innan siffervalen

                bcol1, bcol2, bcol3 = st.columns(3)  # Gör tre kolumner för Vuxna, Barn och Betalsätt
                with bcol1:  # Kolumn 1:
                    adults = st.number_input("Vuxna", min_value=1, value=1)  # Välj antal vuxna (minst 1, startar på 1)
                with bcol2:  # Kolumn 2:
                    children = st.number_input("Barn", min_value=0, value=0)  # Välj antal barn (minst 0, startar på 0)
                with bcol3:  # Kolumn 3:
                    payment_method = st.selectbox(  # Rullgardinsmeny för betalsätt
                        "Betalsätt", ["Swish", "Kort", "Klarna"]  # De tre sätten man kan betala på
                    )  # Betalsätt valt

                total_price, buss_avgift, antal_kommuner, antal_resenarer = (  # Ber maskinrummet räkna ut vad kalaset kostar:
                    backend.berakna_respris(  # Anropar priskalkylatorn i backend.py
                        st.session_state.user["municipality_id"],  # Skickar med kundens hemkommun
                        st.session_state.valda_mal,  # Alla valda resmål i kundvagnen
                        adults,  # Antal vuxna
                        children,  # Antal barn
                    )  # Kalkylatorn räknar så det ryker!
                )  # Och ger oss totalpris, bussavgift, antal besökta kommuner och totalt antal resenärer

                
                st.write(  # Skriver ut hur bussavgiften är uträknad för vuxna (45 kr) och barn (0.5 × 45 kr):
                    f"Bussavgift ({antal_kommuner} kommuner · {adults} vuxna × 45 kr, {children} barn × 22.50 kr): **{buss_avgift:.2f} kr**"  # Tydlig prisinfo
                        )  # Bussavgiftsrad klar
                st.markdown(f"### Totalpris: {total_price:.2f} kr")  # Skriver ut hela totalpriset med stor rubrikstil!

                for_manga_resenarer = antal_resenarer > lediga_platser  # Kollar om sällskapet är större än antalet lediga säten i bussen
                if for_manga_resenarer and not bussen_redan_ute:  # Om de är för många för bussen:
                    st.warning(  # Visa en gul varningsruta:
                        f"Du har valt {antal_resenarer} resenärer men det finns endast {lediga_platser} platser kvar."  # Förklarar läget
                    )  # Varning klar

                if st.button(  # Ritar den stora köpknappen längst ner:
                    "Slutför bokning & betala",  # Texten på knappen
                    type="primary",  # Snygg mörk huvudknapp
                    disabled=for_manga_resenarer or bussen_redan_ute or lediga_platser <= 0,  # Spärrad om datumet är idag (bussen kör redan) eller om platser saknas!
                    use_container_width=True,  # Gör knappen lika bred som rutan
                ):  # Om kunden klickar på knappen:
                    booking_id, fel = backend.spara_bokning_i_db(  # Skicka hela beställningen till maskinrummet för att sparas i databasen!
                        user=st.session_state.user,  # Vem som bokar
                        valda_mal=st.session_state.valda_mal,  # Vilka ställen som ska besökas
                        travel_date=st.session_state.valt_datum,  # Vilket datum bussen går
                        adults=adults,  # Hur många vuxna
                        children=children,  # Hur många barn
                        total_price=total_price,  # Vad det kostar totalt
                        payment_method=payment_method,  # Hur kunden betalade (Swish, Kort eller Klarna)
                    )  # Maskinrummet svarar med ett nytt bokningsnummer (booking_id) eller ett felmeddelande
                    if booking_id:  # Om allt gick vägen och vi fick ett bokningsnummer:
                        st.session_state.boknings_meddelande = (  # Lägg ett glatt kvittomeddelande i korttidsminnet:
                            f"Betalning genomförd med {payment_method}! Bokningsnummer #{booking_id}. "  # Bekräftar betalning och nummer
                            f"Kvitto finns under Betalningshistorik i kontomenyn."  # Tipsar om var kvittot hittas
                        )  # Meddelande klart
                        st.session_state.valda_mal = []  # Töm kundvagnen nu när resan är bokad och betald
                        st.rerun()  # Ladda om sidan så det gröna hurraropet visas högst upp!
                    else:  # Om något gick galet i databasen:
                        st.error(f"Kunde inte spara bokningen: {fel}")  # Visa felet i en röd ruta

# 5. Adminflik (Visas endast för Kund-ID #1)  # Chefens hemliga kontrollrum!
if ar_admin_inloggad:  # Dubbelkollar att det verkligen är Administratören (Kund #1) som är inloggad:
    with flikar[4]:  # Kliver in i den femte fliken ("Admin")
        with st.container(border=True):  # Ritar en snygg ram runt adminpanelen
            st.markdown("#### Administratörsvy (Kund-ID #1)")  # Rubrik för chefen
            st.caption(  # Liten hjälptext som påminner om att admin även kan redigera allas resor via menyn uppe till höger
                "Alla kunders bokningar och kvitton nås även via kontomenyn längst upp till höger."  # Hjälptext
            )  # Text klar
            alla_kunder = backend.hamta_alla_kunder()  # Ber maskinrummet hämta hela kundregistret från databasen
            st.dataframe(alla_kunder, use_container_width=True, hide_index=True)  # Ritar upp en interaktiv, sorterbar tabell med alla kunder!
import base64                               # Verktygslådan som förvandlar bildfiler till textsträngar så att webbläsaren kan visa dem direkt
from pathlib import Path                    # Vår digitala spårhund som hittar rätt mapp och fil
from datetime import date, datetime         # Kalender- och klockverktyg så vi har koll på dagens datum och stängningstider
import mysql.connector                      # "Tolken" som gör att Python kan prata med vår MySQL-databas
import streamlit as st                      # Hämtar Streamlit så vi faktiskt kan använda de
from sshtunnel import SSHTunnelForwarder    # James Bond verktyget som bygger en krypterad, hemlig tunnel till databasservern på mitt domän

#-- Import slut av verktyg

# I Python kan vi inte använda /*Kommentarer*/ på detta viset... man måste använda "#"...

#-- Början av "förberedelser för att underlätta senare"

                                            # Sökvägen till mappen där backend.py och bilderna ligger  # En kommentar som berättar vad raden under gör
BASE_DIR = Path(__file__).parent            # Visar platsen till mappen där just den här filen ("backend.py") bor så vi kan berätta att allt finns där egentligen...

# Siffror som gäller för vår kära superduper buss (stora bokstäver = "rör ej i onödan!")
MAX_BUSS_PLATSER = 50           # Bussen har totalt 50 säten
DEFAULT_BOKADE_PLATSER = 45     # Vi låtsas att 45 pensionärer redan sitter på bussen från start, varje dag... 365 dagar om året.. (så det blir något att visa vid fullbokning över de 5 sista platserna xD)
SIMULERAD_TID = None            # Sätt t.ex. till "16:01" eller "19:00" vid simulering, eller None för datorns riktiga klocka!

VECKODAGAR = {      # En liten parlör/fickbok/innehåll/handbok som översätter veckodagsnummer till vanlig svenska:
    1: "Måndag",    # Dag 1 är Måndag
    2: "Tisdag",    # Dag 2 är Tisdag
    3: "Onsdag",    # Dag 3 är Onsdag
    4: "Torsdag",   # Dag 4 är Torsdag
    5: "Fredag",    # Dag 5 är Fredag (bästa dagen!)
    6: "Lördag",    # Dag 6 är Lördag
    7: "Söndag",    # Dag 7 är Söndag
}                   # "Parleouren" är stängd

def lokal_bild_till_url(filnamn, fallback_text="Bild+saknas"):  # Ett recept som letar upp en bild på datorn och gör den redo för webben, annars "bild saknas"
    """Hittar en lokal bild i samma mapp (även med annan/dubbel filändelse) och gör om till Base64-URL."""  # Beskrivning av vad receptet gör
    bas_namn = Path(filnamn).stem               # Klipper bort filändelsen (så "tosselilla.jpg" blir bara "tosselilla")
    
    mojliga_namn = [                            # Gör en parlör på alla tänkbara sätt som bildfilen kan heta (ifall någon råkat döpa den till .png eller .jpg.jpg):
        filnamn,                                # Exakt det namn vi bad om
        f"{filnamn}.jpg",                       # Om någon råkat döpa filen till "bild.jpg.jpg"
        f"{filnamn}.png",                       # Eller "bild.jpg.png"
        f"{bas_namn}.jpg",                      # Vanlig .jpg-bild
        f"{bas_namn}.jpeg",                     # .jpeg-bild (samma sak som jpg men med ett extra e)
        f"{bas_namn}.png",                      # .png-bild
        f"{bas_namn}.webp",                     # Modern .webp-bild
    ]                                           # Listan med "gissningar" stängs

    # Sök igenom mappen, förklarar att vi inte bryr oss om stora eller små bokstäver
    filer_i_mappen = {f.name.lower(): f for f in BASE_DIR.iterdir() if f.is_file()}  # Skapar ett register över alla filer som faktiskt ligger i vår mapp just nu

    for namn in mojliga_namn:                                                       # Går igenom våra gissningar en efter en:
        matchad_fil = filer_i_mappen.get(namn.lower())                              # Kollar om gissningen finns i mapp-registret
        if matchad_fil:                                                             # OM vi hittade bildfilen på datorn:
            ext = matchad_fil.suffix.lower().lstrip(".")                            # Kollar vilken filändelse den hade (t.ex. "jpg" eller "png")
            mime = "jpeg" if ext in ("jpg", "jpeg") else ext                        # Webbläsare är petiga och vill att "jpg" ska kallas "jpeg"
            b64_data = base64.b64encode(matchad_fil.read_bytes()).decode("utf-8")   # Översätter bildens pixlar till en lång textsträng (Base64)
            return f"data:image/{mime};base64,{b64_data}"                           # Skickar tillbaka den färdiga bild-strängen som webbläsaren kan rita ut direkt!

    # Om filen inte hittas skrivs en varning ut i terminalen, de ovan, alltså om vi inte hittade filen på alla gissningar:
    print(f"Hittade inte bildfilen '{filnamn}' i {BASE_DIR}")       # Skriv ut ett litet "rop på hjälp" i terminalen haha...
    return f"https://placehold.co/600x300?text={fallback_text}"     # Och visa en helt grå "reservbild" från placehold.co hemsidan inte flippar ur!


BILD_FILER = {                                                      # En katalog som parar ihop (kategori, ID-nummer) med rätt bildfil och reservtext:
    ("amusement", 1): ("ystad_djurpark.jpg", "Ystad+Djurpark"),     # Nöje nr 1 får bilden på Ystad Djurpark
    ("amusement", 2): ("tosselilla.jpg", "Tosselilla"),             # Nöje nr 2 får bilden på Tosselilla Sommarland
    ("amusement", 3): ("malmo_museum.jpg", "Malmo+Museum"),         # Nöje nr 3 får bilden på Malmö Museum
    ("place", 1): ("glumslovs_backar.jpg", "Glumslovs+Backar"),     # Plats nr 1 får bilden på Glumslövs Backar
    ("place", 2): ("soderasen.jpg", "Soderasen"),                   # Plats nr 2 får bilden på Söderåsens nationalpark
    ("place", 3): ("ales_stenar.jpg", "Ales+Stenar"),               # Plats nr 3 får bilden på Ales Stenar
    ("fika", 1): ("ebbas_fik.jpg", "Ebbas+Fik"),                    # Fika nr 1 får bilden på 50-talsfiket Ebbas Fik
    ("fika", 2): ("farg_fran_forr.jpg", "Farg+fran+forr"),          # Fika nr 2 får bilden på Färg från förr
    ("fika", 3): ("alice_och_katten.jpg", "Alice+och+Katten"),      # Fika nr 3 får bilden på Alice och Katten
}#Bildkatalogen via ID är klar!


BILD_FILER_NAMN = {                                                 # En extra reservkatalog som letar efter rätt bild baserat på platsens namn istället för ID:
    "ystad djurpark": "ystad_djurpark.jpg",                         # Om namnet innehåller "ystad djurpark" -> ta denna bild
    "tosselilla": "tosselilla.jpg",                                 # Om namnet innehåller "tosselilla" -> ta denna bild
    "malmö museum": "malmo_museum.jpg",                             # Om namnet innehåller "malmö museum" -> ta denna bild
    "glumslövs backar": "glumslovs_backar.jpg",                     # Om namnet innehåller "glumslövs backar" -> ta denna bild
    "söderåsen": "soderasen.jpg",                                   # Om namnet innehåller "söderåsen" -> ta denna bild
    "ales stenar": "ales_stenar.jpg",                               # Om namnet innehåller "ales stenar" -> ta denna bild
    "ebbas fik": "ebbas_fik.jpg",                                   # Om namnet innehåller "ebbas fik" -> ta denna bild
    "färg från förr": "farg_fran_forr.jpg",                         # Om namnet innehåller "färg från förr" -> ta denna bild
    "alice och katten": "alice_och_katten.jpg",                     # Om namnet innehåller "alice och katten" -> ta denna bild
}# Namn-katalogen slut


def hamta_bild_for_aktivitet(kategori, item_id, namn):                  # Receptet som bestämmer vilken bild ett utflyktsmål ska få
    """Slår upp bild via (kategori, id) eller via platsens namn."""     # Kort förklaring av receptet
    if (kategori, item_id) in BILD_FILER:                               # Kollar först om kombinationen av kategori och ID finns i vår första katalog:
        fil, fallback = BILD_FILER[(kategori, item_id)]                 # Plockar ut filnamnet och reservtexten
        return lokal_bild_till_url(fil, fallback)                       # Laddar in bilden och skickar tillbaka den!

    namn_lower = (namn or "").lower()                                   # Om ID-numret inte fick napp, gör om platsens namn till små bokstäver
    for nyckel_ord, fil in BILD_FILER_NAMN.items():                     # Gå igenom vår namn-katalog:
        if nyckel_ord in namn_lower:                                    # Om platsens namn stämmer med något av våra nyckelord...
            return lokal_bild_till_url(fil, namn)                       # ladda in den matchande bilden!

    return f"https://placehold.co/600x300?text={namn}"                  # Sista utvägen: skapa en reservbild med platsens namn på... 

# Pre-loading ish
BILD_KATALOG = {                                                                    # En förladdad katalog med alla bilder (bra att ha redo i minnet):
    ("amusement", 1): lokal_bild_till_url("ystad_djurpark.jpg", "Ystad+Djurpark"),  # Förladdar Ystad Djurpark
    ("amusement", 2): lokal_bild_till_url("tosselilla.jpg", "Tosselilla"),          # Förladdar Tosselilla
    ("amusement", 3): lokal_bild_till_url("malmo_museum.jpg", "Malmo+Museum"),      # Förladdar Malmö Museum
    ("place", 1): lokal_bild_till_url("glumslovs_backar.jpg", "Glumslovs+Backar"),  # Förladdar Glumslövs Backar
    ("place", 2): lokal_bild_till_url("soderasen.jpg", "Soderasen"),                # Förladdar Söderåsen
    ("place", 3): lokal_bild_till_url("ales_stenar.jpg", "Ales+Stenar"),            # Förladdar Ales Stenar
    ("fika", 1): lokal_bild_till_url("ebbas_fik.jpg", "Ebbas+Fik"),                 # Förladdar Ebbas Fik
    ("fika", 2): lokal_bild_till_url("farg_fran_forr.jpg", "Farg+fran+forr"),       # Förladdar Färg från förr
    ("fika", 3): lokal_bild_till_url("alice_och_katten.jpg", "Alice+och+Katten"),   # Förladdar Alice och Katten
}  # Hela bildkatalogen är nu inläst!


#-- Slutet av "förberedelser för att underlätta senare"


#---------------------------------------
# Den hemliga tunneln till databasen! "De gula texten har jag förberett i en secrets fil och visas inte här"
# Databaskoppling  # Här ser vi till att vi kan prata säkert med MySQL-databasen på servern
# --------------------------------------

@st.cache_resource                                                  # Säger åt Streamlit: "Bygg bara den här tunneln EN gång och återanvänd den, annars blir servern yr!"
def get_ssh_tunnel():                                               # Receptet som borrar vår krypterade SSH-tunnel till servern
    tunnel = SSHTunnelForwarder(                                    # Startar tunnelborraren med uppgifter från vår hemliga kassaskåpsfil (st.secrets):
        (st.secrets["SSH_HOST"].strip(), 22),                       # Adressen till SSH-servern och port 22 (standarddörren för SSH)
        ssh_username=st.secrets["SSH_USER"].strip(),                # Användarnamnet för att komma in i tunneln
        ssh_password=st.secrets["SSH_PASSWORD"],                    # Det hemliga lösenordet till tunneln
        remote_bind_address=(                                       # Vart tunneln ska leda när vi väl är inne på servern:
            st.secrets["DB_HOST"].replace(":3306", "").strip(),     # Adressen till själva databasservern
            3306,                                                   # Port 3306 (vilket är MySQL-databasers favoritport xD)
        ),  # maskineriet redo

        set_keepalive=30.0,                                         # Skickar ett litet livstecken var 30:e sekund så länken inte somnar och stängs
    )  # Tunneln är confad
    tunnel.start()                                                  # Trycker på den stora röda startknappen så tunneln öppnas!
    return tunnel                                                   # Lämnar över den öppna tunneln


def _connect_mysql(port):                           # Hjälprecept som ringer upp MySQL-databasen genom vår öppna tunnel
    return mysql.connector.connect(                 # Startar telefonsamtalet till databasen:
        host="127.0.0.1",                           # "127.0.0.1" betyder "samma plats" eftersom tunneln mynnar ut från localhost
        port=port,                                  # Den lokala dörren (porten) som tunneln har öppnat åt oss
        user=st.secrets["DB_USER"].strip(),         # Databas-användarnamnet ur kassaskåpet
        password=st.secrets["DB_PASSWORD"],         # Databas-lösenordet ur kassaskåpet
        database=st.secrets["DB_NAME"].strip(),     # Namnet på själva databasen vi vill jobba med
        connection_timeout=10,                      # Om databasen inte svarar inom 10 sekunder, lägg på luren (så appen inte fryser...)
        use_pure=True,                              # Använder ren Python-kod för kopplingen (stabilt och bra!)
    )  # Nu har vi linjen öppen till databasen!


def get_db_connection():                                    # Huvudregeln som ser till att vi ALLTID får en fungerande databaskoppling (även om tunneln råkat somna)
    try:                                                    # "try" betyder: "Försök göra detta, och få inte panik om något går fel"
        tunnel = get_ssh_tunnel()                           # Hämta vår SSH-tunnel
        if not tunnel.is_active:                            # Om tunneln har tagit en tupplur och inte är aktiv:
            tunnel.restart()                                # Väcka den genom att starta om den!
        try:                                                # Försök nu koppla upp mot MySQL genom tunneln:
            return _connect_mysql(tunnel.local_bind_port)   # Om det funkar, skicka tillbaka den färdiga kopplingen!
        except Exception:                                   # Om MySQL-samtalet misslyckades trots att tunneln såg vaken ut:
            try:                                            # Försök stänga den gamla trötta tunneln...
                tunnel.stop()                               # ...stänger tunneln
            except Exception:                               # Om den redan var stängd...
                pass                                        # ...strunta i det och gå vidare ("pass" = gör ingenting)
            get_ssh_tunnel.clear()                          # Rensa bort den gamla tunneln ur Streamlits minne
            tunnel = get_ssh_tunnel()                       # Bygg en helt sprillans ny tunnel från grunden
            return _connect_mysql(tunnel.local_bind_port)   # Och ring upp databasen på nytt!
    except Exception as err:                                # Om precis ALLT ovan sprack (t.ex. om internet slutat fungera):
        print(f"CRITICAL DB CONNECTION ERROR: {err}")       # Skriv ut felet i terminalen så vi kan felsöka
        raise mysql.connector.Error(str(err))               # Skicka vidare felet så appen kan visa ett prydligt felmeddelande


# ----------------------------------------  
# Nytt kapitel: Hämta utflyktsmål och öppettider!
# Hämta aktiviteter, info & öppettider från DB  
# Här läser vi in nöjen, platser och fik från databasen
# ----------------------------------------

def _format_tid(val):                                               # Ett litet minirecept som snyggar till klockslag från databasen (så "10:00:00" blir "10:00")
    """Omvandlar MySQL TIME (timedelta eller str) till HH:MM."""    # Beskrivning
    if val is None:                                                 # Om det inte stod någon tid alls i databasen:
        return None                                                 # Skicka tillbaka "ingenting" (None)
    if hasattr(val, "total_seconds"):                               # MySQL skickar ofta tider som "antal sekunder sedan midnatt" (timedelta):
        total_sec = int(val.total_seconds())                        # Plocka ut totala antalet sekunder som ett heltal
        hours = total_sec // 3600                                   # Dela med 3600 (antal sekunder på en timme) för att få timmarna
        minutes = (total_sec % 3600) // 60                          # Ta sekunderna som blev över och dela med 60 för att få minuterna
        return f"{hours:02d}:{minutes:02d}"                         # Skriv ut med två siffror för timme och minut, t.ex. "09:30"
    return str(val)[:5]                                             # Om det redan var vanlig text, klipp bara ut de första 5 tecknen ("HH:MM")


def utvardera_oppetstatus(dag_info, valt_datum=None, simulerad_tid=None):               # Kontrollerar om en aktivitet är öppen, stänger inom kort (2h) eller har stängt för dagen
    """Utvärderar öppetstatus och substatus ('Stänger inom kort' 2h före stängning).""" # Beskrivning
    if not dag_info:                                                                    # Om det inte finns någon tidtabell alls för dagen:
        return True, "Öppet", "Öppet"                                                   # Anta att det är öppet som vanligt

    if not dag_info.get("is_open"):                                                     # Om stället har stängt hela denna veckodag:
        return False, "Stängt", "Stängt"                                                # Returnera stängt läge

    open_str = dag_info.get("opening_time")                                             # Plockar ut öppningstiden (t.ex. "10:00")
    close_str = dag_info.get("closing_time")                                            # Plockar ut stängningstiden (t.ex. "18:00")
    grund_text = dag_info.get("text", f"{open_str}–{close_str}")                        # Grundtexten för dagens öppettider

    if open_str == "00:00" and close_str == "23:59":                                    # Om det är en naturplats som har öppet dygnet runt (24/7):
        return True, "Öppet 24/7", grund_text                                           # Alltid öppet och stänger aldrig

    kontroll_datum = valt_datum if valt_datum is not None else date.today()             # Om inget datum skickades med, utgå från dagens datum
    if kontroll_datum > date.today():                                                   # Om kunden kollar på en framtida dag:
        return True, "Öppet", grund_text                                                # Då har dagens klockslag inte passerat stängningstid än!

    tid_str = simulerad_tid or SIMULERAD_TID or datetime.now().strftime("%H:%M")        # Välj simulerad tid om den är satt, annars datorns riktiga klockslag
    try:                                                                                # Försök räkna om klockslagen till minuter:
        nu_h, nu_m = map(int, str(tid_str)[:5].split(":"))                              # Plockar ut timme och minut för nuvarande/simulerad tid
        stang_h, stang_m = map(int, str(close_str)[:5].split(":"))                      # Plockar ut timme och minut för stängningstiden
        nu_minuter = nu_h * 60 + nu_m                                                   # Räknar ut antal minuter sedan midnatt just nu
        stang_minuter = stang_h * 60 + stang_m                                          # Räknar ut antal minuter sedan midnatt vid stängning

        if nu_minuter >= stang_minuter:                                                 # Om klockan är lika med eller efter stängningstid (t.ex. 19:00 när det stänger 18:00):
            return False, "Stängt för dagen", f"Stängt för dagen ({grund_text})"        # Stäng bokning för dagen!

        if 0 < (stang_minuter - nu_minuter) <= 120:                                     # Om det är 2h eller mindre kvar till stängning (t.ex. 16:01 när det stänger 18:00):
            return True, "Stänger inom kort", grund_text                                # Sätt substatus till "Stänger inom kort" för simulering och framtida syfte!
    except ValueError:                                                                  # Om något klockslag hade ett oväntat format:
        pass                                                                            # Gå vidare utan att krascha

    return True, "Öppet", grund_text                                                    # Annars är aktiviteten helt vanligt öppen!


def _hamta_oppettider_dict(cursor, tabell_namn, id_kolumn):                             # Recept som hämtar alla öppettider ur en viss databastabell
    """Hämtar öppettider grupperade per aktivitets-ID från angiven öppettidstabell."""  # Beskrivning
    cursor.execute(                                                                     # Skickar en fråga (SQL-query) till databasen via vår budbärare ("cursor"):
        f"""
        SELECT {id_kolumn} AS item_id, weekday, is_open, opening_time, closing_time     -- Hämta ID, veckodag, om det är öppet samt öppnings- och stängningstid
        FROM {tabell_namn}                                                              -- Från den öppettidstabell vi bad om (nöjen, platser eller fika)
        ORDER BY {id_kolumn} ASC, weekday ASC                                           -- Sortera prydligt efter ID-nummer och veckodag (Måndag till Söndag)
        """  # Slut på SQL-frågan
    )  # Databasen har nu tagit fram svaret

    oppettider_per_id = {}                              # Skapar en tom uppslagsbok där vi ska sortera in öppettiderna per besöksmål
    for row in cursor.fetchall():                       # Går igenom varje rad som databasen skickade tillbaka:
        item_id = row["item_id"]                        # Plockar ut besöksmålets ID-nummer
        oppettider_per_id.setdefault(item_id, {})       # Om besöksmålet inte har en sida i vår uppslagsbok än, skapa en!
        open_str = _format_tid(row["opening_time"])     # Snyggar till öppningstiden (t.ex. "10:00")
        close_str = _format_tid(row["closing_time"])    # Snyggar till stängningstiden (t.ex. "17:00")

        if not row["is_open"]:                                  # Om databasen säger att stället har stängt denna veckodag:
            visnings_text = "Stängt"                            # Sätt texten till "Stängt"
        elif open_str == "00:00" and close_str == "23:59":      # Om det är öppet från midnatt till midnatt (t.ex. en naturpark):
            visnings_text = "Öppet 24/7"                        # Skriv ut att man kan åka dit när som helst på dygnet!
        else:                                                   # Annars (vanliga öppettider):
            visnings_text = f"{open_str}–{close_str}"           # Sätt ihop öppnings- och stängningstid, t.ex. "10:00–17:00"

        dag_paket = {                                                                   # Bygger paketet med dagens tider:
            "weekday": int(row["weekday"]),                                             # Veckodagens nummer (1-7)
            "dag_namn": VECKODAGAR.get(int(row["weekday"]), f"Dag {row['weekday']}"),   # Veckodagens namn på svenska (t.ex. "Måndag")
            "is_open": bool(row["is_open"]),                                            # True om det är öppet, False om det är stängt
            "opening_time": open_str,                                                   # Öppningstid
            "closing_time": close_str,                                                  # Stängningstid
            "text": visnings_text,                                                      # Den färdiga texten som ska visas på kortet
        }                                                                               # Grundpaketet klart
        _, substatus, _ = utvardera_oppetstatus(dag_paket, date.today())                # Räknar ut substatus (t.ex. "Stänger inom kort" vid 16:01)
        dag_paket["substatus"] = substatus                                              # Sparar substatus i paketet för simulering och framtida syfte
        oppettider_per_id[item_id][int(row["weekday"])] = dag_paket                     # Sparar dagens tider under rätt besöksmål och veckodagsnummer
    return oppettider_per_id                                    # Skickar tillbaka hela den färdiga uppslagsboken med öppettider


@st.cache_data(ttl=60)                                          #Sparar resultatet i 60 sekunder så vi slipper fråga databasen vid varje litet musklick
def hamta_alla_aktiviteter():                                   # Stora receptet som hämtar ALLA utflyktsmål i hela Skåne
    """  # Startar beskrivningstexten
    Hämtar samtliga nöjen, platser och fikaställen inklusive deras  # Berättar vad som hämtas
    infotext, kommun och öppettider direkt från databasen.          # Och varifrån det kommer
    """  # Slut på beskrivningen
    aktiviteter = []                                            # En tom lista där vi ska lägga alla nöjen, platser och fikaställen
    try:                                                        # Försök hämta allt från databasen:
        conn = get_db_connection()                              # Öppna linjen till databasen
        cursor = conn.cursor(dictionary=True)                   # Skapa en budbärare ("cursor") som ger oss svaren med tydliga kolumnnamn (dictionary=True)

        amusement_hours = _hamta_oppettider_dict(               # Hämta alla öppettider för Nöjen:
            cursor, "amusement_opening_hours", "amusement_id"   # Från tabellen "amusement_opening_hours"
        )  # Nöjestider klara
       
        place_hours = _hamta_oppettider_dict(                   # Hämta alla öppettider för Platser:
            cursor, "place_opening_hours", "place_id"           # Från tabellen "place_opening_hours"
        )  # Platstider klara
        
        fika_hours = _hamta_oppettider_dict(                    # Hämta alla öppettider för Fikaställen:
            cursor, "fika_opening_hours", "fika_id"             # Från tabellen "fika_opening_hours"
        )  # Fikatider klara





        # Nöjen (amusements)  # Först hämtar vi alla nöjesparker och museer
        cursor.execute(  # Skickar SQL-frågan för nöjen:
            """
            SELECT a.amusement_id AS id, a.amusement_name AS namn, a.amusement_info AS info,    -- Hämta ID, namn och beskrivning
                   a.ticket_price AS pris, a.municipality_id, m.municipality_name               -- Samt biljettpris och vilken kommun det ligger i
            FROM amusements a                                                                   -- Från nöjestabellen (som vi ger kortnamnet "a")
            JOIN municipalities m ON a.municipality_id = m.municipality_id                      -- Para ihop med kommuntabellen ("m") så vi får kommunens namn!
            ORDER BY a.amusement_id ASC                                                         -- Sortera i nummerordning
            """  # Slut på SQL-frågan
        )  # Databasen har svarat

        for row in cursor.fetchall():           # Går igenom varje nöje som hittades:
            item_id = row["id"]                 # Plockar ut nöjets ID
            aktiviteter.append(                 # Lägger till nöjet i vår stora aktivitetslista:
                {                               # Packar ihop ett snyggt litet infopaket:
                    "kategori": "amusement",    # Märker paketet med kategorin "amusement"
                    "id": item_id,              # ID-numret
                    "plats_namn": row["namn"],  # Namnet (t.ex. "Ystad Djurpark")
                    "kort_info": f"Kommun: {row['municipality_name']}",                         #Kommunnamnet
                    "bild_url": hamta_bild_for_aktivitet("amusement", item_id, row["namn"]),    #Hämtar rätt fotografi via vår bildfixare!
                    "lang_text": row["info"],                           # Den långa beskrivningstexten
                    "municipality_id": row["municipality_id"],          # Kommunens ID-nummer
                    "municipality_name": row["municipality_name"],      # Kommunens namn
                    "pris": float(row["pris"]),                         # Inträdespriset som decimaltal
                    "oppettider": amusement_hours.get(item_id, {}),     # Klistrar på rätt öppettider som vi hämtade nyss!
                }  # Infopaketet klart
            )  # Och inlagt i listan!





        # Platser (places) Nu hämtar vi alla sevärdheter
        cursor.execute(                                                             # Skickar SQL-frågan för platser:
            """
            SELECT p.place_id AS id, p.place_name AS namn, p.place_info AS info,    -- Hämta ID, namn och beskrivning
                   p.municipality_id, m.municipality_name                           -- Samt kommun-ID och kommunnamn
            FROM places p                                                           -- Från platstabellen ("p")
            JOIN municipalities m ON p.municipality_id = m.municipality_id          -- Para ihop med kommuntabellen ("m")
            ORDER BY p.place_id ASC                                                 -- Sortera i nummerordning
            """  # Slut på SQL-frågan
        )  # Svaret är klart

        for row in cursor.fetchall():                                                   # Går igenom varje sevärdhet:
            item_id = row["id"]                                                         # Plockar ut platsens ID
            aktiviteter.append(                                                         # Lägger till platsen i vår stora lista:
                {                                                                       # Packar infopaketet:
                    "kategori": "place",                                                # Märker med "place"
                    "id": item_id,                                                      # ID-numret
                    "plats_namn": row["namn"],                                          # Namnet (t.ex. "Ales Stenar")
                    "kort_info": f"Kommun: {row['municipality_name']}",                 # Kommun-info
                    "bild_url": hamta_bild_for_aktivitet("place", item_id, row["namn"]),  # Hämtar bild
                    "lang_text": row["info"],                                           # Beskrivningstexten
                    "municipality_id": row["municipality_id"],                          # Kommunens ID
                    "municipality_name": row["municipality_name"],                      # Kommunens namn
                    "pris": 0.00,                                                       # Sevärdheter i naturen har 0 kr i entréavgift (frisk luft är gratis!)
                    "oppettider": place_hours.get(item_id, {}),                         # Klistrar på platsens öppettider
                }  # Infopaketet klart
            )  # Inlagt i listan!






        # 3. Fika (fika) sist men absolut inte minst... fika...
        cursor.execute(                                                             # Skickar SQL-frågan för fika:
            """
            SELECT f.fika_id AS id, f.fika_name AS namn, f.fika_info AS info,       -- Hämta ID, namn på fiket och beskrivning
                   f.municipality_id, m.municipality_name                           -- Samt kommun-ID och kommunnamn
            FROM fika f                                                             -- Från fikatabellen ("f")
            JOIN municipalities m ON f.municipality_id = m.municipality_id          -- Para ihop med kommuntabellen ("m")
            ORDER BY f.fika_id ASC                                                  -- Sortera i nummerordning
            """  # Slut på SQL-frågan
        )  # Svaret

        for row in cursor.fetchall():                                                   # Går igenom varje kafé:
            item_id = row["id"]                                                         # Plockar ut fikets ID
            aktiviteter.append(                                                         # Lägger till fiket i vår stora lista:
                {                                                                       # Packar infopaketet:
                    "kategori": "fika",                                                 # Märker med "fika"
                    "id": item_id,                                                      # ID-numret
                    "plats_namn": row["namn"],                                          # Namnet (t.ex. "Ebbas Fik")
                    "kort_info": f"Kommun: {row['municipality_name']}",                 # Kommun-info
                    "bild_url": hamta_bild_for_aktivitet("Fika", item_id, row["namn"]),  # Hämtar fotografiet på fiket
                    "lang_text": row["info"],                                           # Beskrivning av stället
                    "municipality_id": row["municipality_id"],                          # Kommunens ID
                    "municipality_name": row["municipality_name"],                      # Kommunens namn
                    "pris": 0.00,                                                       # Själva bokningen av fikastoppet är 0 kr (man köper sin kanelbulle på plats!)
                    "oppettider": fika_hours.get(item_id, {}),                          # Klistrar på fikets öppettider
                }  # Infopaketet klart
            )  # Inlagt i listan!

        cursor.close()          # Tackar budbäraren för hjälpen och klappar den på axeln
        conn.close()            # Lägger på luren till databasen så vi inte håller linjen upptagen i onödan xD
        return aktiviteter      # Skickar tillbaka hela skattkistan med alla infopaket
    except mysql.connector.Error as err:                                    # Om databasen fick ont i magen på vägen:
        st.error(f"Kunde inte hämta aktiviteter från databasen: {err}")     # Visa ett rött felmeddelande på skärmen
        return []                                                           # Och skicka tillbaka en tom lista så appen inte kraschar




# -----------------------------
# Sökfilter, hur vi och filtrerar bort sånt man inte sökt på
# -----------------------------
def berakna_respris(kund_kommun_id, valda_mal, adults, children):                   # Vår prisräknare!
    """Räknar ut bussavgift, antal unika kommuner och totalpris för en resa."""     # Beskrivning
    unika_kommuner = {kund_kommun_id}                                               # Skapar en "mängd" (måsvingar) som automatiskt tar bort dubbletter! Vi startar med kundens hemkommun.
    biljett_pris_per_person = 0.0                                                   # Startar räknaren för inträdesbiljetter på 0 kronor

    for mal in valda_mal:                                                           # Går igenom alla utflyktsmål som kunden har valt:
        biljett_pris_per_person += mal["pris"]                                      # Plussar på ställets inträdespris på biljetträknaren
        unika_kommuner.add(mal["municipality_id"])                                  # Lägger till målets kommun i vår kommun-samling (ligger den redan där händer ingenting!)

    antal_resenarer = adults + children                                             # Räknar ihop totalt antal vuxna + barn som ska ha varsitt säte på bussen
    pris_faktor = adults + (children * 0.5)                                         # Vuxna betalar fullpris (1.0x) och barn betalar halva priset (0.5x)
    buss_avgift = len(unika_kommuner) * 45.00 * pris_faktor                         # Bussavgiften är 45 kr per kommun × (vuxna + 0.5 × barn)
    total_price = (biljett_pris_per_person * antal_resenarer) + buss_avgift         # Totalpriset = (alla inträden × baserat på vilka) + bussavgiften

    return total_price, buss_avgift, len(unika_kommuner), antal_resenarer           # Skickar tillbaka alla fyra siffrorna till kassan i frontend!


def filtrera_aktiviteter(kategori_kod, sok_ord=""):                                                 # Sökmotorn som plockar fram rätt kort under rätt flik
    """Hämtar aktiviteter från databasen för en kategori och filtrerar på eventuell sökfras."""     # Beskrivning
    alla = hamta_alla_aktiviteter()                                                                 # Hämtar hela listan med alla utflyktsmål
    items = [a for a in alla if a["kategori"] == kategori_kod]                                      # Behåller bara de mål som hör till den flik vi tittar på just nu
    if sok_ord and sok_ord.strip():                                                                 # Om användaren har skrivit något i sökrutan:
        s = sok_ord.lower().strip()                                                                 # Gör om sökordet till små bokstäver och ta bort onödiga mellanslag
        items = [                                                                                   # Filtrera listan så vi bara behåller utflyktsmål ("a") där...
            a                                                                                       # ...utflyktsmålet...
            for a in items                                                                          # ...i vår kategorilista...
            if s in a["plats_namn"].lower()                                                         # ...har sökordet i sitt namn (t.ex. "ystad")
            or s in a["kort_info"].lower()                                                          # ...ELLER har sökordet i kommunnamnet
            or s in a["lang_text"].lower()                                                          # ...ELLER har sökordet någonstans i beskrivningstexten!
        ]                                                                                           # Filtreringen är klar
    return items                                                                                    # Skickar tillbaka de utflyktsmål som klarade "filtret"!


# ----------------------------------------
# Nytt kapitel: Kundklubben!
# Användare, Inloggning & Kommuner
# Allt som har med konton, lösenord och skånska kommuner att göra
# ----------------------------------------

def hamta_kommuner():                                                                               # Hämtar listan på alla kommuner (används i rullgardinen när man skapar konto)
    try:                                                                                            # Försök fråga databasen:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor(dictionary=True)                                                       # Skapa vår budbärare
        cursor.execute(                                                                             # Be om ID och namn på alla kommuner i bokstavsordning:
            "SELECT municipality_id, municipality_name FROM municipalities ORDER BY municipality_name"  # Själva SQL-frågan
        )                                                                                           # Databasen svarar
        kommuner = cursor.fetchall()                                                                # Ta emot hela listan med kommuner
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return kommuner                                                                             # Skicka tillbaka kommunlistan!
    except mysql.connector.Error:                                                                   # Om databasen inte svarar:
        return []                                                                                   # Skicka tillbaka en tom lista


def registrera_kund_i_db(first_name, last_name, email, password, phone, municipality_id):           # Sparar en ny kund i databasen
    try:                                                                                            # Försök lägga in den nya kunden:
        conn = get_db_connection()                                                                  # Öppna linjen till databasen
        cursor = conn.cursor()                                                                      # Skapa budbäraren
        query = """
            INSERT INTO customers (first_name, last_name, email, password, phone, municipality_id)  -- Lägg till en ny rad i kundtabellen
            VALUES (%s, %s, %s, %s, %s, %s)                                                         -- "%s" är säkra platshållare där kundens uppgifter fylls i
        """                                                                                         # SQL-mallen är klar
        cursor.execute(                                                                             # Skicka in mallen tillsammans med kundens riktiga uppgifter:
            query,                                                                                  # SQL-mallen
            (                                                                                       # Uppgifterna som ska stoppas in på "%s"-platserna:
                first_name.strip(),                                                                 # Förnamn (städat från mellanslag)
                last_name.strip(),                                                                  # Efternamn (städat)
                email.strip(),                                                                      # E-post (städad)
                password,                                                                           # Lösenordet
                phone.strip() if phone.strip() else None,                                           # Telefonnummer (eller "None" = tomt i databasen om man inte fyllde i något)
                municipality_id,                                                                    # Hemkommunens ID-nummer
            ),                                                                                      # Alla 6 uppgifter är med
        )                                                                                           # Nu ligger raden redo i databasen
        conn.commit()                                                                               # VIKTIGT! "commit()" är som att trycka på "Spara" – utan denna rad glömmer databasen allt vi nyss gjorde!
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return True, "Konto skapat! Du är nu inloggad."                                             # Meddela frontend att allt gick galant!
    except mysql.connector.Error as err:                                                            # Om databasen sa STOPP:
        if err.errno == 1062:                                                                       # Felkod 1062 i MySQL betyder "Dubblett! Det här finns redan!"
            return False, "E-postadressen eller telefonnumret finns redan registrerat."             # Översätt felkoden till begriplig svenska
        elif err.errno == 3819:                                                                     # Felkod 3819 betyder att någon av databasens inbyggda ordningsregler (CHECK constraints) bröts
            return False, "Uppgifterna uppfyller inte databasens formatkrav (kontrollera namn, e-post och lösenord)."   # Förklara vad som hände
        return False, f"Databasfel vid registrering: {err}"                                         # För alla andra fel, skicka med feltexten


def verifiera_inloggning(email, password):                                                          # Dörrvakten som kollar om en kund får logga in
    """Kollar om e-post och lösenord stämmer i tabellen customers."""                               # Beskrivning
    try:                                                                                            # Försök kolla med databasen:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor(dictionary=True)                                                       # Skapa budbärare som ger svar med kolumnnamn
        query = """
            SELECT c.*, m.municipality_name                                                         -- Hämta alla uppgifter om kunden + namnet på kundens hemkommun
            FROM customers c                                                                        -- Från kundtabellen ("c")
            LEFT JOIN municipalities m ON c.municipality_id = m.municipality_id                     -- Koppla ihop med kommuntabellen ("m")
            WHERE c.email = %s AND c.password = %s                                                  -- MEN bara om både e-post OCH lösenord stämmer exakt!
        """                                                                                         # SQL-frågan klar
        cursor.execute(query, (email.strip(), password))                                            # Kör frågan med mejlen och lösenordet som användaren skrev in
        user = cursor.fetchone()                                                                    # Hämta den matchande kunden ("fetchone" = hämta en rad, eller None om ingen hittades)
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return user                                                                                 # Skicka tillbaka kundens uppgifter (eller None om det var fel lösenord)
    except mysql.connector.Error as err:                                                            # Om databasen strular:
        st.error(f"Databasfel vid inloggning: {err}")                                               # Visa felet på skärmen
        return None                                                                                 # Och släpp inte in någon


def hamta_alla_kunder():                                                                            # Chefens favoritfunktion: hämtar hela kundlistan till Admin-fliken!
    """Hämtar alla registrerade kunder för Adminpanelen."""                                         # Beskrivning
    try:                                                                                            # Försök hämta kunderna:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor(dictionary=True)                                                       # Skapa budbärare
        cursor.execute(                                                                             # Be om ID, förnamn, efternamn, mejl, telefon och kommun (men INTE lösenord, för vi är väluppfostrade!):
            """
            SELECT c.customer_id, c.first_name, c.last_name, c.email, c.phone, m.municipality_name  -- Välj dessa kolumner
            FROM customers c                                                                        -- Från kundtabellen
            JOIN municipalities m ON c.municipality_id = m.municipality_id                          -- Kopplat till kommuntabellen
            ORDER BY c.customer_id ASC                                                              -- Sorterat efter kundnummer från 1 och uppåt
            """                                                                                     # Slut på SQL-frågan
        )                                                                                           # Svaret är klart
        alla_kunder = cursor.fetchall()                                                             # Plocka ut alla rader
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return alla_kunder                                                                          # Skicka tabellen till Admin-fliken!
    except mysql.connector.Error:                                                                   # Vid databasfel:
        return []                                                                                   # Skicka en tom lista


# ----------------------------------------
# Nytt kapitel: Bussbiljetter och Bokningar!
# Bussplatser & Bokningar
# Här håller vi räkningen på sätena i Superduperbussen och sparar resor
# ----------------------------------------

def hamta_lediga_platser(travel_date, exkludera_booking_id=None):                                   # Räknar hur många säten som är lediga en viss dag
    """                                                                                             # Start på beskrivning
    Räknar ut lediga platser på bussen (Max 50 platser, 45 bokade som default).                     # Förklarar bussregeln
    Vid redigering exkluderas bokningens egna platser.                                              # Och varför vi ibland räknar bort en bokning
    """                                                                                             # Slut på beskrivning
    try:                                                                                            # Försök räkna platserna i databasen:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor()                                                                      # Skapa budbärare
        if exkludera_booking_id:                                                                    # Om en kund håller på att ÄNDRA en befintlig bokning:
            query = """
                SELECT COALESCE(SUM(number_of_adults + number_of_children), 0)                      -- Räkna ihop alla vuxna + barn (blir det tomt, säg 0)
                FROM bookings                                                                       -- I bokningstabellen
                WHERE travel_date = %s AND booking_status != 'Cancelled' AND booking_id != %s       -- På valt datum, som inte är avbokade, UTOM kundens egen bokning!
            """                                                                                     # SQL-fråga klar
            cursor.execute(query, (travel_date, exkludera_booking_id))                              # Kör frågan med datum och bokningsnumret som ska ignoreras
        else:                                                                                       # Vid en helt vanlig nybokning:
            query = """
                SELECT COALESCE(SUM(number_of_adults + number_of_children), 0)                      -- Räkna ihop alla bokade vuxna + barn
                FROM bookings                                                                       -- I bokningstabellen
                WHERE travel_date = %s AND booking_status != 'Cancelled'                            -- På valt datum som inte är avbokade
            """                                                                                     # SQL-fråga klar
            cursor.execute(query, (travel_date,))                                                   # Kör frågan med valt datum

        bokade_i_db = int(cursor.fetchone()[0])                                                     # Plocka ut siffran som databasen räknade fram
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren

        totalt_bokade = DEFAULT_BOKADE_PLATSER + bokade_i_db                                        # Lägg ihop våra 45 stammis-passagerare med de som bokat via appen
        lediga = max(0, MAX_BUSS_PLATSER - totalt_bokade)                                           # Dra bort bokade från 50 (och använd "max(0, ...)" så det aldrig kan stå "-2 platser kvar")
        return lediga, totalt_bokade                                                                # Skicka tillbaka både antal lediga och antal bokade säten!
    except mysql.connector.Error:                                                                   # Om databasen inte går att nå:
        return 0, MAX_BUSS_PLATSER                                                                  # Säg för säkerhets skull att det är 0 platser kvar så ingen bokar i blindo


def spara_bokning_i_db(                                                                             # Den stora bokningsmaskinen som skapar en hel resa i databasen!
    user, valda_mal, travel_date, adults, children, total_price, payment_method                     # Alla ingredienser som behövs för en bokning
):                                                                                                  # Startar receptet:
    """Skapar rutt, paket, kopplingar, bokning och betalning i MySQL."""                            # Beskrivning av de 5 stegen
    if travel_date <= date.today():                                                                 # Säkerhetskontroll: bussen är redan ute och kör på dagens datum!
        return None, "Bussen är redan ute och kör idag. Bokningar kan tidigast göras från och med imorgon."  # Stoppa bokning för idag

    try:                                                                                            # Försök genomföra hela bokningskedjan:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor()                                                                      # Skapa vår trogna budbärare

        start_kommun = user["municipality_id"]                                                      # Bussresan startar i kundens egen hemkommun
        slut_kommun = valda_mal[-1]["municipality_id"]                                              # Och slutar i kommunen där det sista valda utflyktsmålet ("-1" = sist i listan) ligger!
        rutt_namn = f"Resa för {user['first_name']} ({travel_date})"                                # Döp bussrutten till t.ex. "Resa för Anna (2026-10-22)"

        cursor.execute(                                                                             # Steg 1: Spara själva bussrutten i tabellen "routes":
            "INSERT INTO routes (route_name, from_municipality_id, to_municipality_id) VALUES (%s, %s, %s)",    # SQL-kommando
            (rutt_namn, start_kommun, slut_kommun),                                                 # Ruttens namn, startkommun och slutkommun
        )                                                                                           # Rutten är inlagd
        route_id = cursor.lastrowid                                                                 # Ta reda på vilket ID-nummer den nya rutten precis fick av databasen!

        paket_namn = f"Skräddarsytt paket - {user['first_name']}"                                   # Döp kundens resepaket
        beskrivning = ", ".join([m["namn"] for m in valda_mal])                                     # Gör en kommadelerad text av alla valda mål, t.ex. "Tosselilla, Ebbas Fik"
        cursor.execute(                                                                             # Steg 2: Spara resepaketet i tabellen "packages" (med transportation_id = 1 som är vår buss):
            "INSERT INTO packages (package_name, description, route_id, transportation_id) VALUES (%s, %s, %s, 1)",  # SQL-kommando
            (paket_namn, beskrivning[:255], route_id),                                              # Paketnamn, beskrivning (max 255 tecken så databasen inte svämmar över) och rutt-ID
        )                                                                                           # Paketet är inlagt
        package_id = cursor.lastrowid                                                               # Fånga upp ID-numret som det nya resepaketet fick!

        for mal in valda_mal:                                                                       # Steg 3: Gå igenom varje valt utflyktsmål och koppla ihop det med resepaketet:
            if mal["kategori"] == "amusement":                                                      # Om målet är ett nöje...
                cursor.execute(                                                                     # ...lägg in kopplingen i tabellen "package_amusements"
                    "INSERT INTO package_amusements (package_id, amusement_id) VALUES (%s, %s)",    # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paketets ID och nöjets ID
                )                                                                                   # Nöjet är kopplat
            elif mal["kategori"] == "place":                                                        # Om målet är en sevärdhet/plats...
                cursor.execute(                                                                     # ...lägg in kopplingen i tabellen "package_places"
                    "INSERT INTO package_places (package_id, place_id) VALUES (%s, %s)",            # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paketets ID och platsens ID
                )                                                                                   # Platsen är kopplad
            elif mal["kategori"] == "fika":                                                         # Om målet är ett fikaställe...
                cursor.execute(                                                                     # ...lägg in kopplingen i tabellen "package_fika"
                    "INSERT INTO package_fika (package_id, fika_id) VALUES (%s, %s)",                # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paketets ID och fikets ID
                )                                                                                   # Fikat är kopplat!

        cursor.execute(                                                                             # Steg 4: Skapa själva bokningen i tabellen "bookings":
            """
            INSERT INTO bookings                                                                    -- Lägg in i bokningstabellen:
            (customer_id, package_id, travel_date, number_of_adults, number_of_children, total_price, booking_status)   -- Dessa kolumner
            VALUES (%s, %s, %s, %s, %s, %s, 'Confirmed')                                            -- Med status "Confirmed" (Bekräftad!)
            """,                                                                                    # SQL-mall klar
            (                                                                                       # Uppgifterna som ska in i bokningen:
                user["customer_id"],                                                                # Vem som bokar
                package_id,                                                                         # Vilket resepaket det gäller
                travel_date,                                                                        # Vilket datum resan sker
                adults,                                                                             # Antal vuxna
                children,                                                                           # Antal barn
                total_price,                                                                        # Totalpriset
            ),                                                                                      # Alla bokningsuppgifter redo
        )                                                                                           # Bokningen är skapad
        booking_id = cursor.lastrowid                                                               # Ta hand om det nya bokningsnumret!

        cursor.execute(                                                                             # Steg 5: Registrera betalningen/kvittot i tabellen "payments":
            """
            INSERT INTO payments (booking_id, amount, payment_method, payment_status)               -- Lägg in i betalningstabellen
            VALUES (%s, %s, %s, 'Paid')                                                             -- Med status "Paid" (Betald och klar!)
            """,                                                                                    # SQL-mall klar
            (booking_id, total_price, payment_method),                                              # Bokningsnummer, belopp och betalsätt (Swish/Kort/Klarna)
        )                                                                                           # Betalningen är registrerad!

        conn.commit()                                                                               # Tryck på den stora SPARA-knappen i databasen så alla 5 stegen låses fast permanent!
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return booking_id, None                                                                     # Skicka tillbaka det nya bokningsnumret och "None" (inga fel!)
    except mysql.connector.Error as err:                                                            # Om något av stegen snubblade på mållinjen:
        return None, str(err)                                                                       # Skicka tillbaka "inget bokningsnummer" och felmeddelandet


def hamta_redigerbara_bokningar(customer_id, is_admin=False):                                       # Hämtar resor som ligger i framtiden så man kan ändra dem
    """Hämtar bekräftade bokningar som inte har inträffat ännu samt deras valda resmål."""          # Beskrivning
    try:                                                                                            # Försök hämta bokningarna:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor(dictionary=True)                                                       # Skapa budbärare

        where_clause = (                                                                            # Bestämmer urvalsregeln i databasen:
            "WHERE b.booking_status = 'Confirmed' AND b.travel_date > CURDATE()"                    # Admin får se ALLAS bekräftade resor som sker efter idag ("CURDATE()")
            if is_admin                                                                             # (om man är admin)
            else "WHERE b.customer_id = %s AND b.booking_status = 'Confirmed' AND b.travel_date > CURDATE()"    # Vanlig kund får bara se sina EGNA framtida resor
        )                                                                                           # Urvalsregel klar
        query = f"""
            SELECT                                                                                  -- Plocka fram följande info:
                b.booking_id,                                                                       -- Bokningsnumret
                b.customer_id,                                                                      -- Kundnumret
                b.package_id,                                                                       -- Paketets ID
                b.travel_date,                                                                      -- Avresedatumet
                b.number_of_adults,                                                                 -- Antal vuxna
                b.number_of_children,                                                               -- Antal barn
                b.total_price,                                                                      -- Vad kunden betalat hittills
                p.route_id,                                                                         -- Bussruttens ID
                p.description,                                                                      -- Beskrivningen av resmålen
                c.first_name,                                                                       -- Kundens förnamn
                c.last_name,                                                                        -- Kundens efternamn
                c.municipality_id AS kund_kommun_id                                                 -- Kundens hemkommun-ID (behövs när vi räknar om busspriset!)
            FROM bookings b                                                                         -- Utgå från bokningstabellen ("b")
            JOIN packages p ON b.package_id = p.package_id                                          -- Koppla ihop med pakettabellen ("p")
            JOIN customers c ON b.customer_id = c.customer_id                                       -- Koppla ihop med kundtabellen ("c")
            {where_clause}                                                                          -- Klistra in vår urvalsregel (admin eller vanlig kund)
            ORDER BY b.travel_date ASC, b.booking_id DESC                                           -- Sortera så närmaste avresedatum kommer överst
        """                                                                                         # SQL-frågan är klar
        if is_admin:                                                                                # Om admin frågar:
            cursor.execute(query)                                                                   # Kör frågan direkt utan att begränsa till ett specifikt kund-ID
        else:                                                                                       # Om en vanlig kund frågar:
            cursor.execute(query, (customer_id,))                                                   # Skicka med kundens eget ID-nummer
        bokningar = cursor.fetchall()                                                               # Ta emot listan med bokningar

        for b in bokningar:                                                                         # För varje bokning behöver vi också veta exakt vilka kryssrutor som var ikryssade:
            pid = b["package_id"]                                                                   # Plocka ut paketets ID-nummer
            valda_nycklar = set()                                                                   # Skapa en samling för ID-nycklarna (t.ex. "fika_1")

            cursor.execute(                                                                         # Kolla vilka nöjen som ingår i detta paket:
                "SELECT amusement_id FROM package_amusements WHERE package_id = %s",                # SQL-fråga
                (pid,),                                                                             # Paketets ID
            )                                                                                       # Svar klart
            for row in cursor.fetchall():                                                           # För varje nöje som hittades...
                valda_nycklar.add(f"amusement_{row['amusement_id']}")                               # ...lägg till nyckeln (t.ex. "amusement_2")

            cursor.execute(                                                                         # Kolla vilka platser/sevärdheter som ingår i detta paket:
                "SELECT place_id FROM package_places WHERE package_id = %s", (pid,)                 # SQL-fråga med paket-ID
            )                                                                                       # Svar klart
            for row in cursor.fetchall():                                                           # För varje plats som hittades...
                valda_nycklar.add(f"place_{row['place_id']}")                                       # ...lägg till nyckeln (t.ex. "place_3")

            cursor.execute(                                                                         # Kolla vilka fikaställen som ingår i detta paket:
                "SELECT fika_id FROM package_fika WHERE package_id = %s", (pid,)                    # SQL-fråga med paket-ID
            )                                                                                       # Svar klart
            for row in cursor.fetchall():                                                           # För varje fik som hittades...
                valda_nycklar.add(f"fika_{row['fika_id']}")                                         # ...lägg till nyckeln (t.ex. "fika_1")

            b["valda_nycklar"] = valda_nycklar                                                      # Fäst samlingen med nycklar direkt på bokningen så kryssrutorna i frontend vet vad som ska vara förifyllt!

        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return bokningar                                                                            # Skicka tillbaka de redigerbara bokningarna!
    except mysql.connector.Error:                                                                   # Vid databasfel:
        return []                                                                                   # Skicka en tom lista


def uppdatera_bokning_i_db(                                                                         # Receptet som skriver över en bokning när kunden ändrat sig
    booking_id,                                                                                     # Vilket bokningsnummer som ska ändras
    package_id,                                                                                     # Vilket paket-ID som hör till bokningen
    route_id,                                                                                       # Vilket rutt-ID som hör till bokningen
    nya_mal,                                                                                        # Den nya listan med valda utflyktsmål
    nytt_datum,                                                                                     # Det nya avresedatumet
    adults,                                                                                         # Nytt antal vuxna
    children,                                                                                       # Nytt antal barn
    nytt_totalpris,                                                                                 # Det nya totalpriset
    mellanskillnad,                                                                                 # Prisskillnaden (positiv om kunden betalar mer, negativ vid återbetalning)
    payment_method,                                                                                 # Valda betalsättet för mellanskillnaden
):                                                                                                  # Startar uppdateringen:
    """Uppdaterar rutt, paket, destinationer, bokning och skapar ny betalningsrad vid prisskillnad."""  # Beskrivning
    if nytt_datum <= date.today():                                                                  # Kontrollera att nytt datum är tidigast imorgon
        return False, "Bussen kan tidigast bokas från och med imorgon."                             # Stoppa om någon försöker boka dagens datum

    try:                                                                                            # Försök spara alla ändringar:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor()                                                                      # Skapa budbärare

        slut_kommun = nya_mal[-1]["municipality_id"]                                                # Kolla vilken kommun det nya sista besöksmålet ligger i
        cursor.execute(                                                                             # Steg 1: Uppdatera slutkommunen på bussrutten:
            "UPDATE routes SET to_municipality_id = %s WHERE route_id = %s",                        # SQL-kommando för att ändra en rad
            (slut_kommun, route_id),                                                                # Nya slutkommunen och ruttens ID
        )                                                                                           # Rutt uppdaterad

        ny_beskrivning = ", ".join([m["plats_namn"] for m in nya_mal])                              # Skriv en ny sammanfattning av utflyktsmålen
        cursor.execute(                                                                             # Steg 2: Uppdatera beskrivningen på resepaketet:
            "UPDATE packages SET description = %s WHERE package_id = %s",                           # SQL-kommando
            (ny_beskrivning[:255], package_id),                                                     # Nya beskrivningen (max 255 tecken) och paketets ID
        )                                                                                           # Paketbeskrivning uppdaterad

        cursor.execute(                                                                             # Steg 3a: Städa bort paketets gamla nöjes-kopplingar...
            "DELETE FROM package_amusements WHERE package_id = %s", (package_id,)                   # Tar bort gamla val
        )                                                                                           # Gamla nöjen rensade
        cursor.execute(                                                                             # Steg 3b: Städa bort paketets gamla plats-kopplingar...
            "DELETE FROM package_places WHERE package_id = %s", (package_id,)                       # Tar bort gamla val
        )                                                                                           # Gamla platser rensade
        cursor.execute(                                                                             # Steg 3c: Städa bort paketets gamla fika-kopplingar...
            "DELETE FROM package_fika WHERE package_id = %s", (package_id,)                         # Tar bort gamla val
        )                                                                                           # Gamla fik rensade (nu är bordet rent!)

        for mal in nya_mal:                                                                         # Steg 4: Lägg in de NYA valda utflyktsmålen i kopplingstabellerna:
            if mal["kategori"] == "amusement":                                                      # Om det är ett nöje...
                cursor.execute(                                                                     # ...lägg in i "package_amusements"
                    "INSERT INTO package_amusements (package_id, amusement_id) VALUES (%s, %s)",    # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paket-ID och nöjes-ID
                )                                                                                   # Nöje inlagt
            elif mal["kategori"] == "place":                                                        # Om det är en plats...
                cursor.execute(                                                                     # ...lägg in i "package_places"
                    "INSERT INTO package_places (package_id, place_id) VALUES (%s, %s)",            # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paket-ID och plats-ID
                )                                                                                   # Plats inlagd
            elif mal["kategori"] == "fika":                                                         # Om det är ett fik...
                cursor.execute(                                                                     # ...lägg in i "package_fika"
                    "INSERT INTO package_fika (package_id, fika_id) VALUES (%s, %s)",                # SQL-kommando
                    (package_id, mal["id"]),                                                        # Paket-ID och fika-ID
                )                                                                                   # Fik inlagt

        cursor.execute(                                                                             # Steg 5: Uppdatera själva bokningsraden med nytt datum, antal personer och totalpris:
            """
            UPDATE bookings                                                                         -- Ändra i bokningstabellen:
            SET travel_date = %s,                                                                   -- Sätt nytt avresedatum
                number_of_adults = %s,                                                              -- Sätt nytt antal vuxna
                number_of_children = %s,                                                            -- Sätt nytt antal barn
                total_price = %s                                                                    -- Sätt nytt totalpris
            WHERE booking_id = %s                                                                   -- För just det här bokningsnumret
            """,                                                                                    # SQL-mall klar
            (nytt_datum, adults, children, nytt_totalpris, booking_id),                             # De nya siffrorna som ska in
        )                                                                                           # Bokningen är uppdaterad

        if abs(mellanskillnad) >= 0.01:                                                             # Steg 6: Om priset ändrades med minst 1 öre (åt något håll):
            cursor.execute(                                                                         # Skapa ett nytt kvitto i betalningstabellen för tillägget eller återbetalningen!
                """
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)           -- Ny rad i betalningstabellen
                VALUES (%s, %s, %s, 'Paid')                                                         -- Med status "Paid"
                """,                                                                                # SQL-mall klar
                (booking_id, mellanskillnad, payment_method),                                       # Bokningsnr, mellanskillnaden (t.ex. -150 kr eller +200 kr) och betalsätt
            )                                                                                       # Nytt kvitto skapat!

        conn.commit()                                                                               # Tryck på SPARA i databasen så alla ändringar spikas fast!
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return True, None                                                                           # Säg till frontend att allt gick som smort!
    except mysql.connector.Error as err:                                                            # Om databasen protesterade:
        return False, str(err)                                                                      # Meddela att det inte gick och skicka med felorsaken


def avboka_bokning_i_db(booking_id, aterbetalning_belopp, payment_method):                          # Receptet som avbokar en betald resa och skapar ett återbetalningskvitto
    """Sätter bokningsstatus till Cancelled och registrerar återbetalning i payments."""            # Beskrivning
    try:                                                                                            # Försök genomföra avbokningen i databasen:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor()                                                                      # Skapa vår budbärare

        cursor.execute(                                                                             # Steg 1: Ändra bokningens status till 'Cancelled':
            "UPDATE bookings SET booking_status = 'Cancelled' WHERE booking_id = %s",               # SQL-kommando för avbokning
            (booking_id,),                                                                          # Bokningsnumret som ska avbokas
        )                                                                                           # Bokningen är nu markerad som avbokad

        if float(aterbetalning_belopp) > 0:                                                         # Steg 2: Om kunden har betalat pengar som ska återbetalas:
            negativt_belopp = -abs(round(float(aterbetalning_belopp), 2))                           # Gör beloppet negativt så det syns som återbetalning på kvittot
            cursor.execute(                                                                         # Lägg in återbetalningsraden i tabellen "payments":
                """
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)           -- Ny rad i betalningstabellen
                VALUES (%s, %s, %s, 'Paid')                                                         -- Med status "Paid"
                """,                                                                                # SQL-mall klar
                (booking_id, negativt_belopp, payment_method),                                      # Bokningsnr, minusbeloppet och valt betalsätt
            )                                                                                       # Återbetalningskvitto skapat!

        conn.commit()                                                                               # Spara avbokningen och återbetalningen permanent i databasen
        cursor.close()                                                                              # Stäng budbäraren
        conn.close()                                                                                # Lägg på luren
        return True, None                                                                           # Meddela frontend att avbokningen lyckades!
    except mysql.connector.Error as err:                                                            # Om något gick snett i databasen:
        return False, str(err)                                                                      # Skicka tillbaka felmeddelandet


# ----------------------------------------
# Sista kapitlet: Kvittolådan!
# Betalningshistorik (Nyaste överst)
# Hämtar alla kvitton så kunden (och admin) har järnkoll på ekonomin
# ----------------------------------------

def hamta_betalningshistorik(customer_id, is_admin=False):                                          # Receptet som plockar fram alla kvitton
    """Hämtar alla bokningar och tillhörande betalningar, sorterat med nyaste överst."""            # Beskrivning
    try:                                                                                            # Försök hämta kvittohistoriken:
        conn = get_db_connection()                                                                  # Ring upp databasen
        cursor = conn.cursor(dictionary=True)                                                       # Skapa budbärare
        where_clause = "" if is_admin else "WHERE b.customer_id = %s"                               # Admin har inget filter (ser allt!), vanlig kund filtreras på sitt eget kundnummer
        query = f"""
            SELECT                                              -- Hämta hela denna önskelista med kolumner:
                b.booking_id,                                   -- Bokningsnumret
                b.customer_id,                                  -- Kundnumret
                c.first_name,                                   -- Kundens förnamn
                c.last_name,                                    -- Kundens efternamn
                b.booking_date,                                 -- När bokningen ursprungligen gjordes
                b.travel_date,                                  -- Vilket datum bussen går
                b.number_of_adults,                             -- Antal vuxna
                b.number_of_children,                           -- Antal barn
                b.total_price,                                  -- Bokningens totalpris
                b.booking_status,                               -- Bokningens status (t.ex. "Confirmed")
                p.package_name,                                 -- Namnet på resepaketet
                p.description AS resmal,                        -- Vilka besöksmål som ingår i paketet
                m_from.municipality_name AS start_kommun,       -- Namnet på kommunen där resan startar
                m_to.municipality_name AS slut_kommun,          -- Namnet på kommunen där resan slutar
                pay.payment_id,                                 -- Kvittots eget ID-nummer
                pay.amount,                                     -- Beloppet som betalades (eller återbetalades) på just detta kvitto
                pay.payment_method,                             -- Betalsättet (Swish, Kort eller Klarna)
                pay.payment_status,                             -- Betalningsstatus ("Paid")
                pay.payment_date                                -- Exakt datum och klockslag för betalningen
            FROM bookings b                                     -- Utgå från bokningstabellen ("b")
            JOIN customers c ON b.customer_id = c.customer_id   -- Koppla på kundtabellen ("c") för att få kundens namn
            JOIN packages p ON b.package_id = p.package_id      -- Koppla på pakettabellen ("p") för att få resmålen
            JOIN routes r ON p.route_id = r.route_id            -- Koppla på ruttabellen ("r") för att se var bussen kör
            JOIN municipalities m_from ON r.from_municipality_id = m_from.municipality_id                           -- Slå upp namnet på startkommunen
            JOIN municipalities m_to ON r.to_municipality_id = m_to.municipality_id                                 -- Slå upp namnet på slutkommunen
            LEFT JOIN payments pay ON b.booking_id = pay.booking_id                                                 -- Koppla på alla betalningar/kvitton som hör till bokningen
            {where_clause}                                                                                          -- Lägg till filtret (tomt för admin, specifikt kund-ID för vanlig kund)
            ORDER BY COALESCE(pay.payment_date, b.booking_date) DESC, pay.payment_id DESC, b.booking_id DESC        -- Sortera så det absolut nyaste kvittot hamnar allra överst!
        """                                         # Den maffiga SQL-frågan är klar
        if is_admin:                                # Om det är chefen som begär kvitton:
            cursor.execute(query)                   # Kör frågan utan kund-ID-begränsning
        else:                                       # Om det är en vanlig kund:
            cursor.execute(query, (customer_id,))   # Skicka med kundens ID-nummer så de bara ser sina egna kvitton
        historik = cursor.fetchall()                # Ta emot alla kvittorader från databasen
        cursor.close()                              # Stäng budbäraren
        conn.close()                                # Lägg på luren till databasen för sista gången i filen
        return historik                             # Leverera hela bunten med kvitton upp till popup-fönstret i frontend!
    except mysql.connector.Error:                   # Om databasen skulle råka ha stängt för dagen:
        return []                                   # Skicka tillbaka en tom lista så allt landar mjukt
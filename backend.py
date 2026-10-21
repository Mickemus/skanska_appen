import mysql.connector
import streamlit as st
from sshtunnel import SSHTunnelForwarder
# Konstanter för Superduperbussen
MAX_BUSS_PLATSER = 50
DEFAULT_BOKADE_PLATSER = 45

# Katalog över alla aktiviteter
ALLA_AKTIVITETER = [
    # --- NÖJEN ---
    {
        "kategori": "amusement",
        "id": 1,
        "plats_namn": "Ystad Djurpark",
        "kort_info": "Info om Ystad Djurpark",
        "bild_url": "https://placehold.co/600x300?text=Ystad+Djurpark",
        "lang_text": "Information om Ystad Djurpark, djuren, matställen och aktiviteter.",
        "municipality_id": 29,
        "pris": 299.00,
    },
    {
        "kategori": "amusement",
        "id": 2,
        "plats_namn": "Tosselilla",
        "kort_info": "Info om Tosselilla",
        "bild_url": "https://placehold.co/600x300?text=Tosselilla",
        "lang_text": "Information om Tosselilla Sommarland, vattenland och karuseller.",
        "municipality_id": 26,
        "pris": 415.00,
    },
    {
        "kategori": "amusement",
        "id": 3,
        "plats_namn": "Malmö Museum",
        "kort_info": "Info om Malmö Museum",
        "bild_url": "https://placehold.co/600x300?text=Malmo+Museum",
        "lang_text": "Information om Malmö Museum, slottet, akvariet och utställningarna.",
        "municipality_id": 17,
        "pris": 60.00,
    },
    # --- PLATSER ---
    {
        "kategori": "place",
        "id": 1,
        "plats_namn": "Glumslövs Backar",
        "kort_info": "Info om Glumslövs Backar",
        "bild_url": "https://placehold.co/600x300?text=Glumslovs+Backar",
        "lang_text": "Information om vandringsleder och utsikten över Öresund.",
        "municipality_id": 14,
        "pris": 0.00,
    },
    {
        "kategori": "place",
        "id": 2,
        "plats_namn": "Söderåsens Nationalpark",
        "kort_info": "Info om Söderåsens Nationalpark",
        "bild_url": "https://placehold.co/600x300?text=Soderasen",
        "lang_text": "Information om Kopparhatten, Skäralid och bokskogarna.",
        "municipality_id": 11,
        "pris": 0.00,
    },
    {
        "kategori": "place",
        "id": 3,
        "plats_namn": "Ales Stenar",
        "kort_info": "Info om Ales Stenar",
        "bild_url": "https://placehold.co/600x300?text=Ales+Stenar",
        "lang_text": "Information om skeppssättningen vid Kåseberga.",
        "municipality_id": 29,
        "pris": 0.00,
    },
    # --- FIKA ---
    {
        "kategori": "fika",
        "id": 1,
        "plats_namn": "Ebbas Fik",
        "kort_info": "Info om Ebbas Fik",
        "bild_url": "https://placehold.co/600x300?text=Ebbas+Fik",
        "lang_text": "Information om 50-talsfiket i Helsingborg.",
        "municipality_id": 6,
        "pris": 0.00,
    },
    {
        "kategori": "fika",
        "id": 2,
        "plats_namn": "Färg från förr",
        "kort_info": "Info om Färg från förr",
        "bild_url": "https://placehold.co/600x300?text=Farg+fran+forr",
        "lang_text": "Information om Färg från förr, byggnadsvård och fika.",
        "municipality_id": 29,
        "pris": 0.00,
    },
    {
        "kategori": "fika",
        "id": 3,
        "plats_namn": "Alice och Kattens Tesalong",
        "kort_info": "Info om Alice och Kattens Tesalong",
        "bild_url": "https://placehold.co/600x300?text=Alice+och+Katten",
        "lang_text": "Information om tesalongen i Lund.",
        "municipality_id": 16,
        "pris": 0.00,
    },
]


# ----------------------------------------
# Databaskoppling
# ----------------------------------------


@st.cache_resource
def get_ssh_tunnel():
    tunnel = SSHTunnelForwarder(
        (st.secrets["SSH_HOST"].strip(), 22),
        ssh_username=st.secrets["SSH_USER"].strip(),
        ssh_password=st.secrets["SSH_PASSWORD"],
        remote_bind_address=(
            st.secrets["DB_HOST"].replace(":3306", "").strip(),
            3306,
        ),
    )
    tunnel.start()
    return tunnel


def get_db_connection():
    try:
        tunnel = get_ssh_tunnel()
        if not tunnel.is_active:
            tunnel.restart()

        return mysql.connector.connect(
            host="127.0.0.1",
            port=tunnel.local_bind_port,
            user=st.secrets["DB_USER"].strip(),
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_NAME"].strip(),
            connection_timeout=10,
            use_pure=True,
        )
    except Exception as err:
        st.error(f"🚨 Kunde inte ansluta till databasen: {err}")
        print(f"CRITICAL DB CONNECTION ERROR: {err}")
        raise

def verifiera_inloggning(email, password):
    """Kollar om e-post och lösenord stämmer i tabellen customers."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, m.municipality_name 
            FROM customers c
            LEFT JOIN municipalities m ON c.municipality_id = m.municipality_id
            WHERE c.email = %s AND c.password = %s
        """
        cursor.execute(query, (email.strip(), password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except mysql.connector.Error as err:
        st.error(f"Databasfel vid inloggning: {err}")
        print(f"DB ERROR: {err}")
        return None


# ----------------------------------------
# Affärslogik: Prisberäkning och Sökfilter
# ----------------------------------------
def berakna_respris(kund_kommun_id, valda_mal, adults, children):
    """Räknar ut bussavgift, antal unika kommuner och totalpris för en resa."""
    unika_kommuner = {kund_kommun_id}
    biljett_pris_per_person = 0.0

    for mal in valda_mal:
        biljett_pris_per_person += mal["pris"]
        unika_kommuner.add(mal["municipality_id"])

    antal_resenarer = adults + children
    buss_avgift = len(unika_kommuner) * 45.00
    total_price = (biljett_pris_per_person * antal_resenarer) + buss_avgift

    return total_price, buss_avgift, len(unika_kommuner), antal_resenarer


def filtrera_aktiviteter(kategori_kod, sok_ord=""):
    """Hämtar aktiviteter för en kategori och filtrerar på eventuell sökfras."""
    items = [a for a in ALLA_AKTIVITETER if a["kategori"] == kategori_kod]
    if sok_ord and sok_ord.strip():
        s = sok_ord.lower().strip()
        items = [
            a
            for a in items
            if s in a["plats_namn"].lower()
            or s in a["kort_info"].lower()
            or s in a["lang_text"].lower()
        ]
    return items


# ----------------------------------------
# Användare, Inloggning & Kommuner
# ----------------------------------------
def hamta_kommuner():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT municipality_id, municipality_name FROM municipalities ORDER BY municipality_name"
        )
        kommuner = cursor.fetchall()
        cursor.close()
        conn.close()
        return kommuner
    except mysql.connector.Error:
        return []


def registrera_kund_i_db(first_name, last_name, email, password, phone, municipality_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = """
            INSERT INTO customers (first_name, last_name, email, password, phone, municipality_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                first_name.strip(),
                last_name.strip(),
                email.strip(),
                password,
                phone.strip() if phone.strip() else None,
                municipality_id,
            ),
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Konto skapat! Du är nu inloggad."
    except mysql.connector.Error as err:
        if err.errno == 1062:
            return False, "E-postadressen eller telefonnumret finns redan registrerat."
        elif err.errno == 3819:
            return False, "Uppgifterna uppfyller inte databasens formatkrav (kontrollera namn, e-post och lösenord)."
        return False, f"Databasfel vid registrering: {err}"


def verifiera_inloggning(email, password):
    """Kollar om e-post och lösenord stämmer i tabellen customers."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, m.municipality_name 
            FROM customers c
            LEFT JOIN municipalities m ON c.municipality_id = m.municipality_id
            WHERE c.email = %s AND c.password = %s
        """
        cursor.execute(query, (email.strip(), password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except mysql.connector.Error:
        return None


def hamta_alla_kunder():
    """Hämtar alla registrerade kunder för Adminpanelen."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT c.customer_id, c.first_name, c.last_name, c.email, c.phone, m.municipality_name
            FROM customers c
            JOIN municipalities m ON c.municipality_id = m.municipality_id
            ORDER BY c.customer_id ASC
            """
        )
        alla_kunder = cursor.fetchall()
        cursor.close()
        conn.close()
        return alla_kunder
    except mysql.connector.Error:
        return []


# ----------------------------------------
# Bussplatser & Bokningar
# ----------------------------------------
def hamta_lediga_platser(travel_date, exkludera_booking_id=None):
    """
    Räknar ut lediga platser på bussen (Max 50 platser, 45 bokade som default).
    Vid redigering exkluderas bokningens egna platser.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if exkludera_booking_id:
            query = """
                SELECT COALESCE(SUM(number_of_adults + number_of_children), 0)
                FROM bookings
                WHERE travel_date = %s AND booking_status != 'Cancelled' AND booking_id != %s
            """
            cursor.execute(query, (travel_date, exkludera_booking_id))
        else:
            query = """
                SELECT COALESCE(SUM(number_of_adults + number_of_children), 0)
                FROM bookings
                WHERE travel_date = %s AND booking_status != 'Cancelled'
            """
            cursor.execute(query, (travel_date,))

        bokade_i_db = int(cursor.fetchone()[0])
        cursor.close()
        conn.close()

        totalt_bokade = DEFAULT_BOKADE_PLATSER + bokade_i_db
        lediga = max(0, MAX_BUSS_PLATSER - totalt_bokade)
        return lediga, totalt_bokade
    except mysql.connector.Error:
        return 0, MAX_BUSS_PLATSER


def spara_bokning_i_db(
    user, valda_mal, travel_date, adults, children, total_price, payment_method
):
    """Skapar rutt, paket, kopplingar, bokning och betalning i MySQL."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        start_kommun = user["municipality_id"]
        slut_kommun = valda_mal[-1]["municipality_id"]
        rutt_namn = f"Resa för {user['first_name']} ({travel_date})"

        cursor.execute(
            "INSERT INTO routes (route_name, from_municipality_id, to_municipality_id) VALUES (%s, %s, %s)",
            (rutt_namn, start_kommun, slut_kommun),
        )
        route_id = cursor.lastrowid

        paket_namn = f"Skräddarsytt paket - {user['first_name']}"
        beskrivning = ", ".join([m["namn"] for m in valda_mal])
        cursor.execute(
            "INSERT INTO packages (package_name, description, route_id, transportation_id) VALUES (%s, %s, %s, 1)",
            (paket_namn, beskrivning[:255], route_id),
        )
        package_id = cursor.lastrowid

        for mal in valda_mal:
            if mal["kategori"] == "amusement":
                cursor.execute(
                    "INSERT INTO package_amusements (package_id, amusement_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )
            elif mal["kategori"] == "place":
                cursor.execute(
                    "INSERT INTO package_places (package_id, place_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )
            elif mal["kategori"] == "fika":
                cursor.execute(
                    "INSERT INTO package_fika (package_id, fika_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )

        cursor.execute(
            """
            INSERT INTO bookings 
            (customer_id, package_id, travel_date, number_of_adults, number_of_children, total_price, booking_status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Confirmed')
            """,
            (
                user["customer_id"],
                package_id,
                travel_date,
                adults,
                children,
                total_price,
            ),
        )
        booking_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO payments (booking_id, amount, payment_method, payment_status)
            VALUES (%s, %s, %s, 'Paid')
            """,
            (booking_id, total_price, payment_method),
        )

        conn.commit()
        cursor.close()
        conn.close()
        return booking_id, None
    except mysql.connector.Error as err:
        return None, str(err)


def hamta_redigerbara_bokningar(customer_id, is_admin=False):
    """Hämtar bekräftade bokningar som inte har inträffat ännu samt deras valda resmål."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        where_clause = (
            "WHERE b.booking_status = 'Confirmed' AND b.travel_date > CURDATE()"
            if is_admin
            else "WHERE b.customer_id = %s AND b.booking_status = 'Confirmed' AND b.travel_date > CURDATE()"
        )
        query = f"""
            SELECT 
                b.booking_id,
                b.customer_id,
                b.package_id,
                b.travel_date,
                b.number_of_adults,
                b.number_of_children,
                b.total_price,
                p.route_id,
                p.description,
                c.first_name,
                c.last_name,
                c.municipality_id AS kund_kommun_id
            FROM bookings b
            JOIN packages p ON b.package_id = p.package_id
            JOIN customers c ON b.customer_id = c.customer_id
            {where_clause}
            ORDER BY b.travel_date ASC, b.booking_id DESC
        """
        if is_admin:
            cursor.execute(query)
        else:
            cursor.execute(query, (customer_id,))
        bokningar = cursor.fetchall()

        for b in bokningar:
            pid = b["package_id"]
            valda_nycklar = set()

            cursor.execute(
                "SELECT amusement_id FROM package_amusements WHERE package_id = %s",
                (pid,),
            )
            for row in cursor.fetchall():
                valda_nycklar.add(f"amusement_{row['amusement_id']}")

            cursor.execute(
                "SELECT place_id FROM package_places WHERE package_id = %s", (pid,)
            )
            for row in cursor.fetchall():
                valda_nycklar.add(f"place_{row['place_id']}")

            cursor.execute(
                "SELECT fika_id FROM package_fika WHERE package_id = %s", (pid,)
            )
            for row in cursor.fetchall():
                valda_nycklar.add(f"fika_{row['fika_id']}")

            b["valda_nycklar"] = valda_nycklar

        cursor.close()
        conn.close()
        return bokningar
    except mysql.connector.Error:
        return []


def uppdatera_bokning_i_db(
    booking_id,
    package_id,
    route_id,
    nya_mal,
    nytt_datum,
    adults,
    children,
    nytt_totalpris,
    mellanskillnad,
    payment_method,
):
    """Uppdaterar rutt, paket, destinationer, bokning och skapar ny betalningsrad vid prisskillnad."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        slut_kommun = nya_mal[-1]["municipality_id"]
        cursor.execute(
            "UPDATE routes SET to_municipality_id = %s WHERE route_id = %s",
            (slut_kommun, route_id),
        )

        ny_beskrivning = ", ".join([m["plats_namn"] for m in nya_mal])
        cursor.execute(
            "UPDATE packages SET description = %s WHERE package_id = %s",
            (ny_beskrivning[:255], package_id),
        )

        cursor.execute(
            "DELETE FROM package_amusements WHERE package_id = %s", (package_id,)
        )
        cursor.execute(
            "DELETE FROM package_places WHERE package_id = %s", (package_id,)
        )
        cursor.execute(
            "DELETE FROM package_fika WHERE package_id = %s", (package_id,)
        )

        for mal in nya_mal:
            if mal["kategori"] == "amusement":
                cursor.execute(
                    "INSERT INTO package_amusements (package_id, amusement_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )
            elif mal["kategori"] == "place":
                cursor.execute(
                    "INSERT INTO package_places (package_id, place_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )
            elif mal["kategori"] == "fika":
                cursor.execute(
                    "INSERT INTO package_fika (package_id, fika_id) VALUES (%s, %s)",
                    (package_id, mal["id"]),
                )

        cursor.execute(
            """
            UPDATE bookings
            SET travel_date = %s,
                number_of_adults = %s,
                number_of_children = %s,
                total_price = %s
            WHERE booking_id = %s
            """,
            (nytt_datum, adults, children, nytt_totalpris, booking_id),
        )

        if abs(mellanskillnad) >= 0.01:
            cursor.execute(
                """
                INSERT INTO payments (booking_id, amount, payment_method, payment_status)
                VALUES (%s, %s, %s, 'Paid')
                """,
                (booking_id, mellanskillnad, payment_method),
            )

        conn.commit()
        cursor.close()
        conn.close()
        return True, None
    except mysql.connector.Error as err:
        return False, str(err)


# ----------------------------------------
# Betalningshistorik (Nyaste överst)
# ----------------------------------------
def hamta_betalningshistorik(customer_id, is_admin=False):
    """Hämtar alla bokningar och tillhörande betalningar, sorterat med nyaste överst."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        where_clause = "" if is_admin else "WHERE b.customer_id = %s"
        query = f"""
            SELECT 
                b.booking_id,
                b.customer_id,
                c.first_name,
                c.last_name,
                b.booking_date,
                b.travel_date,
                b.number_of_adults,
                b.number_of_children,
                b.total_price,
                b.booking_status,
                p.package_name,
                p.description AS resmal,
                m_from.municipality_name AS start_kommun,
                m_to.municipality_name AS slut_kommun,
                pay.payment_id,
                pay.amount,
                pay.payment_method,
                pay.payment_status,
                pay.payment_date
            FROM bookings b
            JOIN customers c ON b.customer_id = c.customer_id
            JOIN packages p ON b.package_id = p.package_id
            JOIN routes r ON p.route_id = r.route_id
            JOIN municipalities m_from ON r.from_municipality_id = m_from.municipality_id
            JOIN municipalities m_to ON r.to_municipality_id = m_to.municipality_id
            LEFT JOIN payments pay ON b.booking_id = pay.booking_id
            {where_clause}
            ORDER BY COALESCE(pay.payment_date, b.booking_date) DESC, pay.payment_id DESC, b.booking_id DESC
        """
        if is_admin:
            cursor.execute(query)
        else:
            cursor.execute(query, (customer_id,))
        historik = cursor.fetchall()
        cursor.close()
        conn.close()
        return historik
    except mysql.connector.Error:
        return []
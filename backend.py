import mysql.connector
import streamlit as st
from sshtunnel import SSHTunnelForwarder

# Konstanter för Superduperbussen
MAX_BUSS_PLATSER = 50
DEFAULT_BOKADE_PLATSER = 45

VECKODAGAR = {
    1: "Måndag",
    2: "Tisdag",
    3: "Onsdag",
    4: "Torsdag",
    5: "Fredag",
    6: "Lördag",
    7: "Söndag",
}

# Standardbilder kopplade till kategori och ID (eftersom bild-URL inte lagras i DB)
BILD_KATALOG = {
    ("amusement", 1): "https://placehold.co/600x300?text=Ystad+Djurpark",
    ("amusement", 2): "https://placehold.co/600x300?text=Tosselilla",
    ("amusement", 3): "https://placehold.co/600x300?text=Malmo+Museum",
    ("place", 1): "https://placehold.co/600x300?text=Glumslovs+Backar",
    ("place", 2): "https://placehold.co/600x300?text=Soderasen",
    ("place", 3): "https://placehold.co/600x300?text=Ales+Stenar",
    ("fika", 1): "https://placehold.co/600x300?text=Ebbas+Fik",
    ("fika", 2): "https://placehold.co/600x300?text=Farg+fran+forr",
    ("fika", 3): "https://placehold.co/600x300?text=Alice+och+Katten",
}


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
        set_keepalive=30.0,
    )
    tunnel.start()
    return tunnel


def _connect_mysql(port):
    return mysql.connector.connect(
        host="127.0.0.1",
        port=port,
        user=st.secrets["DB_USER"].strip(),
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_NAME"].strip(),
        connection_timeout=10,
        use_pure=True,
    )


def get_db_connection():
    try:
        tunnel = get_ssh_tunnel()
        if not tunnel.is_active:
            tunnel.restart()
        try:
            return _connect_mysql(tunnel.local_bind_port)
        except Exception:
            try:
                tunnel.stop()
            except Exception:
                pass
            get_ssh_tunnel.clear()
            tunnel = get_ssh_tunnel()
            return _connect_mysql(tunnel.local_bind_port)
    except Exception as err:
        print(f"CRITICAL DB CONNECTION ERROR: {err}")
        raise mysql.connector.Error(str(err))


# ----------------------------------------
# Hämta aktiviteter, info & öppettider från DB
# ----------------------------------------
def _format_tid(val):
    """Omvandlar MySQL TIME (timedelta eller str) till HH:MM."""
    if val is None:
        return None
    if hasattr(val, "total_seconds"):
        total_sec = int(val.total_seconds())
        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    return str(val)[:5]


def _hamta_oppettider_dict(cursor, tabell_namn, id_kolumn):
    """Hämtar öppettider grupperade per aktivitets-ID från angiven öppettidstabell."""
    cursor.execute(
        f"""
        SELECT {id_kolumn} AS item_id, weekday, is_open, opening_time, closing_time
        FROM {tabell_namn}
        ORDER BY {id_kolumn} ASC, weekday ASC
        """
    )
    oppettider_per_id = {}
    for row in cursor.fetchall():
        item_id = row["item_id"]
        oppettider_per_id.setdefault(item_id, {})
        open_str = _format_tid(row["opening_time"])
        close_str = _format_tid(row["closing_time"])

        if not row["is_open"]:
            visnings_text = "Stängt"
        elif open_str == "00:00" and close_str == "23:59":
            visnings_text = "Öppet dygnet runt (24/7)"
        else:
            visnings_text = f"{open_str}–{close_str}"

        oppettider_per_id[item_id][int(row["weekday"])] = {
            "weekday": int(row["weekday"]),
            "dag_namn": VECKODAGAR.get(int(row["weekday"]), f"Dag {row['weekday']}"),
            "is_open": bool(row["is_open"]),
            "opening_time": open_str,
            "closing_time": close_str,
            "text": visnings_text,
        }
    return oppettider_per_id


@st.cache_data(ttl=60)
def hamta_alla_aktiviteter():
    """
    Hämtar samtliga nöjen, platser och fikaställen inklusive deras
    infotext, kommun och öppettider direkt från databasen.
    """
    aktiviteter = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        amusement_hours = _hamta_oppettider_dict(
            cursor, "amusement_opening_hours", "amusement_id"
        )
        place_hours = _hamta_oppettider_dict(
            cursor, "place_opening_hours", "place_id"
        )
        fika_hours = _hamta_oppettider_dict(
            cursor, "fika_opening_hours", "fika_id"
        )

        # 1. Nöjen (amusements)
        cursor.execute(
            """
            SELECT a.amusement_id AS id, a.amusement_name AS namn, a.amusement_info AS info,
                   a.ticket_price AS pris, a.municipality_id, m.municipality_name
            FROM amusements a
            JOIN municipalities m ON a.municipality_id = m.municipality_id
            ORDER BY a.amusement_id ASC
            """
        )
        for row in cursor.fetchall():
            item_id = row["id"]
            aktiviteter.append(
                {
                    "kategori": "amusement",
                    "id": item_id,
                    "plats_namn": row["namn"],
                    "kort_info": f"📍 Kommun: {row['municipality_name']}",
                    "bild_url": BILD_KATALOG.get(
                        ("amusement", item_id),
                        f"https://placehold.co/600x300?text={row['namn']}",
                    ),
                    "lang_text": row["info"],
                    "municipality_id": row["municipality_id"],
                    "municipality_name": row["municipality_name"],
                    "pris": float(row["pris"]),
                    "oppettider": amusement_hours.get(item_id, {}),
                }
            )

        # 2. Platser (places)
        cursor.execute(
            """
            SELECT p.place_id AS id, p.place_name AS namn, p.place_info AS info,
                   p.municipality_id, m.municipality_name
            FROM places p
            JOIN municipalities m ON p.municipality_id = m.municipality_id
            ORDER BY p.place_id ASC
            """
        )
        for row in cursor.fetchall():
            item_id = row["id"]
            aktiviteter.append(
                {
                    "kategori": "place",
                    "id": item_id,
                    "plats_namn": row["namn"],
                    "kort_info": f"📍 Kommun: {row['municipality_name']}",
                    "bild_url": BILD_KATALOG.get(
                        ("place", item_id),
                        f"https://placehold.co/600x300?text={row['namn']}",
                    ),
                    "lang_text": row["info"],
                    "municipality_id": row["municipality_id"],
                    "municipality_name": row["municipality_name"],
                    "pris": 0.00,
                    "oppettider": place_hours.get(item_id, {}),
                }
            )

        # 3. Fika (fika)
        cursor.execute(
            """
            SELECT f.fika_id AS id, f.fika_name AS namn, f.fika_info AS info,
                   f.municipality_id, m.municipality_name
            FROM fika f
            JOIN municipalities m ON f.municipality_id = m.municipality_id
            ORDER BY f.fika_id ASC
            """
        )
        for row in cursor.fetchall():
            item_id = row["id"]
            aktiviteter.append(
                {
                    "kategori": "fika",
                    "id": item_id,
                    "plats_namn": row["namn"],
                    "kort_info": f"📍 Kommun: {row['municipality_name']}",
                    "bild_url": BILD_KATALOG.get(
                        ("fika", item_id),
                        f"https://placehold.co/600x300?text={row['namn']}",
                    ),
                    "lang_text": row["info"],
                    "municipality_id": row["municipality_id"],
                    "municipality_name": row["municipality_name"],
                    "pris": 0.00,
                    "oppettider": fika_hours.get(item_id, {}),
                }
            )

        cursor.close()
        conn.close()
        return aktiviteter
    except mysql.connector.Error as err:
        st.error(f"Kunde inte hämta aktiviteter från databasen: {err}")
        return []


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
    """Hämtar aktiviteter från databasen för en kategori och filtrerar på eventuell sökfras."""
    alla = hamta_alla_aktiviteter()
    items = [a for a in alla if a["kategori"] == kategori_kod]
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
    except mysql.connector.Error as err:
        st.error(f"Databasfel vid inloggning: {err}")
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
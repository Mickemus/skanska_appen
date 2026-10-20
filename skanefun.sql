/*
   --------------------------------------------------------------------------
   Database: skanefun
   --------------------------------------------------------------------------
   Created by:
   Aurita Milazimi,
   Mirjana Momiroska,
   Emil Christian Randau,
   Mikael Söderstjerna
   --------------------------------------------------------------------------
   Innehåll:
   
   /* Kommuner (municipalities) för skånes 33 kommuner
   /* Kunder (customers)
   /* Superduperbussen (transportations)
   /* Rutter (routes) A-B
   
   /* Platser (places)
   /* Fika (fika)
   /* Nöjen (amusements)
   
   /* resepaketet (packages)
   
   /* En rutt genom kommuner (route_municipalities) kopplingstabell
   /* places i paket (package_places) kopplingstabell
   /* nöjen i paketformat (package_amusements) kopplingstabell
   /* fika som paket (package_fika) kopplingstabell
   
   /* Bokningar (bookings)
   /* Moneeeey (payments)
   --------------------------------------------------------------------------
 */
 
DROP DATABASE IF EXISTS skanefun;
CREATE DATABASE skanefun;
USE skanefun;

/* Kommuner (municipalities) för skånes 33 kommuner
   
   Den här tabellen är själva hjärtar i databasen som innehåller samtliga 33 kommuner 
   för Skåne. Varje kommun får ett eget id, namn, koordinater och en liten fee för att 
   passera.
--------
   Uppbyggnad:
--------	
    auto_increment primary key: Rräknar upp id (1, 2, 3...) för varje kommun.
   
	unique på namn: Förhindrar att man råkar lägga in samma kommun.
   
	point: En särskild datatyp för koordinater, long och lat, 
	vilket gör att man kan räkna ut avstånden mellan kommuners points.
    
    decimal(10,2) DEFAULT 45.00: Cash ska alltid lagras som decimaltal och standard 45kr.
    
   check (inga_dubbla_mellanslag_kommun): hindrar slarvfel med dubbla mellanslag i kommunnamnet.
---------
   koppling
---------  
  Det här är en "föräldratabell" som massa pekar mot:
   kunder har en "hemkommun".
   rutter startar, passerar och slutar via kommuner.
   places, fika, amusements tillhör en kommun.
----------slut kommuntabell-----------------*/

CREATE TABLE municipalities (
    municipality_id INT AUTO_INCREMENT PRIMARY KEY,
    municipality_name VARCHAR(50) NOT NULL UNIQUE,
        CONSTRAINT inga_dubbla_mellanslag_kommun 
        CHECK (municipality_name NOT LIKE '%  %'),
    coordinates POINT NOT NULL,
    pass_cost DECIMAL(10,2) NOT NULL DEFAULT 45.00
);

INSERT INTO municipalities (municipality_name, coordinates) VALUES
('Bjuv', POINT(12.919, 56.084)), 			/*1*/
('Bromölla', POINT(14.469, 56.074)), 		/*2*/
('Burlöv', POINT(13.070, 55.636)), 			/*3*/
('Båstad', POINT(12.833, 56.427)), 			/*4*/
('Eslöv', POINT(13.304, 55.839)), 			/*5*/
('Helsingborg', POINT(12.694, 56.046)), 	/*6*/
('Hässleholm', POINT(13.766, 56.159)), 		/*7*/
('Höganäs', POINT(12.555, 56.200)), 		/*8*/
('Hörby', POINT(13.662, 55.852)), 			/*9*/
('Höör', POINT(13.543, 55.934)), 			/*10*/
('Klippan', POINT(13.129, 56.135)), 		/*11*/
('Kristianstad', POINT(14.156, 56.031)), 	/*12*/
('Kävlinge', POINT(13.109, 55.794)), 		/*13*/
('Landskrona', POINT(12.830, 55.870)), 		/*14*/
('Lomma', POINT(13.068, 55.673)), 			/*15*/
('Lund', POINT(13.191, 55.704)), 			/*16*/
('Malmö', POINT(13.003, 55.605)), 			/*17*/
('Osby', POINT(13.993, 56.382)), 			/*18*/
('Perstorp', POINT(13.394, 56.138)), 		/*19*/
('Simrishamn', POINT(14.350, 55.556)), 		/*20*/
('Sjöbo', POINT(13.706, 55.632)), 			/*21*/
('Skurup', POINT(13.502, 55.479)), 			/*22*/
('Staffanstorp', POINT(13.208, 55.643)), 	/*23*/
('Svalöv', POINT(13.110, 55.912)), 			/*24*/
('Svedala', POINT(13.235, 55.509)), 		/*25*/
('Tomelilla', POINT(13.951, 55.544)), 		/*26*/
('Trelleborg', POINT(13.157, 55.376)), 		/*27*/
('Vellinge', POINT(13.019, 55.471)), 		/*28*/
('Ystad', POINT(13.820, 55.429)), 			/*29*/
('Åstorp', POINT(12.946, 56.134)), 			/*30*/
('Ängelholm', POINT(12.862, 56.242)), 		/*31*/
('Örkelljunga', POINT(13.278, 56.283)), 	/*32*/
('Östra Göinge', POINT(14.080, 56.257)); 	/*33*/


/* Kunder (customers)
   Sparar information om kunder som förnamn, efternamn, mejladress, 
   telefonnummer samt vilken kommun de bor i.
--------
   Uppbyggnad:
--------	
   email unique: Två konton får inte ha samma mailadress.
   phone varchar(25): Telefonnummer sparas som text (VARCHAR).
   municipality_id: Genom att koppla kunden till en hemkommun vet vi direkt 
   var kunden utgår ifrån... en möjlighet att välja en annan "startposition" bör lyftas.

---------
   koppling
---------  
   hämtar "municipalities" via foreign key (municipality_id)
   kopplad till tabellen "bookings" för vilken kund som har gjort 
   vilken bokning.
*/
CREATE TABLE customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(60) NOT NULL,
    last_name VARCHAR(60) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(25) UNIQUE,
    municipality_id INT NOT NULL,

    /* Stor första bokstav, resten små + inga dubbla mellanslag */
    CONSTRAINT inga_dubbla_mellanslag_fornamn
        CHECK (first_name NOT LIKE '%  %'),
    CONSTRAINT format_fornamn_case
        CHECK (
            first_name COLLATE utf8mb4_bin = CONCAT(
                UPPER(LEFT(first_name, 1)),
                LOWER(SUBSTRING(first_name, 2))
            ) COLLATE utf8mb4_bin
        ),

    CONSTRAINT inga_dubbla_mellanslag_efternamn
        CHECK (last_name NOT LIKE '%  %'),
    CONSTRAINT format_efternamn_case
        CHECK (
            last_name COLLATE utf8mb4_bin = CONCAT(
                UPPER(LEFT(last_name, 1)),
                LOWER(SUBSTRING(last_name, 2))
            ) COLLATE utf8mb4_bin
        ),

    /* måste ha text + @ + domän + punkt + toppdomän (t.ex. .com/.se) och inga dubbla mellanslag */
    CONSTRAINT giltig_email
        CHECK (
            email LIKE '%_@_%.__%'
            AND email NOT LIKE '%  %'
            AND email NOT LIKE '% %'
        ),

    /* Lösenord: Måste vara längre än 6 tecken (dvs minst 7 tecken) */
    CONSTRAINT losenord_langd
        CHECK (CHAR_LENGTH(password) > 6),

    FOREIGN KEY (municipality_id) REFERENCES municipalities(municipality_id)
);

INSERT INTO customers (first_name, last_name, email, password, phone, municipality_id) VALUES
('Admin', 'Skånefun', 'admin@skanefun.se', 'admin123', '070-0000001', 6),         /* Admin */
('Pappa', 'Söderstjerna', 'pappa@gmail.com', '1234567', '070-1234567', 6),         /* Helsingborg */
('Flugan', 'Momiroska', 'flugan@exempel.se', '1234567', '071-2345678', 5),         /* Eslöv */
('Hot-shot', 'Randau', 'hotshot@exempel.se', '1234567', '072-3456789', 12),        /* Kristianstad */
('Scrum-master', 'Milazimi', 'scrummaster@exempel.se', '1234567', '073-4567890', 6); /* Helsingborg */


/* Superduperbussen (transportations)
   En tabell som håller reda på vilka färdmedel som finns till
   våra resepaket....... 1 buss haha.
--------
   Uppbyggnad:
--------	
   enum('Bus') bestämt i listan.
   egen entitet? varför?: Även om vi bara har buss görs en separat tabell det 
   superenkelt att bygga ut systemet senare utan att behöva bygga om paket tabellen.
---------
   koppling
---------  
   kopplas till tabellen packages, där varje paket väljer vilket transportsätt som ingår.
*/
CREATE TABLE transportations (
    transportation_id INT AUTO_INCREMENT PRIMARY KEY,
    transportation_name ENUM('Bus') NOT NULL,
    max_seats INT NOT NULL DEFAULT 50,
    default_booked_seats INT NOT NULL DEFAULT 45
);

INSERT INTO transportations (transportation_name, max_seats, default_booked_seats) 
VALUES ('Bus', 50, 45);


/* Rutter (routes) A-B
   
   Skapar själva grundrutten för en resa, med ett namn på rutten, vilken 
   kommun resan startar i (from_municipality_id) och vilken kommun som är 
   målet (to_municipality_id).
--------
   Uppbyggnad:
--------	
   Istället för att skriva kommunnamnen i fritext använder vi två fk som båda pekar på samma kommuntabell. 
   Whaaaat? Ping-pong
---------
   koppling
---------  
Pekar mot "municipalities" två gånger: en gång för start och en gång för mål.
"route_municipalities" hämtar från denna för att lista alla kommuner bussen 
passerar på vägen mellan start och mål.
Används även av "packages"-tabellen så att ett resepaket vet vilken väg bussen tar.
 */
 
CREATE TABLE routes (
    route_id INT AUTO_INCREMENT PRIMARY KEY,
    route_name VARCHAR(100) NOT NULL,
    from_municipality_id INT NOT NULL, 
    to_municipality_id INT NOT NULL,  
    FOREIGN KEY (from_municipality_id) REFERENCES municipalities(municipality_id),
    FOREIGN KEY (to_municipality_id) REFERENCES municipalities(municipality_id)
);


/* Platser (places)
	första katalogen med sevärdheter och naturupplevelser (gratis besöksmål).

--------
   Uppbyggnad:
--------	
kommun och "kostnadsfria" platser

---------
   koppling
--------- 
Mot "municipalities" via municipality_id, så vi vet vilken kommun platsen befinner sig i.
kopplas sedan ihop med resepaket ("packages") via kopplingstabell (package_places).
 */
 
CREATE TABLE places (
    place_id INT AUTO_INCREMENT PRIMARY KEY,
    municipality_id INT NOT NULL,
    place_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (municipality_id) REFERENCES municipalities(municipality_id)
);

INSERT INTO places (municipality_id, place_name) VALUES 
(14, 'Glumslövs Backar'),        
(11, 'Söderåsens Nationalpark'), 
(29, 'Ales stenar');             

/* Fika (fika)
	andra katalogen med fika/kafeer.

--------
   Uppbyggnad:
--------	
kommun och "egen bekostad" plats

---------
   koppling
--------- 
Mot "municipalities" via municipality_id, så vi vet vilken kommun platsen befinner sig i.
kopplas sedan ihop med resepaket ("packages") via kopplingstabell (package_fika).
 */
 
CREATE TABLE fika (
    fika_id INT AUTO_INCREMENT PRIMARY KEY,
    municipality_id INT NOT NULL,
    fika_name VARCHAR(50) NOT NULL,
    CONSTRAINT inga_dubbel_mellanslag 
        CHECK (fika_name NOT LIKE '%  %'),
    FOREIGN KEY (municipality_id) REFERENCES municipalities(municipality_id)
);

INSERT INTO fika (municipality_id, fika_name) VALUES 
(6,  'Ebbas Fik'),                  
(29, 'Färg från förr'),             
(16, 'Alice och Kattens Tesalong');

/* Nöjen (amusements)
	tredje katalogen med nöjen.
--------
   Uppbyggnad:
--------	
kommun, aktivitet och inträdesbiljett i pris

---------
   koppling
--------- 
Mot "municipalities" via municipality_id, så vi vet vilken kommun platsen befinner sig i.
kopplas sedan ihop med resepaket ("packages") via kopplingstabell (package_amusements).
 */
CREATE TABLE amusements (
    amusement_id INT AUTO_INCREMENT PRIMARY KEY,
    municipality_id INT NOT NULL,
    amusement_name VARCHAR(50) NOT NULL,
        CONSTRAINT inga_dubbel_mellanslag_amusement 
        CHECK (amusement_name NOT LIKE '%  %'),
    ticket_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,

    FOREIGN KEY (municipality_id) REFERENCES municipalities(municipality_id)
);

INSERT INTO amusements (municipality_id, amusement_name, ticket_price) VALUES 
(29, 'Ystad Djurpark', 299.00), /*Pris taget från google*/
(26, 'Tosselilla',     415.00), /*Pris taget från google*/
(17, 'Malmö Museum',   60.00);  /*Pris taget från google*/


/* resepaketet (packages)
   själva produkten kunden bokar
   Samlar ihop en resa till ett färdigt paket med namn, beskrivning, vilken 
   rutt som ska köras och vilket transportmedel som används.

--------
   Uppbyggnad:
--------	
   Genom att skapa en "paket-tabell" slipper kunden boka rutt, buss, fika, 
   platser och nöjen var för sig allt knyts istället till ett enda "package_id".

---------
   koppling
--------- 
	Mot "routes" och superbussen.
    Kopplar ihop platser, nöjen och fika via de tre kopplingstabellerna package_%
    Skickar till "bookings".
*/
CREATE TABLE packages (
    package_id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    route_id INT NOT NULL,
    transportation_id INT NOT NULL,
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (transportation_id) REFERENCES transportations(transportation_id)
);


/* En rutt genom kommuner (route_municipalities) kopplingstabell
--------
   Uppbyggnad:
--------	
   När bussen åker från kommun A till kommun B passerar den ofta flera 
   kommuner längs vägen. Den här tabellen listar exakt vilka kommuner som 
   ingår i en rutt och i vilken turordning (stop_order: 1, 2, 3...) de passeras.

---------
   koppling
--------- 
    många till många alltså en rutt kan gå genom många kommuner, och en 
     kommun kan passeras av många olika rutter.
   Sammanfogad pk (route_id, stop_order)som gör att en och samma rutt 
     inte kan ha två "stopp nummer 1" av misstag.
  on delete cascade: vi raderar en rutt i tabellen "routes" städas 
     alla dess delstopp i den här tabellen bort automatiskt

   binder ihop "routes" med "municipalities" och gör det möjligt att räkna 
     ut kostnaden för kommuner bussen passerar (pass_cost).
 */
CREATE TABLE route_municipalities (
    route_id INT NOT NULL,
    municipality_id INT NOT NULL,
    stop_order INT NOT NULL,
    PRIMARY KEY (route_id, stop_order),
    FOREIGN KEY (route_id) REFERENCES routes(route_id) ON DELETE CASCADE,
    FOREIGN KEY (municipality_id) REFERENCES municipalities(municipality_id)
);


/* places i paket (package_places) kopplingstabell

   Kopplar ihop ett resepaket med en eller flera sevärdheter/platser.

--------
   Uppbyggnad:
--------	
   ett paket kan innehålla flera sevärdheter, och samma sevärdhet kan ingå 
	i flera olika resepaket, many to many igen.
   sammansvetsad pk (package_id, place_id): Förhindrar att samma plats läggs 
     till två gånger i samma paket... kanske?
    ON DELETE CASCADE: Tas paketet bort så försvinner kopplingen automatiskt.

---------
   koppling
--------- 
   bbrygga mellan "packages" och "places".
   ========================================================================== */
CREATE TABLE package_places (
    package_id INT NOT NULL,
    place_id INT NOT NULL,
    PRIMARY KEY (package_id, place_id),
    FOREIGN KEY (package_id) REFERENCES packages(package_id) ON DELETE CASCADE,
    FOREIGN KEY (place_id) REFERENCES places(place_id)
);


/* nöjen i paketformat (package_amusements) kopplingstabell

   Kopplar ihop ett resepaket med ett eller flera nöjen.
--------
   Uppbyggnad:
--------	
   valfritt om ett paket ska ha 0, 1 eller flera nöjen utan 
     att det blir tomma kolumner i paket tabellen.
   primary key (package_id, amusement_id) stoppar dubbletter i samma paket.
   - ON DELETE CASCADE: Städar bort kopplingen om själva resepaketet raderas.

---------
   koppling
--------- 
   brygga mellan "packages" och "amusements" där även 
     biljettpriset hämtas.
 */
CREATE TABLE package_amusements (
    package_id INT NOT NULL,
    amusement_id INT NOT NULL,
    PRIMARY KEY (package_id, amusement_id),
    FOREIGN KEY (package_id) REFERENCES packages(package_id) ON DELETE CASCADE,
    FOREIGN KEY (amusement_id) REFERENCES amusements(amusement_id)
);


/* fika som paket (package_fika) kopplingstabell

   Kopplar ihop ett resepaket med ett eller flera fikaställen.
--------
   Uppbyggnad:
--------	
   kombinera vilka kaféer som helst med vilka paket som helst.
   PK igen (package_id, fika_id) samma kafé inte kan läggas in 
     dubbelt i samma paket.

---------
   koppling
--------- 
  brygga mellan "packages" och "fika".
   ========================================================================== */
CREATE TABLE package_fika (
    package_id INT NOT NULL,
    fika_id INT NOT NULL,
    PRIMARY KEY (package_id, fika_id),
    FOREIGN KEY (package_id) REFERENCES packages(package_id) ON DELETE CASCADE,
    FOREIGN KEY (fika_id) REFERENCES fika(fika_id)
);


/* Bokningar (bookings)

   Sparar själva beställningen, vilken kund som bokar, vilket paket som 
   bokas, när bokningen gjordes, avresedatum, antal passengers, totalpris 
   och bokningsstatus.

--------
   Uppbyggnad:
--------	
    datetime default current_timestamp: Stämplar automatiskt in exakt datum 
     och klockslag i samma sekund som bokningen skapades.
    CHECK-regler: Skyddar databasen mot ologiska bokningar – det måste 
     vara minst 1 vuxen (number_of_adults >= 1),  pris får aldrig 
     vara minusvärden, och statusen får bara vara 'Pending' (väntar), 
     'Confirmed' (bekräftad) eller 'Cancelled' (avbokad).

---------
   koppling
--------- 
   Mot "customers" resenär och "packages" om vad.
   Skickar till "payments" för att koppla en betalning till rätt bokning.
 */
 
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    package_id INT NOT NULL,
    booking_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    travel_date DATE NOT NULL,
		
        number_of_adults INT NOT NULL DEFAULT 1,
		CHECK (number_of_adults >= 1),
		number_of_children INT NOT NULL DEFAULT 0,
		CHECK (number_of_children >= 0),
		total_price DECIMAL(10,2) NOT NULL,
		CHECK (total_price >= 0),
		booking_status VARCHAR(20) NOT NULL DEFAULT 'Pending',
		CHECK (booking_status IN ('Pending', 'Confirmed', 'Cancelled')),

    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (package_id) REFERENCES packages(package_id)
);


/* Moneeeey (payments)

   registrerar hur och när en bokning betalas, vilket belopp som drogs, vilket 
   betalsätt kunden valde som kort, klarna eller swish samt om betalningen 
   gick igenom eller inte... vi leker vidare med de senare.

--------
   Uppbyggnad:
--------	
		egen tabell skild från "bookings" pga om en betalning misslyckas
		och kunden försöker igen med ett annat betalsätt t.ex byter från kort 
		till swish kan vi spara hela betalningshistoriken utan att skriva över 
		själva bokningen...
     
		enum på betalsätt och status för att endast godkända betalmetoder 
		och giltiga statuslägen kan läggas in.

---------
   koppling
--------- 
   Skickar till "bookings" via FOREIGN KEY (booking_id) och knyter ihop hela säcken 
     Kommun -> Rutt/Aktivitet -> Paket -> Bokning -> Betalning.
*/
CREATE TABLE payments (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method ENUM('Kort', 'Klarna', 'Swish') NOT NULL,
    payment_status ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Pending',
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);




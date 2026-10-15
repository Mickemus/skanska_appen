import base64
import streamlit as st

st.set_page_config(page_title="Skånska Upplevelser", layout="wide")

#--- Konvertera till binärdata och gör om den till en textsträng
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

#--- Läs in bakgrundsbilden
bg_img = get_base64_image("bakgrund.jpg")


# ------------------------------------------------------------------------------------------------------------------
# --- Snabbsök ---
# ------------------------------------------------------------------------------------------------------------------
# --- STIL ---

# --- FLIKAR

# --- NÖJEN ---
# --- PLATSER ---
# --- FIKA ---
# ------------------------------------------------------------------------------------------------------------------





# --- STIL ---


st.markdown(
    f"""
    <style>
    /*Appens Bakgrundsbild */
             .stApp {{
             background-image: url("data:image/jpeg;base64,{bg_img}");
             background-size: cover;
             background-position: center;
             background-attachment: fixed;
             }}

    /*Appens Rubrik*/
            h1 {{
                color: #FFFFFF !important;
                text-shadow: 1px 1px 1px #000000D2 !important;
             }}
            

    /*Appens Expanders*/
         /*Bakgrund*/  
         div[data-testid="stExpander"] {{
                background-color: #F3E2C3;
                border-radius: 10px;
            }}

        /*Knapparnas bakgrund*/
            div[data-testid="stExpander"] 
            summary {{
                background-color: #ECCF9D !important;
                border-radius: 10px;
            }}
    
        /*Text*/
            div[data-testid="stExpander"] 
            summary p {{
                color: #000000 !important;
                font-weight: bold;
                font-size: 1.4rem;
            }}

        /*Brödtext*/
            div[data-testid="stExpanderDetails"] p, 
            div[data-testid="stExpanderDetails"] span,
            button[data-baseweb="tab"] p {{
                color: #000000 !important; /* Mörkgrå textfärg för allt innehåll */
            }}
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Slut STIL ---


# ------------------------------------------------------------------------------------------------------------------
# --- FLIKAR -Expanders -Tabs -Flikar
# ------------------------------------------------------------------------------------------------------------------

def visa_plats(plats_namn, kort_info, bild_url, lang_text):
    st.write(kort_info)

    with st.container(height=350, border=False):
        st.subheader(plats_namn)
        st.image(bild_url, use_container_width=True)
        st.write(lang_text)
        st.write(
            "Här kan du fylla på med grejsimojs Emil."
            " Kartor också?"
            " Kanske adress"
        )


st.markdown(
    "<h1 style='text-align: center;'>Skånska Upplevelser</h1>",
    unsafe_allow_html=True,
)
st.write("")



#Jag delar skärmen i 3 kolumner varav mitt delen blir 5/7 sjundedelar
col1, col2, col3 = st.columns([1, 5, 1])

with col2:     #<---- Här är den stora mitt delen av skärmen vi jobbar med
    # --- NÖJEN ---
    with st.expander("Nöjen"):
        flik1, flik2, flik3 = st.tabs(
            ["Ystad Djurpark", "Tosselilla", "Malmö Museum"]
        )
        with flik1:
            visa_plats(
                plats_namn="Ystad Djurpark",
                kort_info="Info om Ystad Djurpark",
                bild_url="https://placehold.co/600x300?text=Ystad+Djurpark",  #----<< Temp placeholder
                lang_text="Information om Ystad Djurpark, djuren, matställen och aktiviteter.",
            )
        with flik2:
            visa_plats(
                plats_namn="Tosselilla",
                kort_info="Info om Tosselilla",
                bild_url="https://placehold.co/600x300?text=Tosselilla",      #----<< Temp placeholder
                lang_text="Information om Tosselilla Sommarland, vattenland och karuseller.",
            )
        with flik3:
            visa_plats(
                plats_namn="Malmö Museum",
                kort_info="Info om Malmö Museum",
                bild_url="https://placehold.co/600x300?text=Malmo+Museum",    #----<< Temp placeholder
                lang_text="Information om Malmö Museum, slottet, akvariet och utställningarna.",
            )

    # --- PLATSER ---
    with st.expander("Platser"):
        flik1, flik2, flik3 = st.tabs(
            ["Glumslövs Backar", "Söderåsens Nationalpark", "Ales Stenar"]
        )
        with flik1:
            visa_plats(
                plats_namn="Glumslövs Backar",
                kort_info="Info om Glumslövs Backar",
                bild_url="https://placehold.co/600x300?text=Glumslovs+Backar", #----<< Temp placeholder
                lang_text="Information om vandringsleder och utsikten över Öresund.",
            )
        with flik2:
            visa_plats(
                plats_namn="Söderåsens Nationalpark",
                kort_info="Info om Söderåsens Nationalpark",
                bild_url="https://placehold.co/600x300?text=Soderasen",        #----<< Temp placeholder
                lang_text="Information om Kopparhatten, Skäralid och bokskogarna.",
            )
        with flik3:
            visa_plats(
                plats_namn="Ales Stenar",
                kort_info="Info om Ales Stenar",
                bild_url="https://placehold.co/600x300?text=Ales+Stenar",      #----<< Temp placeholder
                lang_text="Information om skeppssättningen vid Kåseberga.",
            )

    # --- FIKA ---
    with st.expander("Fika"):
        flik1, flik2, flik3 = st.tabs(
            ["Ebbas Fik", "Färg från förr", "Alice och Kattens Tesalong"]
        )
        with flik1:
            visa_plats(
                plats_namn="Ebbas Fik",
                kort_info="Info om Ebbas Fik",
                bild_url="https://placehold.co/600x300?text=Ebbas+Fik",        #----<< Temp placeholder
                lang_text="Information om 50-talsfiket i Helsingborg.",
            )
        with flik2:
            visa_plats(
                plats_namn="Färg från förr",
                kort_info="Info om Färg från förr",
                bild_url="https://placehold.co/600x300?text=Farg+fran+forr",   #----<< Temp placeholder
                lang_text="Information om Färg från förr, byggnadsvård och fika.",
            )
        with flik3:
            visa_plats(
                plats_namn="Alice och Kattens Tesalong",
                kort_info="Info om Alice och Kattens Tesalong",
                bild_url="https://placehold.co/600x300?text=Alice+och+Katten",  #----<< Temp placeholder
                lang_text="Information om tesalongen i Lund.",
            )

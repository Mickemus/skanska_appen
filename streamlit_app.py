import streamlit as st

st.set_page_config(page_title="Skånes Smultronställen", layout="wide")

st.markdown(
    """
    <style>
    div[data-testid="stHorizontalBlock"] > div {
        transition: all 0.1s ease-in-out;
    }

    div[data-testid="stHorizontalBlock"]:has(details[open]) > div:nth-child(1),
    div[data-testid="stHorizontalBlock"]:has(details[open]) > div:nth-child(3) {
        flex: 1 1 calc(10% - 1rem) !important;
        width: calc(10% - 1rem) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(details[open]) > div:nth-child(2) {
        flex: 1 1 calc(80% - 1rem) !important;
        width: calc(80% - 1rem) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
    "<h1 style='text-align: center;'>Skånes Smultronställen</h1>",
    unsafe_allow_html=True,
)
st.write("")

col1, col2, col3 = st.columns([1, 1, 1])

with col2:
    # --- NÖJEN ---
    with st.expander("Nöjen"):
        flik1, flik2, flik3 = st.tabs(
            ["Ystad Djurpark", "Tosselilla", "Malmö Museum"]
        )
        with flik1:
            visa_plats(
                plats_namn="Ystad Djurpark",
                kort_info="Info om Ystad Djurpark",
                bild_url="https://placehold.co/600x300?text=Ystad+Djurpark",
                lang_text="Information om Ystad Djurpark, djuren, matställen och aktiviteter.",
            )
        with flik2:
            visa_plats(
                plats_namn="Tosselilla",
                kort_info="Info om Tosselilla",
                bild_url="https://placehold.co/600x300?text=Tosselilla",
                lang_text="Information om Tosselilla Sommarland, vattenland och karuseller.",
            )
        with flik3:
            visa_plats(
                plats_namn="Malmö Museum",
                kort_info="Info om Malmö Museum",
                bild_url="https://placehold.co/600x300?text=Malmo+Museum",
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
                bild_url="https://placehold.co/600x300?text=Glumslovs+Backar",
                lang_text="Information om vandringsleder och utsikten över Öresund.",
            )
        with flik2:
            visa_plats(
                plats_namn="Söderåsens Nationalpark",
                kort_info="Info om Söderåsens Nationalpark",
                bild_url="https://placehold.co/600x300?text=Soderasen",
                lang_text="Information om Kopparhatten, Skäralid och bokskogarna.",
            )
        with flik3:
            visa_plats(
                plats_namn="Ales Stenar",
                kort_info="Info om Ales Stenar",
                bild_url="https://placehold.co/600x300?text=Ales+Stenar",
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
                bild_url="https://placehold.co/600x300?text=Ebbas+Fik",
                lang_text="Information om 50-talsfiket i Helsingborg.",
            )
        with flik2:
            visa_plats(
                plats_namn="Färg från förr",
                kort_info="Info om Färg från förr",
                bild_url="https://placehold.co/600x300?text=Farg+fran+forr",
                lang_text="Information om Färg från förr, byggnadsvård och fika.",
            )
        with flik3:
            visa_plats(
                plats_namn="Alice och Kattens Tesalong",
                kort_info="Info om Alice och Kattens Tesalong",
                bild_url="https://placehold.co/600x300?text=Alice+och+Katten",
                lang_text="Information om tesalongen i Lund.",
            )

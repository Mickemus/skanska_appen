import streamlit as st

st.markdown(
    "<h1 style='text-align: center;'>Skånes Smultronställen</h1>",
    unsafe_allow_html=True,
)
st.write("")
st.write("")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    with st.expander("Nöjen"):
        flik1, flik2, flik3 = st.tabs(
            ["Ystad Djurpark", "Tosselilla", "Malmö Museum"]
        )
        with flik1:
            st.write("Info om Ystad Djurpark")
        with flik2:
            st.write("Info om Tosselilla")
        with flik3:
            st.write("Info om Malmö Museum")

    with st.expander("Platser"):
        flik1, flik2, flik3 = st.tabs(
            ["Glumslövs Backar", "Söderåsens Nationalpark", "Ales Stenar"]
        )
        with flik1:
            st.write("Info om Glumslövs Backar")
        with flik2:
            st.write("Info om Söderåsens Nationalpark")
        with flik3:
            st.write("Info om Ales Stenar")

    with st.expander("Fika"):
        flik1, flik2, flik3 = st.tabs(
            ["Ebbas Fik", "Färg från förr", "Alice och Kattens Tesalong"]
        )
        with flik1:
            st.write("Info om Ebbas Fik")
        with flik2:
            st.write("Info om Färg från förr")
        with flik3:
            st.write("Info om Alice och Kattens Tesalong")

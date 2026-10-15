import streamlit as st

st.title("Skanska-appen")
st.write("Streamlit fungerar!")

# Enkel interaktiv knapp
if st.button("Klicka här flower-power för ballonger xD"):
    st.balloons()
    st.success("Woo-hooo!")

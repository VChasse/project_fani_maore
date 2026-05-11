import streamlit as st

st.set_page_config(layout="wide")

with open("pages/carte_villages_seismes.html", "r", encoding="utf-8") as file:
    html_content = file.read()

st.markdown(
    f"""
    <iframe
        srcdoc='{html_content}'
        width="100%"
        height="900"
        style="border:none;"
    ></iframe>
    """,
    unsafe_allow_html=True,
)

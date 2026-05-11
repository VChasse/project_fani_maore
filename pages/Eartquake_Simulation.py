import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

with open("pages/carte_villages_seismes.html", "r", encoding="utf-8") as f:
    html_content = f.read()

components.html(html_content, height=900, scrolling=True)

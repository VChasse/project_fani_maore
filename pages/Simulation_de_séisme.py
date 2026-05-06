import streamlit as st

# Read the HTML file
with open("pages/carte_villages_seismes.html", "r", encoding="utf-8") as file:
    html_content = file.read()
st.set_page_config(layout="wide")
st.components.v1.html(html_content, height=900, scrolling=True)

st.sidebar.header("Calculations used")
st.sidebar.text("The largest circle was created using an empirical approximation formula to estimate the maximum affected distance, which is as follows:")
st.sidebar.latex(r"R = 10^{0.5M - 1.8}")
st.sidebar.markdown(r"$R$ = Distance to which intensity reaches a significant level")
st.sidebar.markdown(r"$M$= Magnitude on the Richter scale")
st.sidebar.text("Then the other circles were created using a general formula for intensity attenuation:")
st.sidebar.latex(r"I = I_0 - \beta \times \log_{10}(D)")
st.sidebar.markdown(r"$I$ = Intensity felt at distance D")
st.sidebar.markdown(r"$I_0$ = Maximum intensity at epicenter")
st.sidebar.markdown(r"$D$ = Distance to epicenter (km)")
st.sidebar.markdown(r"$\beta$ = coefficient that varies depending on soil type, we have beta=4 which corresponds to Mayotte's soil type (volcanic)")
st.sidebar.text("The vulnerability index was calculated from soil types and population with the following formula:")
st.sidebar.latex(r"\text{vulnerabilityIndexRaw} = \left( \text{pctEarth} \times 3 + \text{pctConcrete} \times 2 + \text{pctTile} \times 1 \right) \times \log(\text{Population}) \times \text{residentsPerDwelling}")
st.sidebar.text("The index was then scaled to 100 by dividing it by the theoretical maximum and then multiplying this result by 100")

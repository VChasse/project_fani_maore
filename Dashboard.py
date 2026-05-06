from streamlit_folium import st_folium
import streamlit as st
import folium
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

st.set_page_config(
    layout="wide",
)

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, sep=';')
    df.columns = df.columns.str.strip()
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    return df
    
# --- Data loading ---
data = load_data('basemayotte.csv')

st.title("Aftershocks Analysis")

# Select year and month
year_filter = st.sidebar.selectbox("Choose year", data['Time'].dt.year.unique())

# Use the month name in the selectbox
# For this, format the date as month name (depending on configured locale)
month_filter = st.sidebar.selectbox("Choose month", data['Time'].dt.strftime('%B').unique())

# Filter data by year and month (by comparing month string)
filtered_data = data[
    (data['Time'].dt.year == year_filter) & 
    (data['Time'].dt.strftime('%B') == month_filter)
]

# Display the number of events for the selected period
st.sidebar.markdown(f"**Events for {month_filter} {year_filter}**")
st.sidebar.markdown(f"Number of events: {len(filtered_data)}")


# --- 1. Main event selection ---
st.sidebar.header("Main Event")

# Magnitude threshold for mainshock selection (e.g., 5.0)
seuil_principal = st.sidebar.slider(
    "Magnitude threshold for main event", 
    min_value=3.0, max_value=9.0, value=3.0, step=0.1
)

# Filter candidate events to be a mainshock among the selected period
candidats_principal = (
    filtered_data[filtered_data['Magnitude'] >= seuil_principal]
    .sort_values('Time')
    .reset_index(drop=True)
)

if candidats_principal.empty:
    st.error("No event meets the selected magnitude threshold.")
    st.stop()

# Create a descriptive list for selection
options_principal = candidats_principal.apply(
    lambda row: f"{row['Time'].strftime('%Y-%m-%d %H:%M:%S')} | Mag: {row['Magnitude']:.1f}", axis=1
).tolist()

ev_principal_str = st.sidebar.selectbox("Choose the main event", options_principal)
# Get the index of the selected event from the list
index_selection = options_principal.index(ev_principal_str)
principal = candidats_principal.iloc[index_selection]
principal['Temps'] = principal['Time'].strftime('%Y-%m-%d %H:%M')

#Function for distance calculation
def haversine(lat1, lon1, lat2, lon2):
        R = 6371  # Earth's radius in km
        dLat = np.radians(lat2 - lat1)
        dLon = np.radians(lon2 - lon1)
        a = np.sin(dLat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dLon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        return R * c


col1, col2 = st.columns([4,6])

with col1:
    st.markdown(f"### Selected Main Event")
    st.write(principal[['Temps', 'Magnitude', 'Latitude', 'Longitude', 'Profondeur']])

    # --- 2. Threshold settings for aftershocks ---
    st.sidebar.header("Aftershock Parameters")
    rayon_spatial = st.sidebar.slider("Spatial radius for aftershocks (km)", 
                                          min_value=5, max_value=200, value=50, step=5)
    fenetre_temporelle_jours = st.sidebar.slider("Time window after main event (days)", 
                                         min_value=1, max_value=30, value=7, step=1)
    fenetre_temporelle = pd.Timedelta(days=fenetre_temporelle_jours)

    # --- 3. Aftershock identification ---
    # We consider as aftershocks the events occurring after the mainshock,
    # within the defined spatial radius and given time window.

    # Select events occurring after the main event
    candidats = data[data['Time'] > principal['Time']].copy()
    # Calculate distance between mainshock and each candidate
    candidats['Distance'] = candidats.apply(
        lambda row: haversine(principal['Latitude'], principal['Longitude'], row['Latitude'], row['Longitude']),
        axis=1
    )
    # Calculate time difference
    candidats['Time difference'] = candidats['Time'] - principal['Time']

    # Filter based on spatial and temporal thresholds
    repliques = candidats[
        (candidats['Distance'] <= rayon_spatial) &
        (candidats['Time difference'] <= fenetre_temporelle)
    ].copy()
    
    repliques["Temps"] = repliques["Time"].apply(lambda x : x.strftime('%Y-%m-%d %H:%M'))
    
    st.markdown("### Identified Aftershocks")
    st.write(f"Number of aftershocks found: {len(repliques)}")
    st.dataframe(repliques[['Temps', 'Magnitude', 'Latitude', 'Longitude', 'Distance', 'Time difference']].round(2))

# --- 4. Visualization on the map ---
# Display the mainshock and aftershocks on the map.
# The mainshock will be displayed in red, first aftershocks in orange and last ones in green.
# Set map center on the mainshock
m = folium.Map(location=[principal['Latitude'], principal['Longitude']], zoom_start=10)

# Add the mainshock
popup_principal = (f"<b>Main shock</b><br>"
                   f"<b>Time:</b> {principal['Temps']}<br>"
                   f"<b>Magnitude:</b> {principal['Magnitude']}<br>"
                   f"<b>Depth:</b> {principal['Profondeur']} km")
folium.CircleMarker(
    location=[principal['Latitude'], principal['Longitude']],
    radius=10 + principal['Magnitude'] * 2,
    color='red',
    fill=True,
    fill_color='red',
    fill_opacity=0.9,
    popup=popup_principal
).add_to(m)

# Sort aftershocks by date
repliques_sorted = repliques.sort_values(by='Time')

# Divide aftershocks into two groups: first (orange) and last (green)
premieres_repliques = repliques_sorted.iloc[:len(repliques_sorted)//2]
dernières_repliques = repliques_sorted.iloc[len(repliques_sorted)//2:]

# Add a legend
legend_html = """
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 200px; height: 120px; 
                 background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                 padding: 10px;">
         <b>Legend:</b><br>
         <i style="background: orange; width: 15px; height: 15px; float: left; margin-right: 5px;"></i> 
         First aftershocks<br>
         <i style="background: green; width: 15px; height: 15px; float: left; margin-right: 5px;"></i> 
         Last aftershocks<br>
         <i style="background: #FF4500; width: 15px; height: 15px; float: left; margin-right: 5px;"></i> 
         Mainshock<br>
     </div>
"""
# Add legend to map
m.get_root().html.add_child(folium.Element(legend_html))


# Add first aftershocks in orange
for idx, row in premieres_repliques.iterrows():
    popup_text = (f"<b>Aftershock</b><br>"
                  f"<b>Time:</b> {row['Time']}<br>"
                  f"<b>Magnitude:</b> {row['Magnitude']}<br>"
                  f"<b>Distance:</b> {row['Distance']:.1f} km<br>"
                  f"<b>ΔTime:</b> {row['Time difference']}")
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5 + row['Magnitude'] * 2,
        color='orange',
        fill=True,
        fill_color='orange',
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(m)
    # Optional: draw a line connecting the mainshock to the aftershock
    folium.PolyLine(
        locations=[(principal['Latitude'], principal['Longitude']),
                   (row['Latitude'], row['Longitude'])],
        color='orange',
        weight=2,
        opacity=0.6
    ).add_to(m)

# Add last aftershocks in green
for idx, row in dernières_repliques.iterrows():
    popup_text = (f"<b>Aftershock</b><br>"
                  f"<b>Time:</b> {row['Time']}<br>"
                  f"<b>Magnitude:</b> {row['Magnitude']}<br>"
                  f"<b>Distance:</b> {row['Distance']:.1f} km<br>"
                  f"<b>ΔTime:</b> {row['Time difference']}")
    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=5 + row['Magnitude'] * 2,
        color='green',
        fill=True,
        fill_color='green',
        fill_opacity=0.7,
        popup=popup_text
    ).add_to(m)
    # Optional: draw a line connecting the mainshock to the aftershock
    folium.PolyLine(
        locations=[(principal['Latitude'], principal['Longitude']),
                   (row['Latitude'], row['Longitude'])],
        color='green',
        weight=2,
        opacity=0.6
    ).add_to(m)

with col2:
    # Display the map
    st.markdown("### Interactive Aftershocks Map")
    st_folium(m, width=800, height=800)







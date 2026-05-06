import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import numpy as np
import folium
import streamlit as st
from streamlit_folium import folium_static


@st.cache_data
def load_data(path):
    df = pd.read_csv(path, sep=';')
    df.columns = df.columns.str.strip()
    df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
    v_bat = pd.read_excel("types_batiments.xlsx",sheet_name="PRINC2")
    return df,v_bat
st.set_page_config(layout="wide")

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 30% !important; # Set the width to your desired value
        }
    </style>
    """,
    unsafe_allow_html=True,
)

data,villes_bat = load_data('basemayotte.csv')
fani_maore = (-12.8479964, 45.4654728)

data['Mois'] = data['Time'].dt.to_period('M').astype(str)  # Format YYYY-MM
data['Year'] = data['Time'].dt.year

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    phi1 = np.radians(lat1)
    phi2 = np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)
    
    a = np.sin(delta_phi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c  # Distance in kilometers
    return distance



# Filter to keep only earthquakes with magnitude > 2
data_filtered = data[data['Magnitude'] > 4].copy()

# ----- 2. Convert to GeoDataFrame and reproject -----
# Create a GeoDataFrame in EPSG:4326 from Longitude/Latitude columns
gdf = gpd.GeoDataFrame(
    data_filtered,
    geometry=gpd.points_from_xy(data_filtered.Longitude, data_filtered.Latitude),
    crs="EPSG:4326"
)

# Reproject to a CRS in meters adapted to Mayotte.
# For Mayotte, we can use UTM zone 38S (EPSG:32738).
gdf = gdf.to_crs(epsg=32738)

# ----- 3. Create a 1000 m x 1000 m grid -----
xmin, ymin, xmax, ymax = gdf.total_bounds
grid_width = 4000  # width in meters
grid_height = 4000  # height in meters

# Create intervals to build the grid
cols = np.arange(xmin, xmax + grid_width, grid_width)
rows = np.arange(ymin, ymax + grid_height, grid_height)

polygons = []
for x in cols[:-1]:
    for y in rows[:-1]:
        polygons.append(Polygon([
            (x, y),
            (x + grid_width, y),
            (x + grid_width, y + grid_height),
            (x, y + grid_height)
        ]))

# Create grid GeoDataFrame
grid = gpd.GeoDataFrame({'geometry': polygons}, crs=gdf.crs)

# ----- 4. Assign each event to a grid cell -----
# Perform a spatial join to associate each earthquake with the corresponding cell
joined = gpd.sjoin(gdf, grid, how="left", predicate="within")

# ----- 5. Calculate risk per cell -----
# Calculate the total number of years in the data (to normalize per year)
total_years = data_filtered['Year'].nunique()

# Count the number of events per cell (each cell is identified by 'index_right')
risk_df = joined.groupby('index_right').size().reset_index(name='event_count')

# Calculate annual frequency (λ) and risk according to Poisson law
risk_df['lambda'] = risk_df['event_count'] / total_years
risk_df['risk'] = 1 - np.exp(-risk_df['lambda'])  # probability of at least one event next year

# Merge this information with the grid
grid['risk'] = risk_df.set_index('index_right')['risk']
grid['risk'] = grid['risk'].fillna(0)  # no observation → risk 0

# ----- 6. Reproject for display on Leaflet (EPSG:4326) -----
grid = grid.to_crs(epsg=4326)


# Convert catalog to GeoDataFrame
gdf = gpd.GeoDataFrame(
    data_filtered,
    geometry=gpd.points_from_xy(data_filtered.Longitude, data_filtered.Latitude),
    crs="EPSG:4326"
)

# ----- Definition of a simplified GMPE -----
def gmpe(magnitude, distance):
    """
    Very simplified model for predicting peak ground acceleration (PGA) in g.
    To avoid log(0), we add a constant 'c' to the distance.
    
    PGA = exp( a + b * magnitude - ln(distance + c) )
    """
    a = -1.5
    b = 0.5
    c = 10.0  # scale factor (distance in km)
    return np.exp(a + b * magnitude - np.log(distance + c))

# Exceedance threshold (e.g., PGA >= 0.1 g) -> from 0.1, damage can occur
PGA_threshold = st.sidebar.slider('PGA Threshold (in g)', min_value=0.05, max_value=1.0, value=0.15, step=0.01)  # Slider to adjust PGA threshold

# ----- Estimation of annual event rate -----
# Calculate observation duration in years
total_months = data_filtered['Mois'].nunique()
observation_years = total_months / 12

# Assign each event an annual rate (approximated by 1 occurrence over the period)
data_filtered['annual_rate'] = 1 / observation_years

# ----- PSHA calculation for each village -----
villes_pha = []
for idx, ville in villes_bat.iterrows():
    total_annual_rate = 0  # sum of contributions from each event
    for _, event in data_filtered.iterrows():
        # Calculate distance (in km) between village and event
        d = haversine(ville["Latitude"], ville["Longitude"],
                      event["Latitude"], event["Longitude"])
        # PGA prediction via GMPE
        pga = gmpe(event["Magnitude"], d)
        
        # If predicted PGA exceeds threshold, add this event's annual rate
        if pga >= PGA_threshold:
            total_annual_rate += event['annual_rate']
    
    # Calculate annual probability of exceeding threshold (Poisson law)
    p_exceed = 1 - np.exp(-total_annual_rate)
    
    villes_pha.append({
        'Nom Village': ville["Nom Village"],
        'Latitude': ville["Latitude"],
        'Longitude': ville["Longitude"],
        'total_annual_rate': total_annual_rate,
        'P_exceed': p_exceed
    })

villes_pha_df = pd.DataFrame(villes_pha)



# Create a map centered on Mayotte
m = folium.Map(location=fani_maore, zoom_start=10)

# Add the Fani Maoré volcano marker
folium.Marker(
    location=fani_maore,
    popup="Fani Maoré Volcano",
    icon=folium.Icon(color="red", icon="volcano", prefix='fa')
).add_to(m)


# Create layer groups
square_group = folium.FeatureGroup(name="Risk Grid")
circle_group = folium.FeatureGroup(name="Cities with Probability")

# Style function to color cells based on risk (for risk grid)
def style_function(feature):
    risk = feature['properties']['risk']
    if risk is None:
        risk = 0
    if risk < 0.2:
        color = '#00ff00'  # vert
    elif risk < 0.25:
        color = '#ffff00'  # jaune
    elif risk < 0.5:
        color = '#ffa500'  # orange
    elif risk < 0.8:
        color = '#ff0000'  # red
    else:
        color = '#8b0000'  # dark red
    return {
        'fillOpacity': 0.6,
        'weight': 0.5,
        'color': color
    }

# Filter cells with risk less than 0.0001
grid_filtered = grid[grid['risk'] >= 0.0001].round(4)

# Add filtered grid to "Risk Grid" group
folium.GeoJson(
    grid_filtered.to_json(),
    name="Risk Grid",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['risk'], aliases=['Risk'])
).add_to(square_group)

# Add circles for each city in the "Cities with Probability" group
min_radius = 700  # Minimum radius (in meters) for circles to remain visible
max_radius = 1200  # Maximum radius for highest probabilities
max_prob = villes_pha_df['P_exceed'].max()  # Find maximum probability

for idx, row in villes_pha_df.iterrows():
    color = 'red' if row['P_exceed'] > 0.05 else 'green'
    radius = min_radius + (row['P_exceed'] / max_prob) * (max_radius - min_radius)
    
    folium.Circle(
        location=[row['Latitude'], row['Longitude']],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.4,
        popup=f"<u>{row['Nom Village']}</u><br>Annual probability: <b>{row['P_exceed']*100:.2f} %</b>"
    ).add_to(circle_group)

# Add legend
legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 200px; height: 160px;
                 background-color: white; border:2px solid grey; z-index: 9999;
                 font-size: 12px; padding: 10px;">
     <b>Risk legend</b><br>
     <i style="background: #00ff00; width: 18px; height: 18px; float: left;"></i> Low (0 - 0.2)<br>
     <i style="background: #ffff00; width: 18px; height: 18px; float: left;"></i> Very Low (0.2 - 0.25)<br>
     <i style="background: #ffa500; width: 18px; height: 18px; float: left;"></i> Moderate (0.25 - 0.5)<br>
     <i style="background: #ff0000; width: 18px; height: 18px; float: left;"></i> High (0.5 - 0.8)<br>
     <i style="background: #8b0000; width: 18px; height: 18px; float: left;"></i> Extreme (> 0.8)
     </div>
'''

m.get_root().html.add_child(folium.Element(legend_html))

# Add layer groups to map
square_group.add_to(m)
circle_group.add_to(m)

# Add layer control to allow switching between layers
folium.LayerControl().add_to(m)



# Display map in Streamlit
st.title(f"Annual earthquake risk map exceeding PGA of {PGA_threshold}")
st.markdown("""
    <style>
        iframe {
            height: 85vh;
            width: 100%;
            border: none;
        }
    </style>
""", unsafe_allow_html=True)
folium_static(m,width=1500)
st.sidebar.markdown("""
###
| PGA (𝑔)         | Expected effects                                              |
|------------------|-------------------------------------------------------------|
| < 0.02 g         | Not felt, no damage                               |
| 0.02 - 0.05 g    | Slightly felt, no damage                               |
| 0.05 - 0.10 g    | Light vibrations, possible falling objects                 |
| 0.10 - 0.20 g    | Small cracks in walls, light damage to fragile buildings |
| 0.20 - 0.40 g    | Moderate damage to unreinforced buildings                |
| 0.40 - 0.60 g    | Significant damage to unreinforced masonry buildings |

""")
st.sidebar.markdown("""
## Calculation and method details
""")

st.sidebar.markdown("""
### 1. Distance calculation (Haversine Formula)
To determine the distance between two points from their coordinates (latitude and longitude), we use the Haversine formula:
""")
st.sidebar.latex(r"""
a = \sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)
""")
st.sidebar.latex(r"""
c = 2 \, \arctan2\left(\sqrt{a}, \sqrt{1 - a}\right)
""")
st.sidebar.latex(r"""
d = R \times c
""")
st.sidebar.markdown("""
where $ \phi_1 $ and $ \phi_2 $ are the latitudes (in radians), $ \Delta \phi $ and $ \Delta \lambda $ represent the latitude and longitude differences, and $ R $ is the Earth's radius (6371 km).
""")

st.sidebar.markdown("""
### 2. Risk grid and risk calculation per cell
Filtered earthquakes are assigned to grid cells (here, 4000m*4000m in size). For each cell:
""")
st.sidebar.markdown("""
1. **Annual frequency $ \lambda $** :
""")
st.sidebar.latex(r"""
\lambda = \frac{N}{T}
""")
st.sidebar.markdown("""
with $ N $ the number of events and $ T $ the number of years of observation.
""")
st.sidebar.markdown("""
2. **Annual risk** (Poisson law) :
""")
st.sidebar.latex(r"""
\text{Risk} = 1 - \exp(-\lambda)
""")

st.sidebar.markdown("""
### 3. Simplified GMPE model for PGA calculation
The PGA (Peak Ground Acceleration) is estimated by:
""")
st.sidebar.latex(r"""
\text{PGA} = \exp\Big(a + b \cdot M - \ln(d + c)\Big)
""")
st.sidebar.markdown("""
with $ M $ the magnitude, $ d $ the distance (in km), $ a = -1.5 $, $ b = 0.5 $ and $ c = 10.0 $.
""")

st.sidebar.markdown("""
### 4. Annual rate estimation and probability of exceeding a PGA threshold
- **Annual rate per event** :
""")
st.sidebar.latex(r"""
\text{annual\_rate} = \frac{1}{\text{Number of years of observation}}
""")
st.sidebar.markdown("""
- **Probability of exceeding threshold** :
""")
st.sidebar.latex(r"""
P_{\text{exceed}} = 1 - \exp\left(-\sum \text{annual\_rate}\right)
""")

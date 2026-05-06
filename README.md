# Fani Maoré - Seismic Risk Assessment for Mayotte

A comprehensive seismic risk assessment application for Mayotte, featuring aftershock analysis, probabilistic seismic hazard assessment (PSHA), and interactive earthquake simulation.

## Overview

This Streamlit-based application provides tools for analyzing seismic activity around Mayotte, particularly focused on the Fani Maoré underwater volcano. The application includes three main modules:

1. **Aftershocks Analysis** - Analyze aftershock patterns following main seismic events
2. **Risk Analysis** - Calculate annual seismic risk using PSHA methodology
3. **Earthquake Simulation** - Interactive earthquake simulation with village vulnerability assessment

## Features

### 1. Aftershocks Analysis (Dashboard.py)
- Select main seismic events by magnitude threshold
- Filter events by year and month
- Define spatial radius and temporal window for aftershock detection
- Interactive map visualization showing:
  - Main shock (red marker)
  - First aftershocks (orange markers)
  - Last aftershocks (green markers)
  - Connecting lines between main shock and aftershocks

### 2. Risk Analysis (pages/Analyse_des_risques.py)
- Grid-based risk assessment using Poisson distribution
- Peak Ground Acceleration (PGA) threshold analysis
- Village-level probability calculations
- Interactive map layers:
  - Risk grid (4000m x 4000m cells)
  - Village probability circles
  - Fani Maoré volcano marker
- Adjustable PGA threshold slider (0.05g - 1.0g)
- Detailed sidebar with calculation formulas:
  - Haversine distance formula
  - Annual frequency (λ) calculation
  - Simplified GMPE (Ground Motion Prediction Equation)
  - Poisson-based probability estimation

### 3. Earthquake Simulation (pages/Simulation_de_séisme.py)
- Interactive HTML-based earthquake simulation
- Village data import from Excel (types_batiments.xlsx)
- Filtering options:
  - Soil type (Packed Earth, Concrete, Tile)
  - Vulnerability index (0-100)
  - Minimum population
- Click-to-simulate earthquake functionality
- Real-time intensity calculations
- Categorized affected cities (High/Medium/Low intensity)
- Vulnerability index based on:
  - Soil composition
  - Population density
  - Average residents per dwelling

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Dependencies

Install required packages using:

```bash
pip install -r requirements.txt
```

Required packages:
- streamlit
- streamlit-folium
- folium
- pandas
- numpy
- geopandas
- shapely
- scikit-learn
- openpyxl

## Usage

### Running the Application

1. Navigate to the project directory:
```bash
cd project_fani_maore
```

2. Launch the Streamlit application:
```bash
streamlit run Dashboard.py
```

3. The application will open in your default web browser at `http://localhost:8501`

### Data Requirements

#### Seismic Data (basemayotte.csv)
The application expects a CSV file with semicolon (;) separator containing:
- **Time**: Timestamp of seismic event
- **Magnitude**: Earthquake magnitude
- **Latitude**: Event latitude
- **Longitude**: Event longitude
- **Profondeur** (Depth): Event depth in kilometers

#### Building Types Data (types_batiments.xlsx)
Required for the Earthquake Simulation module, containing:
- **Nom Village**: Village name
- **Latitude**: Village latitude
- **Longitude**: Village longitude
- **Sol en terre battue**: Number of packed earth floor dwellings
- **Sol en beton**: Number of concrete floor dwellings
- **Sol en carrelage ou autre**: Number of tile/other floor dwellings
- **Total**: Total dwellings
- **Nombre moyen de personnes par logement**: Average persons per dwelling

## Navigation

The application uses Streamlit's multi-page structure:
- **Home Page**: Aftershocks Analysis (Dashboard.py)
- **Risk Analysis**: Access via sidebar navigation
- **Earthquake Simulation**: Access via sidebar navigation

## Methodology

### Distance Calculation
Uses the Haversine formula to calculate great-circle distances between coordinates:
```
a = sin²(Δφ/2) + cos(φ₁)·cos(φ₂)·sin²(Δλ/2)
c = 2·atan2(√a, √(1-a))
d = R × c
```
Where R = 6371 km (Earth's radius)

### Risk Assessment
Annual risk per grid cell using Poisson distribution:
```
λ = N / T
Risk = 1 - exp(-λ)
```
Where N = number of events, T = observation period in years

### GMPE (Simplified)
Peak Ground Acceleration estimation:
```
PGA = exp(a + b·M - ln(d + c))
```
Where M = magnitude, d = distance (km), a = -1.5, b = 0.5, c = 10.0

### Intensity Attenuation
```
I = I₀ - β × log₁₀(D)
```
Where β = 4 (volcanic terrain coefficient for Mayotte)

### Maximum Affected Radius
```
R = 10^(0.5M - 1.8)
```

### Vulnerability Index
```
vulnerabilityIndexRaw = (pctEarth × 3 + pctConcrete × 2 + pctTile × 1) × log(Population) × residentsPerDwelling
```
Normalized to 0-100 scale

## PGA Impact Reference

| PGA (g)       | Expected Effects                                    |
|---------------|-----------------------------------------------------|
| < 0.02 g      | Not felt, no damage                                 |
| 0.02 - 0.05 g | Slightly felt, no damage                            |
| 0.05 - 0.10 g | Light vibrations, possible falling objects          |
| 0.10 - 0.20 g | Small cracks in walls, light damage to fragile buildings |
| 0.20 - 0.40 g | Moderate damage to unreinforced buildings           |
| 0.40 - 0.60 g | Significant damage to unreinforced masonry buildings|

## Project Structure

```
project_fani_maore/
│
├── Dashboard.py                          # Main page - Aftershocks Analysis
├── requirements.txt                       # Python dependencies
├── basemayotte.csv                       # Seismic event data
├── types_batiments.xlsx                  # Building types data (user-provided)
├── README.md                             # This file
│
└── pages/
    ├── Analyse_des_risques.py           # Risk Analysis module
    ├── Simulation_de_séisme.py          # Earthquake Simulation wrapper
    ├── carte_villages_seismes.html      # Interactive simulation interface
    └── basemayotte.csv                  # Seismic data copy
```

## Features by Module

### Dashboard (Aftershocks Analysis)
- ✅ Year and month filters
- ✅ Magnitude threshold slider
- ✅ Spatial radius configuration (5-200 km)
- ✅ Temporal window configuration (1-30 days)
- ✅ Interactive Folium map
- ✅ Aftershock data table
- ✅ Color-coded temporal progression

### Risk Analysis
- ✅ 4000m × 4000m risk grid
- ✅ PGA threshold slider (0.05-1.0 g)
- ✅ Village-level probability calculations
- ✅ Toggleable map layers
- ✅ Risk legend (Low/Very Low/Moderate/High/Extreme)
- ✅ Comprehensive methodology sidebar
- ✅ UTM projection (EPSG:32738) for accurate calculations

### Earthquake Simulation
- ✅ Excel file import
- ✅ Multi-criteria village filtering
- ✅ Click-to-simulate earthquakes
- ✅ Real-time intensity calculations
- ✅ Categorized impact assessment
- ✅ Vulnerability index visualization
- ✅ Alphabetically sorted village selector
- ✅ Intensity-based circular zones

## Technical Notes

- **CRS**: Uses EPSG:4326 (WGS84) for display, EPSG:32738 (UTM 38S) for calculations
- **Grid Size**: 4000m × 4000m for risk assessment
- **Default PGA Threshold**: 0.15g
- **Magnitude Range**: 1.0 - 10.0 (simulation)
- **Beta Coefficient**: 4 (volcanic terrain)
- **Map Library**: Leaflet.js via Folium
- **Data Processing**: Pandas, NumPy, GeoPandas

## Contributing

This project analyzes seismic data for Mayotte. To contribute:
1. Ensure data format consistency with existing CSV structure
2. Follow Streamlit best practices for page organization
3. Maintain calculation methodology documentation
4. Test with various magnitude ranges and thresholds

## License

This project is intended for seismic risk assessment and educational purposes.

## Acknowledgments

- Seismic data sourced from Mayotte monitoring networks
- GMPE methodology adapted for local volcanic terrain
- Village vulnerability assessment based on census data

## Contact

For questions about seismic data or methodology, refer to the calculation details in the application sidebars.

---

**Note**: This application is for risk assessment and educational purposes. For official seismic warnings and emergency procedures, consult local authorities and seismic monitoring agencies.

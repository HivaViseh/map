import pandas as pd
import geopandas as gpd
import folium
import numpy as np
import branca
from folium import FeatureGroup
from branca.colormap import linear
import os
from folium.features import GeoJsonTooltip
my_email = "hiva.viseh@technicalsafetybc.ca"
map_address = "/Users/hviseh/Hiva - Projects/map risk/lcsd000b16a_e/lcsd000b16a_e.shp"
df_address = "/Users/hviseh/Hiva - Projects/CO_Incidents_2007-2023/Count_CO_Incident_Rate/"

df1 = pd.read_csv("clustes_IncidentID.csv")
df2_csv = pd.read_csv("data.csv")
df1 = pd.merge(df1, df2_csv, on="Incident_ID", how='left')


Canada_shapefile_path = shapefile_path = map_address
Canada_map = gpd.read_file(Canada_shapefile_path)

province_name = 'British Columbia / Colombie-Britannique'
bc_map = Canada_map[Canada_map['PRNAME'] == province_name]

m = folium.Map(location=(53.7267, -127.6476), zoom_start=6, tiles="cartodb positron", attr=my_email)


used_col = ["Longtitude", "Latitude", "CDpop_2021", "CDtdwell_2021", "ERpop_2021", "ERtdwell_2021" ]
df = pd.read_csv(os.path.join(df_address, "CO_incident_CD_ER.csv"), usecols=used_col)
df = pd.merge(df,df1, on=["Longtitude", "Latitude"], how='left')
df.dropna(subset=["Cluster"], inplace=True)
df["Cluster"] = df["Cluster"].astype(int)

geometry = gpd.points_from_xy(df["Longtitude"], df["Latitude"])
incidents_gdf = gpd.GeoDataFrame(df, geometry=geometry)


if incidents_gdf.crs is None:
    incidents_gdf.crs = {'init': 'epsg:4326'} 

incidents_gdf = incidents_gdf.to_crs(bc_map.crs)

joined_data = gpd.sjoin(bc_map, incidents_gdf, how='left', op='contains')

joined_data['Count'] = np.where(~joined_data['Latitude'].isna(), 1, 0)



incident_counts_1 = joined_data[joined_data["Cluster"] == 1.0]
incident_counts_2 = joined_data[joined_data["Cluster"] == 2.0]
incident_counts_3 = joined_data[joined_data["Cluster"] == 3.0]

incident_counts_1 = incident_counts_1.groupby('ERNAME').agg(incident_count=('Count', 'sum'), ERtdwell_2021=('ERtdwell_2021', 'first')).reset_index()
incident_counts_2 = incident_counts_2.groupby('ERNAME').agg(incident_count=('Count', 'sum'), ERtdwell_2021=('ERtdwell_2021', 'first')).reset_index()
incident_counts_3 = incident_counts_3.groupby('ERNAME').agg(incident_count=('Count', 'sum'), ERtdwell_2021=('ERtdwell_2021', 'first')).reset_index()


incident_counts_1['CO Incident per 1000 Private Dwellings_ER'] = np.where(
    incident_counts_1['incident_count'] != 0,
    round((incident_counts_1['incident_count'] / incident_counts_1['ERtdwell_2021'])*1000,4),
    0
)

bc_map_with_counts_1 = bc_map.merge(incident_counts_1, on='ERNAME', how='left')

incident_counts_2['CO Incident per 1000 Private Dwellings_ER'] = np.where(
    incident_counts_2['incident_count'] != 0,
    round((incident_counts_2['incident_count'] / incident_counts_2['ERtdwell_2021'])*1000,4),
    0
)

bc_map_with_counts_2 = bc_map.merge(incident_counts_2, on='ERNAME', how='left')

incident_counts_3['CO Incident per 1000 Private Dwellings_ER'] = np.where(
    incident_counts_3['incident_count'] != 0,
    round((incident_counts_3['incident_count'] / incident_counts_3['ERtdwell_2021'])*1000,4),
    0
)

bc_map_with_counts_3 = bc_map.merge(incident_counts_3, on='ERNAME', how='left')

cols = ['incident_count', 'CO Incident per 1000 Private Dwellings_ER']

legendnames = ['Cluster 1', 'Cluster 2', 'Cluster 3']

names = ['Cluster 1', 'Cluster 2', 'Cluster 3']


bc_map_with_counts = [bc_map_with_counts_1, bc_map_with_counts_2,bc_map_with_counts_3]


# Initialize the color map and geojson layers list
color_map = []
geojson_layers = []
layer_groups = []
# Loop through each cluster data
for i in range(len(bc_map_with_counts)):

    bc_map_with_counts[i] = bc_map_with_counts[i].replace({0: np.nan, np.nan: np.nan})

    legendname = legendnames[i]
    layer_name = names[i]

    # Assuming 'col_name' is a valid column name in 'bc_map_with_counts'
    col_range = (bc_map_with_counts[i]['CO Incident per 1000 Private Dwellings_ER'].min(), bc_map_with_counts[i]['CO Incident per 1000 Private Dwellings_ER'].max())

    # Find the first value larger than 0
    first_non_zero_value = next((value for value in sorted(bc_map_with_counts[i]['CO Incident per 1000 Private Dwellings_ER'].unique()) if value > 0), None)

    dynamic_num_bins = len(np.unique(bc_map_with_counts[i]['CO Incident per 1000 Private Dwellings_ER']))

    choropleth = folium.Choropleth(
        geo_data=bc_map_with_counts[i],
        data=bc_map_with_counts[i],
        columns=["ERNAME", 'CO Incident per 1000 Private Dwellings_ER'],
        key_on="feature.properties.ERNAME",
        fill_color="YlOrRd",
        fill_opacity=0.5,
        line_opacity=0.3,
        nan_fill_color='white',
        nan_fill_opacity=0.4,
        bins=dynamic_num_bins,
        legend_name=legendname,
        name=layer_name,
        overlay=True,
        highlight=True,
        show=False
    ).add_to(m)

    # Fill NaNs
    bc_map_with_counts[i]['incident_count'].fillna(0, inplace=True)
    bc_map_with_counts[i]['CO Incident per 1000 Private Dwellings_ER'].fillna(0, inplace=True)

    # Define style and highlight functions for GeoJSON layers
    style_function = lambda x: {
        'fillColor': '#ffffff', 
        'color': '#000000', 
        'fillOpacity': 0.1, 
        'weight': 1.0  # Set line width (thicker line)
    }

    highlight_function = lambda x: {
        'fillColor': '#000000', 
        'color': '#000000', 
        'fillOpacity': 0.50, 
        'weight': 2.0  # Set line width when highlighted (thicker line)
    }


    for feature in choropleth.geojson.data['features']:
        feature['properties']['popup'] = (
            f"<div style='font-size: 14px;'>CO Incident per 1000 Private Dwellings: {feature['properties'].get('CO Incident per 1000 Private Dwellings_ER', 'N/A')}</div>"
        )
        feature['properties']['tooltip'] = (
            f"Economic Region: {feature['properties'].get('ERNAME', 'N/A')}\n"
            f"CO Incident per 1000 Private Dwellings: {feature['properties'].get('CO Incident per 1000 Private Dwellings_ER', 'N/A')}\n"
            f"CO Incidents: {feature['properties'].get('incident_count', 'N/A')}"
        )
        


    folium.GeoJson(
        data=choropleth.geojson.data,
        style_function=style_function,
        highlight_function=highlight_function,
        tooltip=folium.GeoJsonTooltip(fields=["tooltip"], aliases=["Info"], labels=False),
        popup=folium.GeoJsonPopup(fields=["popup"]),
        name=f"Cluster Information{i+1}"  # Set the name of the layer
    ).add_to(m)


folium.LayerControl(collapsed=False).add_to(m)

# Save the map to an HTML file
m.save("CO_clusters_map.html")



import geopandas as gpd
from geographiclib.geodesic import Geodesic
from shapely.geometry import Point
from shapely.geometry import Point, MultiLineString, LineString
import numpy as np
import main as m

# Set up the Geodesic calculator (WGS84 ellipsoid)
geod = Geodesic.WGS84

country = "Russia"
#berlin
targetlat = 52.33 #52.52
targetlon = 13.47 #13.405

# Berlin's center coordinates (latitude, longitude)
target_coords = (targetlon, targetlat)

# Load the shapefile (naturalearth data)
# You need to download the shapefile from naturalearthdata.com and provide its path here
shapefile_path = 'countries/ne_110m_admin_0_countries.shp'
#shapefile_path = 'ne_110m_admin_0_countries2.json'
gdf = gpd.read_file(shapefile_path)
#gdf = m.load_data(shapefile_path)

# Function to calculate the azimuth from the point to a given boundary point
def calculate_azimuth(point1, point2):
    return geod.Inverse(point1[1], point1[0], point2[1], point2[0])['azi1']

def calculate_distance(point1, point2):
    return geod.Inverse(point1[1], point1[0], point2[1], point2[0])['s12']

def calculate_angles(country, target_coords, max_distance=''):
    print(f"\nLooking at {country}")
    # Select the country you are interested in (e.g., Germany)
    country_gdf = gdf[gdf['NAME'] == country]

    # Get the boundary of the country (external polygon)
    country_geometry = country_gdf.boundary.iloc[0]
    # Calculate the azimuths for all points in the boundary
    angles = []
    # Check the geometry type and handle accordingly
    if isinstance(country_geometry, MultiLineString):
        for linestring in country_geometry.geoms:
            angles2 = []
            for point in linestring.coords:
                distance = calculate_distance(target_coords, point)
                if max_distance :
                    if distance > max_distance :
                        continue
                angle = calculate_azimuth(target_coords, point)
                #if angle < 0 : angle += 180
                angles2.append(angle)
            if len(angles2) > 0 :
                minpart = min(angles2)
                maxpart = max(angles2)
                print(f"One part min/max: {minpart}/{maxpart}")
                angles.extend(angles2)
    elif isinstance(country_geometry, LineString):
        for point in country_geometry.coords:
            distance = calculate_distance(target_coords, point)
            if max_distance:
                if distance > max_distance :
                    continue
            angle = calculate_azimuth(target_coords, point)
            angles.append(angle)
        print("LineString")
        print(angles)
    elif country_geometry.geom_type == 'MultiPolygon':
        for polygon in country_geometry:
            for point in polygon.exterior.coords:
                distance = calculate_distance(target_coords, point)
                if max_distance:
                    if distance > max_distance :
                        continue
                angle = calculate_azimuth(target_coords, point)
                angles.append(angle)
        print("MultiPolygon")
    elif country_geometry.geom_type == 'Polygon':
        for point in country_geometry.exterior.coords:
            distance = calculate_distance(target_coords, point)
            if max_distance:
                if distance > max_distance :
                    continue
            angle = calculate_azimuth(target_coords, point)
            angles.append(angle)
        print("Polygon")
    else:
        print(f"Unhandled geometry type: {country_geometry.geom_type}")

    # Find the maximum and minimum azimuth angles
    angles = np.array(angles)
    
    angles[angles < 0] += 360
    #print(angles)
    
    max_angle = max(angles)
    min_angle = min(angles)
    def_direction = (max_angle + min_angle) / 2
    sector_size = max_angle - min_angle
    print("Max distance =", max_distance)
    print("Defense Direction =", def_direction)
    print("Sector Size", sector_size)
    

    # Print the result
    print(f"Target location at Lat={target_coords[1]} / Lon={target_coords[0]}")
    print(f"Maximum viewing angle to view {country}: {max_angle}°")
    print(f"Minimum viewing angle to view {country}: {min_angle}°")

    if len(angles[angles<0]) > 0 and len(angles[angles>0]) > 0:
        print("Angle could also cover the sign flip, and would then be")
        max2 = max(angles[angles<0])
        min2 = min(angles[angles>0])
        print(f"Maximum viewing angle to view {country}: {min2}°")
        print(f"Minimum viewing angle to view {country}: {max2}°")
        
    return(def_direction, sector_size)

#country = "Australia"
#max_distance = ''#10000000
#calculate_angles(country, target_coords, max_distance)
"""
calculate_angles("Austria", target_coords)

calculate_angles("France", target_coords)

calculate_angles("Iran", target_coords)
"""
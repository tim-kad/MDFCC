#from short_search import omegashift_2_xy
import main as m
from math import sin, cos, asin, acos, ceil, radians, degrees, atan2, floor, pi
from fcc_constants import R_e, angle_eps, mrl_factor1, mrl_factor2, footprint_path, \
    zigzag_for_intersection_limit, inside_check, chart_path, no_zigzag
#import chart3d_window as c3
import numpy as np
from geographiclib.geodesic import Geodesic
from spherical_geometry import polygon, graph
import geojson
import matplotlib.pyplot as plt
import tkinter as tk
import time
import c_classes as cc
#from main import keep_old_file
from os import path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg#, NavigationToolbar2Tk
from cycler import cycler

print("debug=", graph.DEBUG)
graph.DEBUG = False
print("debug=", graph.DEBUG)

geo_sphere = Geodesic(R_e, 0)

def omegashift_2_fidist(omega, shift, mrange):
    """
    Converts shift, omega and mrange to fi and dist -- on the surface of earth-sphere.
    Calculation uses "law of cosines"

    Parameters
    ----------
    omega : float, in radians
        diherdal angle between trajectory plane and ILP-MLP plane        
    shift : float, in meters
        ILP-MLP distance on the sphere surface
    mrange : float, in meters
        missile range on the sphere surface

    Returns
    -------
    fi : float, radians
    dist : float, km
        coordinates centered at ILP,  on the sphere surface
    
    temporary solution:
        fi, dist -> unfold to plane -> x, y

    """
    f_alfa = mrange / R_e
    f_gamma = shift / R_e
    if abs(omega) <= angle_eps :
        dist = (shift - mrange) #/ 1000
        if dist > 0 :
            fi_deg = 0
        else :
            fi_deg = 180
            dist = -dist
    else :
        f_delta = acos(cos(f_gamma) * cos(f_alfa) + sin(f_gamma) * sin(f_alfa) * cos(omega))
        dist = f_delta * R_e #/ 1000
        #fi = asin(sin(omega) * sin(f_alfa) / sin(f_delta))
        fi = acos((cos(f_alfa) - cos(f_gamma) * cos(f_delta)) / sin(f_gamma) / sin(f_delta))
            
        fi_deg = degrees(fi)
        if omega < 0 :
            fi_deg = 360 - fi_deg
            
    return(fi_deg, dist)

""" End of omegashift_2_fide """


def fprint_m2tom1(ftprint, no_zigzag=False) :
    """
    For Mod2 footprint converts Mod2 coords (shift and omega) to Mod1 coords (fi and dist)

    Parameters
    ----------
    ftprint : Mod 2 footprint [[[angle, shift, acc, x, y], ], [[angle, shift, acc, x, y], ]]
        DESCRIPTION. Array of two np.arrays representing two parts of a Mod2 footprint

    Returns
    -------
        Footprint in notation [[[fi, dist, acc, x, y], ], [[fi, dist, acc, x, y], ]] 
    """
    ftprint_m1 = []
    for footprint in ftprint :
        fp_part_m1 = np.empty([0, 5]) #_like(footprint)
        if len(footprint) > 0 :
            mrange = footprint[0][1] - footprint[0][4] * 1000
            for f_point in footprint :
                omega = f_point[0]
                shift = f_point[1]
                """
                if f_point[2] == 2 :
                    fi, dist = omegashift_2_fidist(omega, shift, mrange * mrl_factor2)
                elif f_point[2] == 3 :
                    fi, dist = omegashift_2_fidist(omega, shift, mrange * mrl_factor1)
                else :
                    fi, dist = omegashift_2_fidist(omega, shift, mrange)
                """
                fi, dist = omegashift_2_fidist(omega, shift, mrange)
                if no_zigzag :
                    fp_part_m1 = np.append(fp_part_m1, [[fi, dist, f_point[2], f_point[3], f_point[4]]], axis=0)
                else :
                    if f_point[2] == 2 :
                        fp_part_m1 = np.append(fp_part_m1, [[fi, dist * mrl_factor2, f_point[2], f_point[3], f_point[4]]], axis=0)
                    elif f_point[2] == 3 :
                        fp_part_m1 = np.append(fp_part_m1, [[fi, dist * mrl_factor1, f_point[2], f_point[3], f_point[4]]], axis=0)
                    else :
                        fp_part_m1 = np.append(fp_part_m1, [[fi, dist, f_point[2], f_point[3], f_point[4]]], axis=0)
        ftprint_m1.append(fp_part_m1)

    return(ftprint_m1)


def fp_part_rotate(fp_part, r_angle):
    """
    rotates mod1 footprint or one part of mod2 footprint (in mod1 notation) by angle degrees

    Parameters
    ----------
    fp_part : Mod1 footprint data array: [[angle, distance, accuracy, x, y], ]
    r_angle : float, degrees

    Returns
    -------
    rtd_fppart

    """
    #print(fp_part)
    rtd_fppart = np.empty([0, 5]) #_like(fp_part)
    if len(fp_part) > 0 :
        for fp_point in fp_part :
            rtd_angle = fp_point[0] + r_angle
            rtd_x = -fp_point[1] * sin(radians(rtd_angle)) / 1000
            rtd_y =  fp_point[1] * cos(radians(rtd_angle)) / 1000
            rtd_fppart = np.append(rtd_fppart, [[rtd_angle, fp_point[1], fp_point[2], rtd_x, rtd_y]], axis=0)

    return(rtd_fppart)


def fprint_rotate(ftprint, r_angle, no_zigzag=False) :
    """
    Rotates foorptint by angle in degrees

    Parameters
    ----------
    ftprint_arr : np.array
        DESCRIPTION.
            for mod1: [[angle, distance, accuracy, x, y],]
            for mod2: [[[angle, shift, acc, x, y], ], [[angle, shift, acc, x, y], ]]
    r_angle : TYPE
        DESCRIPTION. Rotation angle, in degrees

    Returns
    -------
    rotated footprint in m1 format

    """
    if (len(ftprint) > 0) and (len(ftprint[0]) > 0) :
        if type(ftprint[0][0]) != np.ndarray : #i.e. mode1
            a = ftprint[0]
            b = ftprint[0][0]
            rtd_ftprint = fp_part_rotate(ftprint, r_angle)
        else: # mode2
            ftprint_m1 = fprint_m2tom1(ftprint, no_zigzag)
            rtd_ftpart1 = fp_part_rotate(ftprint_m1[0], r_angle)
            rtd_ftpart2 = fp_part_rotate(ftprint_m1[1], r_angle)
            rtd_ftprint = [rtd_ftpart1, rtd_ftpart2]
    
    return(rtd_ftprint)

def fppart_2lonlat(fp_part, lon, lat, azi) :
    """
    Convert footprint part (in m1 notation) to geo coords with ILP at lon, lat, azimuth of the defense direction = azi 
    Sufficient for Mod1 footprints, for Mod2 see ftprint_2lonlat()
    Parameters
    ----------
    ftprint : [[angle, distance, accuracy, x, y],]
        footprint in mod1 notation
    lon : float
        longitude
    lat : float
        latitude
    azi : float
        azimuth

    Returns
    -------
    footprint in lat, lon coords.

    """
    #geo_sphere = Geodesic(R_e, 0)
    fp_part_ll = np.empty([0, 2]) #_like(fp_part)
    far_pt_num = ceil((len(fp_part) - 1) / 2)
    if fp_part[0][0] == fp_part[far_pt_num][0] : # true for second part of a split footprint, or when first part is behind ILP
        inside_dist = (fp_part[far_pt_num][1] + fp_part[0][1]) /2
        inside_fi = fp_part[0][0]
    else :
        if fp_part[0][1] < fp_part[far_pt_num][1] :
            inside_dist = (fp_part[far_pt_num][1] - fp_part[0][1]) /2
            inside_fi = fp_part[far_pt_num][0]
        else : 
            inside_dist = (fp_part[0][1] - fp_part[far_pt_num][1]) /2
            inside_fi = fp_part[0][0]
        
    inside_geo = geo_sphere.Direct(lat, lon, azi + inside_fi, inside_dist)
    inside_ll = (inside_geo['lon2'], inside_geo['lat2']) 
    #print(fp_part)
    for fp_point in fp_part :
        az_i = azi + fp_point[0]
        s_i  = fp_point[1]
        p_i = geo_sphere.Direct(lat, lon, az_i, s_i) # from (ilat, ilon) direction az_i distance s_i
        fp_part_ll = np.append(fp_part_ll, [[p_i['lon2'], p_i['lat2']]], axis=0)

    return(fp_part_ll, inside_ll)


def ftprint_2lonlat(ftprint, lon, lat, azi) :
    """
    Convert footprint part to geo coords with ILP at lat, lon, azimuth of the defense direction = azi 

    Parameters
    ----------
    ftprint : [[angle, distance, accuracy, x, y],]
        footprint in mod1 notation
    lat : float
        latitude
    lon : float
        longitude
    azi : float
        azimuth

    Returns
    -------
    footprint in lon, lat coords.

    """
    
    if (len(ftprint) > 0) and (len(ftprint[0]) > 0) :
        if type(ftprint[0][0]) != np.ndarray : #i.e. mode1
            ftprint_ll, inside_ll = fppart_2lonlat(ftprint, lon, lat, azi)
        else: # mode 2
            ftprint_ll_1, inside_ll_1 = fppart_2lonlat(ftprint[0], lon, lat, azi)
            if len(ftprint[1]) > 0 :
                ftprint_ll_2, inside_ll_2 = fppart_2lonlat(ftprint[1], lon, lat, azi)
                ftprint_ll  = [ftprint_ll_1, ftprint_ll_2]
                inside_ll   = [inside_ll_1, inside_ll_2]
            else :
                ftprint_ll  = [ftprint_ll_1, []]
                inside_ll   = [inside_ll_1, []]
                
    else :
        ftprint_ll = []
        inside_ll  = []
    
    return(ftprint_ll, inside_ll)

    
def draw_polygon(poly, title, lon, lat, azi, f_size, save_chart_fname='default', keep_chart=True) :
    
    def chart_save() :
        #keep_chart = set_keep_fp_chart_var.get()
        #print(keep_chart)
        #save_chart_fname = ent_chart_fname.get()
        if save_chart_fname :
            f_save_chart_fname = chart_path + "/" + save_chart_fname
            if keep_chart :
                m.keep_old_file(f_save_chart_fname)
            ax.get_figure().savefig(f_save_chart_fname, dpi=300, bbox_inches='tight', pad_inches=0.2)
            #print("Footprint Chart saved to ", f_save_chart_fname)

    u = np.linspace(0, 2 * pi, 500)
    v = np.linspace(0, pi, 500)
    u, v = np.meshgrid(u, v)
    x_sphere = np.sin(v) * np.cos(u)
    y_sphere = np.sin(v) * np.sin(u)
    z_sphere = np.cos(v)
    
    # Plot the sphere and the polygons
    fig = plt.figure(figsize = (6, 7), dpi=100)
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the sphere
    ax.plot_surface(x_sphere, y_sphere, z_sphere, color='lightblue', alpha=0.2, rstride=10, cstride=10)
    
    """
    bw = False
    if bw :
        linestyle_cycler = cycler('linestyle', ['-', '--', ':', '-.', (0, (3, 3, 1, 3, 1, 3))])
    else : 
        linestyle_cycler = cycler('color', ['tab:blue', 'g', 'm', 'k', 'c']) +\
                       cycler('linestyle', ['-', '--', ':', '-.', (0, (3, 3, 1, 3, 1, 3))])
    ax.set_prop_cycle(linestyle_cycler)
    """
    if not isinstance(poly, list) :
        poly = [poly, []]

    colorset = ['Orange', 'Magenta', 'tab:Blue', 'Black', 'Cyan']
    line_set = ['--', ':', '-', '-.', (0, (3, 3, 1, 3, 1, 3))]
    
    i_p = 0
    for i_poly in poly :
        
        if len(i_poly) == 0 :
            i_p += 1
            continue

        poly_list = list(i_poly.polygons)[0]
        num_polygons = len(list(i_poly.polygons)[0])
        
        poly_points = list(i_poly.points)
        poly_inside = list(i_poly.inside)
        
        i_s = 1
        for subpolygon in i_poly :
            subpoly_points = subpolygon.points
            subpoly_inside = subpolygon.inside
            xs, ys, zs = zip(*subpoly_points)
            #xs, ys, zs = zip(*list(subpolygon.points)[0])
            ax.plot(xs, ys, zs, color=colorset[i_p], linestyle=line_set[i_p])
            #ax.plot(xs, ys, zs, color='blue', label='Footprint part {}'.format(i_s))
            px, py, pz = subpolygon.inside
            """ inside point! """
            #ax.plot(px, py, pz, marker='x', ms=5, mfc=colorset[i_p], mec=colorset[i_p])
            i_s += 1

        i_p += 1
                    
        """
        if num_polygons > 1:
            inside1, inside2 = poly.inside
            x1, y1, z1 = zip(*list(poly.points)[0])
            ax.plot(x1, y1, z1, color='green', label='Polygon 1_1')
            x2, y2, z2 = zip(*list(poly.points)[1])
            ax.plot(x2, y2, z2, color='blue', label='Polygon 1_2')
            p1x, p1y, p1z = inside1 
            ax.plot(p1x, p1y, p1z, marker='o', ms=2, mfc='c', mec='c')
            p2x, p2y, p2z = inside2 
            ax.plot(p2x, p2y, p2z, marker='o', ms=2, mfc='m', mec='m')
        else :
            x1, y1, z1 = zip(*list(poly.points)[0])
            ax.plot(x1, y1, z1, color='green', label='Polygon 1_1')
            p1x, p1y, p1z = tuple(poly.inside)[0] 
            ax.plot(p1x, p1y, p1z, marker='o', ms=2, mfc='y', mec='y')
        """
    """end of for i_poly cycle """
    """
    zs_min = min(zs)
    zs_max = max(zs)
    #i_min = zs.index(zs_min)
    i_max = zs.index(zs_max)
    high_angle = asin(zs_max)
    low_angle  = asin(zs_min)
    
    elev = degrees((high_angle + low_angle) / 2)
    azim = degrees(atan2(ys[i_max], xs[i_max]))
    """
    """
    f_size_equat = f_size * sin(radians(azi))
    f_size_merid = f_size * cos(radians(azi))
    az_shift = degrees(f_size_equat /R_e * 1000 /3)
    el_shift = degrees(f_size_merid /R_e * 1000 /3)
    """
    azim = lon #az_shift
    elev = lat #- el_shift
    #print("f_size={:.2f}, f_size_equat={:8.2f}, lon={:.2f}, az_shift={:.2f}, azim={:.2f}".format(f_size, f_size_equat, lon, az_shift, azim))
    #print("azi   ={:.2f}, f_size_merid={:8.2f}, lat={:.2f}, el_shift={:.2f}, elev={:.2f}".format(azi, f_size_merid, lat, el_shift, elev))
    #zoom_factor = floor(5000 / f_size)
    zoom_factor = round (4000 / f_size)
    if zoom_factor < 1 :
        zoom_factor = 1
    elif zoom_factor > 15 :
        zoom_factor = 15
    
    # Set viewing angle (optional)
    ax.view_init(elev=elev, azim=azim)  # 30 degrees elevation, 60 degrees azimuth
    
    ax.set_box_aspect([1, 1, 1])

    ax.set_xlim([-1/zoom_factor, 1/zoom_factor])
    ax.set_ylim([-1/zoom_factor, 1/zoom_factor])
    ax.set_zlim([-1/zoom_factor, 1/zoom_factor])
    
    ax.grid(True)

    # Hide the tick labels on all axes
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.set_zticklabels([])

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(title + ", zoom factor {}".format(zoom_factor))
    #if num_polygons < 5 :
    #    ax.legend()
    chart_save()
    
    #plt.show()
    return(fig)


def footprintm1_2polygon(ftprint_m1, lon, lat, azi):
    """
    Convert footprint in m1 notation to polygon as defined in spherical_geometry, with ILP having coords lon, lat, and azimuth of defense direction azi    

    Parameters
    ----------
    ftprintm1 : footprint in m1 notation
        DESCRIPTION. [[[fi, dist, acc, x, y], ], [[fi, dist, acc, x, y], ]]

    Returns
    -------
    Footprint as polygon as defined in spherical_geometry

    """
    
    ftprint_ll, inside_ll = ftprint_2lonlat(ftprint_m1, lon, lat, azi)
    
    if (len(ftprint_ll) > 0) and (len(ftprint_ll[0]) > 0) :
        if type(ftprint_ll[0][0]) != np.ndarray : #i.e. mode1
            lon_1, lat_1 = zip(*ftprint_ll)
            f_polygon = polygon.SphericalPolygon.from_radec(lon_1, lat_1, inside_ll) # (lon, lat) is the inside point, which is ILP
        else: # mode 2
            lon_11, lat_11 = zip(*ftprint_ll[0])
            f_polygon_1 = polygon.SphericalPolygon.from_radec(lon_11, lat_11, inside_ll[0])
            fpol1_points = list(f_polygon_1.points)
            fpol1_inside = list(f_polygon_1.inside)
            #draw_polygon(f_polygon_1)
            if len(ftprint_ll[1]) > 0 :
                lon_12, lat_12 = zip(*ftprint_ll[1])
                f_polygon_2 = polygon.SphericalPolygon.from_radec(lon_12, lat_12, inside_ll[1])
                fpol2_points = list(f_polygon_2.points)
                fpol2_inside = list(f_polygon_2.inside)
                #draw_polygon(f_polygon_2)
            else :
                f_polygon_2 = polygon.SphericalPolygon([])
                
            #f_polygon = f_polygon_1.union(f_polygon_2)
            f_polygon   = polygon.SphericalPolygon([f_polygon_1, f_polygon_2])
            fpol_points = list(f_polygon.points)
            fpol_inside = list(f_polygon.inside)
            #draw_polygon(f_polygon)
    else :
        f_polygon = polygon.SphericalPolygon([])
    
    return(f_polygon)

#def sphpolygon_2fprint(sphpolygon) :
def geojson_proof(polylist_of_lists) :
    """
    Correct values in a line so that geojson does no jumping

    Parameters
    ----------
    polylist_t : TYPE list of lists [lon, lat]
        DESCRIPTION.
        
    Returns
    -------
    "Correct" list of tuples.

    """
    for i_d in range(1, len(polylist_of_lists)):
        lon1 = polylist_of_lists[i_d][0]
        lon0 = polylist_of_lists[i_d - 1][0]

        if lon1 - lon0 > 180 :                      # Geojson doesn't like big jumps
            polylist_of_lists[i_d][0] = lon1 - 360
        elif lon1 - lon0 < -180 :
            polylist_of_lists[i_d][0] = lon1 + 360

    return(polylist_of_lists)


def zigzag_count(f_print) :
    if (len(f_print) > 0) and (len(f_print[0]) > 0) :
        if type(f_print[0][0]) != np.ndarray : #i.e. mode1
            count = np.sum(f_print[:, 2] == 2)
        else: # mode 2
            count = 0
            for fp_part in f_print :
                if len(fp_part) > 0 :
                    count += np.sum(fp_part[:, 2] == 2)
                
    return(count)

def fp_size(f_print) :
    """
    Footprint size: distance from closest to ILP to farthest along the defense direction

    Parameters
    ----------
    f_print : TYPE np.array
        DESCRIPTION.
            for mod1: [[angle, distance, accuracy, x, y],]
            for mod2: [[[angle, shift, acc, x, y], ], [[angle, shift, acc, x, y], ]]

    Returns
    -------
    size : float, footprint size in km

    """
    if (len(f_print) > 0) and (len(f_print[0]) > 0) :
        if type(f_print[0][0]) != np.ndarray : #i.e. mode1
            mid_num = ceil((len(f_print) - 1) / 2)
            f_size = (f_print[0][1] + f_print[mid_num][1]) / 1000
        else: # mode 2
            if len(f_print[0]) > 0 :
                mid_num = ceil((len(f_print[0]) - 1) / 2)
                front_dist = f_print[0][0][4]
                back_dist  = f_print[0][mid_num][4]
                if len(f_print[1]) > 0 :
                    mid_num = ceil((len(f_print[1]) - 1) / 2)
                    back_dist  = f_print[1][mid_num][4]
                f_size = front_dist - back_dist
    else :
        print("Empty footprint or main part of Mode 2 Footprint")
        return(0)
                
    return(f_size)
"""
def set_inside_points_old(poly, lon, lat, azi) :
    
    Finds inside points for all subpolygons in pole by finding in the polygon two pointson on the azimuth from ILP 

    Parameters
    ----------
    poly : TYPE
        DESCRIPTION. intersection of polygons with symmetrical defense direction with respect to the axis of the defense sector
    lon : TYPE
        DESCRIPTION. ILP longitude
    lat : TYPE
        DESCRIPTION. ILP latitude
    azi : TYPE 
        DESCRIPTION. azimuth of the axis of the defense sector
        

    Returns
    -------
    Polygon with correct insides.

    
    if not inside_check : return(poly)

    poly_points_ll = list(polygon.SphericalPolygon.to_lonlat(poly))
        
    inside_points_ll = []
    i_poly = True
    for f_polyg in poly_points_ll :
        polylist = list(zip(*f_polyg))
        #polylist_of_lists = [list(duplet) for duplet in polylist]
        
        half_num = ceil((len(polylist) - 1) / 2)
        for i_i in range(half_num) :
            inside_point = []
            lon1 = polylist[i_i][0]
            lat1 = polylist[i_i][1]
            lon2 = polylist[i_i + half_num][0]
            lat2 = polylist[i_i + half_num][1]
            inv_result1 = geo_sphere.Inverse(lat, lon, lat1, lon1)
            inv_result2 = geo_sphere.Inverse(lat, lon, lat2, lon2)
            azimuth1 = inv_result1['azi2']
            azimuth2 = inv_result2['azi2']
            if abs((azimuth2 - azimuth1) % 180) < 0.001 :
                inv_result = geo_sphere.Inverse(lat1, lon1, lat2, lon2)
                distance = inv_result['s12']
                azimuth  = inv_result['azi1']
                midpoint_result = geo_sphere.Direct(lat1, lon1, azimuth, distance / 2)
                mid_lat = midpoint_result['lat2']
                mid_lon = midpoint_result['lon2']
                inside_point = [mid_lon, mid_lat]
                break
        #inside_points_ll.append(inside_point)
        #print("f_polyg")
        if len(inside_point) > 0 :
            f_polyg = polygon.SphericalPolygon.from_radec(f_polyg[0], f_polyg[1], inside_point)
        else :
            f_polyg = polygon.SphericalPolygon.from_radec(f_polyg[0], f_polyg[1])            
        if i_poly :
            new_poly = f_polyg
            i_poly = False
        else :
            new_poly = new_poly.union(f_polyg)
    
    new_poly_ll = list(polygon.SphericalPolygon.to_lonlat(new_poly))
    
    new_poly_points = list(new_poly.points)
    new_poly_inside = list(new_poly.inside)
    
    return(new_poly)
"""

def set_inside_points(poly, lon, lat, azi) :
    """
    Finds inside points for all subpolygons in pole by finding in the polygon two pointson on the azimuth from ILP 

    Parameters
    ----------
    poly : TYPE
        DESCRIPTION. intersection of polygons with symmetrical defense direction with respect to the axis of the defense sector
    lon : TYPE
        DESCRIPTION. ILP longitude
    lat : TYPE
        DESCRIPTION. ILP latitude
    azi : TYPE 
        DESCRIPTION. azimuth of the axis of the defense sector
        

    Returns
    -------
    Polygon with correct insides.

    """
    def find_inside_point(f_polylist) :
        
        half_num = ceil((len(f_polylist) - 1) / 2)
        inside_point = []
        for i_i in range(half_num) :
            lon1 = f_polylist[i_i][0]
            lat1 = f_polylist[i_i][1]
            lon2 = f_polylist[i_i + half_num][0]
            lat2 = f_polylist[i_i + half_num][1]
            inv_result1 = geo_sphere.Inverse(lat, lon, lat1, lon1)
            inv_result2 = geo_sphere.Inverse(lat, lon, lat2, lon2)
            azimuth1 = inv_result1['azi2']
            azimuth2 = inv_result2['azi2']
            if abs((azimuth2 - azimuth1) ) < 5 : #% 180) < 10:
                inv_result = geo_sphere.Inverse(lat1, lon1, lat2, lon2)
                distance = inv_result['s12']
                azimuth  = inv_result['azi1']
                midpoint_result = geo_sphere.Direct(lat1, lon1, azimuth, distance / 2)
                mid_lat = midpoint_result['lat2']
                mid_lon = midpoint_result['lon2']
                inside_point = [mid_lon, mid_lat]
                break
        return(inside_point)
    """end of find_inside_point """
    
    if not inside_check :
        return(poly, False)
    
    poly_points_ll = list(polygon.SphericalPolygon.to_lonlat(poly))
    
    max_length = 0
    max_index1 = -1
    max_index2 = -1
    
    for i_f, subpoly in enumerate(poly_points_ll):
        length = len(subpoly[0])  # Length of one array in the tuple
        if length > max_length:
            max_length = length
            max_index1  = i_f
            max_index2 = -1
        else :
            if length == max_length :
                max_index2 = i_f
    
    inside_point_set = False
    if max_index1 != -1 :
        sub_polygons = list(poly.polygons)
        f_polyg1 = poly_points_ll[max_index1]
        polylist1 = list(zip(*f_polyg1))
        ip1 = find_inside_point(polylist1)
        if len(ip1) > 0 :
            new_subpolyg1 = polygon.SphericalPolygon.from_radec(f_polyg1[0], f_polyg1[1], ip1)
            sub_polygons[max_index1] = new_subpolyg1
            inside_point_set = True
            
        if max_index2 != -1 :
            f_polyg2 = poly_points_ll[max_index2]
            polylist2 = list(zip(*f_polyg2))
            ip2 = find_inside_point(polylist2)
            if len(ip2) > 0 :
                new_subpolyg2 = polygon.SphericalPolygon.from_radec(f_polyg2[0], f_polyg2[1], ip2)
                sub_polygons[max_index2] = new_subpolyg2
                inside_point_set = True

        new_poly = polygon.SphericalPolygon(sub_polygons)
        
        new_poly_ll = list(polygon.SphericalPolygon.to_lonlat(new_poly))
        
        new_poly_points = list(new_poly.points)
        new_poly_inside = list(new_poly.inside)
    else :
        return(poly, False)

    return(new_poly, inside_point_set)


def ftp_intersection(ftprint, lon, lat, azi, azm_dist, angle, angle_step, root, save_chart_fname='') :
    """
    Create intersection footprint for footprints with ILP at lon, lat, and defense direction from azi to azi+angle, with angle increment of angle_step 

    Parameters
    ----------
    ftprint : TYPE
        DESCRIPTION. Original footprint Mod 1 or Mod 2
    lon, lat : TYPE float, lon from  -180 to +180, lat from -90 to +90
        DESCRIPTION. ILP  geo coordinates
    azi : TYPE float, from  -180 to +180
        DESCRIPTION. defense direction azimuth, central axis of the defense sector
    azm_dist : float
        length of the defense direction line
    angle : TYPE float 0 <= angle <= 360, angle between rightmost and leftmost defense directions
        DESCRIPTION.
    angle_step : TYPE float
        DESCRIPTION. angle increment for finding footprint intersections

    Returns
    -------
    ###Intersection of footprints as an array of lon, lat pairs - changed
    Featurelist of ILP, marginal defense directions, and intersection of footprints.

    """
    global win3d
    
    featurelist = []
    ilp_f0 = geojson.Point([lon, lat])
    ilp_f = geojson.Feature(geometry = ilp_f0, properties = {})

    line_plist1 = [] #Defense Direction
    line_plist2 = [] #Defense Direction
    
    dist_step = 100000 # 100 km between dots
    line_steps = ceil(azm_dist/dist_step)
    if line_steps > 30 :
        line_steps = 30
    
    for d_dist in np.linspace(0, azm_dist, line_steps): # 30

        p1 = geo_sphere.Direct(lat, lon, azi - angle/2, d_dist)
        line_plist1.append([p1['lon2'], p1['lat2']])

        p2 = geo_sphere.Direct(lat, lon, azi + angle/2, d_dist)
        line_plist2.append([p2['lon2'], p2['lat2']])
        
    new_line_plist1 = geojson_proof(line_plist1)
    new_line_plist2 = geojson_proof(line_plist2)

    imline1 = geojson.LineString(new_line_plist1)
    imline1_f = geojson.Feature(geometry=imline1, properties = {'stroke': 'red'})

    imline2 = geojson.LineString(new_line_plist2)
    imline2_f = geojson.Feature(geometry=imline2, properties = {'stroke': 'red'})

    featurelist.append(ilp_f)
    featurelist.append(imline1_f)
    featurelist.append(imline2_f)
    
    """ begins here """

    """
    if angle < angle_step :
        angle_step = angle
    n_angle = ceil(angle / angle_step)
    angle_incr = angle / n_angle
    
    for i_f in range(n_angle + 1) :
        fprint_i = fprint_rotate(ftprint, angle_incr * i_f)
        fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
        fp_points_ll = list(polygon.SphericalPolygon.to_lonlat(fp_polygon))
        #fppll_list1 = list(zip(*fp_points_ll[0]))
        #fppll_list1  = np.stack(fp_points_ll[0], axis=-1)
        fp_points = list(fp_polygon.points)
        draw_polygon(fp_polygon)
        f_polygons.append(fp_polygon)
    """
    #zz_proc = False
    #def_directions2 = []            

    """
    if angle > 2 * angle_step :
        if zigzag_count(ftprint) > zigzag_for_intersection_limit :
            zz_proc = True
            print("zigzag processing: {}".format(zz_proc))
            def_directions = [0, angle, angle/2]    
            def_directions2 = [angle/4, angle*3/4]            
        else :
            def_directions = [0, angle, angle/2, angle/4, angle*3/4]    
    elif angle > angle_step :
        def_directions = [0, angle, angle/2]
    else :
        def_directions = [0, angle]
    """
    
    do_inside_correction = True
    if (len(ftprint) > 0) and (len(ftprint[0]) > 0) :
        if type(ftprint[0][0]) != np.ndarray : #i.e. mode1
            do_inside_correction = False
        else: # mode 2
            if len(ftprint[1]) == 0 : # i.e. no second part
                do_inside_correction = False
    else: # no main part of footprint ergo no footprint
        return(featurelist)



    def_directions = []
    """
    if angle > 2 * angle_step :
            def_directions.append([-angle/2, 0]) #angle/4])
            def_directions.append([angle/2]) #-angle/4, angle/2])            
            def_directions.append([])
            last_call = 2
    elif False : #angle > angle_step :
            def_directions.append([-angle/2, angle/2])
            def_directions.append([])
            def_directions.append([])
            last_call = 3
    else :
            def_directions.append([-angle/2, angle/2])
            def_directions.append([])
            def_directions.append([])
            last_call = 1
    """

    #print("Proc:  azi={} angle={}".format(azi, angle))
    #print("def_directions=", def_directions)
 
    try :
        if win3d.state() == "normal" : win3d.destroy()
    except :
        pass
    finally :
        win3d = tk.Toplevel(root)
        win3d.title("Footprint in 3D")
        #win3d.title('Footprint Chart')
        #c3.create_3dchart_window(master=win3d)
            
        win3d.grid_columnconfigure(0, weight=1)
        win3d.grid_columnconfigure(1, weight=0)
        win3d.grid_columnconfigure(2, weight=1)

        win3d.protocol("WM_DELETE_WINDOW", win3d.destroy)

        def draw_3d_chart(fig):
            """Draws or updates the 3D chart in a Tkinter window."""
        
            # Create the canvas for the 3D plot if it doesn't exist
            canvas = FigureCanvasTkAgg(fig, win3d) # master=win3d)
            canvas.draw()
            canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, sticky='nsew')
        
            # Create a frame for the toolbar
            toolbar_frame = tk.Frame(win3d)
            toolbar_frame.grid(row=1, column=1)
        
            # Initialize and add the toolbar
            toolbar = cc.CustomNavigationToolbar(canvas, toolbar_frame, True)
            #a = toolbar.toolitems
            toolbar.update()
            
        """ End of draw_3d_chart """
        
        def draw_3d_polychart(polygon, title, fpsize, chart_fname) :
            global win3d
            
            fig = draw_polygon(polygon, title, lon, lat, azi, fpsize, chart_fname)
            draw_3d_chart(fig)
            #print(title)
            plt.close(fig)
            win3d.update()
        """ End of draw_3d_polychart() """            
        
        
        f_polygons = []
        f_polygons2 = []
        fpsize = fp_size(ftprint)

        """
        for i_angle in def_directions :
            fprint_i = fprint_rotate(ftprint, i_angle)
            fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
            #fp_points_ll = list(polygon.SphericalPolygon.to_lonlat(fp_polygon))
            #fp_points = list(fp_polygon.points)
            fig = draw_polygon(fp_polygon, "Defense Direction {:.2f}".format(i_angle), lon, lat, azi, fpsize)
            c3.draw_3d_chart(fig)
            print("Defense Direction {:.2f}".format(i_angle))
            f_polygons.append(fp_polygon)
            plt.close(fig)
        
            p_intersection = polygon.SphericalPolygon.multi_intersection(f_polygons)

        if zz_proc :
            fig = draw_polygon(p_intersection, "Intersection 1", lon, lat, azi, fpsize)
            c3.draw_3d_chart(fig)
            print("Intersection 1")
            plt.close(fig)

            for i_angle in def_directions2 :
                fprint_i = fprint_rotate(ftprint, i_angle)
                fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
                fig = draw_polygon(fp_polygon, "*Defense Direction {:.2f}".format(i_angle), lon, lat, azi, fpsize)
                c3.draw_3d_chart(fig)
                print("*Defense Direction {:.2f}".format(i_angle))
                f_polygons2.append(fp_polygon)
                plt.close(fig)

            p_intersection2 = polygon.SphericalPolygon.multi_intersection(f_polygons2)
            fig = draw_polygon(p_intersection2, "Intersection 2", lon, lat, azi, fpsize)
            c3.draw_3d_chart(fig)
            print("intersection 2")
            plt.close(fig)
            
            p_intersection = p_intersection.intersection(p_intersection2)
        """
        
        n_intsec = int(angle / angle_step) # int drops decimal part
        if n_intsec < 1 :
            n_intsec = 1
        angle_incr = angle / n_intsec

        chartf_name, chartf_extension = path.splitext(save_chart_fname)
        i_intsec = 0
        p_intsec = []
        
        i_angle = -angle / 2
        for i_a in range(n_intsec + 1) :
            fprint_i = fprint_rotate(ftprint, i_angle, no_zigzag)
            fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
            i_chart_fname = chartf_name + "-d{}".format(i_a) + chartf_extension
            title = "Defense Direction {}/{} {:7.2f}".format(i_a, n_intsec, i_angle)
            draw_3d_polychart([fp_polygon, p_intsec, []], title, fpsize, i_chart_fname)
            """
            if i_a == 0 :
                draw_3d_polychart([fp_polygon, p_intsec, []], title, fpsize, i_chart_fname)
            else :
                draw_3d_polychart([fp_polygon, p_intsec, []], title, fpsize, i_chart_fname)
            """
            #fig = draw_polygon(fp_polygon, title, lon, lat, azi, fpsize, i_chart_fname)
            #draw_3d_chart()
            #print(title)
            #plt.close(fig)

            if p_intsec == [] :
                p_intsec = fp_polygon
                p_intsec_ll = list(p_intsec.to_lonlat())
            else :                
                p_intsec_new = p_intsec.intersection(fp_polygon)
                p_intsec_new_ll = list(p_intsec.to_lonlat())
                i_intsec += 1
                if (i_a == n_intsec) :
                    title = "Final Intersection"
                    i_chart_fname = chartf_name + "-final ({})".format(i_intsec) + chartf_extension
                else :
                    if do_inside_correction :
                        title = "Intersection {} before inside correction".format(i_intsec)
                        i_chart_fname = chartf_name + "-i{}".format(i_intsec) + chartf_extension
                        draw_3d_polychart([fp_polygon, p_intsec, p_intsec_new], title, fpsize, i_chart_fname)
#                        fig = draw_polygon(p_intsec, title, lon, lat, azi, fpsize, i_chart_fname)
#                        draw_3d_chart()
#                        print(title)
#                        plt.close(fig)
                        p_intsec_new, inside_updated = set_inside_points(p_intsec_new, lon, lat, azi)
                        if inside_updated :
                            i_chart_fname = chartf_name + "-{}_ic".format(i_intsec) + chartf_extension
                            title = "Intersection {} after inside correction".format(i_intsec)
                        else :
                            i_chart_fname = chartf_name + "-{}_uc".format(i_intsec) + chartf_extension
                            title = "Intersection {}, inside not corrected".format(i_intsec)
                    else :
                        i_chart_fname = chartf_name + "-i{}_nc".format(i_intsec) + chartf_extension
                        title = "Intersection {}".format(i_intsec)
                draw_3d_polychart([fp_polygon, p_intsec, p_intsec_new], title, fpsize, i_chart_fname)
                p_intsec = p_intsec_new
                #fig = draw_polygon(p_intsec, title, lon, lat, azi, fpsize, i_chart_fname)
                #draw_3d_chart()
                #print(title)
                ##f_polygons.append(fp_polygon)
                #plt.close(fig)

            i_angle += angle_incr
 
            
        """
        i_intersection = 0
        p_intersection = []
        i_goes = 0
        chartf_name, chartf_extension = path.splitext(save_chart_fname)
        for def_dirs in def_directions :
            i_goes += 1
            if len(def_dirs) == 2 :
                f_polygons = []
                i_d = 0
                for i_angle in def_dirs :
                    i_d += 1
                    fprint_i = fprint_rotate(ftprint, i_angle)
                    fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
                    i_chart_fname = chartf_name + "-{}-{}_d".format(i_goes, i_d) + chartf_extension
                    title = "Defense Direction {:7.2f}".format(i_angle)
                    fig = draw_polygon(fp_polygon, title, lon, lat, azi, fpsize, i_chart_fname)
                    c3.draw_3d_chart(fig, win3d)
                    print(title)
                    f_polygons.append(fp_polygon)
                    plt.close(fig)
                
                #polygon_ll_1 = list(f_polygons[0].to_lonlat()) #TODO delete ll's TODO
                #polygon_ll_2 = list(f_polygons[1].to_lonlat())
                inters_tmp = f_polygons[0].intersection(f_polygons[1])
                i_intersection += 1
                i_chart_fname = chartf_name + "-{}_i".format(i_goes) + chartf_extension
                if (i_goes >= last_call) and  p_intersection == []: # ">=" is just to be safe, "==" should suffice
                    title = "Final Intersection"
                else :
                    if do_inside_correction :
                        title = "Intersection {} before inside correction".format(i_intersection)
                        fig = draw_polygon(inters_tmp, title, lon, lat, azi, fpsize, i_chart_fname)
                        c3.draw_3d_chart(fig, win3d)
                        print(title)
                        inters_tmp_ll = list(inters_tmp.to_lonlat())
                        inters_tmp, inside_updated = set_inside_points(inters_tmp, lon, lat, azi)
                        inters_tmp_ll = list(polygon.SphericalPolygon.to_lonlat(inters_tmp))
                        if inside_updated :
                            i_chart_fname = chartf_name + "-{}_ic".format(i_goes) + chartf_extension
                            title = "Intersection {} after inside correction".format(i_intersection)
                        else :
                            i_chart_fname = chartf_name + "-{}_no".format(i_goes) + chartf_extension
                            title = "Intersection {}, inside not corrected".format(i_intersection)
                    else :
                        title = "Intersection {}".format(i_intersection)
                fig = draw_polygon(inters_tmp, title, lon, lat, azi, fpsize, i_chart_fname)
                c3.draw_3d_chart(fig, win3d)
                print(title)
                #f_polygons.append(fp_polygon)
                plt.close(fig)

            elif len(def_dirs) == 1 :
                i_angle = def_dirs[0]
                fprint_i = fprint_rotate(ftprint, i_angle)
                fp_polygon = footprintm1_2polygon(fprint_i, lon, lat, azi)
                i_chart_fname = chartf_name + "-{}_d".format(i_goes) + chartf_extension
                title = "Defense Direction {:7.2f}".format(i_angle)
                fig = draw_polygon(fp_polygon, title, lon, lat, azi, fpsize, i_chart_fname)
                c3.draw_3d_chart(fig, win3d)
                print(title)
                plt.close(fig)
                inters_tmp = fp_polygon
            else :
                continue                
                
            if p_intersection :
                inters_tmp = p_intersection.intersection(inters_tmp)
                i_intersection += 1
                inters_tmp_ll = list(polygon.SphericalPolygon.to_lonlat(inters_tmp))
                i_chart_fname = chartf_name + "-{}_i".format(i_goes) + chartf_extension
                if i_goes >= last_call :
                    title = "Final Intersection"
                else :
                    if do_inside_correction :
                        title = "Intersection {} before inside correction".format(i_intersection)
                        fig = draw_polygon(inters_tmp, title, lon, lat, azi, fpsize, i_chart_fname)
                        c3.draw_3d_chart(fig, win3d)
                        print(title)
                        inters_tmp, inside_updated = set_inside_points(inters_tmp, lon, lat, azi)
                        inters_tmp_ll = list(polygon.SphericalPolygon.to_lonlat(inters_tmp))
                        if inside_updated :
                            i_chart_fname = chartf_name + "-{}_ic".format(i_goes) + chartf_extension
                            title = "Intersection {} after inside correction".format(i_intersection)
                        else :
                            i_chart_fname = chartf_name + "-{}_no".format(i_goes) + chartf_extension
                            title = "Intersection {}, inside not corrected".format(i_intersection)
                    else :
                        title = "Intersection {}".format(i_intersection)
                fig = draw_polygon(inters_tmp, title, lon, lat, azi, fpsize, i_chart_fname)
                c3.draw_3d_chart(fig, win3d)
                print(title)
                #f_polygons.append(fp_polygon)
                plt.close(fig)
                
            p_intersection = inters_tmp
        """      
        """
        fig = draw_polygon(p_intersection, "Intersection", lon, lat, azi, fpsize, i_chart_fname)
        c3.draw_3d_chart(fig, win3d)
        print("intersection")
        plt.close(fig)
        """
        #isec_points = list(intersection.points)
        
        p_intsec_ll = list(polygon.SphericalPolygon.to_lonlat(p_intsec))
    
        footprint2p_ll = []
        for polyg in p_intsec_ll :
            polylist = list(zip(*polyg))
            
            """
            for i_d, (lon_d, lat_d) in enumerate(polylist):
                if lon_d > 180:
                    polylist[i_d] = (lon_d - 360, lat_d)  # Replace tuple at index i
            """
            polylist_of_lists = [list(duplet) for duplet in polylist]
    
            polylist_of_lists = geojson_proof(polylist_of_lists)
                    
            new_polylist = [tuple(tuplet) for tuplet in polylist_of_lists]
            
            footprint2p_ll.append(new_polylist)
                        
            fp_polygon = geojson.Polygon([new_polylist])
            poly_f = geojson.Feature(geometry = fp_polygon, properties = {'fill': 'blue', 'fill-opacity': 0.3})
    
            featurelist.append(poly_f)
    
        return(featurelist)

"""
if __name__ == '__main__':

    #test_fname = footprint_path + "/footprint_mode2_m11_i11_son_dr240.json"   
    test_fname = footprint_path + "/footprint_mode2_m3_i11_son_test.json"   
    
    fpmod2_test_file = test_fname
    header, fp_list1 = m.load_data(fpmod2_test_file)
    fp_list = fp_list1[0]
    
    #fpart_1 = np.array(fp_list[0])
    #fpart_2 = np.zeros((0,5))
    #fp = [fpart_1, fpart_2]
    fp = [np.array(fp_list[0]), np.array(fp_list[1])]
    
    root = tk.Tk()
    # Create a separate chart window attached to the main Tkinter root
    c3.create_3dchart_window(master=root)
    featurelist = ftp_intersection(fp, -45, 60, 0, 1500000, 10, 10, root)
    # Start the Tkinter main loop for the whole application
    root.mainloop()
    
    fp_featcoll = geojson.FeatureCollection(featurelist)
    
    #print(fp_featcoll)
          
"""
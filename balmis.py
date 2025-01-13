from ambiance import Atmosphere # https://pypi.org/project/ambiance/
import numpy as np 
import rocket_data as rd
from math import pi, sin, cos, asin, acos, atan, sqrt, radians, degrees, \
    ceil, atan2, tan
import time

from fcc_constants import eps, angle_eps, R_e, dist_limit, check_fpa, \
    int_vl_height, out_time_freq, int_vl_top, control_turn # gui
import fcc_constants

# Optional no-op decorator, comment when you want to profile
#def profile(func): return func

local_fpa = False

def_time = False

#ind_flight_dataprint = False
#trajectory_data = True

mu = 3.986e14 # Newton's const times Earth mass
g_E = mu/R_e/R_e #9.81

d_t = 0.1 # time step delta t, s
rv_la = R_e # launch polar radius coord = launch altitude + R_e, m
g_la = mu/rv_la/rv_la # grav accel at launch
#g_la = mu/(rv_la - R_e + R_e0)/(rv_la - R_e + R_e0)  # for when R_N != 1
atm_limit = 81000 # upper limit of atmosphere, m
atm_limit_100 = 100000

gtheight_beg = 100.0
gtheight_end = 12000.0
launcher_length = 20 # length of launcher, m -- gravity force normal to trajectory is set to zero for the first launcher_length m of trajectory

range_eps = 1 # epsilon for range measurements

#if trajectory_data :
#    trj = np.array([0, rv_la, 0], ndmin=2, dtype='f') 

def c_drag0(v_mach):
    """
    NOT USED
    Drag coefficient depending on speed expressed Mach number, based on Altmann, p. 180, Fig. 5-2.

    Parameters
    ----------
    v_mach : float
        speed, Mach number
    Returns
    -------
    k : float
        drag coefficient.

    """

    if v_mach < 1 :
        k = 1
    elif v_mach < 1.2:
        k = 1 + (v_mach - 1) * 2
    elif v_mach < 1.3:
        k = 1.4
    elif v_mach < 2:
        k = 1.4 - (v_mach - 1.3) / 3.5
    elif v_mach < 5:
        k = 1.2 - (v_mach - 2) / 15
    else: k = 1

    return k


def c_drag(v_mach, cd_tab):
    
    len_cdtab = len(cd_tab)
    for i in range(len_cdtab) :
        if v_mach <= cd_tab[i, 0] :
            break
        
    if i == 0 :
        return cd_tab[0, 1]
    elif i == len_cdtab - 1 :
        return cd_tab[len_cdtab - 1, 1]
    else :
        cdrag = cd_tab[i -1 , 1] + (v_mach - cd_tab[i - 1, 0]) * (cd_tab[i, 1] - cd_tab[i - 1, 1]) / (cd_tab[i, 0] - cd_tab[i - 1, 0])
        if cdrag < 0 :
            print(cd_tab)
            print(v_mach, i)

        return cdrag

"""Not used""" #???
def atm_100_tab(h_tab, tab_4) :
    R_gas = 287.05287   # specific gas constant
    kappa = 1.4         # adiabatic index
    
    len_cdtab = len(tab_4)
    for i in range(len_cdtab) :
        if h_tab <= tab_4[i, 0] :
            break
        
    if i == 0 :
        temperature = tab_4[0, 1]
        ro          = tab_4[0, 2]
        pressure    = tab_4[0, 3]
    elif i == len_cdtab - 1 :
        temperature = tab_4[len_cdtab - 1, 1]
        ro          = tab_4[len_cdtab - 1, 2]
        pressure    = tab_4[len_cdtab - 1, 3]
    else :
        temperature = tab_4[i -1 , 1] + (h_tab - tab_4[i - 1, 0]) * (tab_4[i, 1] - tab_4[i - 1, 1]) / (tab_4[i, 0] - tab_4[i - 1, 0])
        ro          = tab_4[i -1 , 2] + (h_tab - tab_4[i - 1, 0]) * (tab_4[i, 2] - tab_4[i - 1, 2]) / (tab_4[i, 0] - tab_4[i - 1, 0])
        pressure    = tab_4[i -1 , 3] + (h_tab - tab_4[i - 1, 0]) * (tab_4[i, 3] - tab_4[i - 1, 3]) / (tab_4[i, 0] - tab_4[i - 1, 0])

    vsound = sqrt(kappa * R_gas * temperature)
    #print(h_tab, ro, vsound, pressure)

    return ro, vsound, pressure


def Xatmosphere_100(h_100) :
    """ NOT GOOD! Temperature at 80 km < h_100 <= 100 km """
    R_gas = 287.05287   # specific gas constant
    kappa = 1.4         # adiabatic index

    if h_100 >= 80000 : #atm_limit :
        if h_100 <= 84852 : # check constants!!!
            temp_100 = 357.6916 - 0.0020 * h_100
        elif h_100 < 89716 :
            temp_100 = 186.87
        else :
            temp_100 = 1e-7 * h_100*h_100 - 0.0215 * h_100 + 1155.6
        
        p_100 = 2e6 * np.exp(-2e-4 * h_100)
        ro_100 = p_100 / R_gas / temp_100
        vsound_100 = sqrt(kappa * R_gas * temp_100)
        
        return ro_100, vsound_100
    
    else :
        print(f"Altitude h_100 = {h_100} m out of limits")
        return False, False


def f_d(v, h, ab, c_type):
    """
    Force of aerodynamic drag    

    Parameters
    ----------
    v : float
        speed, m/s.
    h : float
        elevation over sea level, m.
    ab : float
        for boost cross area, m2, for re-entry m/c_bal in m2
    c_type : string
        drag type: for boost phase "ls", "ll", "v2"; for re-entry "re"

    Returns
    -------
    float
        aerodynamic drag force.

    """
    if fcc_constants.no_atmosphere :
        return(0)
        
    if h <= atm_limit :    
        vsound = Atmosphere(h).speed_of_sound[0]
        ro = Atmosphere(h).density[0]
    elif h <= atm_limit_100 :
        ro, vsound, pressure = atm_100_tab(h, rd.atmosphere100)
    else :
        print(f"Altitude h = {h} m out of limits")
        return False
        
    
    if c_type == "ls" :
        cdrag = c_drag(v/vsound, rd.drag_solid_tab)
    elif c_type == "ll" :
        cdrag = c_drag(v/vsound, rd.drag_liq_tab)
    elif c_type == "v2" :
        cdrag = c_drag(v/vsound, rd.drag_V2_tab)
#    elif c_type == "al" :
#        cdrag = c_drag(v/vsound, rd.drag_Alt_tab) * 0.25 # 0.25 added for KMR testing (JA)
#    elif c_type == "al-re" :
#        cdrag = c_drag(v/vsound, rd.drag_Alt_tab) * 0.15 # 0.15 for warhead re-entry -- NOT USED!
    elif c_type == "re" :
        cdrag = 1 
    else :
        print("Wrong c_type!")

    #if h > atm_limit :
    #    print(h, cdrag, cdrag * ro * v * v * ab /2)
            
    return cdrag * ro * v * v * ab /2

"""
def f_d_0(v, h, a, cd0):
    ""
    Force of aerodynamic drag    

    Parameters
    ----------
    v : float
        speed, m/s.
    h : float
        elevation over sea level, m.
    a : float
        cross area, m2.
    cd0 : float
        drag coefficient at zero velocity

    Returns
    -------
    float
        aerodynamic drag force.

    ""
    atmosphere = Atmosphere(h)
    
    vsound = atmosphere.speed_of_sound[0]
    ro = atmosphere.density[0]
    cdrag = cd0 * c_drag(v/vsound, rd.drag_Alt_tab)

    return cdrag * ro * v * v * a /2
"""

def balmisflight(m_data, trajectory_data=True, ind_flight_dataprint=False) :
    """
    Calculates ballistic missile trajectory for missile/interceptor data passed as parameter.
    Types of trajectory:
        ballistic missile -- vertical start with gravity turn (angle from vertical) starting at height
        interceptor exoatmospheric -- vertical start up to 25 km, then maintain flight path angle (from horizontal) until burnout
        interceptor endoatmospheric - launch at flight path angle (from horizontal), maintained until burnout,
                                      the first 20 m calculated as from a launcher (G normal to velocity zeroed)

    Parameters
    ----------
    m_data : TYPE
        see "rocket_data" module
    trajectory_data : Boolean
        return trajectory array or just range. The default is True.
    ind_flight_dataprint : Boolean
        print individual flight data. The default is False

    Returns
    -------
    range or trajectory.

    """
    #print("bm no_atm", fcc_constants.no_atmosphere)

    m_st = m_data["m_st"] # stage mass, kg
    m_fu = m_data["m_fu"] # fuel mass, kg
    v_ex = m_data["v_ex"] # exhaust velocity, m/s
    v_ex = [x if x > 1000 else x * g_E for x in v_ex] # Isp entered if > 1000
    t_bu = m_data["t_bu"]  # burn time, s
    t_delay = m_data["t_delay"] # stage delay, s
    #t_delay = 0 if m_data["t_delay"] == [] else m_data["t_delay"]
    a_mid = m_data["a_mid"] # stage cross area, m2
    cd_type = m_data["cd_type"] # type of cd vs speed line
    #cd_0 = m_data["cd_0"] # stage drag coeff
    m_shroud = 0 if m_data["m_shroud"] == [] else m_data["m_shroud"] # payload shroud mass (extra to m_pl)
    t_shroud = 0 if m_data["t_shroud"] == [] else m_data["t_shroud"]# time of shroud release
    m_pl = m_data["m_pl"]
    #m_wh = m_data["m_wh"]
    m_warhead = 0 if m_data["m_warhead"] == [] else m_data["m_warhead"]# time of shroud release
    a_nz = m_data["a_nz"]
    #a_pl = m_data["a_pl"] # payload cross area, m2
    #cd_pl = m_data["cd_pl"] # payload drug coeff
    c_bal = m_data["c_bal"] # ballistic coefficient in kg/m2
    #psi = radians(m_data["psi"]) # launch angle velocity and vertical at launch, rad
    traj_type = m_data["traj_type"]
    
    albm = False
    note = m_data['range'].strip().lower()
    if note.startswith('albm') :
        note_str = note.strip('albm ')
        v_la_albm = eval(note_str)
        albm = True
            #traj_type = 'albm'
    """
    if traj_type == 'albm' :
        albm = True
        traj_type = 'bal_mis'
    """

    vl_height = m_data["vert_launch_height"] # missile gravity angle or interc flight path angle starts at altitude, m
    if traj_type == "bal_mis" :
        gt_angle = radians(m_data["grav_turn_angle"]) # gravity turn angle, rad
    else: 
        fp_angle = radians(m_data["flight_path_angle"]) # interceptor trajectory flight path angle, degrees
    
    if (traj_type == 'int_exo') or (traj_type == 'int_endo') :
        if control_turn :
            if vl_height >= int_vl_top :
                print("Vertical launch height needs to be below {:.0f} m".format(int_vl_top))
                return False
    
    # missile total mass at start
    m0 = sum(m_st) + sum(m_fu) + m_pl + m_shroud
    # missile mass at ignition of next stage
    #print("m_shroud = {:.2f} kg, m_launch = {:.2f} kg".format(m_shroud, m0))
 
    v_la = 0.0 # launch speed
    rv_la = R_e
    g_la = mu/rv_la/rv_la
    
    psi = 0.0 # vertical launch
    if albm :
        v_la = v_la_albm
        psi = gt_angle
        rv_la = R_e + vl_height # launch polar radius coord = launch altitude + R_e, m
        g_la = mu/rv_la/rv_la # grav accel at launch
         
    if traj_type == "int_endo" :
        psi = pi/2 - fp_angle
        #l_length = m_data["launcher_length"]
        l_length = launcher_length

     
    s_psi_t = s_psi_t0 = sin(psi) # sine of psi at time=0
    c_psi_t = c_psi_t0 = cos(psi) # cosine
    s_khi_t = s_khi_t0 = sin(psi) # sine of khi at time=0 -- at launch thrust always along velocity
    c_khi_t = c_khi_t0 = cos(psi) # cosine
    
    if psi > eps:
        vertical = False
    else :
        vertical = True
    
    vv_la = v_la * c_psi_t # vertical launch speed
    vh_la = v_la * s_psi_t # horisontal launch speed
    
    thrust = True # non-zero thrust
    fd_t = 0.0 # drag force
    d_alfa = 0.0 # delta alfa
    m_t = m0 # missile mass at time=t
    rv_t_0 = rv_t = rv_la # polar radius coord at launch
    g_t = g_la # grav accel at launch
    v_t0 = v_t = v_la # speed at launch
    vv_t0 = vv_t = vv_la # vertical speed
    vh_t0 = vh_t = vh_la # horisontal speed
    alfa_t0 = alfa_t = 0.0 # polar radius, rad
    t_turn_start = 99999.0 # sum(t_bu) + sum(t_delay) # just init, it's determined by vert_launch_height
    v_turn_start = 0.0 # speed at turn start
    qb_max = 0.0 # max drag force during boost
    qb_max_time = 0.0
    qb_max_h = 0.0
    tv_angle = 0.0
    set_zero = False
    first_fpa = False

    v_max = 0.0
    v_max_h = 0
    v_max_time = 0
    
    tr_x0 = tr_x = 0
    tr_y0 = tr_y = rv_la - R_e
    
    rv_max = rv_t
    rv_max_time = 0.0
    max_h_alfa = alfa_t
    max_h_vh = vh_t
    max_h_vv = vv_t
    
    burn_up = False # neded when stage delay = 0 to printout burn up data 

    if ind_flight_dataprint :
        #print("no_atmosphere={}".format(fcc_constants.no_atmosphere))
        if albm :
            print( "\nBalmisflight: Type = {}, Trajectory type = {} ALBM, Launch Angle = {}".format(m_data["type"], traj_type, m_data["grav_turn_angle"]) )
        else :
            if traj_type == 'bal_mis' :
                print( "\nBalmisflight: Type = {}, Trajectory type = {}, Gravity turn Angle = {}".format(m_data["type"], traj_type, m_data["grav_turn_angle"]) )
            else :
                print( "\nBalmisflight: Type = {}, Trajectory type = {}, Flight Path Angle = {}".format(m_data["type"], traj_type, m_data["flight_path_angle"]) )
    if trajectory_data :
        if check_fpa and (traj_type != 'bal_mis') :
            fpa_trj = np.array([0, rv_la - R_e, 90, 0, rv_la - R_e, 0, 0, 0, 0, 0, 0, 0], ndmin=2) # time, r, beta, x, y, tv_angle, fpa(v), fpa(x,y), vv, vh -- distance values in km
            #fpa_trj = np.array([0, 0, 90, 0, 0, 0, 0, 0 , 0], ndmin=2) # time, r, beta, x, y, h, fpa,... -- distance values in km # two extras
        else :
            bmf_trj = np.array([0, rv_la, 0, v_la, 0], ndmin=2) # two extras added JA test
    if def_time : l_time = time.time()
    
    i = 0 #stage count
    t_bu_i = 0 # burn out time current stage or stage+delay
    n_stages = len(m_st)
    t_t = d_t
    
    psi_t0 = psi_t = psi
    
    if traj_type == "bal_mis" or vertical :
        launcher = False
    else : launcher = True
    
    atm_exit_speed = 0
    re_entry_speed = 0
    
    orbital = False
    time_too_long = False
    
    while i < n_stages:
    # i-th stage burn out time from launch
        t_bu_i += t_bu[i]
        #if ind_flight_dataprint : print(i, t_bu_i, t_bu[i])
    # fuel burn rate
        if t_bu[i] :
            m_dot = m_fu[i]/t_bu[i]
        else: 
            break
        f_th_base = m_dot * v_ex[i]
        f_th = f_th_base
        while t_t < t_bu_i + eps : # to avoid rounding error
            #control = False
            m_t0 = m_t
            if m_shroud :
                if t_t > t_shroud :
                    m_t -= m_shroud
                    m_shroud = 0                    
            f_th0 = f_th
            if thrust :
                m_t -= m_dot * d_t
                if (i == 0) and a_nz :
                #if a_nz and (rv_t - R_e) < atm_limit :
                    h_t = rv_t - R_e
                    if not fcc_constants.no_atmosphere :
                        if h_t <= atm_limit :
                            atmosphere = Atmosphere(h_t)
                            f_th = f_th_base + a_nz * (101325 - atmosphere.pressure[0])
                        elif h_t <= atm_limit_100 :
                            par_ro, par_vsound, pressure = atm_100_tab(h_t, rd.atmosphere100)
                            f_th = f_th_base + a_nz * (101325 - pressure)
                        
            g_t0 = g_t
            g_t = mu/rv_t/rv_t
            #g_t = mu/(rv_t - R_e + R_e0)/(rv_t - R_e + R_e0)  # for when R_N != 1
            fd_t0 = fd_t
            if rv_t - R_e > atm_limit_100 :
                if not atm_exit_speed :
                    atm_exit_speed = v_t
                if  rv_t - R_e > atm_limit_100 :
                    fd_t = 0.0
                else :
                    fd_t = f_d(v_t, rv_t - R_e, a_mid[i], cd_type)                    
            else:
                fd_t = f_d(v_t, rv_t - R_e, a_mid[i], cd_type)
                #fd_t = f_d(v_t, rv_t - R_e, a_mid[i], cd_0[i])
                if fd_t > qb_max:
                    qb_max = fd_t
                    qb_max_time = t_t
                    qb_max_h = rv_t - R_e

            if thrust and (traj_type != "bal_mis") : # interceptor trajectory
                s_khi_t0 = s_khi_t
                c_khi_t0 = c_khi_t
                if (traj_type == "int_exo") and control_turn :
                    if (psi_t > eps) or (not vertical) :
                        beta_alt = atan2( rv_t * cos(alfa_t) - int_vl_top - R_e, rv_t * sin(alfa_t) ) # elevation to start + int_vert_height horizontal
                        if (pi/2 - psi_t - fp_angle) > 0.0001 :
                            #control = True
                            """
                            par_fi = sqrt((pi/2 - fp_angle - psi_t) / (pi/2 - fp_angle))
                            par_di = 2.5 * (int_vl_top + rv_t * sin(alfa_t) * tan(fp_angle) - rv_t * cos(alfa_t) + R_e) / (int_vl_top - vl_height)
                            ctrl_angle = atan2(par_di, par_fi)
                            tv_angle = asin(m_t * g_t * cos(fp_angle + alfa_t) / f_th)
                            tv_angle += ctrl_angle - pi/2 + psi_t #) * (par_fi*par_fi + par_di*par_di)
                            #tv_angle *= ctrl_angle / pi * 2
                            #tv_angle = ctrl_angle - pi/2 + psi_t
                            if tv_angle - psi_t > 0 : print(degrees(tv_angle), degrees(psi_t))
                            """
                            """
                            tv_angle = asin(m_t * g_t * cos(fp_angle + alfa_t) / f_th)
                            th_angle = pi/2 - fp_angle + tv_angle
                            if psi_t == 0 :
                                par_di = 999
                                par_fi = 999
                                ctrl_angle = fp_angle
                            else:
                                #print(t_t, degrees(psi_t0), degrees(psi_t))
                                par_fi = (pi/2 - fp_angle - psi_t) / psi_t
                                par_di = (int_vl_top + rv_t * sin(alfa_t) * tan(fp_angle) - rv_t * cos(alfa_t) + R_e) / (rv_t * cos(alfa_t) - R_e)# - vl_height)
                                ctrl_angle = atan((par_di / par_fi) * tan(fp_angle)) #th_angle))
                                if ctrl_angle < 0 : ctrl_angle = 0
                            tv_angle = ctrl_angle - pi/2 + psi_t
                            """
                            tv_angle = max((fp_angle - pi/2 + psi_t) / control_turn, -radians(45))
                            #ctrl_angle = pi/2 -psi_t + tv_angle
                            #par_di = 999
                            #par_fi = 999
                            
                            
                        else :
                            if local_fpa : 
        #                    tv_angle = asin((g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle) / f_th)
                                ft_limit = (g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle) / f_th
                                if (abs(ft_limit) <= 1) and not set_zero :
                                    tv_angle = asin(ft_limit) 
                                    #if t_t > 119 and t_t < 121 or t_t < 1:
                                    #    print(round(t_t, 1), degrees(asin((g_t - v_t * v_t / rv_t) * m_t * vh_t / v_t / f_th)), degrees(psi_t))
                                else : # thrust not sufficient to maintain flight path angle, happens with A3 kv motor
                                    set_zero = True
                                    tv_angle = 0
                                #if int(round(t_t * 10)) % 100 == 0 :
                                #    print(round(t_t, 1), degrees(tv_angle), degrees(psi_t), R_e * alfa_t / 1000, rv_t - R_e)
        #                    tv_angle = asin((g_t * cos(fp_angle) - v_t0 * (vh_t + vh_t0) / 2 / rv_t) * m_t / f_th)
                            else :
                                #ft_limit = (g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle + alfa_t) / f_th
                                ft_limit = m_t * g_t * cos(fp_angle + alfa_t) / f_th
                                if (abs(ft_limit) <= 1) and not set_zero :
                                    tv_angle = asin(ft_limit)
                                else : # thrust not sufficient to maintain flight path angle
                                    set_zero = True
                                    tv_angle = 0

                        c_khi_t = cos(psi_t - tv_angle)
                        s_khi_t = sin(psi_t - tv_angle)
                    else :
                        c_khi_t = cos(psi_t)
                        s_khi_t = sin(psi_t)
                else : # instant direction change, as in Altmann's book
                    if psi_t > eps :
                        if local_fpa : 
    #                    tv_angle = asin((g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle) / f_th)
                            ft_limit = (g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle) / f_th
                            if (abs(ft_limit) <= 1) and not set_zero :
                                tv_angle = asin(ft_limit) 
                                #if t_t > 119 and t_t < 121 or t_t < 1:
                                #    print(round(t_t, 1), degrees(asin((g_t - v_t * v_t / rv_t) * m_t * vh_t / v_t / f_th)), degrees(psi_t))
                            else : # thrust not sufficient to maintain flight path angle, happens with A3 kv motor
                                set_zero = True
                                tv_angle = 0
                            #if int(round(t_t * 10)) % 100 == 0 :
                            #    print(round(t_t, 1), degrees(tv_angle), degrees(psi_t), R_e * alfa_t / 1000, rv_t - R_e)
    #                    tv_angle = asin((g_t * cos(fp_angle) - v_t0 * (vh_t + vh_t0) / 2 / rv_t) * m_t / f_th)
                        else :
                            #ft_limit = (g_t - v_t * v_t / rv_t) * m_t * cos(fp_angle + alfa_t) / f_th
                            ft_limit = m_t * g_t * cos(fp_angle + alfa_t) / f_th
                            if (abs(ft_limit) <= 1) and not set_zero :
                                tv_angle = asin(ft_limit)
                            else : # thrust not sufficient to maintain flight path angle
                                set_zero = True
                                tv_angle = 0

                        c_khi_t = cos(psi_t - tv_angle)
                        s_khi_t = sin(psi_t - tv_angle)
                    else :
                        c_khi_t = cos(psi_t)
                        s_khi_t = sin(psi_t)

            # ap4 = 0
            if (traj_type == "bal_mis") or vertical :
                d_vv_t = ((f_th - fd_t) * c_psi_t / m_t - g_t + (f_th0 - fd_t0) * c_psi_t0 / m_t0 - g_t0) /2 * d_t
                d_vh_t = ((f_th - fd_t) * s_psi_t / m_t +       (f_th0 - fd_t0) * s_psi_t0 / m_t0) /2 * d_t
            else :
                if first_fpa : # i.e. point fo change from vertical to fpa
                    first_fpa = False
                    s_khi_t0 = s_khi_t
                    c_khi_t0 = c_khi_t
                    s_psi_t0 = s_psi_t
                    c_psi_t0 = c_psi_t

                if launcher :
                    # ap4 = rv_t*rv_t + rv_la*rv_la - 2 * rv_t * rv_la * cos(alfa_t)
                    # ap4 = sqrt(abs(rv_t*rv_t + rv_la*rv_la - 2 * rv_t * rv_la * cos(alfa_t)))
                    if (rv_t*rv_t + rv_t_0*rv_t_0 - 2 * rv_t * rv_t_0 * cos(alfa_t)) < l_length*l_length :
                        """ ver 221101 """                        
                        d_vv_t = ((f_th - fd_t) * cos(psi) / m_t + (f_th0 - fd_t0) * cos(psi) / m_t0) / 2 * d_t
                        d_vv_t -= (g_t + g_t0) / 2 * cos(psi) * cos(psi) * d_t
                        d_vh_t = ((f_th - fd_t) * sin(psi) / m_t + (f_th0 - fd_t0) * sin(psi) / m_t0) / 2 * d_t
                        d_vh_t -= (g_t + g_t0) * sin(psi * 2) / 4 * d_t
                        """ v. up to 221031
                        d_vv_t = ((f_th - fd_t) * c_psi_t / m_t + (f_th - fd_t0) * c_psi_t0 / m_t0) /2 * d_t
                        d_vh_t = ((f_th - fd_t) * s_psi_t / m_t + (f_th - fd_t0) * s_psi_t0 / m_t0) /2 * d_t
                        """
                    else : 
                        launcher = False
#                        d_vv_t = ((f_th * c_khi_t - fd_t * c_psi_t) / m_t - g_t + (f_th0 * c_khi_t0 - fd_t0 * c_psi_t0) / m_t0 - g_t0) /2 * d_t
#                        d_vh_t = ((f_th * s_khi_t - fd_t * s_psi_t) / m_t +       (f_th0 * s_khi_t0 - fd_t0 * s_psi_t0) / m_t0) /2 * d_t
                        d_vv_t = ((f_th * c_khi_t - fd_t * c_psi_t) / m_t - g_t) * d_t
                        d_vh_t = ((f_th * s_khi_t - fd_t * s_psi_t) / m_t ) * d_t
                else : 
#                    d_vv_t = ((f_th * c_khi_t - fd_t * c_psi_t) / m_t - g_t + (f_th0 * c_khi_t0 - fd_t0 * c_psi_t0) / m_t0 - g_t0) /2 * d_t
#                    d_vh_t = ((f_th * s_khi_t - fd_t * s_psi_t) / m_t +       (f_th0 * s_khi_t0 - fd_t0 * s_psi_t0) / m_t0) /2 * d_t
                    d_vv_t = ((f_th * c_khi_t - fd_t * c_psi_t) / m_t - g_t) * d_t
                    d_vh_t = ((f_th * s_khi_t - fd_t * s_psi_t) / m_t ) * d_t
                        
            vv_t0 = vv_t
            vv_t += d_vv_t
            vh_t0 = vh_t
            vh_t += d_vh_t
            v_t0 = v_t
            v_t = sqrt(vv_t*vv_t + vh_t*vh_t)
    
            if v_t > v_max :
                v_max = v_t
                vh_max = vh_t
                vv_max = vv_t
                v_max_h = rv_t - R_e
                v_max_time = t_t

            d_rv_t = (vv_t + vv_t0)/2 * d_t
            d_rh_t = (vh_t + vh_t0)/2 * d_t
            d_r_t2 = d_rh_t*d_rh_t + d_rv_t*d_rv_t
            rv_t_0 = rv_t
            rv_t = sqrt(rv_t_0*rv_t_0 + d_r_t2 + 2 * rv_t_0 * d_rv_t)
    
            if rv_t > rv_max:
                rv_max = rv_t
                rv_max_time = t_t
                max_h_alfa = alfa_t
                max_h_vh = vh_t
                max_h_vv = vv_t

            if rv_t + eps < R_e :
                #print("crash at launch: angle={:.2f} height={:.2f}".format(m_data["grav_turn_angle"], m_data["vert_launch_height"]/1000))
                #return 0 # needed for s()
                break
            
            d_alfa = asin(d_rh_t/rv_t)
            alfa_t0 = alfa_t
            alfa_t += d_alfa
            
            """ >>>trajectory data<<< """
            if trajectory_data :
                if check_fpa and (traj_type != 'bal_mis') :
                    tr_x0 = tr_x
                    tr_y0 = tr_y 
                    tr_x = rv_t * sin(alfa_t)
                    tr_y = rv_t * cos(alfa_t) - rv_la
                    tr_r = sqrt(tr_x*tr_x + tr_y*tr_y)
                    beta_alt = atan2(rv_t * cos(alfa_t) - R_e - vl_height, tr_x) # elevation to start horizontal
                    #beta_deg = degrees(beta_alt)
                    if local_fpa : # local horizontal
                        fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta_alt), tr_x/1000, tr_y/1000,  degrees(tv_angle), degrees(asin(vv_t/v_t)), degrees(atan2(tr_y - tr_y0, tr_x - tr_x0)), d_vv_t, d_vh_t, vv_t, vh_t]], axis=0) # fpa to local horizontal
                    else : # to start horizontal
#                        fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000, (rv_t - R_e)/1000, degrees(asin((vv_t * cos(alfa_t) - vh_t * sin(alfa_t)) / v_t))]], axis=0) # fpa to start horizontal
                        #if control :
                            #fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta_alt), tr_x/1000, tr_y/1000, degrees(tv_angle), degrees(asin((vv_t * cos(alfa_t) - vh_t * sin(alfa_t)) / v_t)), degrees(atan2(tr_y - tr_y0, tr_x - tr_x0)), par_di, par_fi, ctrl_angle, tv_angle]], axis=0) # fpa to start horizontal
                        #else :
                        fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta_alt), tr_x/1000, tr_y/1000, degrees(tv_angle), degrees(asin((vv_t * cos(alfa_t) - vh_t * sin(alfa_t)) / v_t)), degrees(atan2(tr_y - tr_y0, tr_x - tr_x0)), d_vv_t, d_vh_t, vv_t, vh_t]], axis=0) # fpa to start horizontal
                else :
                    """ acceleration calc added for JA test """
                    av_t = d_vv_t / d_t #
                    ah_t = d_vh_t / d_t #
                    a_t = sqrt(av_t*av_t + ah_t*ah_t) #
                    if v_t < v_t0 :
                        a_t = -a_t
                    #a_t = (v_t - v_t0) / d_t
                    bmf_trj = np.append(bmf_trj, [[t_t, rv_t, alfa_t, v_t, a_t]], axis=0) # JA test


#            psi_t = atan(vh_t/vv_t) - d_alfa
#            psi_t = asin(vh_t/v_t) - d_alfa
#            if vv_t < 0 : psi_t = pi - psi_t
#            if vv_t < 0 : psi_t = pi - psi_t - 2 * d_alfa

            psi_t0 = psi_t
            if vv_t > 0 :
                psi_t = asin(vh_t/v_t) - d_alfa
            else :
                psi_t = pi - asin(vh_t/v_t) - d_alfa
            
            psi_t_deg = degrees(psi_t)
            
            # start gravity turn at height vl_height
            if ((rv_t - R_e) > vl_height) and vertical and thrust :
                vertical = False
                t_turn_start = t_t
                v_turn_start = v_t
                if traj_type == "bal_mis" :
                    psi_t = gt_angle
                else:
                    if not control_turn :
                        psi_t = pi/2 - fp_angle
                #s_psi_t0 = sin(psi_t)
                #c_psi_t0 = cos(psi_t)
                first_fpa = True
            
            s_psi_t0 = s_psi_t
            c_psi_t0 = c_psi_t
            c_psi_t = cos(psi_t)
            s_psi_t = sin(psi_t)
            vv_t = v_t * c_psi_t
            vh_t = v_t * s_psi_t

#            if trajectory_data : # ???
#                fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000, (rv_t - R_e)/1000, vh_t, c_psi_t, s_psi_t]], axis=0) # not used

# reinsert fpa here
                                        
        # stage delay
            if burn_up :
                burn_up = False
                if ind_flight_dataprint :
                    print("Stage {} b/up : time     = {:7.3f} s,  mass  = {:9.3f} kg,  thrust = {:8.3f} kN, gravity = {:6.3f} m/s2".format(i + 1, t_t, m_t, f_th/1000, g_t))
                    print( "             : altitude = {:7.3f} km, speed = {:9.3f} km/s, range = {:8.3f} km, angle   = {:6.3f} deg".format((rv_t - R_e)/1000, v_t/1000, alfa_t * R_e /1000, degrees(asin(vv_t/v_t))))
            if i+1 < n_stages :        
                if thrust :
                    if t_t + d_t - t_bu_i > eps :
                        if t_delay[i] > d_t:
                            thrust = False
                            f_th = 0
                            t_bu_i += t_delay[i]
                        #m_t -= m_fu[i]
                        if ind_flight_dataprint :
                            #print("Stage {} b/out: time={:.2f}, missile.m={:.1f}, thrust={}, b/out time={:.2f}, g_t={:.3f}".format(i + 1, t_t, m_t, thrust, t_bu_i, g_t))
                            print("Stage {} b/out: time     = {:7.3f} s,  mass  = {:9.3f} kg,  thrust = {:8.3f} kN, gravity = {:6.3f} m/s2".format(i + 1, t_t, m_t, f_th/1000, g_t))
                            print( "             : altitude = {:7.3f} km, speed = {:9.3f} km/s, range = {:8.3f} km, angle   = {:6.3f} deg".format((rv_t - R_e)/1000, v_t/1000, alfa_t * R_e /1000, degrees(asin(vv_t/v_t))))
                            if thrust :
                                burn_up = True
                                #print("Stage {} started without delay.".format(i + 2))
                        m_t -= m_st[i]
                    """
                    else :
                        if burn_up :
                            burn_up = False
                            if ind_flight_dataprint :
                                print("Stage {} b/up : time     = {:7.3f} s,  mass  = {:9.3f} kg,  thrust = {:8.3f} kN, gravity = {:6.3f} m/s2".format(i + 1, t_t, m_t, f_th/1000, g_t))
                                print( "             : altitude = {:7.3f} km, speed = {:9.3f} km/s, range = {:8.3f} km, angle   = {:6.3f} deg".format((rv_t - R_e)/1000, v_t/1000, alfa_t * R_e /1000, degrees(asin(vv_t/v_t))))
                    """
                elif t_t + d_t - t_bu_i > eps:
                    thrust = True
                    if ind_flight_dataprint :
                        #print("Stage {} b/up : time={:.2f}, missile.m={:.1f}, thrust={}, g_t={:.3f}".format(i + 2, t_bu_i, m_t, thrust, g_t))
                        #print("             : alt={:.3f} km, speed={:.3f} km/s, angle={:.3f} deg, range={:.3f} km".format((rv_t - R_e)/1000, v_t/1000, degrees(asin(vv_t/v_t)), alfa_t * R_e /1000))
                        print("Stage {} b/up : time     = {:7.3f} s,  mass  = {:9.3f} kg,  thrust = {:8.3f} kN, gravity = {:6.3f} m/s2".format(i + 2, t_t, m_t, f_th/1000, g_t))
                        print( "             : altitude = {:7.3f} km, speed = {:9.3f} km/s, range = {:8.3f} km, angle   = {:6.3f} deg".format((rv_t - R_e)/1000, v_t/1000, alfa_t * R_e /1000, degrees(asin(vv_t/v_t))))
                    #if ind_flight_dataprint : print("Stage  b/up: cur.stage#={}, time={:.2f}, missile.m={:.1f}, thrust={}, b/up  time={:.2f}".format(i, t_t, m_t, thrust, t_bu_i))

            t_t += d_t
    
        if rv_t < R_e :
            #if ind_flight_dataprint :
            #    print("Hit the ground before burnout")
            break
        i += 1
#        if ind_flight_dataprint : print("Staging: next stage#={}, missile mass={:.1f}".format(i, m_t))
    
    t_burnout = t_t - d_t
    #print(t_burnout)

    if ind_flight_dataprint :    
        """ problems when burnout speed is greater than orbital
        vc2 = mu/rv_t
        vc = sqrt(vc2)
        vbvc2 = v_t*v_t/vc2
        if vbvc2 < 1 :
            range_max = 2 * rv_t * asin( vbvc2 / (2 - vbvc2))
            angle_rmax = acos(1/sqrt(2-vbvc2))
        else :
            range_max = 40000000
            angle_rmax = 0
        axis_a = rv_t / (2 - vbvc2)
        ecce_e = sqrt(1 - vbvc2 * (2 - vbvc2) * cos(angle_rmax)**2) # subst angle_max with acos
        #ecce_e = sqrt(1 - vbvc2)
        height_max = axis_a * (1 + ecce_e) - rv_t
        print("h_bu={:.2f} km, v_bu={:.2f} km/s".format((rv_t - R_e)/1000, v_t/1000))
        # theoretical for launch with v_bu at h_bu -- should not be far off calculated results
        print(">>>theoretical: v_circular={:.2f} km/s, max range={:.1f} km at throw angle={:.1f} deg".format(vc/1000, range_max/1000, degrees(angle_rmax)))
        print(">>>theoretical: max height={:.1f} km (over h_bu)".format(height_max/1000) )
        # print( "m_bu={:.2f}, h_bu={:.2f}, g_bu={:.3f}, vv_bu={:.3f}".format(m_t, rv_t - R_e, g_t, vv_t))
        
        # max height of vertical launch with burnout speed
        hvertmax = mu/((2*mu-v_t*v_t*R_e)/2/R_e)-R_e
        print(">>>theoretical: max height if launched vertically = {:.1f} km".format(hvertmax/1000))
        """
        range_bu = R_e * alfa_t
        angle_bu = 90 # throw angle, deg
        # if vh_t > 0 : angle_bu = degrees(atan(vv_t/vh_t))
        if v_t > 0 : 
            angle_bu = asin(vv_t/v_t)
            angle_bu_start = angle_bu - alfa_t
        #v_bu = v_t
        if vl_height > rv_t - R_e : v_turn_start = 99999
        
        if rv_t < R_e :
            print(">>> The rocket hit the ground before burnout.")
        
        if set_zero :
            print(">>> The interceptor cannot maintain flight path angle due to insufficient thrust.")
        #print("Launch    : mass = {:9.2f} kg, altitude = {:7.3f} km,  gravity = {:6.3f} m/s2,speed = {:6.3f} km/s".format(m0, (rv_la - R_e)/1000, g_la, v_la/1000))
        print("Launch    : mass = {:9.2f} kg, altitude = {:7.3f} km, speed   = {:6.3f} km/s, angle    = {:6.3f}, gravity = {:.3f} m/s2".format(m0, (rv_la - R_e)/1000, v_la/1000, degrees(psi), g_la))

              
        if traj_type == "bal_mis" :
            if gt_angle :
                angle = gt_angle
            else :
                angle = psi
            if t_turn_start > 99000:
                print( "Gravi turn: time =               altitude = {:7.3f} km, speed   =              gt_angle = {:6.3f} deg".format(vl_height/1000, degrees(angle)))
            else :
                print( "Gravi turn: time = {:9.2f} s,  altitude = {:7.3f} km, speed   = {:6.3f} km/s, gt_angle = {:6.3f} deg".format(t_turn_start, vl_height/1000, v_turn_start/1000, degrees(angle)))
        else : 
            angle = fp_angle
            print("Pitch-over: time = {:9.2f} s,  altitude = {:7.3f} km, speed   = {:6.3f} km/s, fp_angle = {:6.3f} deg".format(t_turn_start, vl_height/1000, v_turn_start/1000, degrees(angle)))
        print("Burn out  : time = {:9.2f} s,  altitude = {:7.3f} km, speed   = {:6.3f} km/s, angle_bu = {:6.3f} deg".format(t_burnout, (rv_t - R_e)/1000, v_t/1000, degrees(angle_bu)))
        if control_turn :
            delta_h = int_vl_top + rv_t * sin(alfa_t) * tan(fp_angle) - rv_t * cos(alfa_t) + R_e
            print("Burn out  : range = {:7.3f} km, delta_h = {:7.2f} m, tv_angle = {:7.3f}, angle_bu to start hrz  = {:6.3f} deg".format(range_bu/1000, delta_h, degrees(tv_angle), degrees(angle_bu_start)))
        else :
            print("Burn out  : mass = {:9.2f} kg, range    = {:7.3f} km, gravity = {:6.3f} m/s2, angle_bu to start hrz = {:6.3f} deg".format(m_t, range_bu/1000, g_t, degrees(angle_bu_start)))
        #print( "throw angle = {:.1f} deg".format(90 - psi))
    
    if def_time : 
        b_time = time.time()
        boost_time = b_time - l_time
        print("Calculation elapsed time: d_t={:.3f}s boost time = {:.3f}s ".format(d_t, boost_time))

    """ *********************** """
    """ Post boost phase flight """
    """ *********************** """
    m_m = m_t #m_pl i.e. no warhead separation unless m_warhead > 0, see below
    
    qt_max = 0.0
    qt_max_time = 0.0
    qt_max_h = 0.0

    #d_t = 1.0
    while rv_t + eps > R_e :
        if m_warhead :
            if (t_t - t_burnout) >= t_delay[n_stages - 1] : m_m = m_warhead
        g_t0 = g_t
        g_t = mu/rv_t/rv_t
        #g_t = mu/(rv_t - R_e + R_e0)/(rv_t - R_e + R_e0) # for when R_N != 1
        fd_t0 = fd_t
        if rv_t - R_e > atm_limit_100 :
            if not atm_exit_speed :
                atm_exit_speed = v_t
            if rv_t - R_e > atm_limit_100 :
                fd_t = 0.0
            else :
                if m_warhead and m_m == m_warhead :
                    fd_t = f_d(v_t, rv_t - R_e, m_m / c_bal , 're')
                else :
                    fd_t = f_d(v_t, rv_t - R_e, a_mid[n_stages - 1], cd_type)                
            #re_entry_speed = v_t
        else:
            if atm_exit_speed :
                if not re_entry_speed :
                    re_entry_speed = v_t
                fd_t = f_d(v_t, rv_t - R_e, m_m / c_bal , 're')
                if fd_t < 0 :            
                    print("1 fd_t < 0 !!!")
            else :
                #fd_t = f_d(v_t, rv_t - R_e, a_mid[n_stages - 1], cd_type)
                if m_warhead and m_m == m_warhead :
                    fd_t = f_d(v_t, rv_t - R_e, m_m / c_bal , 're')
                else :
                    fd_t = f_d(v_t, rv_t - R_e, a_mid[n_stages - 1], cd_type)                
                if fd_t < 0 :            
                    print("2 fd_t < 0 !!!, fd_t={:.2f}, v_t={:.3f}, n_stages={}, a_mid={:.2f} cd_type={}".format(fd_t, v_t, n_stages, a_mid[n_stages - 1], cd_type))
                    return
            #fd_t = f_d(v_t, rv_t - R_e, m_m / c_bal , 'al') # for testing JA
            if fd_t > qt_max:
                qt_max = fd_t
                qt_max_time = t_t
                qt_max_h = rv_t - R_e
        #d_vv_t = - (fd_t * abs(c_psi_t)/m_m + g_t + fd_t0 * abs(c_psi_t0)/m_m + g_t0)/2 * d_t
        d_vv_t = - (fd_t * c_psi_t/m_m + g_t + fd_t0 * c_psi_t0/m_m + g_t0)/2 * d_t
        vv_t0 = vv_t
        vv_t += d_vv_t
        d_vh_t = - (fd_t * s_psi_t/m_m + fd_t0 * s_psi_t0/m_m) /2 * d_t
        vh_t0 = vh_t
        vh_t += d_vh_t
        v_t0 = v_t
        v_t = sqrt(vv_t*vv_t + vh_t*vh_t)
    
        if v_t > v_max :
            v_max = v_t
            vh_max = vh_t
            vv_max = vv_t
            v_max_h = rv_t - R_e
            v_max_time = t_t
    
        d_rv_t = (vv_t + vv_t0)/2 * d_t
        d_rh_t = (vh_t + vh_t0)/2 * d_t
        d_r_t2 = d_rh_t*d_rh_t + d_rv_t*d_rv_t
        rv_t_0 = rv_t
        rv_t = sqrt(rv_t_0*rv_t_0 + d_r_t2 + 2 * rv_t_0 * d_rv_t)
    # same    rv_t = sqrt((rv_t_0 + d_rv_t)*(rv_t_0 + d_rv_t) + d_rh_t*d_rh_t)
        
        if rv_t > rv_max:
            rv_max = rv_t
            rv_max_time = t_t
            max_h_alfa = alfa_t
            max_h_vh = vh_t
            max_h_vv = vv_t
    
        d_alfa = asin(d_rh_t/rv_t)
        alfa_t += d_alfa

        """ >>>trajectory data<<< """
        if trajectory_data :
            if not (check_fpa and (traj_type != 'bal_mis')) :
                """ acceleration calc added for JA test """
                av_t = d_vv_t / d_t #
                ah_t = d_vh_t / d_t #
                a_t = sqrt(av_t*av_t + ah_t*ah_t) #
                if v_t < v_t0 :
                    a_t = -a_t
                #a_t = (v_t - v_t0) / d_t
                bmf_trj = np.append(bmf_trj, [[t_t, rv_t, alfa_t, v_t, a_t]], axis=0)
            else :
                tr_x0 = tr_x
                tr_y0 = tr_y 
                tr_x = rv_t * sin(alfa_t)
                tr_y = rv_t * cos(alfa_t) - rv_la
                tr_r = sqrt(tr_x*tr_x + tr_y*tr_y)
                beta = asin(tr_y / tr_r)
                if local_fpa :
                    fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000,  degrees(tv_angle), degrees(asin(vv_t/v_t)), degrees(atan2(tr_y - tr_y0, tr_x - tr_x0)), d_vv_t, d_vh_t, vv_t, vh_t]], axis=0) # fpa to local horizontal
                else :
#                    fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000, (rv_t - R_e)/1000, degrees(asin((vv_t * cos(alfa_t) - vh_t * sin(alfa_t)) / v_t))]], axis=0) # fpa to start horizontal
                    fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000, degrees(tv_angle), degrees(asin((vv_t * cos(alfa_t) - vh_t * sin(alfa_t)) / v_t)), degrees(atan2(tr_y - tr_y0, tr_x - tr_x0)), d_vv_t, d_vh_t, vv_t, vh_t]], axis=0) # fpa to start horizontal
    
#        qq0 = vh_t/v_t
#        qq = asin(vh_t/v_t)
        if vv_t > 0 :
            psi_t = asin(vh_t/v_t) - d_alfa
        else :
            psi_t = pi - asin(vh_t/v_t) - d_alfa
    
        s_psi_t0 = s_psi_t
        c_psi_t0 = c_psi_t
        c_psi_t = cos(psi_t)
        s_psi_t = sin(psi_t)
        vv_t = v_t * c_psi_t
        vh_t = v_t * s_psi_t

#        if trajectory_data : # ???
#            fpa_trj = np.append(fpa_trj, [[t_t, tr_r/1000, degrees(beta), tr_x/1000, tr_y/1000, (rv_t - R_e)/1000, vh_t, c_psi_t, s_psi_t]], axis=0) # not used
    
        if alfa_t > 2 * pi :
            orbital = True
            print("ORBITAL")
            break
        
        if t_t > 10000 :
            time_too_long = True
            print("Flight time >= 10000 s")
            break
            
        t_t += d_t
    
    t_t -= d_t
    alfa_end = alfa_t
    t_end = t_t
    v_end = v_t
    
    if rv_t < R_e :
        t_t0 = t_t - d_t
        alfa_t0 = alfa_t - d_alfa
        h2 = rv_t - R_e
        h1 = rv_t_0 - R_e
        alfa_end = (h1 * alfa_t - h2 * alfa_t0) / (h1 - h2)
        t_end = (h1 * t_t- h2 * t_t0) / (h1 - h2)
        rv_t_end = R_e
        v_end = v_t
        #print("Enf of trajectory, no bmf")
        #print("1: {:.3f}, {:.3f}, {:.3f}".format(t_t0, rv_t_0, degrees(alfa_t0)))
        #print("0: {:.3f}, {:.3f}, {:.3f}".format(t_end, rv_t_end, degrees(alfa_end)))
        #print("2: {:.3f}, {:.3f}, {:.3f}".format(t_t, rv_t, degrees(alfa_t)))
    
    
    if trajectory_data and not (check_fpa and (traj_type != 'bal_mis')):
        trj_len = len(bmf_trj)
        if bmf_trj[trj_len - 1, 1] < R_e :
            h2 = bmf_trj[trj_len - 1, 1] - R_e
            h1 = bmf_trj[trj_len - 2, 1] - R_e
            t2 = bmf_trj[trj_len - 1, 0]
            t1 = bmf_trj[trj_len - 2, 0]
            alfa2 = bmf_trj[trj_len - 1, 2]
            alfa1 = bmf_trj[trj_len - 2, 2]
            alfa_end = (h1 * alfa2 - h2 * alfa1) / (h1 - h2)
            alfa_t = alfa_end
            t_end = (h1 * t2 - h2 * t1) / (h1 - h2)
            veloc = bmf_trj[trj_len - 1, 3] # JA test
            accel = bmf_trj[trj_len - 1, 4] # JA test
            bmf_trj[trj_len - 1] = [t_end, R_e, alfa_end, veloc, accel] # vel and acc for JA test
            #print("Enf of trajsectory, bmf")
            #print("1: {:.3f}, {:.3f}, {:.3f}".format(t1, h1, degrees(alfa1)))
            #print("0: {:.3f}, {:.3f}, {:.3f}".format(t_end, 0, degrees(alfa_end)))
            #print("2: {:.3f}, {:.3f}, {:.3f}".format(t2, h2, degrees(alfa2)))
 
    if def_time :      
        i_time = time.time()
        impact_time = i_time - l_time
        print("Calculation elapsed time: d_t={:.3f}s impact time = {:.3f}s ".format(d_t, impact_time))
    
    range_tot = R_e * alfa_end
    #m_data["range"] = range_tot

    if ind_flight_dataprint :    
        angle_ter = 90
        if vh_t > 0 : angle_ter = degrees(atan(vv_t/vh_t))
        #v_ter = v_t
        
        #print("total range = {:.3f} km, max height = {:.1f} km, max h time = {:.2f} s, angle_ter = {:.1f} deg, v_ter = {:.3f} km/s".format(range_tot/1000, (rv_max-R_e)/1000, rv_max_time, angle_ter, v_ter/1000) )
        print("Apogee : height = {:7.2f} km, time = {:7.2f} s, range  = {:9.3f} km, h_speed = {:6.3f} km/s, v_speed = {:7.3f} km/s".format((rv_max-R_e)/1000, rv_max_time, (max_h_alfa * R_e)/1000, max_h_vh/1000, max_h_vv/1000))
        print("Impact : height = {:7.2f} km, time = {:7.2f} s, range  = {:9.3f} km, speed   = {:6.3f} km/s, angle   = {:7.3f} deg".format((rv_t - R_e)/1000,  t_end,       range_tot/1000, v_end/1000, angle_ter) )
        #print("qb_max = {:.2f} N, qt_max = {:.2f} N, qb_max_h = {:.1f} km, qt_max_h = {:.6f} km".format(qb_max, qt_max, qb_max_h/1000, qt_max_h/1000))
        #print("qb_max_time = {:.1f} s, qt_max_time = {:.1f} s, total time = {:.2f} s".format(qb_max_time, qt_max_time, t_end)) # t_t))
        print("Boost  : qb_max = {:7.3f} kN,  qb_max_h = {:7.2f} km, qb_max_time = {:6.2f} s".format(qb_max/1000, qb_max_h/1000, qb_max_time))
        print("Reentry: qt_max = {:7.3f} kN,  qt_max_h = {:7.2f} km, qt_max_time = {:6.2f} s".format(qt_max/1000, qt_max_h/1000, qt_max_time)) # t_t))

        print("V max  : v_max  = {:7.3f} km/s,  height = {:7.2f} km,  v_max_time = {:6.2f} s".format(v_max/1000, v_max_h/1000, v_max_time))
        #print("max_h time = {:.3f} s, max_h range = {:.3f} km, max_h hrz speed = {:.3f} km/s, max_h vrt speed = {:.3f} km/s".format(rv_max_time, (max_h_alfa * R_e)/1000, max_h_vh/1000, max_h_vv/1000))
        print("Atm exit speed  = {:7.3f} km/s, Re-entry speed = {:7.3f} km/s, Re-entry mass = {:7.2f} kg".format(atm_exit_speed/1000, re_entry_speed/1000, m_m))

    if trajectory_data :
        if check_fpa and (traj_type != 'bal_mis') :
            return(fpa_trj)
        else :
            return(bmf_trj)
    else:
        if orbital : print("here")
        if time_too_long : print("here2")
        return(range_tot)

def balmis_angle_opt(missile_data, gtangle_beg=1, gtangle_end=60, maxrange_acc=0.3):
    """
    Range optimisation over gravity turn angle with vertical launch height fixed (in missile_data).

    Parameters
    ----------
    missile_data :
        missile data as in "rocket_data" module
    gtangle_beg : optional
        begin of gravity turn angle range, >>>deg<<< The default is 1.
    gtangle_end : optional
        end of gravity turn angle range, >>>deg<<<. The default is 60.

    Returns
    -------
        gt_angle, m_range -- optimal angle (for vertical launch height from missile_data) and max range

    """
    
    cycle_list=["    |", "    /", "    -", "    \\"]
    i=0

    ksi = (3-sqrt(5))/2 # ~=0.38 golden section coeff

    if (missile_data['traj_type'] == 'bal_mis') :
        angle_key = 'grav_turn_angle'
    elif (missile_data['traj_type'] == 'albm') : # not used
        angle_key = 'grav_turn_angle'
    else : # 'int_endo' or 'int_exo'
        angle_key = 'flight_path_angle'
        #print("\nCalculating max range for: type = {}, trajectory type = {}".format(missile_data["type"], missile_data["traj_type"]))
        #print("ver_launch_height={} km fp_angle_beg={} fp_angle_end={} maxrange_acc={}".format(missile_data['vert_launch_height']/1000, gtangle_beg, gtangle_end, maxrange_acc))

    stao = time.process_time()

    x1 = gtangle_beg
    missile_data[angle_key] = x1
    i += 1
    i %= 4
    print(cycle_list[i], end='')
    y1 = balmisflight(missile_data, False) # False means return range, rather than trajectory
   
    x4 = gtangle_end
    missile_data[angle_key] = x4
    i += 1
    i %= 4
    print('\r' + cycle_list[i], end='')
    y4 = balmisflight(missile_data, False)
        
    x2 = x1 + ksi * (x4 - x1)
    x3 = x4 - ksi * (x4 - x1)
    
    missile_data[angle_key] = x2
    i += 1
    i %= 4
    print('\r' + cycle_list[i], end='')
    y2 = balmisflight(missile_data, False)
    
    missile_data[angle_key] = x3
    i += 1
    i %= 4
    print('\r' + cycle_list[i], end='')
    y3 = balmisflight(missile_data, False)
    
    y_max = max(y1, y2, y3, y4)
    if y_max == 0 :
        return 0, 0
        
    #while x4 - x1 > angle_acc : 
    y_min = min(y1, y2, y3, y4)                         # testing 230113
    while ((y_max - y_min) / y_max) > maxrange_acc :    # testing 230113
    
        enao = time.process_time()
        duao = enao - stao
        if duao >= out_time_freq :
            i += 1
            i %= 4
            print('\r' + cycle_list[i], end='')
            stao = enao

        if y_max == y1 or y_max == y2 :
            x4 = x3
            y4 = y3
            x3 = x1 + x4 - x2
            missile_data[angle_key] = x3
            #i += 1
            #i %= 4
            #print('\r' + cycle_list[i], end='')
            y3 = balmisflight(missile_data, False)
        else:
            x1 = x2
            y1 = y2
            x2 = x1 + x4 - x3
            missile_data[angle_key] = x2
            #i += 1
            #i %= 4
            #print('\r' + cycle_list[i], end='')
            y2 = balmisflight(missile_data, False)
            """ below looks like an error since x3 did not change """
            #i += 1 
            #i %= 4
            #print('\r' + cycle_list[i], end='')
            #y3 = balmisflight(missile_data, False)
        if x3 < x2 :
            x2, x3 = x3, x2
            y2, y3 = y3, y2

        #print("x1={:.1f}, x2={:.1f}, x3={:.1f}, x4={:.1f}".format(x1,x2,x3,x4))
        #print("y1={:.1f}, y2={:.1f}, y3={:.1f}, y4={:.1f}".format(y1/1000,y2/1000,y3/1000,y4/1000))
        y_max = max(y1, y2, y3, y4)
        if y_max == 0 :
            return 0, 0
        y_min = min(y1, y2, y3, y4)                    # testing 230113
        
        if y_max >= 2 * pi * R_e - 1 :
            break
       
            
    if y_max == y2 :
        gt_angle = x2
        m_range = y2
        end = 2
    elif y_max == y3 :
        gt_angle = x3
        m_range = y3
        end = 3
    elif y_max == y1 :
        gt_angle = x1
        m_range = y1
        end = 1
    else :
        gt_angle = x4
        m_range = y4
        end = 4

    #print( "\rAngle opt end={} angle={:5.2f} height={:5.2f} range={:9.3f}".format(end, gt_angle, missile_data["vert_launch_height"]/1000, m_range/1000 ))
    if angle_key == 'grav_turn_angle' :
        print( "\rMax range = {:9.3f} km at gt_angle = {:8.5f} degr (from vertical) for vert_launch_height = {:6.3f} km".format(m_range/1000, gt_angle, missile_data["vert_launch_height"]/1000 ))
    else :
        print( "\rMax range = {:9.3f} km at fp_angle = {:8.5f} degr (from horizontal) for vert_launch_height = {:6.3f} km".format(m_range/1000, gt_angle, missile_data["vert_launch_height"]/1000 ))

    return m_range, gt_angle

def balmis_maxrange(missile_data, gtheight_beg=100, gtheight_end=12000, gtangle_beg=1, gtangle_end=60, maxrange_acc=0.5):
    """
    Finds ballistic missile's max range for vertical launch height and grav turn angle in given ranges   

    Parameters
    ----------
    missile_data : 
        missile data as in "rocket_data" module
    gtheight_beg : optional
        begin of vert launch height range, m. The default is 100.
    gtheight_end : optional
        end of vert launch height range, m. The default is 12000.
    gtangle_beg :
        begin of gravity turn angle range, >>>deg<<< The default 1.
    gtangle_end :
        end of gravity turn angle range, >>>deg<<<. The default 60.

    Returns
    -------
    None.

    """
    #maxrange_st = time.time()    
    
    ksi = (3-sqrt(5))/2 # golden section coeff
    
    print("\nCalculating max range for: type = {}, trajectory type = {}".format(missile_data["type"], missile_data["traj_type"]))
    if (missile_data["traj_type"]  == "bal_mis") or (missile_data["traj_type"]  == "albm") :
        print("gtheight_beg={}km\tgtheight_end={}km\tgtangle_beg={}\tgtangle_end={}\tmaxrange_acc={}".format(gtheight_beg/1000, gtheight_end/1000, gtangle_beg, gtangle_end, maxrange_acc))
    else : # interceptor
        print("rotheight_beg={}km\trotheight_end={}km\tfpangle_beg={}\tfpangle_end={}\tmaxrange_acc={}".format(gtheight_beg/1000, gtheight_end/1000, gtangle_beg, gtangle_end, maxrange_acc))
    
    if gtheight_beg == gtheight_end :
        gt_height = gtheight_beg
        missile_data["vert_launch_height"] = gt_height
        m_range, gt_angle = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
        end = 0
    
    else :
        h_x1 = gtheight_beg
        missile_data["vert_launch_height"] = h_x1
        h_y1, h_a1 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
        end = 0
    
        
        h_x4 = gtheight_end
        missile_data["vert_launch_height"] = h_x4
        h_y4, h_a4 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
        end = 0
    
            
        h_x2 = h_x1 + ksi * (h_x4 - h_x1)
        h_x3 = h_x4 - ksi * (h_x4 - h_x1)
        
        missile_data["vert_launch_height"] = h_x2
        h_y2, h_a2 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)

        
        missile_data["vert_launch_height"] = h_x3
        h_y3, h_a3 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
        
        h_y_max = max(h_y1, h_y2, h_y3, h_y4)
        #while h_x4 - h_x1 >                                                                         : 
        h_y_min = min(h_y1, h_y2, h_y3, h_y4)               # testing 230113
        if h_y_max == 0 :
            h_y_max = 1
            h_y_min = 1
        #print("h_y_max={}".format(h_y_max))
        while ((h_y_max - h_y_min) / h_y_max) > maxrange_acc : # testing 230113
            
            if h_y_max == h_y1 or h_y_max == h_y2 :
                h_x4 = h_x3
                h_y4 = h_y3
                h_a4 = h_a3
                h_x3 = h_x1 + h_x4 - h_x2
                missile_data["vert_launch_height"] = h_x3
                h_y3, h_a3 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
            else:
                h_x1 = h_x2
                h_y1 = h_y2
                h_a1 = h_a2
                h_x2 = h_x1 + h_x4 - h_x3
                missile_data["vert_launch_height"] = h_x2
                h_y2, h_a2 = balmis_angle_opt(missile_data, gtangle_beg, gtangle_end, maxrange_acc)
            if h_x3 < h_x2 :
                h_x2, h_x3 = h_x3, h_x2
                h_y2, h_y3 = h_y3, h_y2
                h_a2, h_a3 = h_a3, h_a2
         
            #print("h_x1={:.1f}, h_x2={:.1f}, h_x3={:.1f}, h_x4={:.1f}".format(h_x1,h_x2,h_x3,h_x4))
            #print("h_y1={:.1f}, h_y2={:.1f}, h_y3={:.1f}, h_y4={:.1f}".format(h_y1/1000,h_y2/1000,h_y3/1000,h_y4/1000))
            h_y_max = max(h_y1, h_y2, h_y3, h_y4)
            h_y_min = min(h_y1, h_y2, h_y3, h_y4)           # testing 230113
            if h_y_max == 0 :
                h_y_max = 1
                h_y_min = 1
                
            #h_x_max = max(h_x1, h_x2, h_x3, h_x4)
            #h_x_min = min(h_x1, h_x2, h_x3, h_x4)
            if abs((h_x4 - h_x1) / h_x4) < maxrange_acc :
                break
            if abs(h_x4 - h_x1) < 10 :
                break
                
        if h_y_max == h_y2 :
            gt_height = h_x2
            m_range = h_y2
            gt_angle = h_a2
            end = 2
        elif h_y_max == h_y3 :
            gt_height = h_x3
            m_range = h_y3
            gt_angle = h_a3
            end = 3
        elif h_y_max == h_y1 :
            gt_height = h_x1
            m_range = h_y1
            gt_angle = h_a1
            end = 1
        else :
            gt_height = h_x4
            m_range = h_y4
            gt_angle = h_a4
            end = 4
    
    print( "Height opt end={} angle={:.5f} height={:.4f}km range={:.3f}km".format( end, gt_angle, gt_height/1000, m_range/1000 ))
    #print(h_x1, h_x2, h_x3, h_x4, (h_x4 - h_x1) / h_x4)
    #maxrange_et = time.time()
    #maxrange_elapsed_time = maxrange_et - maxrange_st
    #print("Max range calculation time = {:.3f}s".format(maxrange_elapsed_time))
    return m_range, gt_height, gt_angle

def balmis_range_vs_gth_list(missile_data, gtheight_beg=100, gtheight_end=12100, num_i=24):
    """
    Calculate max range for a set of vertical launch heights, optimizing gravity turn angle for each one.

    Parameters
    ----------
    missile_data : TYPE
        DESCRIPTION.
    gtheight_beg : TYPE
        beginning value for the range of grav turn heights
    gtheight_end : TYPE
        ending value for the range of grav turn heights
    num_i : TYPE
        number of values in the range (num_i+1 actually)

    Returns
    -------
    prints the list during calcuclation

    """
    d_h = (gtheight_end - gtheight_beg)/ num_i
    i = 0
    print("Calculating missile max range vs gravity turn height")
    while i <= num_i :
        missile_data["vert_launch_height"] = gtheight_beg + i * d_h
        range_i = balmis_angle_opt(missile_data)[0]
#        print("range_i={:.3f}".format(range_i/1000))
#        print( "Angle opt end={} angle={:.2f} height={:.2f} range={:.3f}".format(end, missile_data["grav_turn_angle"], missile_data["vert_launch_height"]/1000, missile_data["range"]/1000 ))
        i += 1
    print("End list")    


def trj_from_target(traj_0, r_tar, t_shift0) :  # needs correction: beta should not be >90 deg or < -90 deg
    """
    >>> not used by other functions, superseeded by trj_shift_turn (with different t_shift definition) <<<
    Trajectory with impact point at t_shift distance from target point,
    Output coords: distance from target and elevation angle from target over/below target horizon
    r_tar : float
        target point's R from Earth center
    t_shift : float
        shift of missile launch point along target-MLP line, zero when impact is at target point
    """
    traj_1 = np.empty_like(traj_0) # incoming missile traj from target as zero
    d_gamma = t_shift0 / r_tar
    f_gamma = traj_0[len(traj_0) - 1, 2] + d_gamma # polar angle distance between ILP and MLP
    for i in range(len(traj_0)) : # time, angle beta, radius (dist from taget)
        i_0 = traj_0[i,0]
        i_1 = sqrt(r_tar*r_tar + traj_0[i,1]*traj_0[i,1] - 2 * r_tar * traj_0[i, 1] * cos(f_gamma - traj_0[i, 2]))
        if abs(f_gamma - traj_0[i, 2]) < eps*eps :
            i_2 = pi / 2
            if traj_0[i, 1] < r_tar : i_2 = -i_2
        else: i_2 = atan((traj_0[i, 1] * cos(f_gamma - traj_0[i, 2]) - r_tar) / traj_0[i, 1] / sin(f_gamma - traj_0[i, 2]))
        if traj_0[i,2] > f_gamma : i_2 = pi + i_2
        traj_1[i] = [i_0, i_1, i_2] # was degrees(i_2) --?
    return(traj_1)

#@profile
def trj_shift_turn(traj_0, r_tar, t_shift, t_angle) :
    """
    Trajectory with missile launch point at t_shift distance [from ILP] along the launch points line
    and trajectory plane turned around the (Earth center - missile launch point) line by t_angle
    Output coords: distance from ILP and elevation angle from ILP over/below ILP horizon

    Parameters
    ----------
    traj_0 : 
        original trajectory in polar coords from Earth center: time, radius, angle (in rad)
    r_tar : float
        target point's R from Earth center (normally = R_e)
    t_shift : float
        shift of missile launch point along ILP-MLP line == distance ILP-MLP
    t_angle : float, radians
        angle between trajectory plane and ILP-EarthCenter-MLP plane

    Returns
    -------
    traj_shtu - trajectory in polar coords centered at interceptor launch point (time, R, alfa_r, r, beta_r, x, z)

    """
    #traj_shtu = np.empty_like(traj_0)
    traj_shtu = np.empty([len(traj_0), 7])
    f_gamma = t_shift / r_tar # polar anglle ILP and MLP
    """
    if t_angle == 0 :
        for i in range(len(traj_0)) :
            i_1 = sqrt(r_tar*r_tar + traj_0[i, 1]*traj_0[i, 1] - 2 * r_tar * traj_0[i, 1] * cos(f_gamma - traj_0[i, 2]))
            i_2 = asin((traj_0[i, 1] * cos(f_gamma - traj_0[i, 2]) - r_tar) / i_1)
    else: 
    """
    for i in range(len(traj_0)) :
        #i_0 = traj_0[i, 0]
        t0i1 = traj_0[i, 1]
        #if t0i1 < r_tar : t0i1 = r_tar
        t0i2 = traj_0[i, 2]
        sinta2_2 = sin(t_angle/2)**2
        i_1sq = r_tar*r_tar + t0i1*t0i1 - 2 * r_tar * t0i1 * cos(f_gamma - t0i2)
        #i_1sq = r_tar*r_tar + traj_0[i, 1]*traj_0[i, 1] - 2 * r_tar * traj_0[i, 1] * cos(f_gamma - traj_0[i, 2])  #v0      
        if t_angle > eps :
            i_1sq += 4 * r_tar * t0i1 * sin(f_gamma) * sin(t0i2) * sinta2_2
            #i_1sq += 4 * r_tar * traj_0[i, 1] * sin(f_gamma) * sin(traj_0[i, 2]) * sin(t_angle/2)*sin(t_angle/2)  #v0
        i_1 = sqrt(i_1sq) # r

        if (sin(t_angle) < eps*eps) and (abs(f_gamma - t0i2) < eps) :
        #if (t_angle < eps*eps) and (abs(f_gamma - t0i2) < eps*eps) :
            if i > 0 :
                i_2 = traj_shtu[i - 1, 4]
            else :
                print("impossible missile launch place")
                i_2 = pi / 2
            if traj_0[i, 1] < r_tar : i_2 = -i_2 # when "impact" point is below ILP # not happening now that impact is at zero
        else:
            #cos_delta = (r_tar*r_tar + traj_0[i, 1]*traj_0[i, 1] - i_1sq)/ 2 / r_tar / traj_0[i, 1] # old, same as new, but can be >1
            cos_delta = cos(f_gamma - t0i2) - 2 * sin(f_gamma) * sin(t0i2) * sinta2_2 
            #cos_delta = cos(f_gamma - traj_0[i, 2] - 2 * sin(f_gamma) * sin(traj_0[i, 2]) * sin(t_angle/2)*sin(t_angle/2)) #v0
            #i_2 = asin((traj_0[i, 1] * cos_delta - r_tar)/ i_1)
            if abs((t0i1 * cos_delta - r_tar)/ i_1) > 1 :
                print("i = {}, t = {:.1f}, t0i1=R = {:.3f}, cos_delta = {}, i_1=r = {:.3f}, (t0i1 * cos_delta - r_tar)/ i_1) = {}".format(i, traj_0[i, 0], t0i1, cos_delta, i_1, (t0i1 * cos_delta - r_tar)/ i_1))
                print("sin(t_angle) = {}, f_gamma - t0i2 = {}, t0i2 = {} degr".format(sin(t_angle), f_gamma - t0i2, degrees(t0i2)))
            i_2 = asin((t0i1 * cos_delta - r_tar)/ i_1) # beta
        
        traj_shtu[i] = [traj_0[i, 0], traj_0[i, 1], traj_0[i, 2], i_1, i_2, i_1 * cos(i_2), i_1 * sin(i_2)] # was degrees(i_2) --?
    return(traj_shtu)

#@profile
def trj_from_center(t_traj, r_tar, t_fi, t_dist) :
    """
    Trajectory with missile impact point at t_dist distance from interceptor launch point
    at t_angle from direction to missile launch point
    
    Parameters
    ----------
    t_traj : 
        original trajectory in polar coords from Earth center: time, radius, angle
    r_tar : float
        target point's R from Earth center
    t_fi : float, radians
        angle fi between directions to target point and missile launch point (from 
        interceptor launch point)
    t_dist : float
        distance from interceptor launch point to target point

    Returns
    -------
    traj_fidi - trajectory (r, beta) in polar coords centered at interceptor launch point:
        time, R, alfa_r, r, beta_r, x, z
        R and alfa_r - original trajectory

    """
    debug_print = False
    
    traj_fidi = np.empty_like(t_traj)
    f_alfa  = t_traj[len(t_traj) - 1, 2]
    f_range = r_tar * f_alfa
   
    """
    1) Convert ILP-centered dist and angle fi (input) to MLP shift and trajectory plane turn angle omega
       t_fi, t_dist => f_shift, f_omega
       -- to be used with function trj_shift_turn()
    """
 
    """what would it be on a plane: total shift and angle
    
    plane_f_shift = t_dist * cos(t_fi) + sqrt(f_range*f_range - t_dist*t_dist * sin(t_fi) ** 2)
    plane_f_angle = asin(t_dist * sin(t_fi) / f_range)
    
    shift and angle in polar coords"""
    
    if debug_print :
        print("\nrange={:.0f} km, MLP-ILP-MIP fi={:.2f} deg, ILP to MIP={:.3f} km".format(f_range/1000, degrees(t_fi), t_dist/1000))

    if t_dist == 0 :
        f_omega = 0
        f_shift = f_range
    elif t_fi == 0 :
        f_omega = 0
        f_shift = f_range + t_dist
    elif abs(t_fi - pi) < eps :
        f_omega = 0
        f_shift = f_range - t_dist
    elif abs(t_fi) < eps :
        f_omega = 0
        f_shift = f_range + t_dist
    else :
        f_delta = t_dist / r_tar
    
        """ old version, obsolete
        def fi_func(fi, al, ga, de) :
            f_func  = (sin(de/2)**2 - sin(ga/2)**2) * sin((al + ga - de)/2)
            f_func += sin(al + ga) * sin((de - ga)/2)**2
            f_func /= sin(al + ga) * sin(de)**2
            f_func -= sin(fi/2)**2
            return(-f_func)

        x_a = -f_delta
        x_b =  f_delta
        y_a =  fi_func(t_fi, f_alfa, x_a, f_delta)
        #y_b = fi_func(t_fi, f_alfa, x_b, f_delta)
    
        while True :
            
            #x_x = x_a + (x_b - x_a) * f_ksi
            x_x = x_a + (x_b - x_a) / 2
            y_x = fi_func(t_fi, f_alfa, x_x, f_delta)
    
            if abs(y_x) < eps: break
    
            if y_a * y_x < 0 :
                x_b = x_x
            else:
                x_a = x_x
                y_a = y_x
            
        f_gamma = x_x                   # "small" gamma
        f_shift = x_x * r_tar + f_range # ILP-MLP distance (="big" gamma * r_tar)
        
        f_omega  = sin(f_delta/2)**2 - sin(f_gamma/2)**2
        f_omega /= sin(f_alfa) * sin(f_alfa + f_gamma)
        f_omega  = asin(sqrt(f_omega)) * 2
        obsolete version end """
        
        f_a = cos(f_alfa)
        f_b = cos(f_delta)
        f_c = sin(f_delta) * cos(t_fi)
        if (f_c > 0) or (f_b > 0) :
            cos_gme = f_a / sqrt(f_b*f_b + f_c*f_c)
            if abs(cos_gme) > 1 :
                if debug_print : print("Impossible launch point 1")
                return False
            else :
                f_gamma = acos(cos_gme) + atan(f_c / f_b)
                #if (f_alfa + f_delta) > pi :
                #   f_gamma = 2 * pi - f_gamma
                #f_gamma = acos(f_a / sqrt(f_b*f_b + f_c*f_c)) + atan(f_c / f_b)
        elif (f_c < 0) and (f_b < 0) :
            cos_gme = f_a / sqrt(f_b*f_b + f_c*f_c)
            if abs(cos_gme) > 1 :
                if debug_print : print("Impossible launch point 2")
                return False
            else :
                #f_gamma = pi - acos(cos_gme) + atan(f_c / f_b)
                f_gamma = acos(cos_gme) + atan(f_c / f_b) - pi
        elif f_b == 0 :
             f_gamma = asin(f_a / cos(t_fi)) # cos(t_fi) != 0, otherwise f_alfa = pi/2 = f_delta - impossible b/c by choice f_delta<f_alfe
             #f_omega = acos(-cos(t_fi) * cos(f_gamma) / sin(f_alfa)) # a very unlikely possibility, no sense to write special formula
        elif f_c == 0 :
            f_gamma = acos( f_a / f_b) # f_b != 0, otherwise f_alfa = pi/2 = f_delta - impossible b/c by choice f_delta<f_alfe
        else :
            print("Impossible exception in trj_from_center")
        
        cos_omega = (f_b - cos(f_gamma) * f_a) / sin(f_alfa) / sin(f_gamma)

        if abs(cos_omega) > 1 :
            if debug_print : print("Impossible launch point 3")
            return False
        
        if (cos_omega < 0) :
            if debug_print : print("Omega < 0")
            return False         

        f_omega = acos(cos_omega)
        f_shift = f_gamma * r_tar
        #print("omega0={:.6f} omega1={:.6f} gamma0={:.6f} gamma1={:.6f}, fi={:.2f} deg, di={:.0f} km".format(f_omega, f1_omega, f_shift/r_tar, f1_gamma, degrees(t_fi), t_dist/1000))

    #print("range={:.3f} km fi={:.0f} deg dist={:.3f} km".format(f_range/1000, degrees(t_fi), t_dist/1000))
    #print("on plane:  shift={:.3f} km omega={:.3f} deg".format(f_shift_plane/1000, degrees(f_angle_plane)))

    if debug_print : 
        print("on sphere: ILP to MLP={:.3f} km, ILP-MLP-MIP omega={:.6f} deg".format(f_shift/1000, degrees(f_omega)))
        if sin(t_fi) > eps :
            print("gamma={:.3f} deg, gamma_shift={:.3f} km".format(degrees(f_shift/r_tar), f_shift/1000))
    
    """
    2) Trajectory conversion using calculated values of f_shift and f_omega
    """
    
    if f_shift > dist_limit :
        return False
    
    #traj_fidi0 = trj_shift_turn(t_traj, r_tar, f_shift, f_omega)
    if f_shift <= 0 : 
        print("f_shift negative: {:.2f}".format(f_shift/1000))
        return False
    if f_omega >= (pi/2) : 
        print("f_omega > 90 deg: {:.2f}".format(degrees(f_omega)))
        return False
    
    traj_fidi = trj_shift_turn(t_traj, r_tar, f_shift, f_omega)
    
    # TODO $$$ rewrite without append
    """ version with append
    traj_fidi = np.empty([0, 7])
    for f_trdata0 in traj_fidi0 :
        # time, orig r, orig angle, new r, new angle, new x, new y
        f_trdata = [f_trdata0[0], 0, 0, f_trdata0[1], f_trdata0[2], f_trdata0[1]*cos(f_trdata0[2]), f_trdata0[1]*sin(f_trdata0[2])]
        traj_fidi = np.append(traj_fidi, [f_trdata], axis=0)
    end of version with append, version w/o append below """

    """ the following version without append is not needed with modified trj_shift_turn
    len_tfd0 = len(traj_fidi0)
    traj_fidi = np.empty([len_tfd0, 7])
    for i_tf in range(len_tfd0) :
        traj_fidi[i_tf, 5] = traj_fidi0[i_tf, 1] * cos(traj_fidi0[i_tf, 2])
        traj_fidi[i_tf, 6] = traj_fidi0[i_tf, 1] * sin(traj_fidi0[i_tf, 2])

    traj_fidi[:,0] = traj_fidi0[:,0]
    traj_fidi[:,3] = traj_fidi0[:,1]
    traj_fidi[:,4] = traj_fidi0[:,2]
       
    traj_fidi[:,1] = t_traj[:,1]
    traj_fidi[:,2] = t_traj[:,2]
    """
    
    return(traj_fidi)

#@profile
def interceptor_table(interc_data, ind_flight_dataprint=False, psi_step=0.25, arr_obj=True) :
    """>>>>> single processor version <<<<<"""
    """
    Generates array of interceptor trajectories for different psi (90 minus flight path angle) -- if arr_obj==True
    otherwise trajectories are padded with -1 up to max trajectory length, and a 3D array is generated.
    Trajectory for each psi: time, r, beta, x, y

    Parameters
    ----------
    interc_data :
        rocket parameters
    ind_flight_dataprint : Boolean
        print individual flight data
    psi_step : 
        psi value change step
    arr_obj : which array to generate, case of False needs re-writing

    Returns
    -------
    

    """
    #psi_step = 5 # psi step
    psi_n = int(90 / psi_step)
    int_table_0 = np.empty(psi_n, dtype=object)
    #int_traj = np.empty([0, 3])
    t_lengths = []
    print("\nInterceptor trajectory set calculation started, psi goes from [0 up to 90)")
    print("This is going to take some time, you may want to get a cup of tea/coffee...")
    #if gui : print("Calculating trajectory psi", end='')
    if interc_data["traj_type"] == "int_exo" :
        #interc_data["vert_launch_height"] = int_vl_height
        pass
    elif interc_data["traj_type"] == "int_endo" :
        interc_data["vert_launch_height"] = 0
    else :
        print("Unknown interceptor trajectory type")
        
    for i_i in range(psi_n) :
        i_psi = i_i * psi_step
        #if gui :
        #    print("={:.2f}".format(i_psi), end='')
        #else :
        #if i_i % 3 == 0 :
        print("\rCalculating trajectory psi={:.2f}".format(i_psi), end='')
        interc_data["flight_path_angle"] = 90 - i_psi
        int_traj = balmisflight(interc_data, True, ind_flight_dataprint)
        
        int_traj6 = np.empty([0,6]) # psi, time, r, beta, x, y
        t_lengths.append(len(int_traj))

        if i_i == 0 :
            for i_j in range(t_lengths[0]) :
                int_traj6 = np.append(int_traj6, [[0, int_traj[i_j, 0], int_traj[i_j, 1] - R_e, pi/2 , 0, int_traj[i_j, 1] - R_e]], axis=0)
        else : 
            i_rad = int_traj[0, 1] - R_e
            if interc_data["traj_type"] == "int_exo" :
                i_ang = pi/2
            else :
                i_ang = radians(90 - i_psi)
            # i_j = 0 processed separately
            int_traj6 = np.append(int_traj6, [[i_psi, int_traj[0, 0], i_rad, i_ang, 0, i_rad]], axis=0)
            
            for i_j in range(1, t_lengths[i_i]) :
                z_rad = int_traj[i_j, 1]
                z_ang = int_traj[i_j, 2]
#                i_rad = sqrt(R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang))
                i_rad2 = R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang)
                i_rad = sqrt(i_rad2)
                
                """ v. 221030 20:55 """
                #z_1 = cos(z_ang)           # used for debug
                #z_2 = z_rad * z_1 - R_e
                
                if abs(z_ang) < angle_eps :
                    if interc_data["traj_type"] == "int_exo" :
                        i_ang = pi/2
                    else :
                        i_ang = radians(90 - i_psi)
                else :
                    i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
                    if z_ang > pi :
                        if z_ang < 2 * pi :
                            i_ang = - pi - i_ang
                        elif z_ang < 3 * pi :
                            i_ang = - 2 * pi + i_ang
                        else :
                            print("Too long interceptor range, > 60,000 km, alfa={:.1f}".format(degrees(z_ang)))
   
                """ up to 221030 20:53
                if i_rad < range_eps:
                    if interc_data["vert_launch_height"] > 0 :
                        i_ang = pi/2
                    else :
                        i_ang = radians(90 - i_psi)
                else :
                    if z_ang < eps :
                        #if i_i > 0 : print("psi = {:d} time = {:.1f} z_ang = {:.8f} eps = {:.8f}".format(i_psi, i_j*d_t, z_ang, eps))
                        if (interc_data["vert_launch_height"] > 0) and (i_rad <= interc_data["vert_launch_height"]) :
                            i_ang = pi/2
                        else :
                            #i_ang = radians(90 - i_psi)
                            #xtest = z_rad * cos(z_ang) - R_e
                            #ytest = xtest / i_rad
                            sin_beta2 = (z_rad * cos(z_ang) - R_e) ** 2 / i_rad2
#                            if sin_beta2 >= 1 :
#                                i_ang = pi/2
#                            else :
#                                i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
                            i_ang = asin(sqrt(sin_beta2))
                    else :
                        i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
                    """
    
                int_traj6 = np.append(int_traj6, [[i_psi, int_traj[i_j, 0], i_rad, i_ang, i_rad * cos(i_ang), i_rad*sin(i_ang)]], axis=0)
                
        int_table_0[i_i] = int_traj6

    print("\nInterceptor trajectory set calculation complete.")
    if arr_obj :
        return(int_table_0)
    else: # needs re-writing ?
        max_t_length = max(t_lengths)
        int_table_1 = np.empty([0, max_t_length, 6])
        for i_trj in int_table_0 :
            while len(i_trj) < max_t_length :
              i_trj = np.append(i_trj, [[-1, -1, -1, -1, -1, -1]], axis=0)
            int_table_1 = np.append(int_table_1, [i_trj], axis=0)
        return(int_table_1)

""" End of interceptor_table """

def line(p1, p2): # two points => a*x + b*y = c
    a = (p2[1] - p1[1])
    b = (p1[0] - p2[0])
    c = (p1[0]*p2[1] - p2[0]*p1[1])
    return a, b, c

def line_intersection(L1, L2):
    D  = L1[0] * L2[1] - L1[1] * L2[0]
    Dx = L1[2] * L2[1] - L1[1] * L2[2]
    Dy = L1[0] * L2[2] - L1[2] * L2[0]
    if D != 0:
        x = Dx / D
        y = Dy / D
        return x, y
    else:
        if Dx == 0 :
            return 0, 0 # (0, 0) lines coincide => furthest missile traj point is common point
        return False
    
def segment_intersection(ip1, ip2, mp1, mp2):
    Li = line(ip1, ip2)
    Lm = line(mp1, mp2)
    dot_im = line_intersection(Li, Lm)
    if dot_im :
        x, y = dot_im
        if x == y == 0 :
            return dot_im # or m1? <<<<<<<<<<
        else :
            if1 = ((ip1[0] - x) * (ip2[0] - x) <= 0)
            if2 = ((ip1[1] - y) * (ip2[1] - y) <= 0)
            if3 = ((mp1[0] - x) * (mp2[0] - x) <= 0)
            if4 = ((mp1[1] - y) * (mp2[1] - y) <= 0)
            if if1 and if2 and if3 and if4 :
                return dot_im
            else :
                return False
    else :
        return False


def long_search(trj, int_table, h_int_min, t_int_lnc, fi_opt, dist_opt, debug_hits=False) :
    """
    Finds intercept points, if found returns point coords (x,y), if not returns False.
    Iterates along missile trajectory backwards starting with the last trajectory point above h_int_min, until
    missile time flight = t_int_lnc

    Parameters
    ----------
    trj : TYPE
        missile trajectory table -- time, R, alfa
    int_table : TYPE
        interceptor trajectories, array for different psi (psi = 90 minus flight path angle)
        for each psi it's time, r, beta, x, y
    fi_opt : >>> in radians <<<
        direction to MIP point from direction to MLP
    dist_opt : TYPE
        distance to MIP from ILP
    h_int_min : TYPE
        minimum intercept hight (local height)
    t_int_lnc : TYPE
        min time from missile launch to interceptor launch
    debug_hits : TYPE, optional
        find "short hits", print all hit info

    Returns
    -------
    None.

    """
 
    ls_dist_max = trj[len(trj) - 1, 2] * R_e # dist must be less than missile range
    if dist_opt >= ls_dist_max :
        print("\n>>> long_search exception_2: dist = {:f} km >= missile range = {:f} km<<<".format(dist_opt/1000, ls_dist_max/1000))
        return False

    hit = False
    
    st = time.time()

    tar_trj = trj_from_center(trj, R_e, fi_opt, dist_opt)

    global dist_to_trj_min
    dist_to_trj_min = min(tar_trj[:, 5]) / 1000
    
    i_mis = len(tar_trj) - 1
    while tar_trj[i_mis, 1] - R_e < h_int_min : # from impact backwards find the first point above MIA (min intercept altitude)
        i_mis -= 1
        if i_mis == 0 :
            print("long_search exception i_mis == 0 (missile trajectory below min intercept altitude)")
            break

#    i_ksi = (3-sqrt(5))/2 # ~=0.38 golden section  
    i_count = 0 # number of hits found
    while tar_trj[i_mis, 0] > t_int_lnc : # steps along missile trajectory down to earliest interceptor launch time
        for i_psi in range(len(int_table)) :
            i_int = 0
            """
            while int_table[i_psi][i_int, 4] < tar_trj[i_mis, 5] : # find time when Xint is beyond Xmissile
                i_int += 1
                if i_int == len(int_table[i_psi]) : break
            """
            i_a = 0
            i_b = len(int_table[i_psi]) - 1
            if int_table[i_psi][i_b, 4] >= tar_trj[i_mis, 5] :
#                f_a = int_table[i_psi][i_a, 4] - tar_trj[i_mis, 5] 
                while (i_b - i_a) > 1 :
                    i_x  = i_a + int(ceil((i_b - i_a) / 2))
                    f_x  = int_table[i_psi][i_x, 4] - tar_trj[i_mis, 5]
#                    f_x0 = int_table[i_psi][i_x - 1, 4] - tar_trj[i_mis, 5]
#                    if (f_x > 0) and (f_x0 < 0) : break
    
#                    if f_a * f_x < 0 :
                    if f_x >= 0 :
                        i_b = i_x
                    else :
                        i_a = i_x
#                        f_a = f_x
                        
#                if f_a * (int_table[i_psi][i_b, 4] - tar_trj[i_mis, 5]) > 0 : print("\n\n>>>long_search exception_0<<<<")
                i_int = i_b
                
                if int_table[i_psi][i_int, 1] < (tar_trj[i_mis, 0] - t_int_lnc) :

                    if i_int < len(int_table[i_psi]) :
                        if int_table[i_psi][i_int, 4] == tar_trj[i_mis, 5] :
                            print("long_search exception_1 X int = X mis")
                            break
#                        elif int_table[i_psi][i_int + 1, 1] > 0 : # time != -1 => before end of interceptor traj
                        else: 
                            if i_int < (len(int_table[i_psi]) - 1) :
                                i2x = int_table[i_psi][i_int + 1, 4]
                                i2y = int_table[i_psi][i_int + 1, 5]
                                m2x = tar_trj[i_mis + 1, 5]
                                m2y = tar_trj[i_mis + 1, 6]
                            else :
                                i2x = int_table[i_psi][i_int, 4]
                                i2y = int_table[i_psi][i_int, 5]
                                m2x = tar_trj[i_mis, 5]
                                m2y = tar_trj[i_mis, 6]

                            i1x = int_table[i_psi][i_int - 1, 4]
                            i1y = int_table[i_psi][i_int - 1, 5]
                            m1x = tar_trj[i_mis - 1, 5]
                            m1y = tar_trj[i_mis - 1, 6]
                            if (max(i1y, i2y) > min(m1y, m2y)) and (max(m1y, m2y) > min(i1y, i2y)) :
                                hit = segment_intersection([i1x, i1y], [i2x, i2y], [m1x, m1y], [m2x, m2y])
                                if hit :
                                    if hit[0] == hit[1] == 0 :
                                        print(">>> coinciding!!! <<<")
                                        hit = [tar_trj[i_mis, 5], tar_trj[i_mis, 6]]
                                        t_hit_m = tar_trj[i_mis, 0]
                                        t_hit_i = int_table[i_psi][i_int, 1]
                                        r_hit = tar_trj[i_mis, 3]
                                        beta_hit = tar_trj[i_mis, 4]
                                        h_hit = tar_trj[i_mis, 1] - R_e
                                    else :
                                        t_hit_m = tar_trj[i_mis - 1, 0] + d_t * ((hit[0] - m1x) / (m2x - m1x))
                                        t_hit_i = int_table[i_psi][i_int - 1, 1] + d_t * ((hit[0] - i1x) / (i2x - i1x))
                                        r_hit = sqrt(hit[0]*hit[0] + hit[1]*hit[1])
                                        beta_hit = asin(hit[1] / r_hit)
                                        h_hit = sqrt((R_e + hit[1])*(R_e + hit[1]) + hit[0]*hit[0]) - R_e

                                    if t_hit_i < (t_hit_m - t_int_lnc) :
                                        if debug_hits :
                                            i_count += 1
                                            print("\nHit # {:d}".format(i_count))
                                            print("Missile flight time = {:.2f}".format(tar_trj[i_mis, 0]))
                                            print("psi = {:.1f}".format(int_table[i_psi][i_int, 0]))
                                            print("Hit coords: r = {:.3f} beta = {:.3f}, X = {:.3f}, Y = {:.3f}, local height = {:.3f}".format(r_hit/1000, degrees(beta_hit), hit[0]/1000, hit[1]/1000, h_hit/1000 ))
                                            print("missile time = {:.2f}".format(t_hit_m))
                                            print("missile dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(tar_trj[i_mis - 1, 0], tar_trj[i_mis - 1, 3]/1000, degrees(tar_trj[i_mis - 1, 4]), m1x/1000, m1y/1000 ))
                                            print("missile dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(tar_trj[i_mis + 1, 0], tar_trj[i_mis + 1, 3]/1000, degrees(tar_trj[i_mis + 1, 4]), m2x/1000, m2y/1000 ))
                                            print("intceptor time = {:.2f}".format(t_hit_i))
                                            print("intceptor dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(int_table[i_psi][i_int - 1, 1], int_table[i_psi][i_int - 1, 2]/1000, degrees(int_table[i_psi][i_int - 1, 3]), i1x/1000, i1y/1000 ))
                                            print("intceptor dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(int_table[i_psi][i_int + 1, 1], int_table[i_psi][i_int + 1, 2]/1000, degrees(int_table[i_psi][i_int + 1, 3]), i2x/1000, i2y/1000 ))
                                            """ extra check """
                                            if i_int == (len(int_table[i_psi]) - 1) :
                                                print("Type i0m0 hit, end of trajectory")
                                            else :
                                                e_hit = False
                                                """ checking type i0m0 """
                                                i2x = int_table[i_psi][i_int, 4]
                                                i2y = int_table[i_psi][i_int, 5]
                                                m2x = tar_trj[i_mis, 5]
                                                m2y = tar_trj[i_mis, 6]
                                                if (max(i1y, i2y) > min(m1y, m2y)) and (max(m1y, m2y) > min(i1y, i2y)) :
                                                    e_hit = segment_intersection([i1x, i1y], [i2x, i2y], [m1x, m1y], [m2x, m2y])
                                                    if e_hit :
                                                        ii0 = i_int - 1
                                                        ii1 = i_int
                                                        im0 = i_mis - 1
                                                        im1 = i_mis 
                                                        print("Type i0m0 hit")
    
                                                if not e_hit :
                                                    """ checking type i1m0 """
                                                    i1x, i1y =  i2x, i2y
                                                    i2x = int_table[i_psi][i_int + 1, 4]
                                                    i2y = int_table[i_psi][i_int + 1, 5]
                                                    if (max(i1y, i2y) > min(m1y, m2y)) and (max(m1y, m2y) > min(i1y, i2y)) :
                                                        e_hit = segment_intersection([i1x, i1y], [i2x, i2y], [m1x, m1y], [m2x, m2y])
                                                        if e_hit :
                                                            ii0 = i_int
                                                            ii1 = i_int + 1
                                                            im0 = i_mis - 1
                                                            im1 = i_mis 
                                                            print("Type i1m0 hit")
                                                    
                                                if not e_hit :
                                                    m1x, m1y = m2x, m2y
                                                    m2x = tar_trj[i_mis + 1, 5]
                                                    m2y = tar_trj[i_mis + 1, 6]
                                                    if (max(i1y, i2y) > min(m1y, m2y)) and (max(m1y, m2y) > min(i1y, i2y)) :
                                                        e_hit = segment_intersection([i1x, i1y], [i2x, i2y], [m1x, m1y], [m2x, m2y])
                                                        if e_hit :
                                                            ii0 = i_int
                                                            ii1 = i_int + 1
                                                            im0 = i_mis
                                                            im1 = i_mis + 1
                                                            print("Type i1m1 hit")
                                                            
                                                if not e_hit :
                                                    i2x, i2y = i1x, i1y
                                                    i1x = int_table[i_psi][i_int - 1, 4]
                                                    i1y = int_table[i_psi][i_int - 1, 5]                                                
                                                    if (max(i1y, i2y) > min(m1y, m2y)) and (max(m1y, m2y) > min(i1y, i2y)) :
                                                        e_hit = segment_intersection([i1x, i1y], [i2x, i2y], [m1x, m1y], [m2x, m2y])
                                                        if e_hit :
                                                            ii0 = i_int - 1
                                                            ii1 = i_int
                                                            im0 = i_mis
                                                            im1 = i_mis + 1
                                                            print("Type i0m1 hit")
    
                                                if not e_hit :
                                                            print("\nFound long hit, but no short hits\n")
                                            if e_hit :
                                                if e_hit[0] == e_hit[1] == 0 :
                                                    print(">>> e-coinciding!!! <<<")
                                                    e_hit = [tar_trj[im1, 5], tar_trj[im1, 6]]
                                                    t_hit_m = tar_trj[im1, 0]
                                                    t_hit_i = int_table[i_psi][ii1, 1]
                                                    r_hit = tar_trj[im1, 3]
                                                    beta_hit = tar_trj[im1, 4]
                                                    h_hit = tar_trj[im1, 1] - R_e
                                                else :
                                                    t_hit_m = tar_trj[im0, 0] + d_t * ((e_hit[0] - m1x) / (m2x - m1x))
                                                    t_hit_i = int_table[i_psi][ii0, 1] + d_t * ((e_hit[0] - i1x) / (i2x - i1x))
                                                    r_hit = sqrt(e_hit[0]*e_hit[0] + e_hit[1]*e_hit[1])
                                                    beta_hit = asin(e_hit[1] / r_hit)
                                                    h_hit = sqrt((R_e + e_hit[1])*(R_e + e_hit[1]) + e_hit[0]*e_hit[0]) - R_e
                                                if t_hit_i < (t_hit_m - t_int_lnc) :
                                                    print("e_Hit # {:d}".format(i_count))
                                                    print("Missile flight time = {:.2f}".format(tar_trj[im1, 0]))
                                                    print("psi = {:.1f}".format(int_table[i_psi][ii1, 0]))
                                                    print("Hit coords: r = {:.3f} beta = {:.3f}, X = {:.3f}, Y = {:.3f}, local height = {:.3f}".format(r_hit/1000, degrees(beta_hit), e_hit[0]/1000, e_hit[1]/1000, h_hit/1000 ))
                                                    print("missile time = {:.2f}".format(t_hit_m))
                                                    print("missile dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(tar_trj[im0, 0], tar_trj[im0, 3]/1000, degrees(tar_trj[im0, 4]), m1x/1000, m1y/1000 ))
                                                    print("missile dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(tar_trj[im1, 0], tar_trj[im1, 3]/1000, degrees(tar_trj[im1, 4]), m2x/1000, m2y/1000 ))
                                                    print("intceptor time = {:.2f}".format(t_hit_i))
                                                    print("intceptor dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(int_table[i_psi][ii0, 1], int_table[i_psi][ii0, 2]/1000, degrees(int_table[i_psi][ii0, 3]), i1x/1000, i1y/1000 ))
                                                    print("intceptor dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(int_table[i_psi][ii1, 1], int_table[i_psi][ii1, 2]/1000, degrees(int_table[i_psi][ii1, 3]), i2x/1000, i2y/1000 ))
                                            else :
                                                print ("No e_Hit found")
                                                print("missile dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(tar_trj[i_mis - 1, 0], tar_trj[i_mis - 1, 3]/1000, degrees(tar_trj[i_mis - 1, 4]), tar_trj[i_mis - 1, 5]/1000, tar_trj[i_mis - 1, 6]/1000 ))
                                                print("missile dot e: time = {:.2f}, re = {:.3f}, betae = {:.3f}, Xe = {:.3f}, Ye = {:.3f}".format(tar_trj[i_mis, 0],     tar_trj[i_mis, 3]/1000,     degrees(tar_trj[i_mis, 4]),     tar_trj[i_mis, 5]/1000,     tar_trj[i_mis, 6]/1000 ))
                                                print("missile dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(tar_trj[i_mis + 1, 0], tar_trj[i_mis + 1, 3]/1000, degrees(tar_trj[i_mis + 1, 4]), tar_trj[i_mis + 1, 5]/1000, tar_trj[i_mis + 1, 6]/1000 ))
                                                print("intceptor time = {:.2f}".format(t_hit_i))
                                                print("intceptor dot 1: time = {:.2f}, r1 = {:.3f}, beta1 = {:.3f}, X1 = {:.3f}, Y1 = {:.3f}".format(int_table[i_psi][i_int - 1, 1], int_table[i_psi][i_int - 1, 2]/1000, degrees(int_table[i_psi][i_int - 1, 3]), int_table[i_psi][i_int - 1, 4]/1000, int_table[i_psi][i_int - 1, 5]/1000 ))
                                                print("intceptor dot e: time = {:.2f}, re = {:.3f}, betae = {:.3f}, Xe = {:.3f}, Ye = {:.3f}".format(int_table[i_psi][i_int, 1],     int_table[i_psi][i_int, 2]/1000,     degrees(int_table[i_psi][i_int, 3]),     int_table[i_psi][i_int, 4]/1000,     int_table[i_psi][i_int, 5]/1000 ))
                                                print("intceptor dot 2: time = {:.2f}, r2 = {:.3f}, beta2 = {:.3f}, X2 = {:.3f}, Y2 = {:.3f}".format(int_table[i_psi][i_int + 1, 1], int_table[i_psi][i_int + 1, 2]/1000, degrees(int_table[i_psi][i_int + 1, 3]), int_table[i_psi][i_int + 1, 4]/1000, int_table[i_psi][i_int + 1, 5]/1000 ))
                                        else : pass
                                        break
                                    else : hit = False

        if hit : break        
        if debug_hits and (i_mis % 100 == 0) :
            print("\rCurrent missile flight time = {:.2f}".format(tar_trj[i_mis, 0]), end='')
        i_mis -= 1
    
    et = time.time()
    elapsed_time = et - st
    print("Full trajectory generation and search time = {:.3f}s, hit={}".format(elapsed_time, hit != False))
    if hit != False : print(hit)

    return hit
""" END of long_search() """

def footprint_calc(t_trj, t_itable, h_min, t_lnc, t_angle_step, t_acc=.01, t_dist=100000) :
    """
    The first version of footprint calc: 1) uses "long_search" interception algorithm and 2) only two
    limitations: min local height of interception h_min, and interceptor launch delaty counting
    from missile launch t_lnc. Other time limitations should be added to allow use of this function.
    NOTE: "long_search" is much slower but more accurate than "short_search" (see "short_search" module)

    Parameters
    ----------
    t_trj : array of trajectory points
        missile trajectory
    t_itable : array of interceptor trajectories
        interceptor table: a set of trajectories with different angles from vertical
    h_min : float
        min local height of intercept, m
    t_lnc : float
        interceptor launch delay counting from missile launch
    t_angle_step : TYPE
        step of angle from ILP-MLP to ILP-MIP
    t_acc : float
        footprint border location calculation accuracy (distance between last good impact point and first not good one
        divided by distance to the not good one). The default is .01.
    t_dist : float
        Initial distance from ILP, used for finding footprint border distance, m. The default is 100000.
        To speed up the calculation (a bit), it should be set closer to border inside the foor print. Not really important.

    Returns
    -------
    Footprint as an array of polar coordinates, or False if there is no footprint.
    
    """

    dist_max = t_trj[len(t_trj) - 1, 2] * R_e - 1
    #dist_max = 6200000
    if t_dist >= dist_max :
        t_dist = dist_max / 2
#        print("\n>>> footprint_calc exception: dist = {:.0f} km >= missile range = {:.0f} km<<<".format(t_dist/1000, dist_max/1000))
#        return False

    """ First, check if interceptor launch point is defended """
    ilp_ok = long_search(t_trj, t_itable, h_min, t_lnc, 0, 0)

    ftprint = np.empty([0, 3]) # anlge in deg and distance in meters

    if ilp_ok :

        f_dist = t_dist
        f_ang = 0
        while f_ang <= 180 :
#            do_search = False
            f_dist0 = 0
            f_ang_r = radians(f_ang)
            f_ok = long_search(t_trj, t_itable, h_min, t_lnc, f_ang_r, f_dist)
            while f_ok :                
                if f_dist >= dist_max :
                    f_a = 999999999
                    break
                f_dist0 = f_dist
                f_dist *= 2
                f_dist = min(f_dist, dist_max)
                f_ok = long_search(t_trj, t_itable, h_min, t_lnc, f_ang_r, f_dist)
            do_search = not f_ok
            f_a = f_dist0
            f_b = f_dist
            while do_search :
#                f_x = f_a + (f_b - f_a) * f_ksi
                f_x = f_a + (f_b - f_a) / 2
                f_xy = long_search(t_trj, t_itable, h_min, t_lnc, f_ang_r, f_x)
                if f_xy :
                    f_a = f_x
                else :
                    f_b = f_x
                if (f_b - f_a) < f_b * t_acc :
                    break

            ftprint = np.append(ftprint, [[f_ang, f_a, dist_to_trj_min, f_b - f_a]], axis=0)
            f_ang += t_angle_step

        return ftprint
            
    else:
        print("Interceptor undefendable")
        return False

""" END of foorptint_calc """


def angle_dist_tab(t_trj, t_itable, h_min, t_lnc, t_angle_step, t_dist=3000000) :

    dist_max = t_trj[len(t_trj) - 1, 2] * R_e - 1
    angl_dist = np.empty([0, 42])
    
    f_dist = t_dist
    while f_dist <= dist_max :
        f_ang = 158
        angl_dist0 = np.empty([0])
        while f_ang <= 163 :
            f_ang_r = radians(f_ang)
            ls = long_search(t_trj, t_itable, h_min, t_lnc, f_ang_r, f_dist)
            if not ls : ls = [-1, -1]
            x = f_dist * cos(f_ang_r)
            y = f_dist * sin(f_ang_r)            
            angl_dist0 = np.append(angl_dist0, [f_ang, f_dist/1000, dist_to_trj_min, x, y, ls[0], ls[1]])
            f_ang += t_angle_step
        f_dist += 100000
        angl_dist = np.append(angl_dist, [angl_dist0], axis=0)
    return angl_dist


"""END of functions """

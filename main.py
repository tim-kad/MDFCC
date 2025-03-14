import sys, time, json
import numpy as np
from datetime import datetime
from os import path, rename

from fcc_constants import R_e, R_e0, gui, check_fpa, int_table_path
import fcc_constants
from math import degrees, ceil

import balmis as bm
import rocket_data as rd
import tables_v2b as tb
import short_search as ss
import footprintv2 as fp


""" Profiling, see the second part at the bottom
import cProfile, pstats, io
from pstats import SortKey
pr = cProfile.Profile()
pr.enable()
"""

#angle_eps = 0.000001

""" Missile and interceptor types to be used are set here """
mtype = 10
itype = 11

h_int_min = 1000 # minimum intercept altitude (MIA)
h_discr = 0      # height for warhead discrimination, 0 means not used
t_delay = 5      # delay of interceptor launch after an event: missile rise over the horizon or misile burn out
""" Important: warhead detection range is set in rocket_data file for each interceptor   """
""" as an array with det_range value for every missile listed there. Zero means not used """

set_shoot_look_shoot = False # used by both footprint_calc2, n_footprint and angle_dist_tab2, does not affect other routines

""" Regular footprint calculation parameters """
acc = 0.01       # i.e. ~1% -- or 1000 m (built-in)
angle_step = 5   # foorptint angle, grad

set_run_all = False #run what is set below to True for all possible combinations interceptor vs missile)

""" These five to be used for tuning/debugging new missile/interceptor data """
exe_balmisflight = False
exe_balmis_maxrange = True
exe_balmis_range_vs_gth_list = False

exe_interceptor_flight = False
exe_interc_maxrange = False

""" Maxrange parameters """
gtheight_beg = 100
gtheight_end = 25000
gtangle_beg = 1
gtangle_end = 60
maxrange_acc = 0.3

""" This can be used for calculation of interception table in advance of footprint calculations. However,      """
""" if not found, interception table is calculated (and saved) first time it is needed, so this can be omitted """
exe_interception_table = False

exe_footprint = False # Footprint calculation

exe_n_footprint = False # Multiple footprint calculation for one or more det_range values
if exe_n_footprint :
#    det_range_list = [200]
    det_range_list = [50, 76, 100, 250, 500] # list of detection ranges in km
#    det_range_list = [250, 500, 1000, 2000, 4000] # list of detection ranges in km

exe_double_footprint = False # footprints for Shoot_Once and Shoot-Look_Shoot on one chart

exe_angle_dist_tab = False # build a sector of footprint by "probing" -- use when footprint is more than just an "oval"
if exe_angle_dist_tab :
    sect_angle_beg = 0    # footprint sector angle limits and step
    sect_angle_end = 180
    sect_angle_step = 2
    sect_dist_beg = 500000 # footprint sector distance (from center) limits
    sect_dist_num = 30    # (maxrange-sect_dist_beg)/sect_dist_num = N meter steps
    set_mirror_segment = True # add mirror segment (i.e. positive X), used by angle_dist_tab2, does not affect other routines
""" also see set_shoot_look_shoot parameter above """

""" These are to keep or overwrite an old file with the same name """
set_keep_int_tables = True # .npy intereptor table data files (unsampled and sampled)
set_keep_fp_chart = True # keep or overwrite .png file with foot print chart
set_keep_fp_data = True # .csv file with footprint data

""" This is a debug flag """
set_int_table_samp_verify = True # this is within interception_table
""" ==================== """

stdout_to_file = False # to save screen output to a file, used for debugging purposes
set_keep_stdout_file = True
set_time_stamp = False # set to True to prevent accidental overwriting of data files
exe_interceptor_table = False # for debugging, normally not needed to run separately

if set_time_stamp :
    r_now = datetime.now()
    t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
else :
    t_stamp = ''
    



def keep_old_file(f_name) :
    """
    If file f_name exists, rename it by adding its modification date as a time stamp.

    Parameters
    ----------
    f_name : TYPE
        name of the file to keep

    Returns
    -------
    None.

    """
    
    if path.exists(f_name) :
        file_mtime = path.getmtime(f_name)            
        mt_stamp = datetime.fromtimestamp(file_mtime).strftime("%y%m%d-%H%M%S")
        file_name, file_extension = path.splitext(f_name)
        new_f_name = file_name + "-" + mt_stamp + file_extension 
        rename(f_name, new_f_name)


def save_data(svdata, f_name, keep=False) :
    """ saves svdata to f_name in JSON format """
    if keep :
            keep_old_file(f_name)
    json_array = json.dumps(svdata, indent=4)
    with open(f_name, 'w') as rdf:
            rdf.write(json_array)

def load_data(f_name) :
       if path.exists(f_name) :
           with open(f_name, 'r') as rdf:
               l_data = json.loads(rdf.read())
               return l_data
       else :
           return False


def load_cfg(f_name='fcc_config.json', f_name_old='footprint_config.json'):
    if path.exists(f_name) :
        with open(f_name, 'r') as rdf:
            l_data = json.loads(rdf.read())
            return l_data
    else :
       if path.exists(f_name_old) :
           with open(f_name_old, 'r') as rdf:
               l_data = json.loads(rdf.read())
               return l_data
       else :
           return False

        
""" Use this to see if missile data make sense """
def run_balmisflight(m_type) :
    
    missile_data = rd.missile(m_type)
    trajectory_data = False
    ind_flight_dataprint = True
    m_range = bm.balmisflight(missile_data, trajectory_data, ind_flight_dataprint)
    print("Missile range = {:.0f} km".format(m_range/1000))
    
def run_interceptor_flight(i_type) :

    interceptor_data = rd.interceptor(i_type)
    #interceptor_data["flight_path_angle"] = 55 # for quick tests
    trajectory_data = False
    ind_flight_dataprint = True
    i_range = bm.balmisflight(interceptor_data, trajectory_data, ind_flight_dataprint)
    print("Interceptor range = {:.0f} km".format(i_range/1000))

""" Finding gravity turn height and angle for max range of the ballistic missile """
def run_balmis_maxrange(m_type) :
    #mtype = set_mtype
    missile_data = rd.missile(m_type)
    #m_range = bm.balmis_maxrange(missile_data) # search ranges are optional
    #defalt values: gtheight_beg=100, gtheight_end=25000, gtheight_acc=100, gtangle_beg=1, gtangle_end=60, angle_acc=0.5
    m_range = bm.balmis_maxrange(missile_data, gtheight_beg, gtheight_end, gtangle_beg, gtangle_end, maxrange_acc)

def run_interceptor_maxrange(i_type) :

    #itype = set_itype
    interceptor_data = rd.interceptor(i_type)
    traj_type0 = interceptor_data["traj_type"]
    interceptor_data["traj_type"] = "bal_mis"
    #m_range = bm.balmis_maxrange(interceptor_data) # search ranges are optional
    i_range = bm.balmis_maxrange(interceptor_data, gtheight_beg, gtheight_end, gtangle_beg, gtangle_end, maxrange_acc)
    interceptor_data["traj_type"] = traj_type0
    
""" To check if there is more than one max on-screen data output, time-consuming """
def run_balmis_range_vs_gth_list() :
    
    #mtype = set_mtype
    missile_data = rd.missile(mtype)
    bm.balmis_range_vs_gth_list(missile_data) # gt_height range is optional

def run_interceptor_table(itype, f_name='', psi_step=0.25, keep_int_tables=set_keep_int_tables) : # time-consuming; not to be confused with interceptION_table
    """ This is building a set of interceptor trajectories with launch angle from 90 (from vertical)   """
    """ to 0 (not including 0) with a (default) step of 0.25 grad. This is the most time-consuming     """
    """ procedure, therefore save the result in a binary file to be used for further calculations      """
    
    ind_flight_dataprint = False

    #itype = set_itype
    interceptor_data = rd.interceptor(itype, f_name)
    
    if stdout_to_file :
        file_name = int_table_path + '/int_table_i{}{}.txt'.format(itype, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    #interc_table = np.empty([1,0,6])
    interc_table = tb.interceptor_table(interceptor_data, ind_flight_dataprint, psi_step)
    config_data = [psi_step, R_e, fcc_constants.no_atmosphere]
    interc_data = np.array([interceptor_data, config_data, interc_table], dtype=object)

    file_nw = int_table_path + '/int_table_i{}{}.npy'.format(itype, t_stamp)
    if keep_int_tables :
        keep_old_file(file_nw)
        with open(file_nw, 'wb') as intab_f:
            np.save(intab_f, interc_data, allow_pickle=True)
        print("The interceptor table saved to " + file_nw)

    if stdout_to_file :
        sys.stdout = original
        
    return interc_data

def run_interception_table(i_type, rd_fname='', psi_step=0.25, beta_step=0.1, keep_int_tables=set_keep_int_tables, int_table_samp_verify=set_int_table_samp_verify) : # fast; not to be confused with interceptOR_table
    """ Sampling of the set of interceptor trajectories over "beta" flight path angle (from horizontal)  """
    """ starting from the lowest angle (negative) and up to 90 grad, with a (default) step of 0.25 (0.1) """

    #itype = set_itype
    interceptor_data = rd.interceptor(i_type, rd_fname)

    print("\nInterception (sampled) table building routine started...")

    """ Name of the file with a saved set of interceptor trajectories """
    file_nr = int_table_path + '/int_table_i{}.npy'.format(i_type)      
    interc_data_good = False
    if path.exists(file_nr) :
        interc_data_good = True
        with open(file_nr, 'rb') as intab_f: # load interceptor table
            interc_data = np.load(intab_f, allow_pickle=True)
        if len(interc_data) == 3 :
            #interceptor_data_r, psi_step_r, interc_table = interc_data
            interceptor_data_r, config_data_r, interc_table = interc_data
            if type(config_data_r) == float :
                config_data_r = [config_data_r]
            psi_step_r = config_data_r[0]
            #print("config_data_r = ", config_data_r)
            #print("psi_step_r = ", psi_step_r)
            if psi_step_r == psi_step : #check flight-related parameters
                for key in ("cd_type",
                            "m_st",
                            "m_fu",
                            "v_ex",
                            "t_bu",
                            "t_delay", #stage separation delay
                            "a_mid",
                            "m_shroud",
                            "t_shroud",
                            "m_pl",
                            "a_nz",
                            "c_bal",
                            "traj_type",
                            "vert_launch_height"#,                            "mpia"#,                             "op_range"
                            ) :
                    if key in interceptor_data_r : # older data may not contain a later added parameter
                        if interceptor_data_r[key] != interceptor_data[key] :
                            print("R", key, interceptor_data_r[key], interceptor_data[key])
                            interc_data_good = False
                            print("Interceptor data in file is not current, recalculating for current interceptor flight parameters.")
                            break
                        # if interc
                    else :
                        print("R", key, "not present in the file")
                        interc_data_good = False
                        print("Interceptor data in file is not current, recalculating for current interceptor flight parameters.")
                        break

                #for key
                if len(config_data_r) == 3 :
                    R_e_r = config_data_r[1]
                    if R_e_r == R_e :
                        if R_e != R_e0 : print("R_N = {:.3f}".format(R_e_r/R_e0))
                        r_no_atm = config_data_r[2]
                        if r_no_atm == fcc_constants.no_atmosphere :
                            pass
                            #print("no_atmosphere={}".format(r_no_atm))
                        else :
                            interc_data_good = False
                            print("Parameter \'no_atmosphere\' is not the same current: {} vs read: {}".format(fcc_constants.no_atmosphere, r_no_atm))
                    else :
                        interc_data_good = False
                        print("Earth radius is not the same, current: {} vs read: {}".format(R_e/R_e0, R_e_r/R_e0))
                else :
                    interc_data_good = False
                    print("File " + file_nr + " contains incorrect number of data units, calculating new data")
                        
            else :
                interc_data_good = False
                print("psi_step in file is not the same as set, recalculating for the set value")

            if interc_data_good :
                print("The set of interceptor trajectories loaded from file " + file_nr)            
        else :
            interc_data_good = False
            print("File " + file_nr + " contains incorrect number of data units, calculating new data")
    else :
        print("No set of interceptor trajectories " + file_nr + " found.")
        print("Calculating a new one...")

    if not interc_data_good :
        if check_fpa :
            print(">>>")
            print("Set check_fpa=False and restart the program.")
            print(">>>")
            return False

        interc_data = run_interceptor_table(i_type, rd_fname, psi_step, keep_int_tables)
        interceptor_data, config_data, interc_table = interc_data
 
    int_table_v2_w = tb.interception_table(interceptor_data, interc_table, psi_step, beta_step)
    config_data = [psi_step, beta_step, R_e, fcc_constants.no_atmosphere]
    interc_data_w = np.array([interceptor_data, config_data, int_table_v2_w], dtype=object)

    file_nw = int_table_path + '/int_table_samp_i{}{}.npy'.format(i_type, t_stamp)
    if keep_int_tables :
        keep_old_file(file_nw)
        
    with open(file_nw, 'wb') as intab_w:
        np.save(intab_w, interc_data_w, allow_pickle=True)
    print("The sampled interception table saved to " + file_nw)
    
    """ Sampled set verification, just in case, not really necessary """
    if int_table_samp_verify :
        print("Sampled set verification only >>>")
        v_count = 0
        for i in range(len(int_table_v2_w)) :
            #print("\rProcessing beta = {:.2f}  ".format(degrees(int_table_v2_w[i][0, 3])), end='')
            for j in range(len(int_table_v2_w[i]) - 1) :
                if int_table_v2_w[i][j, 1] >= int_table_v2_w[i][j + 1, 1] or int_table_v2_w[i][j, 2] >= int_table_v2_w[i][j + 1, 2] :
                    v_count += 1
                    # print("Sequence violation beta = {:.2f}, psi = {:.2f}".format(degrees(int_table_v2_w[i][0, 3]), int_table_v2_w[i][j, 0]))
        if v_count :
            print("Sampled table verification complete, {} out of sequence elements found.".format(v_count))

        else :
            print("Sampled table verification complete, all good.")

        """
        int_table_v2_list = [itv2_i.tolist() for itv2_i in int_table_v2_w]
        json_array = json.dumps(int_table_v2_list, indent=4)
        with open("int_table_samp_dump-230817.json", 'w') as rdf:
                rdf.write(json_array)
        """

        i_v = 0
        while i_v < (len(int_table_v2_w) - 1) :
            while  len(int_table_v2_w[i_v]) == 0 :
                print("empty i_v = {}, int_table_v2_w[i_v] = {}".format(i_v, int_table_v2_w[i_v]))
                i_v += 1
            j_v = i_v + 1
            while len(int_table_v2_w[j_v]) == 0 : 
                print("empty j_v = {}, int_table_v2_w[j_v] = {}".format(j_v, int_table_v2_w[j_v]))
                j_v += 1
            if int_table_v2_w[i_v][0, 3] >= int_table_v2_w[j_v][0, 3] :
                print(i_v, int_table_v2_w[i_v][0, 3], j_v, int_table_v2_w[j_v][0, 3])
            i_v = j_v
        
        """
        beta_min_deg = degrees(int_table_v2_w[0][0, 3])
        beta_n = ceil((90 - beta_min_deg) / beta_step) + 1
        int_tab_len = len(int_table_v2_w)
        print(beta_min_deg, beta_n, int_tab_len)
        """

    return interc_data_w

""" END of run_interception_table """

def load_int_table(t_itype, psi_step=0.25, beta_step=0.1, f_name='', t_tstamp='', keep_int_tables=set_keep_int_tables, int_table_samp_verify=set_int_table_samp_verify) :
    """
    Loading sampled interception table from a file. If not found, load set of interceptor trajectories from a file,
    then calculate interception table. If the set is not found either, calculate a new one (time consuming). 

    Parameters
    ----------
    t_itype : 
        interceptor type

    Returns
    -------
    int_table:
        interception table for t_itype
    """

    interceptor_data = rd.interceptor(t_itype, f_name)
    
    file_nr = int_table_path + '/int_table_samp_i{}.npy'.format(t_itype)
    interc_data_good = False
    if path.exists(file_nr) :
        interc_data_good = True
        with open(file_nr, 'rb') as intab_f: # load sampled interceptor table
            interc_data_samp = np.load(intab_f, allow_pickle=True)
        if len(interc_data_samp) == 3 :
            #interceptor_data_r, psi_step_r, beta_step_r, interc_table_samp = interc_data_samp
            interceptor_data_r, config_data_r, interc_table_samp = interc_data_samp
            psi_step_r, beta_step_r = config_data_r[0], config_data_r[1]
            if psi_step_r == psi_step :
                if beta_step_r == beta_step : #check flight-related parameters
                    for key in ("cd_type",
                                "m_st",
                                "m_fu",
                                "v_ex",
                                "t_bu",
                                "t_delay", # stage separation delay
                                "a_mid",
                                "m_shroud",
                                "t_shroud",
                                "m_pl",
                                "a_nz",
                                "c_bal",
                                "vert_launch_height",
                                "traj_type"#,                                "mpia" #,                                "op_range"
                                ) :
                        if key in interceptor_data_r : # older data may not contain a later added parameter
                            if interceptor_data_r[key] != interceptor_data[key] :
                                print("N", key, interceptor_data_r[key], interceptor_data[key])
                                interc_data_good = False
                                print("Interceptor data in file is not current, recalculating for current interceptor flight parameters.")
                                break
                            # if interc..
                        else :
                            print("N", key, "not present in the file")
                            interc_data_good = False
                            print("Interceptor data in file is not current, recalculating for current interceptor flight parameters.")
                            break
                            
                    # for key #TODO if inter_data_good : check earth size, otherwise it's done regardless, same for R-table
                    if len(config_data_r) == 4 :
                        #print("Ok load")
                        R_e_r = config_data_r[2]
                        if R_e_r == R_e :
                            if R_e != R_e0 : print("R_N = {:.3f}".format(R_e_r/R_e0))
                            r_no_atm = config_data_r[3]
                            if r_no_atm == fcc_constants.no_atmosphere :
                                pass
                                #print("no_atmosphere={}".format(r_no_atm))
                            else :
                                interc_data_good = False
                                print("Parameter \'no_atmosphere\' is not the same, current: {} vs read: {}".format(fcc_constants.no_atmosphere, r_no_atm))
                        else :
                            interc_data_good = False
                            print("Earth radius is not the same, current: {} vs read: {}".format(R_e/R_e0, R_e_r/R_e0))
                    # if len...
                    else :
                        interc_data_good = False
                        print("File " + file_nr + " contains incorrect number of data units, calculating new data")
                                                
                else :
                    interc_data_good = False
                    print("beta_step in file is not the same as current, recalculating for the current value")
            else :
                interc_data_good = False
                print("psi_step in file is not the same as current, recalculating for the current value")

            if interc_data_good :
                print("Resampled table for interceptor type i{0} loaded from file int_table_samp_i{0}.npy".format(t_itype))
        else :
            interc_data_good = False
            print("File " + file_nr + " contains incorrect number of data units, calculating new data")
    else :
        print("No sampled interception data file " + file_nr + " found.")
        print("Calculating a new one...")

    if not interc_data_good :
        interc_data_samp = run_interception_table(t_itype, f_name, psi_step, beta_step, keep_int_tables, int_table_samp_verify)
        if type(interc_data_samp) != bool :
            interc_table_samp = interc_data_samp[2]
        else :
            return False
        
    return(interc_table_samp)

""" END of load_int_table"""


def run_footprint(m_type, i_type, rd_fname, emode_sls=False, h_int_min=1000, angle_step=10, t_delay=5, h_discr=0, acc=0.01) :
    """ Reads sampled interception table from file.                 """
    """ Some debug data can be printed by setting debug_print flags """
    """ in 'bm.trj_from_center' and 'ss.short_search'               """

    """ Calculation settings begin """
    """****************************"""
    #mtype = set_mtype       # missile type number, see rocket_data module
    #itype = set_itype       # interceptor type number, see rocket_data module

    """ These are moved to the top of the file
    h_int_min = 1000 # minimum intercept altitude (MIA)
    h_discr = 0      # height for warhead discrimination, 0 means not used

    t_delay = 5      # delay of interceptor launch after an event: missile erise over the horizon or misile burn out

    acc = 0.01       # i.e. ~1%
    angle_step = 15   # foorptint angle, grad
    """

    """ End of calculation settings """    
    """*****************************"""

    print("\nFootprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    print("Missile type {} trajectory calculating...".format(m_type), end='')

    if stdout_to_file :
        file_name = 'footprint_m{}_i{}{}.txt'.format(m_type, i_type, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange / 1000))
    
    dist = mrange - 1000 # starting outer limit for search

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][len(missile_data["t_bu"]) - 1]
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    det_range = 0.0
    interceptor_data = rd.interceptor(i_type, rd_fname)
    if "det_range" in interceptor_data.keys() :
        if len(interceptor_data["det_range"]) > m_type :
            det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
        else :
            print("No detaction range value for this missile. Detection range set to 0.")
            print("For quick test run 'N Footprints vs Detection Range' routine.")
    else :
        print("No detaction range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'N Footprints vs Detection Range' routine.")


    fp_st = time.time()

    if not det_range :
        print("Detection range not set.")
        det_range = 0
    else :
        if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
            det_range *= 1000

    int_table = tb.load_int_table(i_type, t_stamp)                

    search_func = ss.short_search
    search_mode = "Shoot_Once"
    save_label = "son"

    if emode_sls :
        search_func = ss.sls_search
        search_mode = "Shoot_Look_Shoot"
        save_label = "sls"
        
    print("Footprint search mode: " + search_mode)
    
    footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, det_range, t_delay, h_discr, acc, dist)

    if np.any(footprint_tab) :
        header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        header_str = header_str.format(m_type, i_type, h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode)
        file_name = "footprint_m{}_i{}_{}{}.csv".format(m_type, i_type, save_label, t_stamp)
        if set_keep_fp_data :
            keep_old_file(file_name)
        np.savetxt(file_name, footprint_tab, fmt='%.3f', delimiter = ',', header=header_str)
        print("Footprint csv data saved to " + file_name)
        file_name = "footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
        fptab_list = footprint_tab.tolist()
        data2save = header_str, fptab_list
        save_data(data2save, file_name)
        
        #with open('footprint_m{}_i{}_{}{}.npy'.format(m_type, i_type, save_label, t_stamp), 'wb') as footprint_f:
        #    np.save(footprint_f, footprint_tab)
        #print("Footprint data saved to footprint_m{}_i{}_{}{}.npy".format(m_type, i_type, save_label, t_stamp))

        chart_info_str = "h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        chart_info_str = chart_info_str.format(h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode)
        title_str = "Footprint: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
        chart_fname = "footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
        if set_keep_fp_chart :
            keep_old_file(chart_fname)
        fp.fp_chart(footprint_tab, chart_info_str, title_str, chart_fname)
        #print("Footprint chart saved to " + chart_fname)

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file :
        sys.stdout = original
        
def run_n_footprint(m_type, i_type, det_range_list, rd_fname='', emode_sls=False, h_int_min=1000, angle_step=10, t_delay=5, h_discr=0, acc=0.01) :

    """ Reads sampled interception table from file.                 """
    """ Some debug data can be printed by setting debug_print flags """
    """ in 'bm.trj_from_center' and 'ss.short_search'               """

    """ Calculation settings begin """
    """****************************"""
    #mtype = set_mtype       # missile type number, see rocket_data module
    #itype = set_itype       # interceptor type number, see rocket_data module

    print("\nMultiple footprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    print("Set of detection ranges: {}".format(str(det_range_list)[1:-1]))
    print("Missile type {} trajectory calculating...".format(m_type), end='')

    if stdout_to_file :
        file_name = 'footprint_m{}_i{}{}.txt'.format(m_type, i_type, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange / 1000))
    
    int_table = tb.load_int_table(i_type, t_stamp)                

    dist = mrange - 1000 # starting outer limit for search

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][len(missile_data["t_bu"]) - 1]
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    fp_st = time.time()

    search_func = ss.short_search
    search_mode = "Shoot_once"
    save_label = "son"

    if set_shoot_look_shoot :
        search_func = ss.sls_search
        search_mode = "Shoot_look_shoot"
        save_label = "sls"
            
    print("Footprint search mode: " + search_mode)

    fprint_tab_lst = []
    label_lst = []
    info_str_b = ''
    for det_range in det_range_list :
        if not det_range :
            print("Detection range not set.")
            det_range = 0
        else :
            if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                det_range *= 1000
    
        print("Detection range = {} km ".format(det_range/1000))
        
        footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, det_range, t_delay, h_discr, acc, dist)
        if np.any(footprint_tab) :
            fprint_tab_lst.append(footprint_tab)
        else:
            fprint_tab_lst.append(np.zeros((0, 5)))
            
        label_lst.append(str(int(det_range/1000)))
        info_str_b += str(int(det_range/1000)) + ', '

        """
        if np.any(footprint_tab) :
            header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
            header_str = header_str.format(m_type, i_type, h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode)
            file_name = "footprint_m{}_i{}_{}{}.csv".format(m_type, i_type, save_label, t_stamp)
            if path.exists(file_name) :
                r_now = datetime.now()
                time_s = "-" + r_now.strftime("%y%m%d-%H%M")
                file_name = "footprint_m{}_i{}_{}{}{}.csv".format(m_type, i_type, save_label, t_stamp, time_s)
            np.savetxt(file_name, footprint_tab, fmt='%.3f', delimiter = ',', header=header_str)
            print("Footprint csv data saved to " + file_name)
            #with open('footprint_m{}_i{}_{}{}.npy'.format(m_type, i_type, save_label, t_stamp), 'wb') as footprint_f:
            #    np.save(footprint_f, footprint_tab)
            #print("Footprint data saved to footprint_m{}_i{}_{}{}.npy".format(m_type, i_type, save_label, t_stamp))
        """
        
    chart_info_str = "h_int_min={} t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
    chart_info_str = chart_info_str.format(h_int_min, t_int_lnc, angle_step, t_delay, h_discr, search_mode)
    chart_info_str += "\nRanges: " + info_str_b[:-2] + " km"
    title_str = "N-Footprint: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
    chart_fname = "n-footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
    if set_keep_fp_chart :
        keep_old_file(chart_fname)
    fp.fp_chart_n(fprint_tab_lst, label_lst, chart_info_str, title_str, chart_fname)
    #print("Footprint chart saved to " + chart_fname)

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("N-Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file :
        sys.stdout = original

def run_angle_dist_tab():  # can be time-consuming depending on ranges and steps
    """ In case footprint doesn't look like oval, this builds a sector of the footprint """
    """ limited by angle and distance ranges as specified.                              """
    
    """ Calculation settings begin """
    """****************************"""
    #mtype = set_mtype       # missile type number, see rocket_data module
    #itype = set_itype       # interceptor type number, see rocket_data module
    
    """ These are  moved to the top of the file
    sect_angle_beg = 105    # footprint sector angle limits and step
    sect_angle_end = 115
    sect_angle_step = 1
    
    sect_dist_beg = 38000 # footprint sector distance (from center) limits
    sect_dist_num = 34    # (maxrange-sect_dist_beg)/sect_dist_num = N meter steps

    h_int_min = 1000 # minimum intercept altitude (MIA)
    h_discr = 0      # height for warhead discrimination, 0 means not used
    
    t_delay = 5      # delay of interceptor launch after an event: missile erise over the horizon or misile burn out
    """
    
    """ End of calculation settings """    
    """*****************************"""

    print("\nFootprint sector calculation by probing started. Missile type m{}, Interceptor type i{}".format(mtype, itype))
    print("Missile type {} trajectory calculating...".format(mtype), end='')

    if stdout_to_file :
        file_name = 'angle_dist_table_m{}_i{}_{}-{}_{}grad-{}km_n{}{}.txt'.format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(mtype)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(mtype, mrange/1000))

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][len(missile_data["t_bu"]) - 1]

    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch (launch detection time + etc.)

    det_range = 0.0
    interceptor_data = rd.interceptor(itype)
    if "det_range" in interceptor_data.keys() :
        if len(interceptor_data["det_range"]) > mtype :
            det_range = interceptor_data["det_range"][mtype] # detection range, this is set in the "rocket_data" module
        else :
            print("No detaction range value for this missile. Detection range set to 0.")
            print("For quick test run 'N Footprints vs Detection Range' routine.")
    else :
        print("No detaction range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'N Footprints vs Detection Range' routine.")

    if det_range < 11000 :
        det_range *= 1000
    
    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    fp_st = time.time()

    int_table = tb.load_int_table(itype, t_stamp)                

    search_func = ss.short_search
    search_mode = "Shoot_Once"
    save_label = "son"

    if set_shoot_look_shoot :
        search_func = ss.sls_search
        search_mode = "Shoot-Look-Shoot"
        save_label = "sls"
        
    print("Footprint sector calculation mode: " + search_mode)
    angle_dist_tab2 = ss.angle_dist_tab2(search_func, trj, int_table, h_int_min, t_int_lnc, op_range, det_range, t_delay, h_discr, sect_angle_beg, sect_angle_end, sect_angle_step, sect_dist_beg, sect_dist_num)

    angle_dist_tab = angle_dist_tab2[0]
    file_name = "angle_dist_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.csv".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp)
    if set_keep_fp_data :
        keep_old_file(file_name)
    np.savetxt(file_name, angle_dist_tab, fmt='%.3f', delimiter = ',', header='angle,distance,dist_to_trj, X, Y, Xx, Zz' + ', ' + search_mode)
    print("Footprint sector data saved to " + file_name)

    fp_scatter = angle_dist_tab2[1]
    #with open("fpsector_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.npy".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp), 'wb') as fpsector_f:
    #    np.save(fpsector_f, fp_scatter)
    #print("Footprint sector scatter data saved to fpscatter_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.npy".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp))

    if set_mirror_segment :
        for i in range(len(fp_scatter)) :
            fp_scatter = np.append(fp_scatter, [[-fp_scatter[i, 0], fp_scatter[i, 1]]], axis=0)

    chart_info_str = "h_int_min={} t_int_lnc={} det_range={} km t_delay={} h_discr={} {}"
    chart_info_str += "\nangle {}-{} by {} grad, range from {:.0f} km, {} steps"
    chart_info_str = chart_info_str.format(h_int_min, t_int_lnc, det_range/1000, t_delay, h_discr, search_mode, sect_angle_beg, sect_angle_end, sect_angle_step, sect_dist_beg/1000, sect_dist_num)
    title_str = "Footprint by probe: itype={} mtype={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
    chart_fname = "fpsector_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.png".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, sect_dist_beg, sect_dist_num, save_label, t_stamp)
    if set_keep_fp_chart :
        keep_old_file(chart_fname)
    sector_chart = fp.fp_sector_chart(fp_scatter, chart_info_str, title_str, chart_fname)

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Footprint sector calculation time = {:.3f}s".format(fp_elapsed_time))
    
    if stdout_to_file :
        sys.stdout = original

def run_double_footprint() :
    """ Reads sampled interception table from file.                 """
    """ Calculates footprints for Shoot_Once and Shoot-Look-Shoot   """
    """ and draws them on one chart                                 """
    """ Some debug data can be printed by setting debug_print flags """
    """ in 'bm.trj_from_center' and 'ss.short_search'               """

    """ Calculation settings begin """
    """****************************"""
    #mtype = set_mtype
    #itype = set_itype

    """ These are  moved to the top of the file
    h_int_min = 1000 # minimum intercept altitude (MIA)
    h_discr = 0      # height for warhead discrimination, 0 means not used

    t_delay = 5      # delay of interceptor launch after event: missil erise over the horizon or misile burn out

    acc = 0.01 # i.e. ~1%
    angle_step = 15 # foorptint angle, grad
    """
    
    """ End of calculation settings """    
    """*****************************"""

    print("\nDouble Footprint calculation routine started. Missile type m{}, Interceptor type i{}".format(mtype, itype))
    print("Missile type {} trajectory calculating...".format(mtype), end='')

    if stdout_to_file :
        file_name = 'double-footprint_m{}_i{}{}.txt'.format(mtype, itype, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    #interceptor_data = rd.interceptor(itype)

    missile_data = rd.missile(mtype)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(mtype, mrange / 1000))
    
    dist = mrange - 1 # starting outer limit for search

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][len(missile_data["t_bu"]) - 1]
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch (launch detection time + etc.)

    det_range = 0.0
    interceptor_data = rd.interceptor(itype)
    if "det_range" in interceptor_data.keys() :
        if len(interceptor_data["det_range"]) > mtype :
            det_range = interceptor_data["det_range"][mtype] # detection range, this is set in the "rocket_data" module
        else :
            print("No detaction range value for this missile. Detection range set to 0.")
            print("For quick test run 'N Footprints vs Detection Range' routine.")
    else :
        print("No detaction range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'N Footprints vs Detection Range' routine.")

    if not det_range :
        print("Detection range not set.")
        det_range = 0
    else :
        if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
            det_range *= 1000

    fp_st = time.time()

    int_table = tb.load_int_table(itype, t_stamp)                

    search_func1 = ss.short_search
    search_mode1 = "Shoot_once"
    save_label1 = "son"

    search_func2 = ss.sls_search
    search_mode2 = "Shoot_look_shoot"
    save_label2 = "sls"
        
    print("Footprint1 search mode: " + search_mode1)
    footprint_tab1 = fp.footprint_calc_v2(search_func1, trj, int_table, h_int_min, t_int_lnc, angle_step, det_range, t_delay, h_discr, acc, dist)

    if np.any(footprint_tab1) :
        fp_1 = True
        header_str = "angle, distance, acc_prm, x, y, mtype={} itype={} h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        header_str = header_str.format(mtype, itype, h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode1)
        file_name = "footprint_m{}_i{}_{}{}.csv".format(mtype, itype, save_label1, t_stamp)
        if set_keep_fp_data :
            keep_old_file(file_name)
        np.savetxt(file_name, footprint_tab1, fmt='%.3f', delimiter = ',', header=header_str)
        print("Footprint1 csv data saved to " + file_name)

        chart_info_str1 = "h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        chart_info_str1 = chart_info_str1.format(h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode1)

        title_str1 = "Footprint: itype={} mtype={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
        chart_fname1 = "footprint_m{}_i{}_{}{}.png".format(mtype, itype, save_label1, t_stamp)
        if set_keep_fp_chart :
            keep_old_file(chart_fname1)
        chart1 = fp.fp_chart(footprint_tab1, chart_info_str1, title_str1, chart_fname1)

    else :
        fp_1 = False
        print("No Footprint for Shoot_Once engagement...")

    print("Footprint2 search mode: " + search_mode2)
    footprint_tab2 = fp.footprint_calc_v2(search_func2, trj, int_table, h_int_min, t_int_lnc, angle_step, det_range, t_delay, h_discr, acc, dist)

    if np.any(footprint_tab2) :
        fp_2 = True
        header_str = "angle, distance, acc_prm, x, y, mtype={} itype={} h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        header_str = header_str.format(mtype, itype, h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode2)
        file_name = "footprint_m{}_i{}_{}{}.csv".format(mtype, itype, save_label2, t_stamp)
        if set_keep_fp_data :
            keep_old_file(file_name)
        np.savetxt(file_name, footprint_tab2, fmt='%.3f', delimiter = ',', header=header_str)
        print("Footprint2 csv data saved to " + file_name)

        chart_info_str2 = "h_int_min={} t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        chart_info_str2 = chart_info_str2.format(h_int_min, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr, search_mode2)

        title_str2 = "Footprint: itype={} mtype={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
        chart_fname2 = "footprint_m{}_i{}_{}{}.png".format(mtype, itype, save_label2, t_stamp)
        if set_keep_fp_chart :
            keep_old_file(chart_fname2)
        chart2 = fp.fp_chart(footprint_tab2, chart_info_str2, title_str2, chart_fname2)

    else :
        fp_2 = False
        print("No Footprint for Shoot-Look-Search engagement...")

    if fp_1 and fp_2 :
        title_str = "Double Footprint: itype={} mtype={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
        chart_fname = "double_footprint_m{}_i{}{}.png".format(mtype, itype, t_stamp)
        if set_keep_fp_chart :
            keep_old_file(chart_fname)
        double_chart = fp.fp_chart_2(footprint_tab1, footprint_tab2, chart_info_str1, chart_info_str2, title_str, chart_fname)

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Double Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    
    if stdout_to_file :
        sys.stdout = original


#@profile
def main_calc() :

    """ Missile and/or interceptor data need to be set in 'rocket_data' module  """
    """ >>> for interceptor(s) make sure 'det_range' list is set and includes   """
    """ >>> values for all missiles                                             """
    
    if exe_balmisflight :
        run_balmisflight(mtype)  
           
    if exe_balmis_maxrange : # time-consuming
        run_balmis_maxrange(mtype)

    if exe_interceptor_flight :
        run_interceptor_flight(itype)
    
    if exe_interc_maxrange :
        run_interceptor_maxrange(itype)

    if exe_balmis_range_vs_gth_list : # time-consuming
        run_balmis_range_vs_gth_list()
    
    if exe_interceptor_table :
        run_interceptor_table()
    
    if exe_interception_table :
        run_interception_table(itype)        
    
    if exe_footprint :
        run_footprint(mtype, itype)
    
    if exe_n_footprint :
        run_n_footprint(mtype, itype, det_range_list)

    if exe_angle_dist_tab :
        run_angle_dist_tab()
    
    if exe_double_footprint :
        run_double_footprint()
    
    if not (exe_balmisflight or exe_interceptor_flight or exe_balmis_maxrange or \
            exe_balmis_range_vs_gth_list or exe_interceptor_table or exe_interception_table or \
            exe_footprint or exe_angle_dist_tab or exe_double_footprint or exe_n_footprint) :
        print("No action chosen for mtype = {}, itype = {}".format(mtype, itype))

""" End of main_run """
if not gui :
    if set_run_all :
        print("\nRun All started")
        for itype in range (11, 14) :  #11, 14
            for mtype in range (1, 8) : #1, 8
                main_calc()
    else :
        main_calc()
        


""" Profiling, see the first part at the top
pr.disable()
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()

file_n = 'profile'
file_e = '.txt'
file_nm = file_n + file_e
if path.exists(file_nm) :
    r_now = datetime.now()
    file_nm = file_n + "-" + r_now.strftime("%y%m%d-%H%M") + file_e
original = sys.stdout
sys.stdout = open(file_nm, 'w')
print(s.getvalue())
sys.stdout = original
"""


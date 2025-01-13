import numpy as np
import balmis as bm
from math import radians, sin, cos, atan, sqrt, degrees, ceil, pi, asin, floor
from os import cpu_count
from multiprocessing import Process, Queue

from fcc_constants import beta_step as set_beta_step, R_e, angle_eps, int_vl_height#, int_vl_height_2
import fcc_constants

import json


def int_trj_calc(queue, int_data, psi_step, i_i, f_multi) :
    i_psi = i_i * psi_step
    ind_flight_dataprint = False
    
    if not f_multi :
        if i_i % 7 == 0 : 
            print("\rCalculating trajectory psi={:.2f}".format(i_psi), end='')
        
    int_data["flight_path_angle"] = 90 - i_psi
    #int_traj = np.empty([0, 3])
    int_traj = bm.balmisflight(int_data, True, ind_flight_dataprint)
    
    int_traj6 = np.empty([0, 6]) # psi, time, r, beta, x, y
    #t_lengths.append(len(int_traj))

    if i_i == 0 :
        for i_j in range(len(int_traj)) : #t_lengths[0]) :
            int_traj6 = np.append(int_traj6, [[0, int_traj[i_j, 0], int_traj[i_j, 1] - R_e, pi/2 , 0, int_traj[i_j, 1] - R_e]], axis=0)
    else : 
        i_rad = int_traj[0, 1] - R_e
        if int_data["traj_type"] == "int_exo" :
            i_ang = pi/2
        else :
            i_ang = radians(90 - i_psi)
        # i_j = 0 precessed separately
        int_traj6 = np.append(int_traj6, [[i_psi, int_traj[0, 0], i_rad, i_ang, 0, i_rad]], axis=0)
        
        for i_j in range(1, len(int_traj)) : #t_lengths[i_i]) :
            z_rad = int_traj[i_j, 1]
            z_ang = int_traj[i_j, 2]
#                i_rad = sqrt(R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang))
            if abs(z_ang) < angle_eps :
                i_rad = z_rad - R_e
            else :
                i_rad2 = R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang)
                i_rad = sqrt(i_rad2)
            
            """ v. 221030 20:55 """
            #z_1 = cos(z_ang)           # used for debug
            #z_2 = z_rad * z_1 - R_e
            
            if abs(z_ang) < angle_eps :
                if int_data["traj_type"] == "int_exo" :
                    i_ang = pi/2
                else :
                    i_ang = radians(90 - i_psi)
            else :
                x = (z_rad * cos(z_ang) - R_e) / i_rad
                i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
                if z_ang > pi :
                    if z_ang < 2 * pi :
                        i_ang = - pi - i_ang
                    elif z_ang < 3 * pi :
                        i_ang = - 2 * pi + i_ang
                    else :
                        print("Too long interceptor range, > 60,000 km, alfa={:.1f}".format(degrees(z_ang)))
   
            int_traj6 = np.append(int_traj6, [[i_psi, int_traj[i_j, 0], i_rad, i_ang, i_rad * cos(i_ang), i_rad*sin(i_ang)]], axis=0)
            
    #int_table_0[i_i] = int_traj6
    if f_multi :
        queue.put([i_i, int_traj6])
    else :
        return int_traj6
# end of int_trj_calc


def interceptor_table(interc_data, ind_flight_dataprint=False, psi_step=0.25, arr_obj=True) :
    """
    === Multiprocessor Version ===
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
    #t_lengths = []
    print("\nInterceptor trajectory set calculation started, psi goes from [0 up to 90)")
    print("This is going to take some time, you may want to get a cup of tea/coffee...")
    #if gui : print("Calculating trajectory psi", end='')
    if interc_data["traj_type"] == "int_exo" :
        interc_data["vert_launch_height"] = int_vl_height
        #if interc_data["i_key"] == 33 :
        #    interc_data["vert_launch_height"] = int_vl_height_2
            
    elif interc_data["traj_type"] == "int_endo" :
        interc_data["vert_launch_height"] = 0
    else :
        print("Unknown interceptor trajectory type")

    n_cores = cpu_count()
    
    f_multi_proc = fcc_constants.multi_proc and (not fcc_constants.no_atmosphere)
    
    # protect the entry point
    if f_multi_proc and (n_cores > 3) : #__name__ == '__main__':
        #print("\nok\n")
        batch_size = n_cores
        # execute in batches
        for i in range(0, psi_n, batch_size) :
            q = Queue()
            processes = []
            rets = []
            i_end = i + batch_size
            if i_end > psi_n : i_end = psi_n
            for j in range(i, i_end) :
                p = Process(target=int_trj_calc, args=(q, interc_data, fcc_constants.psi_step, j, True))
                processes.append(p)
                p.start()

            i_processing = min(i + batch_size, psi_n)
            print("\r(multi-)Processing {:.0f}%".format(i_processing / psi_n * 100), end='')

            for p in processes:
                ret = q.get() # will block
                rets.append(ret)
            #print("\n1")
            for p in processes:
                p.join()
            #print("\n2")
            for j in range(len(rets)) :
                #print("i={} psi={}".format(rets[j][0], rets[j][1][0]))
                int_table_0[rets[j][0]] = rets[j][1]
                
        # report that all tasks are completed
        print('Done', flush=True)
    #end of multiproc
    
    else :
        for j in range(psi_n) :
            int_traj_6 = int_trj_calc(False, interc_data, psi_step, j, False) #False for missing q arguemnt
            int_table_0[j] = int_traj_6
    
    print("\nInterceptor trajectory set calculation complete.")
    if arr_obj :
        return(int_table_0)
    else: # needs re-writing ?
        max_t_length = len(max(int_table_0, key=len)) # max(t_lengths)
        int_table_1 = np.empty([0, max_t_length, 6])
        for i_trj in int_table_0 :
            while len(i_trj) < max_t_length :
              i_trj = np.append(i_trj, [[-1, -1, -1, -1, -1, -1]], axis=0)
            int_table_1 = np.append(int_table_1, [i_trj], axis=0)
        return(int_table_1)

""" End of interceptor_table """



def interception_table(interceptor_data, int_table_v1, psi_step=0.25, beta_step=set_beta_step) :
    """
    Re-sample interceptor table by flight path angle and distance

    Parameters
    ----------
    interceptor_data:
        interceptor data set in "rocket_data" module
    int_table_v1 : TYPE [psi, time, r, beta, x, y]
        set of interceptor trajectories for a set of launch angles at start for endo or after vertical launch for exo, launch angles
        go from 0 (vertical) to 90 (horizontal) not including 90
    psi_step : 
        launch angle step size (in the int_table_v1 array)
    beta_step : 
        flight path angle beta step size, betas go from the lowest -N*beta_step (below horizon) to 90 (vertical)

    Returns
    -------
    Array of sampled trajectories, [psi, time, rad, beta]

    """
    
    """
    int_table_0: array over psi, for each psi: time, r, beta, x, y
    """
    endo = (interceptor_data["traj_type"] == "int_endo")
    t_burn = sum(interceptor_data["t_bu"]) + sum(interceptor_data["t_delay"]) # TODO
    
    beta_max_range = min([int_traj[len(int_traj) - 1][3] for int_traj in int_table_v1 if np.any(int_traj)])
    beta_min = min([min(int_traj[:, 3]) for int_traj in int_table_v1 if np.any(int_traj)])
    """
    min_arr = np.empty([0, 5])
    for int_traj in int_table_v1 :
        if np.any(int_traj) :
            i_min = np.argmin(int_traj[:, 3])
            min_arr = np.append(min_arr, [[i_min, int_traj[i_min, 0], degrees(int_traj[i_min, 3]), len(int_traj), degrees(int_traj[len(int_traj) - 1, 3])]], axis=0)
    i_min_beta = np.argmin(min_arr[:, 2])
    print(min_arr[i_min_beta])
    """
    int_max_range = -2 * beta_max_range * R_e # due to geometry
    print("beta_min={:.3f}, int_max_range={:.1f} km".format(degrees(beta_min), int_max_range/1000))
    
    beta_n = floor((90 - degrees(beta_min)) / beta_step) + 2 # one extra because we finish when all trajectories are above beta
    print("beta_n={}".format(beta_n))

    #int_table_v2 = np.empty(2 * beta_n, dtype=object)
    int_table_v2 = np.empty(beta_n, dtype=object)
       
    int_tab4_0 = np.empty([0, 4]) # psi, time, r, beta
    t_lengths = []
    
    # fill out vertical launch
    for i_t in range(1, np.argmax(int_table_v1[0][:, 2], axis=0)) : # case of i_psi == kpsi == 0 processed separately
        int_tab4_0 = np.append(int_tab4_0, [[0, int_table_v1[0][i_t, 1], int_table_v1[0][i_t, 2], radians(90)]], axis=0)
    int_table_v2[0] = int_tab4_0
#    int_table_v2 = [int_tab4_0]
    t_lengths.append(len(int_tab4_0))
    iter_k_psi = 1
    stop_cycle = 0
    psi_n = len(int_table_v1)
    i_beg = np.full(psi_n, 1)   # fill with 10, 10 is to avoid possible artefacts for low time values -- changed to 3 on 23.09.17 -- changed to 1
    while stop_cycle < (len(int_table_v1) - 1) : # cycle interceptor trajectories [scratch: angles from vertical], stop when no interceptor trajectory crosses elev. angle from above
        stop_cycle = 0
        int_tab4 = np.empty([0, 4]) # psi, time, r, beta
        i_time0 = 0
        i_rad0  = 0
#        k_psi = iter_k_psi * beta_step
        k_beta = radians(90 - iter_k_psi * beta_step)
        int_tab4 = np.append(int_tab4, [[0, 0, 0, k_beta]], axis=0)
        #if iter_k_psi > 2580 :
        #    a_b = 99999
        if iter_k_psi % 47 == 0 :
            print("\rProcessing elevation angle {:.2f} ".format(degrees(k_beta)), end='')
        for iter_psi in range(0, psi_n - 1) : # interceptor trajectories
            i_psi = psi_n - 1 - iter_psi  # go from higher psis, i.e. from lower trajectories
            
            #if False :
            if endo and (abs(k_beta - radians(90 - i_psi * psi_step)) < angle_eps) :
                i_e0 = i_beg[i_psi]
                i_e = i_e0
                while int_table_v1[i_psi][i_e, 1] <= t_burn :
                    if (i_e - i_e0) % 10 == 0 : # add only every 10th of them
                        int_tab4 = np.append(int_tab4, [[i_psi * psi_step, int_table_v1[i_psi][i_e, 1], int_table_v1[i_psi][i_e, 2], k_beta]], axis=0)
                    i_e += 1
                if (i_e - 1 - i_e0) % 10 != 0 : # add the last of them under t_burn if not just added
                    int_tab4 = np.append(int_tab4, [[i_psi * psi_step, int_table_v1[i_psi][i_e - 1, 1], int_table_v1[i_psi][i_e - 1, 2], k_beta]], axis=0)
                        
                i_beg[i_psi] = i_e
                
            else :
            
                no_beta = False
                if int_table_v1[i_psi][i_beg[i_psi], 3] - k_beta > angle_eps : # ***rel1*** -- see below
                    for i_t in range(i_beg[i_psi], len(int_table_v1[i_psi])) : 
                        diff = k_beta - int_table_v1[i_psi][i_t, 3]
                        if diff > angle_eps :
                            i_t2 = i_t
                            i_t1 = i_t - 1
                            i_beg[i_psi] = i_t - 1
                            break
                        elif abs(diff) <= angle_eps :
                            i_t2 = i_t1 = i_t
                            i_beg[i_psi] = i_t - 1
                            break
                        else :
                            if i_t == (len(int_table_v1[i_psi]) - 1) :
                                no_beta = True
                                stop_cycle += 1
                                i_beg[i_psi] = i_t
                                break
                            i_t += 1
                    
                    if not no_beta :
                        if i_t2 > i_beg[i_psi] :
                            if i_t1 == i_t2 :
                                i_time = int_table_v1[i_psi][i_t1, 1]
                                i_rad  = int_table_v1[i_psi][i_t1, 2]
                            else :
                                rad_1 = int_table_v1[i_psi][i_t1, 2]
                                rad_2 = int_table_v1[i_psi][i_t2, 2]
                                beta1 = int_table_v1[i_psi][i_t1, 3]
                                beta2 = int_table_v1[i_psi][i_t2, 3]
                                gamma = atan((rad_2 * cos(beta1 - beta2) - rad_1) / rad_2 / sin(beta1 - beta2))
                                i_rad = rad_1 * cos(gamma) / cos(gamma + beta1 - k_beta)
            
                                time1 = int_table_v1[i_psi][i_t1, 1]
                                time2 = int_table_v1[i_psi][i_t2, 1]
                                dr1_q = rad_1*rad_1 + i_rad*i_rad - 2 * rad_1 * i_rad * cos(beta1 - k_beta)
                                dr_q  = rad_1*rad_1 + rad_2*rad_2 - 2 * rad_1 * rad_2 * cos(beta1 - beta2)
                                i_time = time1 + (time2 - time1) * sqrt(dr1_q/dr_q)
                            
                            """ v. 221030 """
                            if i_time > i_time0 :
                                if i_rad > i_rad0 :
                                    int_tab4 = np.append(int_tab4, [[i_psi * psi_step, i_time, i_rad, k_beta]], axis=0)
                                    i_time0 = i_time
                                    i_rad0 = i_rad
                            elif i_time == i_time0 :
                                if  i_rad > i_rad0 :
                                    int_tab4[len(int_tab4) - 1, 0] = i_psi * psi_step
                                    int_tab4[len(int_tab4) - 1, 2] = i_rad
                                    i_rad0 = i_rad
                            else : # i_time < i_time0
                                if i_rad >= i_rad0 :
                                    # print("\ncheck:", i_psi * psi_step, i_time, i_rad, k_beta, ">>>", i_time0, i_rad0, "\n>>>", int_tab4[len(int_tab4) - 1])
                                    int_tab4[len(int_tab4) - 1, 0] = i_psi * psi_step
                                    int_tab4[len(int_tab4) - 1, 2] = i_rad
                                    i_time0 = i_time
                                    i_rad0 = i_rad
                                else : # i_rad < i_rad0
                                    int_tab4 = np.insert(int_tab4, len(int_tab4) - 1, [[i_psi * psi_step, i_time, i_rad, k_beta]], axis=0)
    
                            """ v. up to 221029
                            if (i_time >= i_time0) and (i_rad > i_rad0) :
                                if i_time == i_time0 :
                                    int_tab4[len(int_tab4) - 1, 0] = i_psi * psi_step
                                    int_tab4[len(int_tab4) - 1, 2] = i_rad
                                else :
                                    int_tab4 = np.append(int_tab4, [[i_psi * psi_step, i_time, i_rad, k_beta]], axis=0)
                                i_time0 = i_time
                                i_rad0  = i_rad
                            else :
                                if (i_time - i_time0) * (i_rad - i_rad0) <= 0 :
                                    print("\nint_table_v2 exception time and rad out of sequence, iter_psi={}, i_time={}, i_time0={}, i_rad={}, i_rad0={}"\
                                        .format(iter_psi, i_time, i_time0, i_rad, i_rad0))                               
                                    #break
                                else :
                                    print("\nint_table_v2 possibly good earlier point found, iter_psi={}, i_time={}, i_time0={}, i_rad={}, i_rad0={}"\
                                        .format(iter_psi, i_time, i_time0, i_rad, i_rad0))                                                              
                                    pass
                            """
        
                        else :      # i.e. i_t2 == i_beg meaning that ***rel1*** is wrong 
                            print("interception_table exception: impossible violaton")
                    else : # no beta
                        #print("*", end='')
                        pass
                            
                else :    # i.e. int_table_v1[i_psi][i_beg, 3] < k_beta
                    pass    

            # if/else endo

        # "psi" for cycle ends
        
        t_lengths.append(len(int_tab4))   


        """ Verifying sequence: time and distance both have to be increasing """
        int_tab4_len = len(int_tab4)

        """ ver from 230108 """
        j = int_tab4_len - 1
        while j > 0 :
            delta_t = int_tab4[j, 1] - int_tab4[j - 1, 1]
            delta_r = int_tab4[j, 2] - int_tab4[j - 1, 2]
            if delta_t <= 0 or delta_r <= 0 :
                if delta_t > 0 : # i.e. delta_r <= 0 :
                    int_tab4 = np.delete(int_tab4, j, axis=0)
                    int_tab4_len -= 1
                    if j == int_tab4_len : j -= 1
                elif delta_t == 0 :
                    if delta_r > 0 :
                        int_tab4 = np.delete(int_tab4, j - 1, axis=0)
                        int_tab4_len -= 1
                        j -= 1
                    else:
                        int_tab4 = np.delete(int_tab4, j, axis=0)
                        int_tab4_len -= 1
                        if j == int_tab4_len : j -= 1
                else : # delta_t < 0
                    if delta_r >= 0 :
                        int_tab4 = np.delete(int_tab4, j - 1, axis=0)
                        int_tab4_len -= 1
                        j -= 1
                    else : # delta_r < 0
                        int_tab4[[j-1, j]] = int_tab4[[j, j-1]] # swap
                        j += 1
                        if j == int_tab4_len : j -= 1
            else :
                j -= 1



        """ ver. until 230108: need to do a step back if current pair is deleted or swapped 
        for j0 in range(int_tab4_len - 1) :
            j = int_tab4_len - 1 - j0
            delta_t = int_tab4[j, 1] - int_tab4[j - 1, 1]
            delta_r = int_tab4[j, 2] - int_tab4[j - 1, 2]
            if delta_t <= 0 or delta_r <= 0 :
                if delta_t > 0 : # i.e. delta_r <= 0 :
                    int_tab4 = np.delete(int_tab4, j, axis=0)
                elif delta_t == 0 :
                    if delta_r > 0 :
                        int_tab4 = np.delete(int_tab4, j - 1, axis=0)
                    else:
                        int_tab4 = np.delete(int_tab4, j, axis=0)
                else : # delta_t < 0
                    if delta_r >= 0 :
                        int_tab4 = np.delete(int_tab4, j - 1, axis=0)
                    else : # delta_r < 0
                        int_tab4[[j-1, j]] = int_tab4[[j, j-1]] # swap
        """

        int_table_v2[iter_k_psi] = int_tab4
#            print("added", len(int_tab4))
        
        iter_k_psi += 1
   
    #if (iter_k_psi - 1) % 47 != 0 : # i.e. not printed, but the last one
    print("\rProcessing elevation angle {:.2f} ".format(degrees(k_beta)), end='')
    print("\nProcessing of {} elevation angles complete".format(iter_k_psi))
#    print("before flip t_lenths=", t_lengths)
#    print("int_table_v2[94]=", int_table_v2[93])
#   int_tab_length = len(int_table_v2)

#    path = 'int_table_test-221031-0300.txt'
#    original = sys.stdout
#    sys.stdout = open(path, 'w')
    int_table = np.empty(iter_k_psi - 1, dtype=object)
    for i_b in range(0, iter_k_psi - 1) :
        int_table[i_b] = int_table_v2[iter_k_psi - 2 - i_b]
#        print(i_b, "\n", int_table_v2[i_b], "\n")
#    sys.stdout = original

#        print(len(int_table[i_b]), len(int_table_v2[iter_k_psi - 1 - i_b]))
    
    int_table_v2 = np.flip(int_table) # so it goes from lowest beta up to 90 grad <- ??
    """ int_table_v2 dump
    int_table_v2_list = [itv2_i.tolist() for itv2_i in int_table_v2]
    json_array = json.dumps(int_table_v2_list, indent=4)
    with open("int_table_samp_dump.json", 'w') as rdf:
            rdf.write(json_array)
    """
    
    return (int_table)

""" End of interception_table """

#@profile
def mis_traj_sample_v0(tar_trj, beta_step=set_beta_step) :
    """
    Samples missile trajectory tar_trj over elevation angle from ILP

    Parameters
    ----------
    tar_trj : TYPE
        Missile trajectory shifted and turned
    beta_n : TYPE
        number of bets steps over 90 degrees angle (0 to 90)
    beta_step : TYPE
        size of beta steps in degrees

    Returns
    -------
    sampled trajectory (time, rad, beta, x, y)

    """

#    amax = np.argmax(tar_trj[:, 4])
#    print(amax,  len(tar_trj), tar_trj[amax])

    beta_n = int(90 / beta_step)
    
    #mis_traj_1 = np.empty([0, 5]) # time, r, beta, x, y -- launch to max beta
    #mis_traj_2 = np.empty([0, 5]) 
    mis_traj_1 = np.empty([len(tar_trj), 5]) #opt
    mis_traj_2 = np.empty([len(tar_trj), 5]) #opt
    
    i_max_beta = np.argmax(tar_trj[:, 4], axis=0)
    max_beta = max(tar_trj[:, 4])

    i_t0 = 0

    m_beta_beg = int(ceil(degrees(tar_trj[0, 4]) / beta_step))
    beta_2_beg = beta_n

    i_mt1 = 0 #opt
    """ ascending part of the trajctory (form ILP point of view) """
    for iter_i_beta in range(0, beta_n + 1 - m_beta_beg) :
        i_beta = radians((iter_i_beta + m_beta_beg) * beta_step)
#        print("\rmissile: processing elevation angle  up {}".format(iter_i_beta * beta_step), end='')
    
        if i_beta <= max_beta :
            
            if tar_trj[i_t0, 4] <= i_beta :
                for i_t in range(i_t0, i_max_beta) :
                    diff = tar_trj[i_t, 4] - i_beta
                    if diff > angle_eps :
                        i_t2 = i_t
                        i_t1 = i_t - 1
                        break
                    elif abs(diff) <= angle_eps :
                        i_t2 = i_t1 = i_t
                        break
                    else:
                        pass
                        #i_t += 1 < check if this was legit #TODO $$$

            if i_t1 == i_t2 : # i_t1 can be used before assignment TODO
                i_time = tar_trj[i_t1, 0]
                i_rad  = tar_trj[i_t1, 3]
            else :
                rad_1 = tar_trj[i_t1, 3]
                rad_2 = tar_trj[i_t2, 3]
                beta1 = tar_trj[i_t1, 4]
                beta2 = tar_trj[i_t2, 4]
                gamma = atan((rad_2 * cos(beta1 - beta2) - rad_1) / rad_2 / sin(beta1 - beta2))
                i_rad = rad_1 * cos(gamma) / cos(gamma + beta1 - i_beta)
        
                time1 = tar_trj[i_t1, 0]
                time2 = tar_trj[i_t2, 0]
                dr1_q = rad_1*rad_1 + i_rad*i_rad - 2 * rad_1 * i_rad * cos(beta1 - i_beta)
                dr_q  = rad_1*rad_1 + rad_2*rad_2 - 2 * rad_1 * rad_2 * cos(beta1 - beta2)
                i_time = time1 + (time2 - time1) * sqrt(dr1_q/dr_q)
            
            #mis_traj_1 = np.append(mis_traj_1, [[i_time, i_rad, i_beta, i_rad * cos(i_beta), i_rad * sin(i_beta)]], axis=0)
            mis_traj_1[i_mt1] = [i_time, i_rad, i_beta, i_rad * cos(i_beta), i_rad * sin(i_beta)] #opt
            i_mt1 += 1 #opt
            i_t0 = i_t2
            
        else:
            beta_2_beg = iter_i_beta + m_beta_beg - 1
            break
        

    #if beta_2_beg == -100 : print("len(tar_trj) = {}, i_max_beta = {}, max_beta = {:.3f}".format(len(tar_trj), i_max_beta, degrees(max_beta)))
    #for
    mis_traj_1 = mis_traj_1[:i_mt1] #opt
    
    mtf_len = len(tar_trj) # missile trajectory full length
    
    m_beta_end = int(ceil(degrees(tar_trj[mtf_len - 3, 4]) / beta_step)) #TODO ??? $$$ NoteA: was -3, see NoteB
    """ -3 here because the last two (might be more) can be spaced too widely """

    i_mt2 = 0 #opt
    """ descending part of the trajctory (form ILP point of view) """   
    for iter_i_beta in range(0, beta_2_beg + 1 - m_beta_end) :
        i_beta = radians((beta_2_beg - iter_i_beta) * beta_step)
#        print("\rmissile: processing elevation angle down {}".format(iter_i_beta * beta_step), end='')
    
        if tar_trj[i_t0, 4] >= i_beta :
            for i_t in range(i_t0, mtf_len) :
                diff = i_beta - tar_trj[i_t, 4]
                if diff > angle_eps :
                    i_t2 = i_t
                    i_t1 = i_t - 1
                    break
                elif abs(diff) <= angle_eps :
                    i_t2 = i_t1 = i_t
                    break
                else: 
                    pass
                    #i_t += 1 #TODO check if this was legit
        # else here means that more than one beta lies between two consecutive missile trajectory points
        # and calculation below takes the next beta (i_beta) between the same missile trajecoty points i_t1 and i_t2
        
        if i_t1 == i_t2 :
            i_time = tar_trj[i_t1, 0]
            i_rad  = tar_trj[i_t1, 3]
        else :
            rad_1 = tar_trj[i_t1, 3]
            rad_2 = tar_trj[i_t2, 3]
            beta1 = tar_trj[i_t1, 4]
            beta2 = tar_trj[i_t2, 4]
            gamma = atan((rad_2 * cos(beta1 - beta2) - rad_1) / rad_2 / sin(beta1 - beta2))
            i_rad = rad_1 * cos(gamma) / cos(gamma + beta1 - i_beta)
    
            time1 = tar_trj[i_t1, 0]
            time2 = tar_trj[i_t2, 0]
            dr1_q = rad_1*rad_1 + i_rad*i_rad - 2 * rad_1 * i_rad * cos(beta1 - i_beta)
            dr_q  = rad_1*rad_1 + rad_2*rad_2 - 2 * rad_1 * rad_2 * cos(beta1 - beta2)
            i_time = time1 + (time2 - time1) * sqrt(dr1_q/dr_q)
    
        #mis_traj_2 = np.append(mis_traj_2, [[i_time, i_rad, i_beta, i_rad * cos(i_beta), i_rad * sin(i_beta)]], axis=0)
        mis_traj_2[i_mt2] = [i_time, i_rad, i_beta, i_rad * cos(i_beta), i_rad * sin(i_beta)] #opt
        i_mt2 += 1 #opt
        i_t0 = i_t2
    # for    
    
    mis_traj_2 = mis_traj_2[:i_mt2]

    mts2_len = len(mis_traj_2) # missile trajectory sampled part 2 length  # == i_mt2
    if mts2_len != beta_2_beg + 1 - m_beta_end :
        print("Exception in mis_traj_sample: trajectory part 2 array size violation")

    """ See NoteA above
    if mts2_len > 0 :
        i_beta -= radians(beta_step)
        if tar_trj[mtf_len - 1, 4] > i_beta : # negatve angle #TODO < i_beta ???
        
            rad_1 = mis_traj_2[mts2_len - 1, 1]
            rad_2 = tar_trj[mtf_len - 1, 3]
            beta1 = mis_traj_2[mts2_len - 1, 2]
            beta2 = tar_trj[mtf_len - 1, 4]
            gamma = atan((rad_2 * cos(beta1 - beta2) - rad_1) / rad_2 / sin(beta1 - beta2))
            i_rad = rad_1 * cos(gamma) / cos(gamma + beta1 - i_beta)
    
            time1 = mis_traj_2[mts2_len - 1, 0]
            time2 = tar_trj[mtf_len - 1, 0]
            dr1_q = rad_1*rad_1 + i_rad*i_rad - 2 * rad_1 * i_rad * cos(beta1 - i_beta)
            dr_q  = rad_1*rad_1 + rad_2*rad_2 - 2 * rad_1 * rad_2 * cos(beta1 - beta2)
            i_time = time1 + (time2 - time1) * sqrt(dr1_q/dr_q)
    
        mis_traj_2 = np.append(mis_traj_2, [[i_time, i_rad, i_beta,  i_rad * cos(i_beta), i_rad * sin(i_beta)]], axis=0)
    """
    
    """ now combine two parts of the trajectory """
    mis_traj = np.append(mis_traj_1, mis_traj_2, axis=0)
    #print("\nprocessing elevation angles complete, angles from {} to {}".format(degrees(mis_traj[0, 2]), degrees(mis_traj[len(mis_traj)-1, 2])))
    
    return(mis_traj)

""" END of mis_traj_sample"""

def mis_traj_sample(tar_trj, beta_step=set_beta_step) :
    """
    Samples missile trajectory tar_trj over elevation angle from ILP

    Parameters
    ----------
    tar_trj : TYPE
        Missile trajectory shifted and turned
    beta_n : TYPE
        number of bets steps over 90 degrees angle (0 to 90)
    beta_step : TYPE
        size of beta steps in degrees

        s
    -------
    sampled trajectory (time, rad, beta, x, y)

    """

#    amax = np.argmax(tar_trj[:, 4])
#    print(amax,  len(tar_trj), tar_trj[amax])
    
    mis_traj = np.empty([3600, 5]) # 2 times 180 deg by 0.1 deg

    qbeta_beg = int(ceil(degrees(tar_trj[0, 4]) / beta_step)) * beta_step # the earliest quantized beta of the missile

    i_mbeta = 0 # index of the quantized trajectory
    i_tr = 0    # index of the original trajectory
    i_qbeta_upp = qbeta_beg
    i_qbeta_low = qbeta_beg - beta_step
    i_qbup_r = radians(i_qbeta_upp)
    i_qblo_r = radians(i_qbeta_low)
    diff = tar_trj[0, 4] - i_qbup_r
    if abs(diff) < angle_eps :
        i_rad = tar_trj[0, 3]
        mis_traj[i_mbeta] = [tar_trj[0, 0], i_rad, i_qbup_r, i_rad * cos(i_qbup_r), i_rad * sin(i_qbup_r)]
        #i_tr += 1
        i_qbeta_low = i_qbeta_upp
        i_qblo_r = i_qbup_r
        i_qbeta_upp = i_qbeta_upp + beta_step
        i_qbup_r = radians(i_qbeta_upp)
        i_mbeta += 1
        i_tr += 1

    while i_tr < len(tar_trj) - 1  :
        add_point = True
        while True :
            diff_up = tar_trj[i_tr + 1, 4] - i_qbup_r
            diff_lo = tar_trj[i_tr + 1, 4] - i_qblo_r
            #if ((diff_up >= 0) and (diff_lo >= 0)) :# or abs(diff_up) < angle_eps :
            if (diff_up >= 0) :
                i_qbeta_r = i_qbup_r 
                i_tr2 = i_tr + 1
                i_tr1 = i_tr                
                i_qbeta_low = i_qbeta_upp
                i_qblo_r = i_qbup_r
                i_qbeta_upp = i_qbeta_upp + beta_step
                #if abs(diff_up) < angle_eps :
                if diff_up == 0 :
                    i_tr += 1
                i_qbup_r = radians(i_qbeta_upp)
                break
            #elif ((diff_up < 0) and (diff_lo < 0)) :# or abs(diff_lo) < angle_eps :
            elif (diff_lo <= 0) :
                i_qbeta_r = i_qblo_r 
                i_tr2 = i_tr + 1
                i_tr1 = i_tr                
                i_qbeta_upp = i_qbeta_low
                i_qbup_r = i_qblo_r
                i_qbeta_low = i_qbeta_low - beta_step
                #if abs(diff_lo) < angle_eps :
                if diff_lo == 0 :
                    i_tr += 1
                i_qblo_r = radians(i_qbeta_low)
                break
            i_tr += 1
            if i_tr > len(tar_trj) - 2 :
                add_point = False
                break

        if add_point :
            rad_1 = tar_trj[i_tr1, 3]
            rad_2 = tar_trj[i_tr2, 3]
            beta1 = tar_trj[i_tr1, 4]
            beta2 = tar_trj[i_tr2, 4]
            gamma = atan((rad_2 * cos(beta1 - beta2) - rad_1) / rad_2 / sin(beta1 - beta2))

            if abs(beta1 - i_qbeta_r) < angle_eps :
                i_rad  = rad_1
                dr1_q = (rad_1 - i_rad) * (rad_1 - i_rad)
            else :
                i_rad = rad_1 * cos(gamma) / cos(gamma + beta1 - i_qbeta_r)        
                dr1_q = rad_1*rad_1 + i_rad*i_rad - 2 * rad_1 * i_rad * cos(beta1 - i_qbeta_r)

            dr_q  = rad_1*rad_1 + rad_2*rad_2 - 2 * rad_1 * rad_2 * cos(beta1 - beta2)

            time1 = tar_trj[i_tr1, 0]
            time2 = tar_trj[i_tr2, 0]
            i_time = time1 + (time2 - time1) * sqrt(dr1_q/dr_q)
                
            mis_traj[i_mbeta] = [i_time, i_rad, i_qbeta_r, i_rad * cos(i_qbeta_r), i_rad * sin(i_qbeta_r)]
            i_mbeta += 1
            
    mis_traj = mis_traj[:i_mbeta]
        
    return(mis_traj)

""" END of mis_traj_sample"""

import numpy as np
from math import radians, sin, cos, tan,  degrees, sqrt, asin, pi
from cycler import cycler
import matplotlib.pyplot as plt

import balmis as bm   
import rocket_data as rd
import main as m 
import tables_v2b as tb
from fcc_constants import R_e, eps, angle_eps, beta_step, fill_ang, mrl_factor1, mrl_factor2, out_time_freq
import fcc_constants
from os import cpu_count
from multiprocessing import Process, Pipe
import time

shift_min = 1000
#mtype = 7
#itype = 13

global dist_to_trj_min


def fp_point(queue, i_i, f_ang, t_dist, s_func, t_trj, t_itable, h_min, maxia, t_lnc, op_range, det_range, t_delay, h_discr, dist_max, t_acc) :
    """ for multiprocessing version of footprint, >>>not usable because of edits to non-multiproc version<<< """
    f_dist = t_dist
    #print("Footprint angle={:5.1f}".format(f_ang))
#            do_search = False
    f_dist0 = 0
    f_ang_r = radians(f_ang)
#            f_ok = True # since ilp_ok == True
    f_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_dist, op_range, det_range, t_delay, h_discr)
    while f_ok :                
        f_dist0 = f_dist
        if f_dist >= dist_max :
            #   f_a = 999999999
            break
        f_dist *= 2
        f_dist = min(f_dist, dist_max)
        f_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_dist, op_range, det_range, t_delay, h_discr)
    do_search = not f_ok
    f_a = f_dist0
    f_b = f_dist
    while do_search :
        f_x = f_a + (f_b - f_a) / 2
        f_xy = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_x, op_range, det_range, t_delay, h_discr)
        if f_xy :
            f_a = f_x
            f_y_keep = f_xy
        else :
            f_b = f_x
        if ((f_b - f_a) < f_b * t_acc) or ((f_b - f_a) < 10) :
            #print("\nf_a = {:.2f} km f_b = {:.2f} km f_b - f_a = {:.2f} km".format((f_a)/1000,(f_b)/1000, (f_b - f_a)/1000))
            break

    if f_a == 0 :
        f_a = f_b
# TODO $$$ !!! this was f_a < dist_max                
    if f_a <= dist_max : # footprint outer edge is NOT farther than max (i.e. missile range)
        # old planar
        # ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, -f_a * sin(f_ang_r) / 1000, f_a * cos(f_ang_r) / 1000]], axis=0)
        if abs(f_ang) <= angle_eps :
            x1 = 0
            y1 = f_a / 1000
        elif abs(f_ang - 180) <= angle_eps :
            x1 = 0
            y1 = -f_a / 1000
        else :
            f_delta = f_a / R_e
            f_delta_x = asin(sin(f_ang_r) * sin(f_delta))
            if f_delta > pi/2 :
                if f_ang_r < pi/2 :
                    f_delta_y = pi - asin(tan(f_delta_x) / tan(f_ang_r))
                else :
                    f_delta_y = -pi - asin(tan(f_delta_x) / tan(f_ang_r))                            
            else :
                f_delta_y = asin(tan(f_delta_x) / tan(f_ang_r))
            x1 = - f_delta_x * R_e / 1000
            y1 =   f_delta_y * R_e / 1000
            
    #queue.put([i_i, [f_ang, f_a, f_b - f_a, x1, y1]])
    queue.send([i_i, [f_ang, f_a, f_b - f_a, x1, y1]])
""" End of fp_point """

#@profile
def footprint_calc_v2_m(s_func,
                      t_trj,
                      t_itable,
                      h_min, 
                      maxia,
                      t_lnc,
                      t_angle_step,
                      op_range,
                      det_range,
                      t_delay = 5,
                      h_discr = 0,
                      t_acc   = .01,
                      t_dist  = 100000,
                      plot_hit_charts = False,
                      hit_chart_angle = 180,
                      m_type = 0,
                      i_type = 0) : # i_type for debug charts
    """
    Multiprocessor version of v2, >>>not usable because of edits to non-multiproc version<<<
    Calculates footprint as array of polar coordinates: angle from the ILP-MLP ray, distance from ILP

    Parameters
    ----------
    trj : array of [time, R, alfa]
        missile trajectory in polar coords, center in Earth center
    t_itable : array of trajectories
        sampled interception table (array)
    h_min :
        min acceptable height of interception
    t_lnc : TYPE
        earliest possible interceptor launch time counted from missile launch (mis burn time + int launch delay)
    t_angle_step : TYPE
        footprint direction angle step, >>> degrees <<<
    det_range :
        detection range
    t_delay : TYPE, optional
        identification, tracking, and launch delay ('0' means criterium not used)
    h_discr : TYPE, optional
        warhead discrimination height (for terminal phase defense)
    t_acc : TYPE, optional
        accuracy. The default is .01.
    t_dist : TYPE, optional -- irrelevant as of 230216
        start value for dist search. The default is 100000.


    Returns
    -------
    Footprint data array: [angle, distance, accuracy, x, y]

    """
    #int_max_range = max([int_traj[len(int_traj) - 1][2] for int_traj in t_itable if np.any(int_traj)])
    # this is in fact max r rather than max range
    beta_min = t_itable[0][0, 3] - radians(beta_step)
    int_max_range = -2 * beta_min * R_e
    #print("beta_min={:.2f}, int_max_range={:.1f} km".format(degrees(beta_min), int_max_range/1000))

    dist_max = t_trj[len(t_trj) - 1, 2] * R_e - 1000
    #dist_max = min(dist_max, 9999000)
    #dist_max = 15000000
    max_reach = max(int_max_range, dist_max)

    #print("Footprint calculation: \nh_min={:.2f} km, t_lnc={:.2f} s, beta_step={:.2f} grad, op_range, det_range={:.2f} km,\nt_delay={:.2f}, h_discr={} km, accuracy={:.2f}".format(h_min/1000, t_lnc, t_angle_step, op_range, det_range/1000, t_delay, h_discr/1000, t_acc))

    """ see lines 91-95 (if f_ang < 90) """
    if t_dist > dist_max :
        t_dist = dist_max
        
    t_dist = dist_max # larger shape in case it's irregular
    #t_dist = 143000 # debug value for m3i11

#        print("\n>>> footprint_calc exception: dist = {:.0f} km >= missile range = {:.0f} km<<<".format(t_dist/1000, dist_max/1000))
#        return False
    """ First, check if interceptor launch point is defendable """
    print("Interceptor launch point defense check...", end='')
    ilp_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, 0, 0, op_range, det_range, t_delay, h_discr)
    #ilp_ok = True
    
    if ilp_ok :
        print("Ok.")
    
        #f_dist = t_dist
        #t_angle_step = 0.01
        f_ang = 180 # = 180
        
        f_ang_n = int(180 / t_angle_step) + 1
        ftprint = np.empty([f_ang_n, 5]) # angle in grad and distance in meters
        n_cores = cpu_count()        
        batch_size = 999 #n_cores
        #print("f_ang_n = {:d}, n_cores = {:d}".format(f_ang_n, n_cores))
        # execute in batches
        """ Pipe version """
        for i in range(0, f_ang_n, batch_size) :
            processes = []
            pipe_list = []
            i_end = i + batch_size
            if i_end > f_ang_n : i_end = f_ang_n
            print("\rProcessing {:.2f}%".format(i_end / f_ang_n * 100), end='')
            for j in range(i, i_end) :
                recv_end, send_end = Pipe(False)
                f_ang = 180 - j * t_angle_step
                if f_ang < 0 : f_ang = 0
                if f_ang < 90 :
                    dist_max = max_reach # for f_ang < 90 interceptor can reach further than m_range if int_max_range > mrange
                    if t_dist > dist_max :
                        t_dist = dist_max
                    t_dist = dist_max # larger shape in case it's irregular
                
                #fp_point(queue, i_i, f_ang, t_dist, s_func, t_trj, t_itable, h_min, maxia, t_lnc, op_range, det_range, t_delay, h_discr, dist_max, t_acc)
                p = Process(target=fp_point, args=(send_end, j, f_ang, t_dist, s_func, t_trj, t_itable, h_min, maxia, t_lnc, op_range, det_range, t_delay, h_discr, dist_max, t_acc))
                processes.append(p)
                pipe_list.append(recv_end)
                p.start()

            for p in processes:
                p.join()
            #print("\n2")
            result_list = [x.recv() for x in pipe_list]
            
            for j in range(len(result_list)) :
                #print("i={} psi={}".format(rets[j][0], rets[j][1][0]))
                ftprint[result_list[j][0]] = result_list[j][1]

        
        
        
        """ Queue version
        for i in range(0, f_ang_n, batch_size) :
            q = SimpleQueue()
            processes = []
            rets = []
            i_end = i + batch_size
            if i_end > f_ang_n : i_end = f_ang_n
            print("\rProcessing {:.2f}%".format(i_end / f_ang_n * 100), end='')
            for j in range(i, i_end) :
                f_ang = 180 - j * t_angle_step
                if f_ang < 0 : f_ang = 0
                if f_ang < 90 :
                    dist_max = max_reach # for f_ang < 90 interceptor can reach further than m_range if int_max_range > mrange
                    if t_dist > dist_max :
                        t_dist = dist_max
                    t_dist = dist_max # larger shape in case it's irregular
                
                #fp_point(queue, i_i, f_ang, t_dist, s_func, t_trj, t_itable, h_min, t_lnc, op_range, det_range, t_delay, h_discr, dist_max, t_acc)
                p = Process(target=fp_point, args=(q, j, f_ang, t_dist, s_func, t_trj, t_itable, h_min, t_lnc, op_range, det_range, t_delay, h_discr, dist_max, t_acc))
                processes.append(p)
                p.start()

            for p in processes:
                ret = q.get() # will block
                rets.append(ret)
            #print("\n1")
            for p in processes:
                p.join()
            #print("\n2")
            for j in range(len(rets)) :
                #print("i={} psi={}".format(rets[j][0], rets[j][1][0]))
                ftprint[rets[j][0]] = rets[j][1]
        """
        
        print("\rFootprint calculation complete.")
        # Now mirror the half-footprint into a full one
        len_ftprint = len(ftprint)
        if len_ftprint > 0 :   
            for i_f in range (len_ftprint - 1) :
                ftprint_if = ftprint[len_ftprint - 2 - i_f]
                ftprint = np.append(ftprint, [ftprint_if], axis=0)
                ftprint[len_ftprint + i_f, 0] = 360 - ftprint_if[0]
                ftprint[len_ftprint + i_f, 3] = - ftprint_if[3]
            return ftprint        
        else :
            print("Footprint not calculated, check input data")
            return False
        
    else:
        print("Interceptor undefendable")
        return False

""" End of multiprocessed footprint_calc_v2 """
#@profile
def footprint_calc_v2(s_func,
                      t_trj,
                      t_itable,
                      h_min, 
                      maxia,
                      t_lnc,
                      t_angle_step,
                      op_range,
                      det_range,
                      t_delay = 5,
                      h_discr = 0,
                      t_acc   = .01,
                      t_dist  = 100000,
                      plot_hit_charts = False,
                      hit_chart_angle = 180,
                      m_type = 0,
                      i_type = 0) : # i_type for debug charts
    """
    Calculates footprint as array of polar coordinates: angle from the ILP-MLP ray, distance from ILP
    For mod2 version see short_search module.

    Parameters
    ----------
    trj : array of [time, R, alfa]
        missile trajectory in polar coords, center in Earth center
    t_itable : array of trajectories
        sampled interception table (array)
    h_min :
        min acceptable height of interception
    t_lnc : TYPE
        earliest possible interceptor launch time counted from missile launch (mis burn time + int launch delay)
    t_angle_step : TYPE
        footprint direction angle step, >>> degrees <<<
    det_range :
        detection range
    t_delay : TYPE, optional
        identification, tracking, and launch delay ('0' means criterium not used)
    h_discr : TYPE, optional
        warhead discrimination height (for terminal phase defense)
    t_acc : TYPE, optional
        accuracy. The default is .01.
    t_dist : TYPE, optional -- irrelevant as of 230216
        start value for dist search. The default is 100000.


    Returns
    -------
    Footprint data array: [angle, distance, accuracy, x, y]

    """
    #int_max_range = max([int_traj[len(int_traj) - 1][2] for int_traj in t_itable if np.any(int_traj)])
    # this is in fact max r rather than max range
    
    beta_min = t_itable[0][0, 3] - radians(beta_step)
    int_max_range = -2 * beta_min * R_e
    print("beta_min={:.2f}, int_max_range={:.1f} km".format(degrees(beta_min), int_max_range/1000))

    mrange = t_trj[len(t_trj) - 1, 2] * R_e 
    dist_max = mrange - shift_min
    #dist_max = min(dist_max, 9999000)
    #dist_max = 15000000
    max_reach = max(int_max_range, dist_max)

    #print("Footprint calculation: \nh_min={:.2f} km, t_lnc={:.2f} s, beta_step={:.2f} grad, op_range, det_range={:.2f} km,\nt_delay={:.2f}, h_discr={} km, accuracy={:.2f}".format(h_min/1000, t_lnc, t_angle_step, op_range, det_range/1000, t_delay, h_discr/1000, t_acc))

    """ see 5 ines below starting with (if f_ang < 90) """
    #if t_dist > dist_max :
    #    t_dist = dist_max
        
    t_dist = dist_max # larger shape in case it's irregular
    #t_dist = 143000 # debug value for m3i11

#        print("\n>>> footprint_calc exception: dist = {:.0f} km >= missile range = {:.0f} km<<<".format(t_dist/1000, dist_max/1000))
#        return False
    """ First, check if interceptor launch point is defendable """
    print("Interceptor launch point defense check...", end='')
    ilp_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, 0, 0, op_range, det_range, t_delay, h_discr)
    #ilp_ok = True

    stfp = time.process_time()
    
    if ilp_ok :
        print("Ok.")
        ftprint = np.empty([0, 5]) # angle in grad and distance in meters
    
        #f_dist = t_dist
        #t_angle_step = 0.01
        f_ang = 180 # = 180
        max_dist_line = False
        while f_ang >= 0 : # >= 0
            if f_ang < 90 :
                dist_max = max_reach # for f_ang < 90 interceptor can reach further than m_range if int_max_range > mrange
                #if t_dist > dist_max :
                #    t_dist = dist_max
                t_dist = dist_max # larger shape in case it's irregular
            
            enfp = time.process_time()
            dufp = enfp - stfp
            if dufp >= out_time_freq :
                print("\rFootprint angle={:5.1f} ".format(f_ang), end='')
                stfp = enfp

            f_dist = t_dist
            #print("\rFootprint angle={:5.1f} ".format(f_ang), end='')
#            do_search = False
            f_dist0 = 0
            f_ang_r = radians(f_ang)
#            f_ok = True # since ilp_ok == True
            f_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_dist, op_range, det_range, t_delay, h_discr)
            while f_ok :                
                f_dist0 = f_dist
                if f_dist >= dist_max :
                    #   f_a = 999999999
                    break
                f_dist *= 2
                f_dist = min(f_dist, dist_max)
                f_ok = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_dist, op_range, det_range, t_delay, h_discr)
            do_search = not f_ok
            f_a = f_dist0
            f_b = f_dist
            while do_search :
                f_x = f_a + (f_b - f_a) / 2
                f_xy = s_func(t_trj, t_itable, h_min, maxia, t_lnc, f_ang_r, f_x, op_range, det_range, t_delay, h_discr)
                if f_xy :
                    f_a = f_x
                    f_y_keep = f_xy
                else :
                    f_b = f_x
                if ((f_b - f_a) < f_b * t_acc) or ((f_b - f_a) < 10) :
                    #print("\nangle={} f_a = {:.2f} km f_b = {:.2f} km f_b - f_a = {:.2f} km".format(f_ang, (f_a)/1000,(f_b)/1000, (f_b - f_a)/1000))
                    break

            if f_a == 0 :
                f_a = f_b
# TODO $$$ !!! this was f_a < dist_max    -- done?
            if f_ang >= 90 :
                if f_a < dist_max : # footprint outer edge is NOT farther than max (i.e. missile range)
                    max_dist_line = False
                    # spherical coords to plane
                    ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, -f_a * sin(f_ang_r) / 1000, f_a * cos(f_ang_r) / 1000]], axis=0)
                    """
                    if abs(f_ang) <= angle_eps :
                        x1 = 0
                        y1 = f_a / 1000
                    elif abs(f_ang - 180) <= angle_eps :
                        x1 = 0
                        y1 = -f_a / 1000
                    else :
                        f_delta = f_a / R_e
                        f_delta_x = asin(sin(f_ang_r) * sin(f_delta))
                        if f_delta > pi/2 :
                            if f_ang_r < pi/2 :
                                f_delta_y = pi - asin(tan(f_delta_x) / tan(f_ang_r))
                            else :
                                f_delta_y = -pi - asin(tan(f_delta_x) / tan(f_ang_r))                            
                        else :
                            f_delta_y = asin(tan(f_delta_x) / tan(f_ang_r))
                        x1 = - f_delta_x * R_e / 1000
                        y1 =   f_delta_y * R_e / 1000
                        
                    ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, x1, y1]], axis=0)
                    """
# plot hit lines were here
                elif (f_a == dist_max) :
                    if max_dist_line : # i.e. previous point is the same, so we can insert the zigzag
                        f_ang_z = f_ang + t_angle_step/2
                        f_ang_z_r = radians(f_ang_z)
                        ftprint = np.append(ftprint, [[f_ang_z, f_a * mrl_factor2, f_b - f_a, -f_a * sin(f_ang_z_r) / 1000 * mrl_factor2, f_a * cos(f_ang_z_r) / 1000 * mrl_factor2]], axis=0)
                    else :
                        max_dist_line = True # i.e. this is the first point at max range
                    #ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, -f_a * sin(f_ang_r) / 1000, f_a * cos(f_ang_r) / 1000]], axis=0)
                    ftprint = np.append(ftprint, [[f_ang, f_a * mrl_factor1, f_b - f_a, -f_a * sin(f_ang_r) / 1000 * mrl_factor1, f_a * cos(f_ang_r) / 1000 * mrl_factor1]], axis=0)
                else :
                    print("Impossible f_a > dist_max")
            else : # f_ang < 90
                if abs(f_ang_r) < angle_eps :
                    sin_omega = 0
                    perp_dist_b = 0 # TODO need to define perp_dist_b more accurately and remove sin_omega
                else :
                    #sin_omega = sin(f_ang_r) * sin(f_a/R_e) / sin(mrange/R_e) # mrange/R_e cannot be == 0 due to f_ang < 90
                    #f_omega = degrees(asin(sin_omega))
                    #perp_dist = asin(sin(f_a/R_e) * sin(f_ang_r)) * R_e
                    perp_dist_b = asin(sin(f_b/R_e) * sin(f_ang_r)) * R_e
                    #print("f_omega = {:.3f} deg, perp_dist = {:.3f} m, perp_dist_b = {:.3f} m, x = {:.3f} m".format(f_omega, perp_dist, perp_dist_b, f_a * sin(f_ang_r)))
                if perp_dist_b > mrange :
                    if max_dist_line : # i.e. previous point is the same, so we can insert the zigzag
                        f_ang_z = f_ang + t_angle_step/2
                        f_ang_z_r = radians(f_ang_z)
                        ftprint = np.append(ftprint, [[f_ang_z, f_a * mrl_factor2, f_b - f_a, -f_a * sin(f_ang_z_r) / 1000 * mrl_factor2, f_a * cos(f_ang_z_r) / 1000 * mrl_factor2]], axis=0)
                    else :
                        max_dist_line = True # i.e. this is the first point at max range
                    #ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, -f_a * sin(f_ang_r) / 1000, f_a * cos(f_ang_r) / 1000]], axis=0)
                    ftprint = np.append(ftprint, [[f_ang, f_a * mrl_factor1, f_b - f_a, -f_a * sin(f_ang_r) / 1000 * mrl_factor1, f_a * cos(f_ang_r) / 1000 * mrl_factor1]], axis=0)
                else :
                    max_dist_line = False
                    ftprint = np.append(ftprint, [[f_ang, f_a, f_b - f_a, -f_a * sin(f_ang_r) / 1000, f_a * cos(f_ang_r) / 1000]], axis=0)                    

# plot hit lines moved here from above            
            if plot_hit_charts and i_type :
                if f_a == dist_max :
                    #if f_ok : 
                    plot_hit(f_ok, t_trj, m_type, i_type, f_ang, f_a, int_max_range/1000, op_range, det_range, t_lnc - t_delay, h_min/1000, h_discr/1000)
                else :
                    pass
                    #if f_y_keep : 
                    plot_hit(f_y_keep, t_trj, m_type, i_type, f_ang, f_a, int_max_range/1000, op_range, det_range, t_lnc - t_delay, h_min/1000, h_discr/1000)

            if (f_ang > 0) and ((f_ang - t_angle_step) < 0) :
                f_ang = 0
            else :
                f_ang -= t_angle_step

        print("\rFootprint calculation complete.")

        if fill_ang :
            len_ftprint = len(ftprint)
            if len_ftprint > 0 :
                fp_fill = np.empty([0, 5])
                fp_fill = np.append(fp_fill, [ftprint[0]], axis=0)
                for i_f in range(len_ftprint - 1) :
                    fl_angle = ftprint[i_f][0] - fill_ang
                    while fl_angle > ftprint[i_f + 1][0] :
                        fl_dist = ftprint[i_f][1] + (ftprint[i_f + 1][1] - ftprint[i_f][1]) / (ftprint[i_f + 1][0] - ftprint[i_f][0]) * (fl_angle - ftprint[i_f][0])
                        fl_angle_r = radians(fl_angle)
                        fp_fill = np.append(fp_fill, [[fl_angle, fl_dist, 1,  -fl_dist * sin(fl_angle_r) / 1000, fl_dist * cos(fl_angle_r) / 1000]], axis=0)
                        fl_angle -= fill_ang
                    fp_fill = np.append(fp_fill, [ftprint[i_f + 1]], axis=0)
                ftprint = fp_fill
        
        # Now mirror the half-footprint into a full one
        len_ftprint = len(ftprint)
        if len_ftprint > 0 :   
            for i_f in range (len_ftprint - 1) :
                ftprint_if = ftprint[len_ftprint - 2 - i_f]
                ftprint = np.append(ftprint, [ftprint_if], axis=0)
                ftprint[len_ftprint + i_f, 0] = 360 - ftprint_if[0]
                ftprint[len_ftprint + i_f, 3] = - ftprint_if[3]
            return ftprint        
        else :
            print("Footprint not calculated, check input data")
            return False
        
        """ v.0 -- valid for when FP recorded from 0 to 180 
        if len_ftprint == int(180 / t_angle_step) + 1 :
            for i_f in range(1, len_ftprint) :
                ftprint_if = ftprint[len_ftprint - 1 - i_f]
                ftprint = np.append(ftprint, [ftprint_if], axis=0)
                ftprint[len_ftprint - 1 + i_f, 0] = 360 - ftprint_if[0]
                if i_f < len_ftprint - 1 :
                    ftprint[len_ftprint - 1 + i_f, 3] = - ftprint_if[3]
            return ftprint
        elif len_ftprint > 0 :
            for i_f in range(1, len_ftprint) :
                ftprint_if = ftprint[len_ftprint - 1]
                ftprint = np.insert(ftprint, i_f - 1, [ftprint_if], axis=0)
                ftprint[i_f - 1, 0] = 360 - ftprint_if[0]
                ftprint[i_f - 1, 3] = - ftprint_if[3]
            return ftprint
        else :
            print("Footprint not calculated, check input data")
            return False
         end of v.0 """
    else:
        print("Interceptor launch point undefendable")
        return False

""" End of original footprint_calc_v2 """

#@profile
def fp_chart(footprint, info_string, title_string, f_name) :

    xpoints = footprint[:, 3]
    ypoints = footprint[:, 4]
    
    plt.figure(dpi=300)
    plt.plot(xpoints, ypoints)
    
    plt.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
    #plt.text(0.5, 0.5, '0', fontsize='x-large')
    
#    font1 = {'family':'monospace','color':'blue','size':20}
#    font2 = {'family':'serif','color':'darkred','size':15}
    
    plt.suptitle(title_string, fontsize=16, y=1)
    plt.title(info_string,fontsize=12)
    
    #plt.title("Footprint", fontdict = font1)
    #plt.xlabel("Average Pulse", fontdict = font2)
    #plt.ylabel("Calorie Burnage", fontdict = font2)
        
    #ax = plt.gca()
    #ax.set_aspect('equal', adjustable='datalim')
    plt.axis('equal')
    plt.grid()

    plt.savefig(f_name, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.show()
    
    print("Footprint chart saved to " + f_name)
    
    return True
    
def fp_chart_2(ftprint_1, ftprint_2, info_string_1, info_string_2, title_string, f_name) :
    
    xpoints1 = ftprint_1[:, 3]
    ypoints1 = ftprint_1[:, 4]
    xpoints2 = ftprint_2[:, 3]
    ypoints2 = ftprint_2[:, 4]
    
      
    plt.figure(dpi=300)
    plt.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
    #plt.text(5, 0, '0', fontsize='x-large')

    plt.plot(xpoints1, ypoints1, ls='--', c='b', label='Shoot Once')
    plt.plot(xpoints2, ypoints2, c='r', label='Shoot-Look-Shoot')
    plt.legend(loc='best', frameon=False, framealpha=1.0)
    
#    font1 = {'family':'monospace','color':'blue','size':20}
#    font2 = {'family':'serif','color':'darkred','size':15}
    
    plt.suptitle(title_string, fontsize=16, y=1.04)
    plt.title(info_string_1 + '\n' + info_string_2,fontsize=10)
    
    #plt.title("Footprint", fontdict = font1)
    #plt.xlabel("Average Pulse", fontdict = font2)
    #plt.ylabel("Calorie Burnage", fontdict = font2)
        
    #ax = plt.gca()
    #ax.set_aspect('equal', adjustable='datalim')
    plt.axis('equal')
    plt.grid()

    plt.savefig(f_name, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.show()
    
    print("Chart saved to " + f_name)
    
    return True
    
def fp_sector_chart(fp_sector, info_string, title_string, f_name) :
    
    xpoints1 = fp_sector[:, 0]
    ypoints1 = fp_sector[:, 1]
    
      
    plt.figure(dpi=300)
    plt.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
    #plt.text(-10, 0, '0', fontsize='x-large')

    plt.scatter(xpoints1, ypoints1, color='g', s=15, alpha=1)
    #plt.scatter(xpoints1, ypoints1, color='green', s=15, alpha=1)
    #plt.plot(xpoints1, ypoints1, ls='--', c='b', label='Shoot Once')
    #plt.legend(loc='best', frameon=False, framealpha=1.0)
    
#    font1 = {'family':'monospace','color':'blue','size':20}
#    font2 = {'family':'serif','color':'darkred','size':15}
    
    plt.suptitle(title_string, fontsize=16, y=1.04)
    plt.title(info_string, fontsize=10)
    
    #plt.title("Footprint", fontdict = font1)
    #plt.xlabel("Average Pulse", fontdict = font2)
    #plt.ylabel("Calorie Burnage", fontdict = font2)
        
    #ax = plt.gca()
    #ax.set_aspect('equal', adjustable='datalim')
    plt.axis('equal')
    plt.grid()

    plt.savefig(f_name, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.show()
    
    print("Chart saved to " + f_name)
    
    return True
    
    
def fp_chart_n__not_used(ftprint_arr, label_arr, info_string, title_string, f_name, bw=False) :
    
    plt.figure(dpi=300)
    if bw :
        linestyle_cycler = cycler('linestyle',['-','--',':','-.'])
    else : 
        linestyle_cycler = cycler('color', ['r', 'g', 'b']) +\
                       cycler('linestyle', ['-', '--', ':', '-.'])
    plt.rc('axes', prop_cycle=linestyle_cycler)
    plt.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')

    n_arr = len(ftprint_arr)
    for i_arr in range(n_arr) :
        xpoints = ftprint_arr[i_arr][:, 3]
        ypoints = ftprint_arr[i_arr][:, 4]
        plt.plot(xpoints, ypoints, label = label_arr[i_arr])
        
    plt.legend(loc='best', frameon=False, framealpha=1.0)
    
#    font1 = {'family':'monospace','color':'blue','size':20}
#    font2 = {'family':'serif','color':'darkred','size':15}
    
    plt.suptitle(title_string, fontsize=16, y=1.04)
    plt.title(info_string, fontsize=10)
    
    #plt.title("Footprint", fontdict = font1)
    #plt.xlabel("Average Pulse", fontdict = font2)
    #plt.ylabel("Calorie Burnage", fontdict = font2)
        
    #ax = plt.gca()
    #ax.set_aspect('equal', adjustable='datalim')
    plt.axis('equal')
    plt.grid()

    plt.savefig(f_name, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.show()
    
    print("Chart saved to " + f_name)
    

def plot_hit(hit_info,
             trj_0,
             m_type,
             i_type,
             d_angle,
             dist,
             int_max_range_km,
             op_range,
             det_range,
             burn_time,
             min_int_alt_km=0,
             h_discr_km=0,
             mode2 = False,
             rd_fname='rocket_data.json',
             chart_fname='charts/hit_chart.png') :
    
    def get_hit_data(i_type, psi, i_lnc_time, rd_fname) :
        
        interceptor_data = rd.interceptor(i_type, rd_fname)
        interceptor_data["flight_path_angle"] = 90 - psi
        int_traj = bm.balmisflight(interceptor_data, True, False)
        """
        if interceptor_data['traj_type'] == "int_endo" :
            launcher_length = 20 # launcher length
        else :
            launcher_length = 0
        """
        irad = np.copy(int_traj[:, 1])
        ibeta = int_traj[:, 2]

        for i in range(len(irad)) :
            z_rad = irad[i]
            z_ang = ibeta[i]
            #i_rad = sqrt(R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang))
            if abs(z_ang) < angle_eps :
                i_rad = z_rad - R_e
            else :
                i_rad2 = R_e*R_e + z_rad*z_rad - 2 * R_e * z_rad * cos(z_ang)
                i_rad = sqrt(i_rad2)

            if abs(z_ang) < angle_eps :
                if interceptor_data["traj_type"] == "int_exo" :
                    i_ang = pi/2
                else :
                    i_ang = radians(90 - hit_i[0])
            else :
                i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
            """
            if i_rad <= launcher_length :
                i_ang = radians(90 - hit_i[0])
            else :
#                print("z_rad={} i_rad={} cos(z_ang)={}".format(z_rad, i_rad, cos(z_ang)))
                i_ang = asin((z_rad * cos(z_ang) - R_e) / i_rad)
            """ 
            irad[i] = i_rad
            ibeta[i] = degrees(i_ang)
    
        irad = irad / 1000
        itime = int_traj[:, 0]
        itime += i_lnc_time
        
        ialti = int_traj[:, 1]
        ialti = ialti - R_e
        ialti = ialti / 1000

        return itime, irad, ibeta, ialti
        
    hit_i, hit_m, hit_i1, hit_i2 = hit_info
    """
    print("\npsi ={:.2f}, itime ={:.2f}, irad ={:.2f}, ibeta ={:.2f}".format(hit_i[0], hit_i[1], hit_i[2]/1000, degrees(hit_i[3])))
    print("            mtime={:.2f}, mrad ={:.2f}, mbeta ={:.2f}".format(hit_m[0], hit_m[1]/1000, degrees(hit_m[2])))
    print("psi1={:.2f}, itime1={:.2f}, irad1={:.2f}, ibeta1={:.2f}".format(hit_i1[0], hit_i1[1], hit_i1[2]/1000, degrees(hit_i1[3])))
    print("psi2={:.2f}, itime2={:.2f}, irad2={:.2f}, ibeta2={:.2f}".format(hit_i2[0], hit_i2[1], hit_i2[2]/1000, degrees(hit_i2[3])))
    """
    i_lnc_time = hit_m[0] - hit_i[1]
    #print("ok2")
    itime,  irad,  ibeta,  ialti  = get_hit_data(i_type,  hit_i[0], i_lnc_time, rd_fname)
    #itime1, irad1, ibeta1, ialti1 = get_hit_data(i_type, hit_i1[0], i_lnc_time, rd_fname)
    #itime2, irad2, ibeta2, ialti2 = get_hit_data(i_type, hit_i2[0], i_lnc_time, rd_fname)

    if not mode2 :    
        tar_trj = bm.trj_from_center(trj_0, R_e, radians(d_angle), dist) # tar_trj elements contain: time, R, alfa_r, r, beta_r, x, y
    else :
        tar_trj = bm.trj_shift_turn(trj_0, R_e, dist, radians(d_angle)) # in mode2: dist_opt is shift, fi_opt is omega
    #hit = [psi_hit, t_hit_i, r_hit, beta_hit, psi1, i1t, r1, psi2, i2t, r2], [t_hit_m, r_hit, beta_hit, r_hit * cos(beta_hit), r_hit * sin(beta_hit)]
    mis_traj = tb.mis_traj_sample(tar_trj)
    
    m_range_km = trj_0[len(trj_0) - 1, 2] * R_e / 1000
    m_flight_time = trj_0[len(trj_0) - 1, 0]
    
    m_beta_launch = tar_trj[0, 4]
    m_beta_land = tar_trj[len(tar_trj) - 1, 4]
    m_beta_min = degrees(min(m_beta_launch, m_beta_land))

    rad  = tar_trj[:, 3]
    rad  = rad / 1000
    beta = tar_trj[:, 4]
    for i in range(len(beta)) :
        beta[i] = degrees(beta[i])
    time = tar_trj[:, 0]
    alti = trj_0[:, 1]
    alti = alti - R_e
    alti = alti / 1000
    
    mtime = mis_traj[:, 0]
    mrad  = mis_traj[:, 1]
    mbeta = mis_traj[:, 2]
    mrad  = mrad / 1000
    for i in range(len(mbeta)) :
        mbeta[i] = degrees(mbeta[i])
    
    
    #it = 714
    #print("itime[{0}]={1:.2f}, irad[{0}]={2:.2f}, ibeta[{0}]={3:.2f}".format(it, itime[it], irad[it], ibeta[it]))

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax12 = ax1.twinx()
 

    ax1.plot(time, beta, c='blue', linestyle='-', label='m_beta')
    ax1.plot(itime, ibeta, c='green', linestyle='-', linewidth=.75, label='i_beta')
    #ax1.plot(itime1, ibeta1, c='g', linewidth=.5, linestyle=':', label='i_beta1')
    #ax1.plot(itime2, ibeta2, c='g', linewidth=.5, linestyle='-.', label='i_beta2')
    #ax1.plot(mtime, mbeta, c='b', linewidth=.75, linestyle='--', label='ms_beta')
    ax1.plot(0, 0, marker=2, ms=5, mfc='k', mec='k') 

    ax12.plot(time,   rad, c='blue', linestyle='--', label='m_rad')
    ax12.plot(itime, irad, c='green', linestyle='--', linewidth=.75, label='i_rad')
    #ax12.plot(itime1, irad1, c='m', linewidth=.5, linestyle=':', label='i_rad1')
    #ax12.plot(itime2, irad2, c='m', linewidth=.5, linestyle='-.', label='i_rad2')
    #ax12.plot(mtime, mrad, c='r', linewidth=.75, linestyle='--', label='ms_rad')
    ax12.plot(time, alti, c='blue', linestyle='-.', label='m_alti')
    ax12.plot(itime, ialti, c='green', linestyle='-.', linewidth=.75, label='i_alti')


    ax1.axvline(x = hit_m[0], color = 'purple', linewidth=1, linestyle=':', label = 'interception time {:.2f}'.format(hit_m[0]))
    ax1.axvline(x = i_lnc_time, color = 'orange', linewidth=1, linestyle=':', label = 'interceptor launch time {:.2f}'.format(i_lnc_time))
    ax1.axvline(x = burn_time, color = 'red', linewidth=1, linestyle=':', label = 'missile burn time={}'.format(burn_time))
    ax1.axhline(y = 0, c = 'red', xmin = .0, xmax = 1., linewidth = 1, linestyle='-', label = 'horizon (beta=0)')
    ax12.axhline(y = det_range/1000, c = 'red', xmin = 0, xmax = 1, linewidth = 1, linestyle='--', label = 'det_range={:.0f}'.format(det_range/1000))
    if min_int_alt_km :
        ax12.axhline(y = min_int_alt_km, c = 'red', xmin = 0, xmax = 1, linewidth = 1, linestyle='-.', label = 'min_int_alt={:.0f}'.format(min_int_alt_km))
    if h_discr_km :
        ax12.axhline(y = h_discr_km, c = 'brown', xmin = 0, xmax = 1, linewidth = 1, linestyle= (0, (3, 2, 1, 2, 1, 2)), label = 'h_discr={:.0f}'.format(h_discr_km))
    if op_range :
        ax12.axhline(y = op_range/1000, c = 'black', xmin = 0, xmax = 1, linewidth = 1, linestyle= (0, (3, 5, 1, 5, 1, 5)), label = 'op_range={:.0f}'.format(op_range/1000))

    ax1.legend(loc=2, frameon=False, framealpha=1.0)
    ax12.legend(loc=1, frameon=False, framealpha=1.0)
    ax12.set_ylim([0, max(int_max_range_km, m_range_km)])
    ax1.set_ylim([m_beta_min - 10, 95])
    ax1.set_xlim([-50, m_flight_time * 1.1])
    
    ax1.set_xlabel('Time from missile launch, s')
    ax1.set_ylabel('Elevation angle from ILP, degrees')
    ax12.set_ylabel('Distance, km')

    if not mode2 :    
        ax1.set_title("Interception Chart (beta and rad vs time)\n mtype={} itype={} angle={:.1f} dist={:.1f} psi={:.2f}".format(m_type, i_type, d_angle, dist/1000, hit_i[0]), va='bottom')
    else :
        ax1.set_title("Interception Chart (beta and rad vs time)\n mtype={} itype={} angle={:.1f} shift={:.1f} psi={:.2f}".format(m_type, i_type, d_angle, dist/1000, hit_i[0]), va='bottom')
    #ax1.grid()
    
    m.keep_old_file(chart_fname)
    #print("ok1")
    fig.savefig(chart_fname, dpi=300, bbox_inches='tight', pad_inches=0.2)
    plt.close()
    
"""End of plot_hit() """
    
def plot_hit2(hit_info,
             trj_0,
             m_type,
             i_type,
             omega,
             shift,
             int_max_range_km,
             op_range,
             det_range,
             burn_time,
             min_int_alt_km=0,
             h_discr_km=0,
             rd_fname='rocket_data.json',
             chart_fname='charts/hit_chart.png') :

    plot_hit(hit_info,
             trj_0,
             m_type,
             i_type,
             omega,
             shift,
             int_max_range_km,
             op_range,
             det_range,
             burn_time,
             min_int_alt_km,
             h_discr_km,
             True,
             rd_fname,
             chart_fname)

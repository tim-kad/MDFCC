bm_range_limit = 19000000 # 19 000 km is the limit for the ballistic missile range 
dist_limit = 20000000     # 20 000 km is the limit for the distance from MLP to ILP  (half of the Earth circumference length)
R_N = 1. # see also formulas with mu/ in balmis
R_e0 = 6.37e6
R_e = R_N * R_e0

sat_delay = 30
no_atmosphere = False

int_vl_height = 100.0 # vertical launch altitude for interceptors
#int_vl_height_2 = 15000.0 # for interceptor i33 (hardcoded)
int_vl_top = 25000.0
op_range = 200000.0
control_turn = 0 # time constant for controlled turn of interceptor after launch to flight path angle

eps = 0.00001
angle_eps = 0.000001
psi_step  = 0.25 # angle step for interceptor trajectories
beta_step = 0.1  # angle step for trajectories sampling (both interceptor and missile)
#mrl_factor = 1.0  # index for zig-zagging footprint's max range line

mrl_factor1 = 1.03  #1.03  # index for zig-zagging footprint's max range line
mrl_factor2 = 1.05 #1.05  # index for zig-zagging footprint's max range line
no_zigzag = False

zigzag_for_intersection_limit = 2 # special treatment for computing sector footprint when single one has zigzagged section(s)

defense_sector_angle = 90
inside_check = True

multi_proc = True # parallel processing for interceptor table

redt_max_x_size = 1200
redt_max_y_size =  800

"""
unchangeable constants to compare to those changeable
"""
c_psi_step  = 0.25 # angle step for interceptor trajectories
c_sat_delay = 30
c_no_atmosphere = False
"""
^^^^^^^^^^^^^^^^^^^^^^unchangeable constants to compare to those changeable
"""




"!!! distance parameter for mode1 calculation is hard-coded as t_dist in footprint_calc_v2 function in footprintv2.py module"
dist_param = 1 / 8    # mrange multiplier for distance from ILP to be used as outer limit to  start search for footprint border in mode1
angle_step_mode2 = 5 #1  # used as angle step for searching fottprint border in Mode 2 #angle step (looking from MLP) for filling large segmeents of footprint border at the same "shift" (distance from MLP)
ang_quant = 5 #1         # angle step for filling out Mode2 footprint, degrees
fill_ang = 0          # angle step for filling out Mode1 footprint, degrees. Not filled if 0.

out_time_freq = 2 # every 2 seconds

check_fpa = False # check interceptor's flight path angle, for debug

version = "0.409.28"
cfg_fname_old = "footprint_config.json"
cfg_fname = "fcc_config.json"
rd_fname = "rocket_data.json"
chart_path = "charts"
footprint_path = "footprints"
trajectory_path = 'trajectories'
int_table_path = "int_tables"
geo_fname = "geo_bmd.json"
geo_path = "geo"

gui = True

"""
stdout_to_file = False
set_keep_stdout_file = True
set_keep_fp_data = True
set_keep_fp_chart = True
set_keep_int_tables = True
set_int_table_samp_verify = True
set_time_stamp = False
set_mirror_segment = True
"""

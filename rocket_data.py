import numpy as np
from math import pi
from os import path
import json
from fcc_constants import rd_fname

""" missile_data_list is intended to be used when file with data was not found,     """
""" but may not work correctly since it's a remnant from early stage of development """
missile_data_list = [
    {
        "m_key" : 15, # David Wright
        "type" : "m15 \"SM-3 Block IIA model with 4.5 km/s burnout speed\"", # Schiller model
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [150, 900 * 0.16, 270 * 0.17], # stage mass, kg
        "m_fu" : [450, 900 * 0.84, 270 * 0.83], # fuel mass, kg
        "v_ex" : [239 * 9.8, 240 * 9.8, 245 * 9.8], # exhaust velocity, m/s
        "t_bu" : [6, 60, 60],  # burn time, s
        "t_delay" : [0, 0], # stage delay, s
        "a_mid" : [.223, .223, .223], # stage cross area, m2
        #"cd_0" : [0.25, 0.25, 0.25], # stage drag coeff -- not used
        "m_shroud" : 20,
        "t_shroud" : 100,
        "m_pl" : 50.0,
        #"m_wh" : 50.0,
        "a_nz" : .2,
        #"a_pl" : 0.031, # payload cross area, m2
        #"cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 500 * 4.88, # in kg/m2
        #"psi" : 0, # angle velocity and vertical
        "vert_launch_height" : 200, # gravity angle starts at altitude, m
        "grav_turn_angle" : 27.6, # gravity turn angle, grad -- to be used for range optimisation as a ballistic missile
        "range" : 10000.0,
        "traj_type" : "bal_mis", # trajectory type: int_exo = exoatm interceptor
        "note" : "max 3375 km @ 33.513 grad 6540 m"
        # max 3375 km @ 33.513 grad 6540 m
    },
    {
        "m_key" : 14, # David Wright
        "type" : "m14 \"Minotaur IV Lite (3-st)\"", # Schiller model
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [3600, 3200, 640], # stage mass, kg
        "m_fu" : [45400, 24500, 7080], # fuel mass, kg # 4.3% unburned
        "v_ex" : [229 * 9.8, 308 * 9.8, 300 * 9.8], # exhaust velocity, m/s
        "t_bu" : [56.5, 61, 72],  # burn time, s
        "t_delay" : [1, 1], # stage delay, s
        "a_mid" : [pi * 2.3 * 2.3 / 4, pi * 2.3 * 2.3 / 4, pi * 2.3 * 2.3 / 4], # stage cross area, m2 #max diam = 2.3 m
        "cd_0" : [0.25, 0.25], # stage drag coeff  -- leftover
        "m_shroud" : 450,
        "t_shroud" : 76,
        "m_pl" : 1800.0,
        "m_wh" : 1800.0,
        "a_nz" : 1.8,
        "a_pl" : 0.185, # payload cross area, m2  -- leftover
        "cd_pl" : 0.25, # payload drug coeff  -- leftover
        "c_bal" : 2500 * 4.88, # in kg/m2
        "grav_turn_angle" : 25.27, # $$$ gravity turn angle, grad
        "vert_launch_height" : 530.0, # gravity angle starts at altitude, m
        "range" : 41000.0, 
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : "notes on the rockets\nmax 41010 km  @ 59.70 grad 8470 m"
        # max 41010 km  @ 59.70 grad 8470 m
    },
    {
        "m_key" : 13, # David Wright
        "type" : "m13 \"3500 km missile based on Minotaur (2-st)\"",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [3000, 1000], # stage mass, kg
        "m_fu" : [25000, 5000], # fuel mass, kg
        "v_ex" : [259 * 9.8, 300 * 9.8], # exhaust velocity, m/s
        "t_bu" : [56.5, 72],  # burn time, s
        "t_delay" : [1], # stage delay, s
        "a_mid" : [pi * 2.3 * 2.3 / 4, pi * 2.3 * 2.3 / 4], # stage cross area, m2 #max diam = 2.3 m
        "cd_0" : [0.25, 0.25], # stage drag coeff  -- leftover
        "m_shroud" : 450,
        "t_shroud" : 76,
        "m_pl" : 1800.0,
        "m_wh" : 1800.0,
        "a_nz" : 1,
        "a_pl" : 0.185, # payload cross area, m2  -- leftover
        "cd_pl" : 0.25, # payload drug coeff  -- leftover
        "c_bal" : 2000 * 4.88, # in kg/m2
        "grav_turn_angle" : 25, # $$$ gravity turn angle, grad
        "vert_launch_height" : 1100.0, # gravity angle starts at altitude, m
        "range" : 3900.0,
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 3868 km  @ 18.33 grad 100 m
    },
    {
        "m_key" : 12, # David Wright
        "type" : "m12 \"2000 km based on Scud-ER\"", # Schiller model
        "cd_type" : "v2", # large solid-fuel
        "m_st" : [700 + 350], # stage mass, kg
        "m_fu" : [7730 - 350], # fuel mass, kg # 4.3% unburned
        "v_ex" : [265 * 9.8], # exhaust velocity, m/s
        "t_bu" : [90],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [pi / 4], # stage cross area, m2 #max diam =1 m
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 500.0,
        "m_wh" : 500.0,
        "a_nz" : 0.135, # nozzle area, 0 = not used
        "a_pl" : 0.185, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 1500 * 4.88, # in kg/m2
        "grav_turn_angle" : 20, # $$$ gravity turn angle, grad
        "vert_launch_height" : 800.0, # gravity angle starts at altitude, m
        "range" : 1400.0,
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 1443 km  @ 9.42 grad 100 m -- before a_nz added
    },
    {
        "m_key" : 11, # David Wrigh
        "type" : "m11 \"Scud-ER\"", # Schiller model
        "cd_type" : "v2", # large solid-fuel
        "m_st" : [1000 + 330], # stage mass, kg
        "m_fu" : [7730 - 330], # fuel mass, kg # 4.3% unburned
        "v_ex" : [230 * 9.8], # exhaust velocity, m/s
        "t_bu" : [127.8],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [pi / 4], # stage cross area, m2 #max diam =1 m
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 500.0,
        "m_wh" : 500.0,
        "a_nz" : 0.135, # nozzle area, 0 = not used
        "a_pl" : 0.185, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 1500 * 4.88, # in kg/m2
        "grav_turn_angle" : 3, # $$$ gravity turn angle, grad
        "vert_launch_height" : 500.0, # gravity angle starts at altitude, m
        "range" : 800.0, 
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 821 km  @ 3.03 grad 510 m
    },
    {
        "m_key" : 10, # David Wright
        "type" : "m10 \"Scud-B\"",
        "cd_type" : "v2", # large solid-fuel
        "m_st" : [1102], # stage mass, kg
        "m_fu" : [3771], # fuel mass, kg
        "v_ex" : [226 * 9.8], # exhaust velocity, m/s
        "t_bu" : [62],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [pi * .88 * .88 / 4], # stage cross area, m2 #max diam =.88 m
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 987.0,
        "m_wh" : 987.0,
        "a_nz" : 0.1352, # nozzle area, 0 = not used
        "a_pl" : 0.185, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 4000 * 4.88, # in kg/m2
        "grav_turn_angle" : 11, # $$$ gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 300.0,
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 334 km 10.38 grad 100 m
    },
    {
        "m_key" : 9, # David Wright
        "type" : "m9 \"GBSD\"", #GBSD model 4-21  (MMIII with increased Isp and fuel fractions)
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [23230 * .11, 7270 * .14, 3710 * .11], # stage mass, kg | total 23230, 7270, 3710
        "m_fu" : [23230 * .89, 7270 * .86, 3710 * .89], # fuel mass, kg | 3306 = 0.89 * 3710
        "v_ex" : [267 * 9.8, 287 * 9.8, 285 * 9.8], # exhaust velocity, m/s
        "t_bu" : [61, 66, 61],  # burn time, s
        "t_delay" : [1, 1], # stage delay, s
        "a_mid" : [2.27, 2.27, 1.37], # stage cross area, m2 | max diam 1.7m, 3d stage from m7
        "cd_0" : [0.25, 0.25, 0.25], # stage drag coeff -- leftover
        "m_shroud" : 150,
        "t_shroud" : 76,
        "m_pl" : 600.0, #600.0, #3 W78 + bus    Standard payload = 1,000 kg --> 9000 km
        "m_wh" : 600.0,
        "a_nz" : 0.68, # nozzle area, 0 = not used
        "a_pl" : 1.37, # payload cross area, m2 -- leftover
        "cd_pl" : 0.25, # payload drug coeff -- leftover
        "c_bal" : 2500 * 4.88, # in kg/m2
        "grav_turn_angle" : 20.72774386, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 10000.0,
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 25259 km 20.73 grad 100 m mpl=600 kg
        # max 8636 km 13.56 grad 100 m mpl=1000 kg
    },
    {
        "m_key" : 8, # David Wright
        "type" : "m8 \"Minuteman 3\"",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [2450, 1030, 404], # stage mass, kg | total 23230, 7270, 3710
        "m_fu" : [20780, 6240, 3306], # fuel mass, kg | 3306 = 0.89 * 3710
        "v_ex" : [267 * 9.8, 287 * 9.8, 285 * 9.8], # exhaust velocity, m/s
        "t_bu" : [61, 66, 61],  # burn time, s
        "t_delay" : [1, 1], # stage delay, s
        "a_mid" : [2.27, 2.27, 1.37], # stage cross area, m2 | max diam 1.7m, 3d stage from m7
        "cd_0" : [0.25, 0.25, 0.25], # stage drag coeff -- leftover
        "m_shroud" : 150,
        "t_shroud" : 76,
        "m_pl" : 900.0, #DW one W78 + bus
        "m_wh" : 900.0,
        "a_nz" : .68, # nozzle area, 0 = not used
        "a_pl" : 1.37, # payload cross area, m2 -- leftover
        "cd_pl" : 0.25, # payload drug coeff -- leftover
        "c_bal" : 2500 * 4.88, # in kg/m2
        "grav_turn_angle" : 15.0, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 10000.0,
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 9881 km 14.74 grad 100 m
    },
    {
        "m_key" : 7, # Altmann
        "type" : "m7",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [1480, 490, 250], # stage mass, kg
        "m_fu" : [21190, 7070, 3530], # fuel mass, kg
        "v_ex" : [2500, 2700, 2700], # exhaust velocity, m/s
        "t_bu" : [50, 50, 50],  # burn time, s
        "t_delay" : [1, 1], # stage delay, s
        "a_mid" : [2.21, 2.21, 1.37], # stage cross area, m2
        "cd_0" : [0.25, 0.25, 0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 1200.0,
        "m_wh" : 1200.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 1.37, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 9240, # in kg/m2
        #"psi" : 0, # launch angle velocity and vertical
        "grav_turn_angle" : 21.0, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 10000.0, # 9733 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max range 9699 km 51 grad 12000 m
        # max 9736 km 21.13 grad 100 m
        # local max 9700 km 52 grad 13-14 km
    },
    {
        "m_key" : 6, # Altmann
        "type" : "m6",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [2059, 1190, 282], # stage mass, kg
        "m_fu" : [14200, 7160, 2120], # fuel mass, kg
        "v_ex" : [2300, 2600, 2700], # exhaust velocity, m/s
        "t_bu" : [50, 50, 50],  # burn time, s
        "t_delay" : [1, 1], # stage delay, s
        "a_mid" : [3.14, 1.43, 0.48], # stage cross area, m2
        "cd_0" : [0.25, 0.25, 0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 990.0,
        "m_wh" : 280.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.48, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 7840, # in kg/m2
        "grav_turn_angle" : 10.0, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 5000.0, # 4939 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
    },
    {
        "m_key" : 5, # Altmann
        "type" : "m5",
        "cd_type" : "ll", # large solid-fuel
        "m_st" : [490, 340], # stage mass, kg
        "m_fu" : [3460, 2160], # fuel mass, kg
        "v_ex" : [2350, 2750], # exhaust velocity, m/s
        "t_bu" : [50, 50],  # burn time, s
        "t_delay" : [1], # stage delay, s
        "a_mid" : [0.785, 0.785], # stage cross area, m2
        "cd_0" : [0.25, 0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 600.0,
        "m_wh" : 600.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.57, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 7020, # in kg/m2
        "grav_turn_angle" : 9.0, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 2000.0, # 2011 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
    },
    {
        "m_key" : 4, # Altmann
        "type" : "m4",
        "cd_type" : "ll", # large solid-fuel
        "m_st" : [450, 370], # stage mass, kg
        "m_fu" : [2000, 1270], # fuel mass, kg
        "v_ex" : [2550, 2750], # exhaust velocity, m/s
        "t_bu" : [50, 50],  # burn time, s
        "t_delay" : [1], # stage delay, s
        "a_mid" : [0.785, 0.385], # stage cross area, m2
        "cd_0" : [0.25, 0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 570.0,
        "m_wh" : 570.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.54, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 7040, # in kg/m2
        "grav_turn_angle" : 7.0, # $$$ gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 1000.0, # 999 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
    },
    {
        "m_key" : 3, # Altmann
        "type" : "m3",
        "cd_type" : "ll", # large solid-fuel
        "m_st" : [450, 370], # stage mass, kg
        "m_fu" : [2000, 1270], # fuel mass, kg
        "v_ex" : [2070, 2070], # exhaust velocity, m/s
        "t_bu" : [50, 50],  # burn time, s
        "t_delay" : [1], # stage delay, s
        "a_mid" : [0.785, 0.385], # stage cross area, m2
        "cd_0" : [0.25, 0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 570.0,
        "m_wh" : 570.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.54, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 7040, # in kg/m2
        "grav_turn_angle" : 5.0, # $$$ gravity turn angle, grad
        "vert_launch_height" : 200.0, # gravity angle starts at altitude, m
        "range" : 500.0, #490 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
    },
    {
        "m_key" : 2, # Altmann
        "type" : "m2",
        "cd_type" : "v2", # large solid-fuel
        "m_st" : [200], # stage mass, kg
        "m_fu" : [570], # fuel mass, kg
        "v_ex" : [2550], # exhaust velocity, m/s
        "t_bu" : [50],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [0.283], # stage cross area, m2
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 220.0,
        "m_wh" : 220.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.185, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 4760, # in kg/m2
        "grav_turn_angle" : 41, # $$$ gravity turn angle, grad
        "vert_launch_height" : 15000.0, # gravity angle starts at altitude, m
        "range" : 200.0, # 208 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
    },
    {
        "m_key" : 1, # Altmann
        "type" : "m1",
        "cd_type" : "v2", # large solid-fuel
        "m_st" : [100], # stage mass, kg
        "m_fu" : [235], # fuel mass, kg
        "v_ex" : [2550], # exhaust velocity, m/s
        "t_bu" : [50],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [0.126], # stage cross area, m2
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 150.0,
        "m_wh" : 150.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.126, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 4760, # in kg/m2
        "grav_turn_angle" : 9.6, # gravity turn angle, grad
        "vert_launch_height" : 100.0, # gravity angle starts at altitude, m
        "range" : 100.0, # 98 km
        "traj_type" : "bal_mis", # trajectory type: bal_mis - ballistic missile, gravity turn
        "note" : ""
        # max 98 km 9.6 grad 100 m
        # local max 97.8 km 40 grad 13 km
    }
]

""" missile_data_list is intended to be used when file with data was not found,     """
""" but may not work correctly since it's a remnant from early stage of development """
interceptor_data_list = [
    { # Interceptor Type 1 - endoatmospheric
        "i_key" : 11, # Altmann
        "type" : "i11",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [0], # stage mass, kg
        "m_fu" : [640], # fuel mass, kg
        "v_ex" : [2450], # exhaust velocity, m/s
        "t_bu" : [12],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [0.132], # stage cross area, m2
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 270.0,
        "m_wh" : 270.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.132, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 8200, # in kg/m2 # = m_pl / a_pl / cd_pl
        "vert_launch_height" : 0.0, # gravity angle starts at altitude, m
        "flight_path_angle" : 40, # interceptor's flight path angle 
        "launcher_length" : 20, # length of launcher, m
        "range" : 100.0,
        "traj_type" : "int_endo", # trajectory type: int_endo = exoatm interceptor
        "det_range" : [0, 142, 129, 99, 85, 76, 67, 0], # detection range of missiles from missile() function above, zero=not used
        "note" : ""
    },
    { # Interceptor Type 2 - endoatmospheric
        "i_key" : 12, # Altmann
        "type" : "i12",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [0], # stage mass, kg
        "m_fu" : [80], # fuel mass, kg
        "v_ex" : [2800], # exhaust velocity, m/s
        "t_bu" : [2],  # burn time, s
        "t_delay" : [], # stage delay, s
        "a_mid" : [0.042], # stage cross area, m2
        "cd_0" : [0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 150.0,
        "m_wh" : 150.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.042, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 14300, # in kg/m2 # = m_pl / a_pl / cd_pl
        "vert_launch_height" : 0.0, # gravity angle starts at altitude, m
        "flight_path_angle" : 40, # interceptor's flight path angle 
        "launcher_length" : 20, # length of launcher, m
        "range" : 100.0,
        "traj_type" : "int_endo", # trajectory type: int_endo = exoatm interceptor
        "det_range" : [0, 142, 129, 99, 85, 76, 67, 0], # detection range of missiles from missile() function above, zero=not used
        "note" : ""
    },
    { # Interceptor Type 3 -- eXoatmospheric
        "i_key" : 13, # Altmann
        "type" : "i13",
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [52,13,0], # stage mass, kg
        "m_fu" : [468,117,4], # fuel mass, kg
        "v_ex" : [2600,2800,2800], # exhaust velocity, m/s
        "t_bu" : [15,15,10],  # burn time, s
        "t_delay" : [0,0], # stage delay, s
        "a_mid" : [0.292,0.159,0.031], # stage cross area, m2
        "cd_0" : [0.25,0.25,0.25], # stage drag coeff
        "m_shroud" : 0,
        "t_shroud" : 0,
        "m_pl" : 36.0,
        "m_wh" : 36.0,
        "a_nz" : 0, # nozzle area, 0 = not used
        "a_pl" : 0.031, # payload cross area, m2
        "cd_pl" : 0.25, # payload drug coeff
        "c_bal" : 4650, # in kg/m2 # = m_pl / a_pl / cd_pl
        "vert_launch_height" : 25000, # gravity angle starts at altitude, m
        "flight_path_angle" : 40, # interceptor's flight path angle 
        "range" : 100.0,
        "traj_type" : "int_exo", # trajectory type: int_exo = exoatm interceptor
        "det_range" : [0, 142, 129, 99, 85, 76, 67, 500], # detection range of missiles from missile() function above, zero=not used
        "note" : ""
    },
    {
        "i_key" : 14, # David Wright
        "type" : "i14 \"SM-3 Block IIA model with 4.5 km/s burnout speed\"", # Schiller model
        "cd_type" : "ls", # large solid-fuel
        "m_st" : [150, 900 * 0.16, 270 * 0.17], # stage mass, kg
        "m_fu" : [450, 900 * 0.84, 270 * 0.83], # fuel mass, kg
        "v_ex" : [239 * 9.8, 240 * 9.8, 245 * 9.8], # exhaust velocity, m/s
        "t_bu" : [6, 60, 60],  # burn time, s
        "t_delay" : [0, 0], # stage delay, s
        "a_mid" : [.223, .223, .223], # stage cross area, m2 # max diam .533 m
        #"cd_0" : [0.25, 0.25, 0.25], # stage drag coeff -- not used
        "m_shroud" : 20,
        "t_shroud" : 100,
        "m_pl" : 50.0,
        #"m_wh" : 50.0,
        "a_nz" : 0.2, # nozzle area, 0 = not used
        #"a_pl" : 0.031, # irrelevant leftover
        #"cd_pl" : 0.25, # irrelevant leftover
        "c_bal" : 500 * 4.88, # in kg/m2
        "vert_launch_height" : 200, # gravity angle starts at altitude, m
        "flight_path_angle" : 40, # interceptor's flight path angle 
        "grav_turn_angle" : 15.7, # gravity turn angle, grad -- to be used for range optimisation as a ballistic missile
        "range" : 100.0,
        "traj_type" : "int_exo", # trajectory type: int_exo = exoatm interceptor
        "mpia" : 100,
        "det_range" : [0, 142, 129, 99, 85, 76, 67, 500], # detection range of missiles from missile() function above, zero=not used
        "note" : "notes on the rockets\nmore notes"
        # max 3375 km @ 33.513 grad 6540 m
    }
]

drag_V2_tab = np.array([
    [0, .15],
    [.6, .15],
    [.7, .16],
    [.8, .18],
    [.9, .23],
    [1, .3],
    [1.12, .4],
    [1.16,.418],
    [1.18,.42],
    [1.2, .418],
    [1.3, .39],
    [1.4, .36],
    [1.5, .325],
    [1.6, .3],
    [1.7, .275],
    [1.8, .26],
    [1.9, .25],
    [2, .24],
    [3, .21],
    [4, .18],
    [5, .155],
    [5.5, .15],
    ])

drag_liq_tab = np.array([
    [0, .2007],
    [.7, .2286],
    [.8, .2486],
    [.9, .2825],
    [1, .3402],
    [1.05, .3838],
    [1.1, .4304],
    [1.15,.4654],
    [1.18, .4747],
    [1.2, .4740],
    [1.4, .4374],
    [1.6, .4034],
    [1.8, .3720],
    [2, .3430],
    [2.5, .2804],
    [3, .2305],
    [3.5, .1918],
    [4, .1626],
    [4.5, .1416],
    [5.5, .1183],
    [6, .1134],
    ])

drag_solid_tab = np.array([
    [0, .1007],
    [.5, .1099],
    [.7, .1286],
    [.8, .1486],
    [.9, .1825],
    [1, .2402],
    [1.05, .2814],
    [1.1, .3229],
    [1.15,.3535],
    [1.2, .3618],
    [1.4, .3358],
    [1.6, .3117],
    [1.8, .2891],
    [2, .2682],
    [2.5, .2226],
    [3, .1859],
    [3.5, .1571],
    [4, .1354],
    [4.5, .1198],
    [5.5, .1035],
    [6, .1010],
    ])

drag_Alt_tab = np.array([
    [0, 1],
    [1, 1],
    [1.2, 1.4],
    [1.3, 1.4],
    [2, 1.2],
    [5, 1],
    [5.5, 1]
    ])

""""altitude, m, temperature, K, density, kg/m3, pressure, N/m2 for altitudes from 80 to 100 km"""
atmosphere100 = np.array([
    [80000,198.639,1.8458E-05,1.0524E+00],
    [80500,197.663,1.7054E-05,9.6761E-01],
    [81000,196.688,1.5750E-05,8.8923E-01],
    [81500,195.713,1.4540E-05,8.1687E-01],
    [82000,194.739,1.3418E-05,7.5009E-01],
    [82500,193.764,1.2378E-05,6.8848E-01],
    [83000,192.79,1.1414E-05,6.3167E-01],
    [83500,191.815,1.0521E-05,5.7930E-01],
    [84000,190.841,9.6940E-06,5.3105E-01],
    [84500,189.867,8.9282E-06,4.8660E-01],
    [85000,188.893,8.2196E-06,4.4568E-01],
    [85500,187.92,7.5641E-06,4.0802E-01],
    [86000,186.87,6.9580E-06,3.7338E-01],
    [86500,186.87,6.3660E-06,3.4163E-01],
    [87000,186.87,5.8240E-06,3.1259E-01],
    [87500,186.87,5.3280E-06,2.8602E-01],
    [88000,186.87,4.8750E-06,2.6173E-01],
    [88500,186.87,4.4600E-06,2.3951E-01],
    [89000,186.87,4.0810E-06,2.1919E-01],
    [89500,186.87,3.7340E-06,2.0060E-01],
    [90000,186.87,3.4160E-06,1.8359E-01],
    [90500,186.87,3.1260E-06,1.6804E-01],
    [91000,186.87,2.8600E-06,1.5381E-01],
    [91500,186.89,2.6160E-06,1.4078E-01],
    [92000,186.96,2.3930E-06,1.2887E-01],
    [92500,187.08,2.1880E-06,1.1798E-01],
    [93000,187.25,2.0000E-06,1.0801E-01],
    [93500,187.47,1.8280E-06,9.8896E-02],
    [94000,187.74,1.6700E-06,9.0560E-02],
    [94500,188.05,1.5260E-06,8.2937E-02],
    [95000,188.42,1.3930E-06,7.5966E-02],
    [95500,188.84,1.2730E-06,6.9592E-02],
    [96000,189.31,1.1620E-06,6.3765E-02],
    [96500,189.83,1.0610E-06,5.8439E-02],
    [97000,190.4,9.6850E-07,5.3571E-02],
    [97500,191.04,8.8420E-07,4.9122E-02],
    [98000,191.72,8.0710E-07,4.5057E-02],
    [98500,192.47,7.3670E-07,4.1342E-02],
    [99000,193.28,6.7250E-07,3.7948E-02],
    [99500,194.15,6.1390E-07,3.4846E-02],
    [100000,195.08,5.6040E-07,3.2011E-02],
    [100500,197.16,4.6950E-07,2.7192E-02],
    [101000,199.53,3.9350E-07,2.3144E-02],
    ])


def one2n(r_data) : # make sure there is correct number of values for all stages and interstages

    n_stages = len(r_data['m_st'])
    r_keys = {'a_mid', 't_delay'}
    for r_key in r_keys :
        if len(r_data[r_key]) == 1 :
            a_mid = r_data[r_key][0]
            a_mid_list = [a_mid]
            for i in range(n_stages - 1) :
                a_mid_list.append(a_mid)
            r_data[r_key] = a_mid_list
    
    if len(r_data['t_delay']) == n_stages - 1 :
        r_data['t_delay'].append(0)

    """
    r_key = 't_delay'
    if  n_stages > 1 :
        if len(r_data[r_key]) <= 1 :
            if r_data[r_key] == [] :
                t_delay = 0
            else :
                t_delay = r_data[r_key][0]
            t_delay_list = [t_delay]
            for i in range(n_stages - 2) :
                t_delay_list.append(t_delay)
            r_data[r_key] = t_delay_list
    """
    return r_data


def str2num(r_data) :
    #print(r_data)
    r_data = {key:val if key in ('m_key', 'i_key') else val.split('#', 1)[0].strip() for key, val in r_data.items()}
    if 'mpia' in r_data.keys() :
        if r_data['mpia'] == '' :
            r_data['mpia'] = 0
    if 'maxia' in r_data.keys() :
        if r_data['maxia'] == '' :
            r_data['maxia'] = 0
    if 'op_range' in r_data.keys() :
        if r_data['op_range'] == '' :
            r_data['op_range'] = 0
    if 'det_range' in r_data.keys() :
        if r_data['det_range'] == '' :
            r_data['det_range'] = [0]
            """ dictionary option next """
        elif ':' in r_data['det_range'] :
            detrange_dict = {}
            detrange_dict_s = r_data['det_range'].split(',')
            for dr_pair_s in detrange_dict_s :
                dr_pair = dr_pair_s.split(':')
                dr_key, dr_val = eval(dr_pair[0]), eval(dr_pair[1])
                detrange_dict[dr_key] = dr_val
            detrange_list = []
            dr_length = max(detrange_dict.keys()) + 1
            for i_dr in range(dr_length) :
                if i_dr in detrange_dict.keys() :
                    detrange_list.append(detrange_dict[i_dr])
                else :
                    detrange_list.append(0)
            r_data['det_range'] = detrange_list
        
    r_data['t_delay']   = [] if (r_data['t_delay'].strip()   == '') else eval(str(r_data['t_delay']),   {'pi' : pi})
    if r_data['t_delay'] == [] : r_data['t_delay'] = 0
    r_data['t_shroud']  = [] if (r_data['t_shroud'].strip()  == '') else eval(str(r_data['t_shroud']),  {'pi' : pi})
    r_data['m_shroud']  = [] if (r_data['m_shroud'].strip()  == '') else eval(str(r_data['m_shroud']),  {'pi' : pi})
    r_data['m_warhead'] = [] if (r_data['m_warhead'].strip() == '') else eval(str(r_data['m_warhead']), {'pi' : pi})
    
    x = r_data['a_nz'].strip().lower()
    if (x  == '') :
        r_data['a_nz'] = []
    elif x.startswith('d') :
        y = eval(x.lstrip("diametr"), {'pi' : pi})
        r_data['a_nz'] = pi * y * y / 4
    else :
        r_data['a_nz'] = eval(x, {'pi' : pi})
        
    x = r_data['a_mid'].strip().lower().split(',')
    z = []
    for x_i in x :
        x_i = x_i.strip()
        if x_i.startswith('d') :
            y = eval(x_i.lstrip("diametr"), {'pi' : pi})
            x_i = pi * y * y / 4
        else : 
            x_i = eval(x_i, {'pi' : pi})
        z.append(x_i)
    r_data['a_mid'] = z

    """ for testing purposes
    for key, val in r_data.items() :
        if key in ('i_key', 'm_key', 'type', 'cd_type', 'traj_type', 'note', 'range') :
            r_data[key] = val
        else:
            val1 = str(val)
            val2 = eval(val1, {'pi' : pi})
            r_data[key] = val2
    """
    r_data = {key:val if key in ('i_key', 'm_key', 'type', 'cd_type', 'traj_type', 'note', 'range') else eval(str(val), {'pi' : pi}) for key, val in r_data.items()}
    for key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") :
        val = r_data[key]
        if type(val) in (int, float) :
            r_data[key] = [val]
        elif len(val) > 1 :
            r_data[key] = list(val)
    #print(r_data)
    #r_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in r_data.items()} # list
    r_data = one2n(r_data)
    return r_data

"""
def str2num_old(r_data) :
    #print(r_data)
    r_data = {key:val if key in ('m_key', 'i_key') else val.split('#', 1)[0] for key, val in r_data.items()}
    if 'mpia' in r_data.keys() :
        if r_data['mpia'] == '' :
            r_data['mpia'] = 0
    if 'det_range' in r_data.keys() :
        if r_data['det_range'] == '' :
            r_data['det_range'] = [0]
            """ """ dictionary version """ """
        elif ':' in r_data['det_range'] :
            detrange_dict = {}
            detrange_dict_s = r_data['det_range'].split(',')
            for dr_pair_s in detrange_dict_s :
                dr_pair = dr_pair_s.split(':')
                dr_key, dr_val = eval(dr_pair[0]), eval(dr_pair[1])
                detrange_dict[dr_key] = dr_val
        
    r_data['t_delay']   = [] if (r_data['t_delay'].strip()   == '') else eval(str(r_data['t_delay']),   {'pi' : pi})
    if r_data['t_delay'] == [] : r_data['t_delay'] = 0
    r_data['t_shroud']  = [] if (r_data['t_shroud'].strip()  == '') else eval(str(r_data['t_shroud']),  {'pi' : pi})
    r_data['m_shroud']  = [] if (r_data['m_shroud'].strip()  == '') else eval(str(r_data['m_shroud']),  {'pi' : pi})
    r_data['m_warhead'] = [] if (r_data['m_warhead'].strip() == '') else eval(str(r_data['m_warhead']), {'pi' : pi})
    
    x = r_data['a_nz'].strip().lower()
    if (x  == '') :
        r_data['a_nz'] = []
    elif x.startswith('d') :
        y = eval(x.lstrip("diametr"), {'pi' : pi})
        r_data['a_nz'] = pi * y * y / 4
    else :
        r_data['a_nz'] = eval(x, {'pi' : pi})
        
    x = r_data['a_mid'].strip().lower().split(',')
    z = []
    for x_i in x :
        x_i = x_i.strip()
        if x_i.startswith('d') :
            y = eval(x_i.lstrip("diametr"), {'pi' : pi})
            x_i = pi * y * y / 4
        else : 
            x_i = eval(x_i, {'pi' : pi})
        z.append(x_i)
    r_data['a_mid'] = z

    """ """ for testing purposes
    for key, val in r_data.items() :
        if key in ('i_key', 'm_key', 'type', 'cd_type', 'traj_type', 'note', 'range') :
            r_data[key] = val
        else:
            val1 = str(val)
            val2 = eval(val1, {'pi' : pi})
            r_data[key] = val2
    """ """
    r_data = {key:val if key in ('i_key', 'm_key', 'type', 'cd_type', 'traj_type', 'note', 'range') else eval(str(val), {'pi' : pi}) for key, val in r_data.items()}
    for key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") :
        val = r_data[key]
        if type(val) in (int, float) :
            r_data[key] = [val]
        elif len(val) > 1 :
            r_data[key] = list(val)
    #print(r_data)
    #r_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in r_data.items()} # list
    r_data = one2n(r_data)
    return r_data
"""

""" Obsolete 
def str2num_v0(r_data) :
    #print(r_data)
    if 'mpia' in r_data.keys() :
        if r_data['mpia'] == '' :
            r_data['mpia'] = '0'
    x = r_data['t_delay']
    r_data['t_delay'] = x.split('#', 1)[0]
    r_data['t_delay'] = [] if (r_data['t_delay'].strip() == '') else eval(str(r_data['t_delay']), {'pi' : pi})
    x = r_data['t_shroud']
    r_data['t_shroud'] = x.split('#', 1)[0]
    r_data['t_shroud'] = [] if (r_data['t_shroud'].strip() == '') else eval(str(r_data['t_shroud']), {'pi' : pi})
    x = r_data['m_shroud']
    r_data['m_shroud'] = x.split('#', 1)[0]
    r_data['m_shroud'] = [] if (r_data['m_shroud'].strip() == '') else eval(str(r_data['m_shroud']), {'pi' : pi})
    x = r_data['a_nz']
    r_data['a_nz'] = x.split('#', 1)[0]
    r_data['a_nz'] = [] if (r_data['a_nz'].strip() == '') else eval(str(r_data['a_nz']), {'pi' : pi})
    r_data = {key:val if key in ('m_key', 'i_key', 't_delay', 't_shroud', 'm_shroud', 'a_nz') else val.split('#', 1)[0] for key, val in r_data.items()}
    r_data = {key:val if key in ('i_key', 'm_key', 'type', 'cd_type', 'traj_type', 'note', 'range') else eval(str(val), {'pi' : pi}) for key, val in r_data.items()}
    for key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") :
        val = r_data[key]
        if type(val) in (int, float) :
            r_data[key] = [val]
        elif len(val) > 1 :
            r_data[key] = list(val)
    #print(r_data)
    #r_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in r_data.items()} # list
    r_data = one2n(r_data)
    return r_data
"""


def delete_this_str2num(r_data) : # to be deleted
    if (r_data['t_delay'].strip() == '') :
        r_data['t_delay'] = [] 
    else :
        r_data['t_delay'] = eval(str(r_data['t_delay']), {'pi' : pi}) # to account for empty string for single stage rockets
    
    #print(str(r_data['t_delay']), type(r_data['t_delay']))
    #r_data = {key:val if key in ('i_key', 'type', 'cd_type', 'traj_type', 'note', 't_delay') else eval(str(val), {'pi' : pi}) for key, val in r_data.items()}
    for key, val in r_data.items() :
        if key not in ('i_key', 'type', 'cd_type', 'traj_type', 'note', 't_delay') :
            r_data[key] = eval(str(val), {'pi' : pi})
    #print(r_data)
    #print(r_data.items())
    #r_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in r_data.items()} # list
    for key, val in r_data.items() :
        print(key, val)
        if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") :
            r_data[key] = list(val)
    
    #print(r_data)
    return r_data

def missile(m_type, rd_filename=rd_fname) : # one missile # reads any data, returns numeric data

    mdata_list = missile_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list, idata_list = json.loads(rd_file.read())

            for m_data in mdata_list :
                if m_data['m_key'] == m_type :
                    """ str() to convert numbers (legacy data); list to convert tuples for string-lists w/o brackets """
                    #m_data = {key:val if key in ('m_key', 'type', 'cd_type', 'traj_type', 'note') else eval(str(val), {'pi' : pi}) for key, val in m_data.items()}
                    #m_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in m_data.items()} # list
                    m_data = str2num(m_data)
                    return m_data

            return False  # no mtype found

        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    else: pass

    for m_data in mdata_list : # from default data
        if m_data['m_key'] == m_type :
            m_data = one2n(m_data)
            return m_data
    
    print("No {} missile found. Check data file.".format(m_type))
    return False


def interceptor(i_type, rd_filename=rd_fname) : # one interceptor # reads any data, returns numeric data

    idata_list = interceptor_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list, idata_list = json.loads(rd_file.read())

            for i_data in idata_list :
                if i_data['i_key'] == i_type :
                    if 'mpia' not in i_data.keys() :
                        i_data['mpia'] = ''
                    if 'maxia' not in i_data.keys() :
                        i_data['maxia'] = ''
                    #i_data = {key:val if key in ('i_key', 'type', 'cd_type', 'traj_type', 'note', 't_delay') else eval(str(val), {'pi' : pi}) for key, val in i_data.items()}
                    #i_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid") else val for key, val in i_data.items()} # list
                    i_data = str2num(i_data)
                    return i_data
        
            return False # no i_type found

        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    else: pass
            
    for i_data in idata_list : # from default data
        if i_data['i_key'] == i_type :
            if 'mpia' not in i_data.keys() :
                i_data['mpia'] = 0
            if 'maxia' not in i_data.keys() :
                i_data['maxia'] = 0
            i_data = one2n(i_data)
            return i_data
    
    print("No {} interceptor found. Check data file.".format(i_type))
    return False


def s_missile(m_type, rd_filename=rd_fname) :  # one missile # reads any data, returns string data

    mdata_list = missile_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list, idata_list = json.loads(rd_file.read())
        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    for m_data in mdata_list :
        if m_data['m_key'] == m_type :
            m_data = {key:val if key == 'm_key' else str(val).translate({ord(x): None for x in ']['}) for key, val in m_data.items()}
            return m_data
        
    return False

def s_interceptor(i_type, rd_filename=rd_fname) : # one interceptor # reads any data, returns string data

    idata_list = interceptor_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list_r, idata_list_r = json.loads(rd_file.read())
            idata_list = idata_list_r
        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    for i_data in idata_list :
        if i_data['i_key'] == i_type :
            i_data = {key:val if key == 'i_key' else str(val).translate({ord(x): None for x in ']['}) for key, val in i_data.items()}
            if 'mpia' not in i_data.keys() :
                i_data['mpia'] = ''
            if 'maxia' not in i_data.keys() :
                i_data['maxia'] = ''
            return i_data
        
    return False

def load_s_mdata(rd_filename=rd_fname) : # all misssiles, string data

    mdata_list = missile_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list, idata_list = json.loads(rd_file.read())
        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    mdata_list.sort(key= lambda x: x['m_key'], reverse=True)
    for m_data in mdata_list :
        """ translate does not work properly when one-line if expression is inside for loop
        print(type(m_data['m_st']), m_data['m_st']) # debug
        m_data = {key:val if key == 'm_key' else str(val).translate({ord(x): None for x in ']['}) for key, val in m_data.items()}
        print(type(m_data['m_st']), m_data['m_st']) # debug
        """
        for key, val in m_data.items() :
            if key != 'm_key' : 
                m_data[key] = str(val).translate({ord(x): None for x in ']['})
        
        if 'm_warhead' not in m_data.keys() :
            m_data['m_warhead'] = ''
        
    #print("load_s_data", type(mdata_list[0]["m_st"]), mdata_list[0]["m_st"], type(m_data))
    
    return mdata_list
   
    
def load_s_idata(rd_filename=rd_fname) : # all interceptors, string data

    idata_list = interceptor_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file :
                mdata_list, idata_list = json.loads(rd_file.read())
        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    idata_list.sort(key= lambda x: x['i_key'], reverse=True)
    for i_data in idata_list :
        #i_data = {key:val if key == 'i_key' else str(val).translate({ord(x): None for x in ']['}) for key, val in i_data.items()}
        for key, val in i_data.items() :
            if key != 'i_key' : 
                i_data[key] = str(val).translate({ord(x): None for x in ']['})
        if 'mpia' not in i_data.keys() : # minimum possible intercept altitude
            i_data['mpia'] = ''
        if 'maxia' not in i_data.keys() : # minimum possible intercept altitude
            i_data['maxia'] = ''
        if 'm_warhead' not in i_data.keys() :
            i_data['m_warhead'] = ''
        if 'op_range' not in i_data.keys() :
            i_data['op_range'] = ''
            

    return idata_list


def load_s_data(rd_filename=rd_fname) : # load all missiles and interceptors, string data
    mdata_list = missile_data_list
    idata_list = interceptor_data_list
    if rd_filename :
        if path.exists(rd_filename) :
            with open(rd_filename, 'r') as rd_file:
                mdata_list, idata_list = json.loads(rd_file.read())
        else :
            print(">>> NOTE: Rocket data file " + rd_filename + " not found, default data loaded.")

    mdata_list.sort(key= lambda x: x['m_key'], reverse=True)
    idata_list.sort(key= lambda x: x['i_key'], reverse=True)

    for m_data in mdata_list :
        for key, val in m_data.items() :
            if key != 'm_key' : 
                m_data[key] = str(val).translate({ord(x): None for x in ']['})

    for i_data in idata_list :
        for key, val in i_data.items() :
            if key != 'i_key' : 
                i_data[key] = str(val).translate({ord(x): None for x in ']['})
        if 'mpia' not in i_data.keys() :
            i_data['mpia'] = ''
        if 'maxia' not in i_data.keys() :
            i_data['maxia'] = ''

    return mdata_list, idata_list


def save_rdata(r_rocket_data, rd_filename=rd_fname) :
    json_array = json.dumps(r_rocket_data, indent=4)
    with open(rd_filename, 'w') as rdf:
            rdf.write(json_array)

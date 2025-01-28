from tkinter import *
#from tkinter import Button, Label, Entry
import tkinter.filedialog as fd

#import tkinter as tk
#import tkinter.ttk as ttk    # shown in docs, but apparently not equired by tkinter-tooltip
try:
    from tktooltip import ToolTip # https://pypi.org/project/tkinter-tooltip/
except:
    tooltips = False
else:
    tooltips = True

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from cycler import cycler

from playsound import playsound # install command: pip install playsound

import sys, time, os
#from PIL import ImageTk,Image
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from math import degrees, radians, ceil, sin, cos

import main as m
import rocket_data as rd
import balmis as bm
#import tables_v2b as tb
import short_search as ss
import footprintv2 as fp
import chart3d_window as c3
from angle import calculate_angles

import intersection as isec

from fcc_constants import *
import fcc_constants

import geojson, json
from geographiclib.geodesic import Geodesic
import urllib.parse
import webbrowser
import traceback

from c_classes import CEntry, TextRedirector, AutoScrollbar

macos = (sys.platform == 'darwin')
if macos :
    right_click = '<Button-2><ButtonRelease-2>'
else :
    right_click = '<Button-3><ButtonRelease-3>'
    

if not os.path.exists(chart_path) :
    os.makedirs(chart_path)
if not os.path.exists(footprint_path) :
    os.makedirs(footprint_path)
if not os.path.exists(trajectory_path) :
    os.makedirs(trajectory_path)
if not os.path.exists(int_table_path) :
    os.makedirs(int_table_path)
if not os.path.exists(geo_path) :
    os.makedirs(geo_path)
#if not os.path.exists(int_table_path) : os.makedirs(int_table_path)

def default_config() :
    global program_config
    program_config = {
        'mtype' : 2,
        'itype' : 11,

        'h_int_min' : 1,   # deintercept altitude (MIA)
        'h_discr' : 0,     # height for warhead discrimination, 0 means not used
        't_delay' : 5,     # delay of interceptor launch after an event: missile rise over the horizon or misile burn out
        
        'h_int_min_list' : "1000, 2000, 3000",
        'h_discr_list' : "0, 10, 20",
        't_delay_list' : "5, 10, 15",

        'fp_calc_mode' : False, # footprint calculation mode, False = mode1, True = mode2
        'acc' : 0.01,       # i.e. ~1% -- or 1000 m (built-in)
        'angle_step' : 5,   # footprint angle, degrees
        #'angle_step_mode2' : 0.5, # mode 2 footprint angle, degrees
        'num_steps_mode2' : 100, # mode 2 number of probes for initial footprint calculation
        'set_shoot_look_shoot' : False,
        'det_range_list' : "50, 76, 100, 250, 500", # list of detection ranges in km
        'mumi_list' : "1, 2, 3",
        'muin_list' : "11, 12, 13",

        'sect_angle_beg' : 30,    # footprint sector angle limits and step
        'sect_angle_end' : 120,
        'sect_angle_step' : 2,
        'sect_dist_beg' : 50, # footprint sector distance (from center) limits
        'sect_dist_num' : 30,    # (maxrange-dist_beg)/dist_num : N meter steps

        'gtheight_beg' : 100,       # max range vs gtheight range search begin
        'gtheight_end' : 25000,     # max range vs gtheight range search end
        'gtangle_beg' : 1,          # max range vs gtangle range search begin
        'gtangle_end' : 60,         # max range vs gtangle range search end
        'maxrange_acc' : 0.03,      # max range search accuracy ( (max - min) / max) )

        'set_mirror_segment' : True, # add mirror segment (i.e. positive X), used by angle_dist_tab2, does not affect other routines
        'plot_hit_charts' : False,
        'hit_chart_angle' : 180,

        'set_keep_int_tables' : True, # .npy intereptor table data files (unsampled and sampled)
        'set_keep_fp_chart' : True, # keep or overwrite .png file with foot print chart
        'set_keep_fp_data' : False, # .json (was .csv) file with footprint data
        'set_keep_trj_data' : True, # keep trajectory data when saved

        'stdout_to_file' : False, # to save screen output to a file, used for debugging purposes
        'set_keep_stdout_file' : True,
        'set_time_stamp' : False, # set to True to prevent accidental overwriting of data files
        'set_int_table_samp_verify' : True, # this is within interception_table
        
        'sound_task_complete' : True,
        'save_config_on_exit' : True,
        #'save_rocket_data_on_exit' : False,
        'show_extra_param' : True,
        'show_extra_procs' : True,
        
        'show_ftprint_probe' : True,
        'show_chart_titles' : True,
        
        'def_sector_step' : 10,
        'set_sat_delay' : 30,
        'set_psi_step': 2,
        'no_atmosphere' : False,
        }

def set_config() :
    mtype_var.set(program_config['mtype'])
    itype_var.set(program_config['itype'])

    mia_var.set(program_config['h_int_min'])
    h_discr_var.set(program_config['h_discr'])
    t_delay_var.set(program_config['t_delay'])

    h_int_min_list_var.set(program_config['h_int_min_list'])
    h_discr_list_var.set(program_config['h_discr_list'])
    t_delay_list_var.set(program_config['t_delay_list'])

    fp_calc_mode_var.set(program_config['fp_calc_mode'])
    acc_var.set(program_config['acc'])
    angle_step_var.set(program_config['angle_step'])
    #angle_step_mode2_var.set(program_config['angle_step_mode2'])
    num_steps_mode2_var.set(program_config['num_steps_mode2'])
    emode_var.set(program_config['set_shoot_look_shoot']) # interception type, True = Shoot-Look-Shoot

    det_range_list_var.set(program_config['det_range_list'])
    mumi_list_var.set(program_config['mumi_list'])
    muin_list_var.set(program_config['muin_list'])

    sect_angle_beg_var.set(program_config['sect_angle_beg'])
    sect_angle_end_var.set(program_config['sect_angle_end'])
    sect_angle_step_var.set(program_config['sect_angle_step'])
    sect_dist_beg_var.set(program_config['sect_dist_beg'])
    sect_dist_num_var.set(program_config['sect_dist_num'])

    gtheight_beg_var.set(program_config['gtheight_beg'])
    gtheight_end_var.set(program_config['gtheight_end'])
    gtangle_beg_var.set(program_config['gtangle_beg'])
    gtangle_end_var.set(program_config['gtangle_end'])
    maxrange_acc_var.set(program_config['maxrange_acc'])

    set_mirror_segment_var.set(program_config['set_mirror_segment'])
    plot_hit_charts_var.set(program_config['plot_hit_charts'])
    hit_chart_angle_var.set(program_config['hit_chart_angle'])

    set_keep_int_tables_var.set(program_config['set_keep_int_tables'])
    set_keep_fp_chart_var.set(program_config['set_keep_fp_chart'])
    set_keep_fp_data_var.set(program_config['set_keep_fp_data'])
    set_keep_trj_data_var.set(program_config['set_keep_trj_data'])

    stdout_to_file_var.set(program_config['stdout_to_file'])
    set_keep_stdout_file_var.set(program_config['set_keep_stdout_file'])
    set_time_stamp_var.set(program_config['set_time_stamp'])
    set_int_table_samp_verify_var.set(program_config['set_int_table_samp_verify'])
    
    sound_task_complete_var.set(program_config['sound_task_complete'])
    save_config_on_exit_var.set(program_config['save_config_on_exit'])
    #save_rocket_data_on_exit_var.set(program_config['save_rocket_data_on_exit'])
    show_extra_param_var.set(program_config['show_extra_param'])
    show_extra_procs_var.set(program_config['show_extra_procs'])
    
    show_ftprint_probe_var.set(program_config['show_ftprint_probe'])
    show_chart_titles_var.set(program_config['show_chart_titles'])

    no_atmosphere_var.set(program_config['no_atmosphere'])
    set_sat_delay_var.set(program_config['set_sat_delay'])
    set_psi_step_var.set(program_config['set_psi_step'])
    def_sector_step_var.set(program_config['def_sector_step'])

    #print(set_sat_delay_var.get(), sat_delay)
    
def check_constants() :
    print("Program configuration data loaded from {}".format(cfg_fname))
    if set_psi_step_var.get() != fcc_constants.psi_step :
        fcc_constants.psi_step = set_psi_step_var.get()
        if fcc_constants.psi_step != c_psi_step :
            print(">>>psi_step = {}".format(fcc_constants.psi_step), file=sys.stderr)
        else :
            print("<<<psi_step = {}".format(fcc_constants.psi_step))
    
    if set_sat_delay_var.get() != fcc_constants.sat_delay :
        fcc_constants.sat_delay = set_sat_delay_var.get()
        if fcc_constants.sat_delay != c_sat_delay :
            print(">>>sat_delay = {}".format(fcc_constants.sat_delay), file=sys.stderr)
        else :
            print("<<<sat_delay = {}".format(fcc_constants.sat_delay))
    
    if no_atmosphere_var.get() != fcc_constants.no_atmosphere :
        fcc_constants.no_atmosphere = no_atmosphere_var.get()
        if fcc_constants.no_atmosphere != c_no_atmosphere :
            print(">>>no_atmosphere = {}".format(fcc_constants.no_atmosphere), file=sys.stderr)
        else :
            print("<<<no_atmosphere = {}".format(fcc_constants.no_atmosphere))



def load_config(cfg_fname) :
    global program_config
    prg_cfg = m.load_cfg(cfg_fname, cfg_fname_old)
    if prg_cfg :
        for cfg_item in prg_cfg.keys() :
            if cfg_item in program_config.keys() :
                program_config[cfg_item] = prg_cfg[cfg_item]
    else :
        print("NOTE: Configuration data not loaded from {}".format(cfg_fname))
        return False   

    
def save_program_config() :
    program_config = {
        'mtype' : mtype_var.get(),
        'itype' : itype_var.get(),
        'h_int_min' : mia_var.get(),
        'h_discr' : h_discr_var.get(),
        't_delay' : t_delay_var.get(),
        
        'h_int_min_list' : h_int_min_list_var.get(),
        'h_discr_list' : h_discr_list_var.get(),
        't_delay_list' : t_delay_list_var.get(),
        
        'fp_calc_mode' : fp_calc_mode_var.get(),
        'acc' : acc_var.get(),
        'angle_step' : angle_step_var.get(),
        #'angle_step_mode2' : angle_step_mode2_var.get(),
        'num_steps_mode2' : num_steps_mode2_var.get(),
        'set_shoot_look_shoot' : emode_var.get(),
        'det_range_list' : det_range_list_var.get(),
        'mumi_list' : mumi_list_var.get(),
        'muin_list' : muin_list_var.get(),

        'sect_angle_beg' : sect_angle_beg_var.get(),
        'sect_angle_end' : sect_angle_end_var.get(),
        'sect_angle_step' : sect_angle_step_var.get(),
        'sect_dist_beg' : sect_dist_beg_var.get(),
        'sect_dist_num' :sect_dist_num_var.get(),

        'gtheight_beg' : gtheight_beg_var.get(),
        'gtheight_end' : gtheight_end_var.get(),
        'gtangle_beg' :  gtangle_beg_var.get(),
        'gtangle_end' :  gtangle_end_var.get(),
        'maxrange_acc' : maxrange_acc_var.get(),

        'set_mirror_segment' : set_mirror_segment_var.get(),
        'plot_hit_charts' : plot_hit_charts_var.get(),
        'hit_chart_angle' : hit_chart_angle_var.get(),
        
        'set_keep_int_tables' : set_keep_int_tables_var.get(),
        'set_keep_fp_chart' : set_keep_fp_chart_var.get(),
        'set_keep_fp_data' : set_keep_fp_data_var.get(),
        'set_keep_trj_data' : set_keep_trj_data_var.get(),

        'stdout_to_file' : stdout_to_file_var.get(),
        'set_keep_stdout_file' : set_keep_stdout_file_var.get(),
        'set_time_stamp' : set_time_stamp_var.get(),
        'set_int_table_samp_verify' : set_int_table_samp_verify_var.get(),
        
        'sound_task_complete' : sound_task_complete_var.get(),
        'save_config_on_exit' : save_config_on_exit_var.get(),
        #'save_rocket_data_on_exit' : save_rocket_data_on_exit_var.get(),
        'show_extra_param' : show_extra_param_var.get(),
        'show_extra_procs' : show_extra_procs_var.get(),
        
        'show_ftprint_probe' : show_ftprint_probe_var.get(),
        'show_chart_titles' : show_chart_titles_var.get(),
        
        'def_sector_step' : def_sector_step_var.get(),
        'set_sat_delay' : set_sat_delay_var.get(),
        'set_psi_step' : set_psi_step_var.get(),
        'no_atmosphere' : no_atmosphere_var.get()
        }
    m.save_data(program_config, cfg_fname)
    print("Program configuration data saved to {}".format(cfg_fname))


def pop_confirm(pop_title, pop_question) :
    
    def f_cancel() :
        ok_var.set(False)
        del_cnf_win.grab_release()
        del_cnf_win.destroy()
        
    def f_confirm() :
        ok_var.set(True)
        del_cnf_win.grab_release()
        del_cnf_win.destroy()

    del_cnf_win = Toplevel(root)
    del_cnf_win.grab_set()
    del_cnf_win.attributes("-topmost", True)
    del_cnf_win.title(pop_title)
    #del_cnf_win.wait_window()
    width = 550
    height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width/2) - (width/2))
    y = int((screen_height/2) - (height/2))
    del_cnf_win.geometry('+{:d}+{:d}'.format(x, y))
    del_cnf_win.columnconfigure(0, weight=1)
    del_cnf_win.columnconfigure(1, weight=1)
    del_cnf_win.config(bg = "white")
    #del_cnf_win.geometry('{}x{}+{:d}+{:d}'.format(width, height, x, y))
    
    ok_var = BooleanVar(del_cnf_win)
    
    lbl_warn = Label(del_cnf_win, text=pop_question, bg='white', justify='center')
    lbl_warn.config(font=('', 16))
    btn_yes = Button(del_cnf_win, text="OK", command=f_confirm)
    btn_no =  Button(del_cnf_win, text="Cancel", command=f_cancel)
    btn_no.focus_set()
    lbl_warn.grid(row=0, column=0, columnspan=2, ipadx=50, ipady=10, pady=10, padx=50)
    btn_yes.grid(row=1, column=0, ipadx=35, ipady=5, pady=(0, 20))
    btn_no.grid(row=1, column=1, ipadx=20, ipady=5, pady=(0, 20))
    
    del_cnf_win.wait_window()
    return ok_var.get()


def pop_message(pop_title, pop_message) :
    
    def f_confirm() :
        message_win.grab_release()
        message_win.destroy()

    message_win = Toplevel(root)
    message_win.grab_set()
    message_win.attributes("-topmost", True)
    message_win.title(pop_title)
    width = 550
    height = 150
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = int((screen_width/2) - (width/2))
    y = int((screen_height/2) - (height/2))
    message_win.geometry('+{:d}+{:d}'.format(x, y))
    message_win.columnconfigure(0, weight=1)
    message_win.columnconfigure(1, weight=1)
    message_win.columnconfigure(2, weight=1)
    message_win.config(bg = "white")
        
    lbl_message = Label(message_win, text=pop_message, bg='white', justify='center')
    lbl_message.config(font=('', 16))
    btn_yes = Button(message_win, text="Ok", command=f_confirm)
    btn_yes.focus_set()
    lbl_message.grid(row=0, column=0, columnspan=3, ipadx=50, ipady=10, pady=10, padx=50)
    btn_yes.grid(row=1, column=1, ipadx=35, ipady=5, pady=(0, 20))
    
    message_win.focus_force()
    message_win.bind('<Escape>', lambda esc: message_win.destroy())
    #message_win.wait_window()


def show_rc_menu(event, rc_menu_s):
    w = event.widget
    rcms = rc_menu_s.lower()
    the_menu = Menu(w, tearoff=0)
    if 'copy' in rcms :
        the_menu.add_command(label="Copy")
        the_menu.entryconfigure("Copy",command=lambda: w.event_generate("<<Copy>>"))
    if 'paste' in rcms :
        the_menu.add_command(label="Paste")
        the_menu.entryconfigure("Paste",command=lambda: w.event_generate("<<Paste>>"))
    if 'cut' in rcms :
        the_menu.add_command(label="Cut")
        the_menu.entryconfigure("Cut", command=lambda: w.event_generate("<<Cut>>"))
    the_menu.tk.call("tk_popup", the_menu, event.x_root, event.y_root)


def extra_param() :
    global extra_param_win
    try :
        if extra_param_win.state() == "normal": extra_param_win.focus()
    except :
        extra_param_win = Toplevel(root)

        extra_param_win.title('Program Settings')
        extra_param_win.geometry('+500+160')
        extra_param_win.attributes('-topmost',True)
        extra_param_win.config(border=3, relief='ridge')

        """not used"""
        def toggle(button, boolvar):
            if toggle_btn.config('relief')[-1] == 'sunken':
                toggle_btn.config(relief="raised", text='ON')
            else:
                toggle_btn.config(relief="sunken", text='OFF')        

        def close(event=None) :
            #print("close")
            
            #print("a", fcc_constants.sat_delay, fcc_constants.no_atmosphere, fcc_constants.psi_step)

            if set_psi_step_var.get() != fcc_constants.psi_step :
                fcc_constants.psi_step = set_psi_step_var.get()
                if fcc_constants.psi_step != c_psi_step :
                    print(">>>psi_step = {}".format(fcc_constants.psi_step), file=sys.stderr)
                else :
                    print("<<<psi_step = {}".format(fcc_constants.psi_step))
                    
            
            if set_sat_delay_var.get() != fcc_constants.sat_delay :
                fcc_constants.sat_delay = set_sat_delay_var.get()
                if fcc_constants.sat_delay != c_sat_delay :
                    print(">>>sat_delay = {}".format(fcc_constants.sat_delay), file=sys.stderr)
                else :
                    print("<<<sat_delay = {}".format(fcc_constants.sat_delay))
            
            if no_atmosphere_var.get() != fcc_constants.no_atmosphere :
                fcc_constants.no_atmosphere = no_atmosphere_var.get()
                if fcc_constants.no_atmosphere != c_no_atmosphere :
                    print(">>>no_atmosphere = {}".format(fcc_constants.no_atmosphere), file=sys.stderr)
                else :
                    print("<<<no_atmosphere = {}".format(fcc_constants.no_atmosphere))
            
            #print("b", fcc_constants.sat_delay, fcc_constants.no_atmosphere, fcc_constants.psi_step)
            
            root.focus_set()
            extra_param_win.destroy()

        lbl_set_keep_int_tables  = Label(extra_param_win, text="set_keep_int_tables",)
        lbl_set_keep_fp_chart    = Label(extra_param_win, text="set_keep_fp_chart")
        lbl_set_keep_fp_data     = Label(extra_param_win, text="set_keep_fp_data")
        lbl_set_keep_trj_data     = Label(extra_param_win, text="set_keep_trj_data")

        lbl_set_mirror_segment   = Label(extra_param_win, text="set_mirror_segment")
        #lbl_show_ftprint_probe   = Label(extra_param_win, text="show_ftprint_probe")
        
        lbl_stdout_to_file       = Label(extra_param_win, text="stdout_to_file")
        lbl_set_keep_stdout_file = Label(extra_param_win, text="set_keep_stdout_file")

        lbl_set_time_stamp       = Label(extra_param_win, text="set_time_stamp")
        lbl_set_int_table_samp_verify = Label(extra_param_win, text="set_int_table_samp_verify")

        lbl_sound_task_complete  = Label(extra_param_win, text="sound_task_complete")
        lbl_save_config_on_exit  = Label(extra_param_win, text="save_config_on_exit")
        #lbl_save_rocket_data_on_exit  = Label(extra_param_win, text="save_rocket_data_on_exit")
        lbl_plot_hit_charts      = Label(extra_param_win, text="plot_hit_charts")
        lbl_hit_chart_angle      = Label(extra_param_win, text="hit_chart_angle")
        lbl_show_extra_param     = Label(extra_param_win, text="show_extra_param")
        lbl_show_extra_procs     = Label(extra_param_win, text="show_extra_procs")
        lbl_def_sector_step        = Label(extra_param_win, text="def_sector_step")
        lbl_set_sat_delay        = Label(extra_param_win, text="set_sat_delay")
        lbl_set_psi_step         = Label(extra_param_win, text="set_psi_step")
        lbl_no_atmosphere        = Label(extra_param_win, text="no_atmosphere")

        lbl_show_chart_titles    = Label(extra_param_win, text="show_chart_titles")

        btn_set_keep_int_tables  = Checkbutton(extra_param_win, variable=set_keep_int_tables_var)
        btn_set_keep_fp_chart    = Checkbutton(extra_param_win, variable=set_keep_fp_chart_var)
        btn_set_keep_fp_data     = Checkbutton(extra_param_win, variable=set_keep_fp_data_var)
        btn_set_keep_trj_data    = Checkbutton(extra_param_win, variable=set_keep_trj_data_var)

        btn_set_mirror_segment   = Checkbutton(extra_param_win, variable=set_mirror_segment_var)
        #btn_show_ftprint_probe   = Checkbutton(extra_param_win, variable=show_ftprint_probe_var)

        btn_stdout_to_file       = Checkbutton(extra_param_win, variable=stdout_to_file_var)
        btn_set_keep_stdout_file = Checkbutton(extra_param_win, variable=set_keep_stdout_file_var)

        btn_set_time_stamp       = Checkbutton(extra_param_win, variable=set_time_stamp_var)
        btn_set_int_table_samp_verify = Checkbutton(extra_param_win, variable=set_int_table_samp_verify_var)


        btn_sound_task_complete  = Checkbutton(extra_param_win, variable=sound_task_complete_var)
        btn_save_config_on_exit  = Checkbutton(extra_param_win, variable=save_config_on_exit_var)
        #btn_save_rocket_data_on_exit = Checkbutton(extra_param_win, variable=save_rocket_data_on_exit_var)
        btn_plot_hit_charts      = Checkbutton(extra_param_win, variable=plot_hit_charts_var)
        ent_hit_chart_angle      = CEntry(extra_param_win, textvariable=hit_chart_angle_var, width=4, justify='right')
        btn_show_extra_param     = Checkbutton(extra_param_win, variable=show_extra_param_var)
        btn_show_extra_procs     = Checkbutton(extra_param_win, variable=show_extra_procs_var)

        btn_show_chart_titles    = Checkbutton(extra_param_win, variable=show_chart_titles_var)

        ent_def_sector_step        = CEntry(extra_param_win, textvariable=def_sector_step_var, width=4, justify='right')
        ent_set_sat_delay        = CEntry(extra_param_win, textvariable=set_sat_delay_var, width=4, justify='right')
        ent_set_psi_step         = CEntry(extra_param_win, textvariable=set_psi_step_var, width=4, justify='right')
        btn_no_atmosphere        = Checkbutton(extra_param_win, variable=no_atmosphere_var)


        lbl_set_keep_int_tables.grid(row=0, column=0, ipadx=15, pady=(10, 0), sticky='w')
        lbl_set_keep_fp_chart.grid(row=1, column=0, ipadx=15, pady=0, sticky='w',)
        lbl_set_keep_fp_data.grid(row=2, column=0, ipadx=15, pady=0, sticky='w')
        lbl_set_keep_trj_data.grid(row=3, column=0, ipadx=15, pady=0, sticky='w')

        lbl_set_mirror_segment.grid(row=4, column=0, ipadx=15, pady=0, sticky='w')
        #lbl_show_ftprint_probe.grid(row=5, column=0, ipadx=15, pady=0, sticky='w')

        lbl_stdout_to_file.grid(row=5, column=0, ipadx=15, pady=0, sticky='w')
        lbl_set_keep_stdout_file.grid(row=6, column=0, ipadx=15, pady=0, sticky='w')

        lbl_set_time_stamp.grid(row=7, column=0, ipadx=15, pady=0, sticky='w')
        lbl_set_int_table_samp_verify.grid(row=8, column=0, ipadx=15, pady=0, sticky='w')

        lbl_sound_task_complete.grid(row=9, column=0, ipadx=15, pady=0, sticky='w')
        lbl_save_config_on_exit.grid(row=10, column=0, ipadx=15, pady=0, sticky='w')
        #lbl_save_rocket_data_on_exit.grid(row=9, column=0, ipadx=15, pady=5, sticky='w')
        lbl_plot_hit_charts.grid(row=11, column=0, ipadx=15, pady=0, sticky='w')
        lbl_hit_chart_angle.grid(row=12, column=0, ipadx=15, pady=0, sticky='w')
        lbl_show_extra_param.grid(row=13, column=0, ipadx=15, pady=0, sticky='w')
        lbl_show_extra_procs.grid(row=14, column=0, ipadx=15, pady=0, sticky='wn')

        lbl_show_chart_titles.grid(row=15, column=0, ipadx=15, pady=(0), sticky='wn')
        
        lbl_def_sector_step.grid(row=16, column=0, ipadx=15, pady=0, sticky='w')
        lbl_set_sat_delay.grid(row=17, column=0, ipadx=15, pady=0, sticky='w')
        lbl_set_psi_step.grid( row=18, column=0, ipadx=15, pady=0, sticky='w')
        lbl_no_atmosphere.grid(row=19, column=0, ipadx=15, pady=(0, 10), sticky='wn')
        
        btn_set_keep_int_tables.grid(row=0, column=1, ipadx=5, pady=(10, 0), sticky='e', )
        btn_set_keep_fp_chart.grid(row=1, column=1, ipadx=5, pady=0, sticky='e')
        btn_set_keep_fp_data.grid(row=2, column=1, ipadx=5, pady=0, sticky='e')
        btn_set_keep_trj_data.grid(row=3, column=1, ipadx=5, pady=0, sticky='e')

        btn_set_mirror_segment.grid(row=4, column=1, ipadx=5, pady=0, sticky='e')
        #btn_show_ftprint_probe.grid(row=5, column=1, ipadx=5, pady=0, sticky='e')

        btn_stdout_to_file.grid(row=5, column=1, ipadx=5, pady=0, sticky='e')
        btn_set_keep_stdout_file.grid(row=6, column=1, ipadx=5, pady=0, sticky='e')

        btn_set_time_stamp.grid(row=7, column=1, ipadx=5, pady=0, sticky='e')
        btn_set_int_table_samp_verify.grid(row=8, column=1, ipadx=5, pady=0, sticky='e')

        btn_sound_task_complete.grid(row=9, column=1, ipadx=5, pady=0, sticky='e')
        btn_save_config_on_exit.grid(row=10, column=1, ipadx=5, pady=0, sticky='e')
        #btn_save_rocket_data_on_exit.grid(row=9, column=1, ipadx=5, pady=(5, 10), sticky='e')
        btn_plot_hit_charts.grid(row=11, column=1, ipadx=5, pady=0, sticky='e')
        ent_hit_chart_angle.grid(row=12, column=1, ipadx=5, padx=(0, 15), pady=0, sticky='e')
        btn_show_extra_param.grid(row=13, column=1, ipadx=5, pady=0, sticky='e')
        btn_show_extra_procs.grid(row=14, column=1, ipadx=5, pady=0, sticky='e')

        btn_show_chart_titles.grid(row=15, column=1, ipadx=5, pady=(0), sticky='e')

        ent_def_sector_step.grid(row=16, column=1, ipadx=5, padx=(0, 15), pady=0, sticky='e')
        ent_set_sat_delay.grid(row=17, column=1, ipadx=5, padx=(0, 15), pady=0, sticky='e')
        ent_set_psi_step.grid( row=18, column=1, ipadx=5, padx=(0, 15), pady=0, sticky='e')
        btn_no_atmosphere.grid(row=19, column=1, ipadx=5, pady=(0, 10), sticky='e')

        extra_param_win.focus_force()
        #extra_param_win.bind('<Escape>', lambda esc: extra_param_win.destroy())
        extra_param_win.bind('<Escape>', close)
        extra_param_win.bind("<FocusOut>", close)
        extra_param_win.protocol("WM_DELETE_WINDOW", close)

def fcc_close():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    sys.stdout.flush()
    sys.stderr.flush()
    root.destroy()
    

def call_longrun(longrun) :
    if busy_running.get() :
        pop_message("Process running", "A process is running. Please wait until it completes...")
    else :
        btn_ch_mis.config(state='disabled')
        btn_ed_mis.config(state='disabled')
        btn_ch_int.config(state='disabled')
        btn_ed_int.config(state='disabled')
        
        busy_running.set(True)
        try :
            longrun()
        except Exception as exc:
            trace_txt = traceback.format_exc()
            print(trace_txt, file=sys.stderr)
        busy_running.set(False)
        btn_ch_mis.config(state='normal')
        btn_ed_mis.config(state='normal')
        btn_ch_int.config(state='normal')
        btn_ed_int.config(state='normal')
        if sound_task_complete_var.get() :
            if os.path.exists('sounds/Purr.mp3') :
                playsound('sounds/Purr.mp3')
            #if os.path.exists('sounds/Purr.aiff') :
            #    os.system('afplay sounds/Purr.aiff')



""" DELETE
def set_h_int_min() :
    h_int_min = float(ent_mia.get())
    #mia_var.set(h_int_min)
    #ent_mia.delete(0, END)
    #ent_mia.insert(0, str(float(h_int_min)))

def set_h_discr() :
    h_discr = float(ent_hdiscr.get())
    #h_discr_var.set(h_discr)
    #ent_hdiscr.delete(0, END)
    #ent_hdiscr.insert(0, str(float(h_discr)))

def set_t_delay() :
    t_delay = float(ent_tdelay.get())
    #t_delay_var.set(t_delay)
    #ent_tdelay.delete(0, END)
    #ent_tdelay.insert(0, str(float(t_delay)))

def set_angle_step() :
    angle_step = int(ent_ang_step.get())
    #angle_step_var.set(angle_step)
    #ent_ang_step.delete(0, END)
    #ent_ang_step.insert(0, str(float(angle_step)))

def set_acc() :
    acc = float(ent_accuracy.get())
    #acc_var.set(acc)
    #ent_accuracy.delete(0, END)
    #ent_accuracy.insert(0, str(int(acc)))
"""

def swap_eng_mode() :
    emode_sls = emode_var.get()
    emode_sls = not emode_sls
    emode_var.set(emode_sls)
    ent_eng_mode.config(state='normal')
    ent_eng_mode.delete(0, END)
    if emode_sls :
        ent_eng_mode.insert(0, 'Shoot-Look-Shoot')
    else :
        ent_eng_mode.insert(0, 'Shoot Once')
    ent_eng_mode.config(state='readonly')


def swap_fp_calc_mode() :
    mode2 = fp_calc_mode_var.get()
    mode2 = not mode2
    fp_calc_mode_var.set(mode2)
    ent_fp_calc_mode.config(state='normal')
    ent_fp_calc_mode.delete(0, END)
    if mode2 :
        ent_fp_calc_mode.insert(0, 'Mode 2')
        lbl_ang_step.grid_remove()
        ent_ang_step.grid_remove()
        lbl_num_steps_mode2.grid()
        ent_num_steps_mode2.grid()
        #lbl_ang_step_mode2.grid()
        #ent_ang_step_mode2.grid()
    else :
        ent_fp_calc_mode.insert(0, 'Mode 1')
        lbl_ang_step.grid()
        ent_ang_step.grid()
        #lbl_ang_step_mode2.grid_remove()
        #ent_ang_step_mode2.grid_remove()
        lbl_num_steps_mode2.grid_remove()
        ent_num_steps_mode2.grid_remove()
        
    try :
        if probing_win.state() == "normal" : probing_win.destroy()
    except :
        pass

    ent_fp_calc_mode.config(state='readonly')

def bind_mouse_scroll_events(event, widget):

    # For Windows and MacOS
    widget.bind_all("<MouseWheel>", on_mouse_wheel)
    # For Linux (may need "Shift+MouseWheel" for horizontal scroll)
    widget.bind_all("<Button-4>", on_mouse_wheel)  # Scroll up
    widget.bind_all("<Button-5>", on_mouse_wheel)  # Scroll down
    
def bind_mousewheel(widget):
    
    def on_mouse_wheel(event):
        # Windows / MacOS use event.delta to scroll (positive for up, negative for down)
        if event.num == 5 or event.delta < 0:
            widget.yview_scroll(1, "units")  # Scroll down
        elif event.num == 4 or event.delta > 0:
            widget.yview_scroll(-1, "units")  # Scroll up

    widget.bind("<Enter>", lambda event: widget.bind_all("<MouseWheel>", lambda e: on_mouse_wheel(e)))
    widget.bind("<Leave>", lambda event: (
        widget.unbind_all("<MouseWheel>"),
        widget.unbind("<Button-4>"),
        widget.unbind("<Button-5>")
    ))
    widget.bind("<Button-4>", lambda event: on_mouse_wheel(event))  # Linux scroll up
    widget.bind("<Button-5>", lambda event: on_mouse_wheel(event))  # Linux scroll down    

        
def choose_missile() :
    global ch_mis_win
    try :
        if ch_mis_win.state() == "normal": ch_mis_win.focus()
    except :
        ch_mis_win = Toplevel(root)
        ch_mis_win.title('Choose Missile')
        ch_mis_win.geometry('470x500+200+100')
        ch_mis_win.config(border=3, relief='ridge')

        
        def set_missile_type(m_key) :
            #missile_data = rd.missile(m_key, rd_fname)
            #missile_type = missile_data["type"]
            for m_data in missile_data_list :
                if m_data['m_key'] == m_key :
                    missile_data = m_data
                    break

            mname_var.set(missile_data["type"])
            mname1_var.set(mname_var.get().split('#', 1)[0])
            #lbl_mis.config(text=missile_label)
            mtype_var.set(m_key)
            #lbl_mkey.config(text=str(m_key))
            ch_mis_win.destroy()

        def close(event=None) :
            root.focus_set()
            ch_mis_win.destroy()
        

        vscrollbar = AutoScrollbar(ch_mis_win)
        vscrollbar.grid(row=0, column=1, sticky='ns')
        #hscrollbar = AutoScrollbar(ch_mis_win, orient=HORIZONTAL)
        #hscrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas = Canvas(ch_mis_win, yscrollcommand=vscrollbar.set) #, xscrollcommand=hscrollbar.set)
        canvas.grid(row=0, column=0, sticky='news')
        
        vscrollbar.config(command=canvas.yview)
        #hscrollbar.config(command=canvas.xview)
        
        # make the canvas expandable
        ch_mis_win.grid_rowconfigure(0, weight=1)
        ch_mis_win.grid_columnconfigure(0, weight=1)
        
        # create canvas contents
        ch_mis_frame = Frame(canvas)
        ch_mis_frame.rowconfigure(1, weight=1)
        ch_mis_frame.columnconfigure(1, weight=1)
        
        missile_data_list = rd.load_s_mdata(rd_fname)
        i_rd = 0
        for m_data in missile_data_list :
            btn_text = m_data["type"]
            mis_key = m_data["m_key"]
            btn_mis = Button(ch_mis_frame, text=btn_text, anchor='w', pady=0, command=lambda key=mis_key: set_missile_type(key))
            #btn_mis.pack(fill='x', expand=1)
            btn_mis.grid(row=i_rd, column=0, sticky='ew')
            i_rd += 1
        
        canvas.create_window(0, 0, anchor=NW, window=ch_mis_frame)
        ch_mis_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind("<1>",     lambda event: canvas.focus_set())
        canvas.bind("<Left>",  lambda event: canvas.xview_scroll(-1, "units"))
        canvas.bind("<Right>", lambda event: canvas.xview_scroll( 1, "units"))
        canvas.bind("<Up>",    lambda event: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Down>",  lambda event: canvas.yview_scroll( 1, "units"))
        canvas.bind("<Prior>", lambda event: canvas.yview_scroll(-1, "pages"))
        canvas.bind("<Next>",  lambda event: canvas.yview_scroll( 1, "pages"))
        canvas.bind("<Home>",  lambda event: canvas.yview_moveto('0.0'))
        canvas.bind("<End>",   lambda event: canvas.yview_moveto('1.0'))

        bind_mousewheel(canvas)

        canvas.focus_set()

        #ch_mis_win.focus_force()
        ch_mis_win.bind('<Escape>', lambda esc: ch_mis_win.destroy())
        ch_mis_win.bind("<FocusOut>", close)


def choose_interceptor() :
    global ch_int_win
    try :
        if ch_int_win.state() == "normal": ch_int_win.focus()
    except :
        ch_int_win = Toplevel(root)
        ch_int_win.title('Choose Interceptor')
        ch_int_win.geometry('360x500+600+100')
        ch_int_win.config(border=3, relief='ridge')
        
        def set_interceptor_type(i_key) :
            #interceptor_data = rd.interceptor(i_key, rd_fname)
            #interceptor_type = interceptor_data["type"]
            for i_data in interceptor_data_list :
                if i_data['i_key'] == i_key :
                    interceptor_data = i_data
                    break
            iname_var.set(interceptor_data["type"])
            iname1_var.set(iname_var.get().split('#', 1)[0]) # name without comments
            #lbl_int.config(text=interceptor_label)
            itype_var.set(i_key)
            ch_int_win.destroy()
        
        def close(event=None) :
            root.focus_set()
            ch_int_win.destroy()

        vscrollbar = AutoScrollbar(ch_int_win)
        vscrollbar.grid(row=0, column=1, sticky='ns')
        #hscrollbar = AutoScrollbar(ch_int_win, orient=HORIZONTAL)
        #hscrollbar.grid(row=1, column=0, sticky='ew')
        
        canvas = Canvas(ch_int_win, yscrollcommand=vscrollbar.set) #, xscrollcommand=hscrollbar.set)
        canvas.grid(row=0, column=0, sticky='news')
        
        vscrollbar.config(command=canvas.yview)
        #hscrollbar.config(command=canvas.xview)
        
        # make the canvas expandable
        ch_int_win.grid_rowconfigure(0, weight=1)
        ch_int_win.grid_columnconfigure(0, weight=1)
        
        # create canvas contents
        ch_int_frame = Frame(canvas)
        ch_int_frame.rowconfigure(1, weight=1)
        ch_int_frame.columnconfigure(1, weight=1)
        
        interceptor_data_list = rd.load_s_idata(rd_fname)
        i_rd = 0
        for i_data in interceptor_data_list :
            btn_text = i_data["type"]
            int_key = i_data["i_key"]
            btn_int = Button(ch_int_frame, text=btn_text, anchor='w', pady=0, command=lambda key=int_key: set_interceptor_type(key))
            #btn_int.pack(fill='x', expand=1)
            btn_int.grid(row=i_rd, column=0, sticky='ew')
            i_rd += 1
            
        canvas.create_window(0, 0, anchor=NW, window=ch_int_frame)
        ch_int_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.bind("<1>",     lambda event: canvas.focus_set())
        canvas.bind("<Left>",  lambda event: canvas.xview_scroll(-1, "units"))
        canvas.bind("<Right>", lambda event: canvas.xview_scroll( 1, "units"))
        canvas.bind("<Up>",    lambda event: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Down>",  lambda event: canvas.yview_scroll( 1, "units"))
        canvas.bind("<Prior>", lambda event: canvas.yview_scroll(-1, "pages"))
        canvas.bind("<Next>",  lambda event: canvas.yview_scroll( 1, "pages"))
        canvas.bind("<Home>",  lambda event: canvas.yview_moveto('0.0'))
        canvas.bind("<End>",   lambda event: canvas.yview_moveto('1.0'))

        bind_mousewheel(canvas)

        canvas.focus_set()

        #ch_int_win.focus_force()
        ch_int_win.bind('<Escape>', lambda esc: ch_int_win.destroy())
        ch_int_win.bind("<FocusOut>", close)

        
def gui_balmis_flight() :
    m_key = mtype_var.get()
    missile_data = rd.missile(m_key, rd_fname)
    #print(missile_data)
    trajectory_data = False
    ind_flight_dataprint = True
    #print("xxx", no_atmosphere, globals()['no_atmosphere'])
    m_range = bm.balmisflight(missile_data, trajectory_data, ind_flight_dataprint)
    print("Missile range = {:.0f} km".format(m_range/1000))
    
def gui_balmis_trajectory() :
    m_key = mtype_var.get()
    missile_data = rd.missile(m_key, rd_fname)
    #print(missile_data)
    trajectory_data = True
    ind_flight_dataprint = True
    trj = bm.balmisflight(missile_data, trajectory_data, ind_flight_dataprint)
    m_range = trj[len(trj) - 1, 2] * R_e
    print("Missile range = {:.0f} km".format(m_range/1000))
    
    file_mt = trajectory_path + '/trajectory_m{}.csv'.format(m_key)
    keep_trj_files = set_keep_trj_data_var.get()
    if keep_trj_files :
        m.keep_old_file(file_mt)
    fmt = '%.2f','%.8f','%.8f','%.8f','%.8f'
    np.savetxt(file_mt, trj, fmt = fmt, delimiter = ',', header = "time, R, alfa_r, veloc, accel")
    print("Missile trajectory saved to " + file_mt)
    

def gui_trajcharts(r_data, is_missile) :
    #m_key = rtype_var.get()
    #missile_data = rd.missile(m_key, rd_fname)
    #print(missile_data)
    trajectory_data = True
    ind_flight_dataprint = True
    #print(r_data)
    trj = bm.balmisflight(r_data, trajectory_data, ind_flight_dataprint)
    m_range = trj[len(trj) - 1, 2] * R_e
    if is_missile :
        print("Missile range = {:.0f} km".format(m_range/1000))
    else :
        print("Interceptor range = {:.0f} km".format(m_range/1000))
        

    global trajchart_win

    try :
        if trajchart_win.state() == "normal" : trajchart_win.destroy()
    except :
        pass
    finally :
        trajchart_win = Toplevel(root)
        trajchart_win.title('Trajectory Chart')
        trajchart_win.geometry("+100+100")
        
        #trajchart_win.geometry('1800x600+100+160')
        #trajchart_win.resizable(width=False, height=False)
        #plt.subplots_adjust(left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)
        

        chwin_row0 = Frame(trajchart_win, border=1)
        chwin_row1 = Frame(trajchart_win, border=1)
        chwin_row1.columnconfigure(0, weight=1)
        chwin_row1.columnconfigure(1, weight=1)
        chwin_row1.columnconfigure(2, weight=1)
        chwin_row1.columnconfigure(3, weight=1)
        
        chwin_row0.pack()
        chwin_row1.pack()  
    
        #rc_menu_string ='copy-paste-cut'
        #chart_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def tc_draw () :
            tc_plot()
        
            canvas = FigureCanvasTkAgg(fig, chwin_row0)
            canvas.draw()
        
            # placing the canvas on the Tkinter chart_win
            canvas.get_tk_widget().pack()
        
            # creating the Matplotlib toolbar
            toolbar = c3.CustomNavigationToolbar(canvas, trajchart_win, disable_coordinates=False)
            toolbar.update()
        
            # placing the toolbar on the Tkinter chart_win
            #canvas.get_tk_widget().pack()
            
        def tc_save() :
            fp_plot()
            keep_chart = set_keep_fp_chart_var.get()
            #print(keep_chart)
            save_chart_fname = ent_chart_fname.get()
            if keep_chart :
                m.keep_old_file(save_chart_fname)
            ax.get_figure().savefig(save_chart_fname, dpi=300, bbox_inches='tight', pad_inches=0.2)
            print("Footprint Chart saved to ", save_chart_fname)
            btn_chart_save.configure(state='disabled')
    
    
        def tc_data_save() :
            keep_data = set_keep_fp_data_var.get()
            #print(keep_data)
            save_data_fname = ent_data_fname.get()
            if keep_data :
                    m.keep_old_file(save_data_fname)
            if not mode2 :
                fp_arr = [fp_i.tolist() for fp_i in ftprint_arr]
            else :
                fp_arr = [[fp1.tolist(), fp2.tolist()] for [fp1, fp2] in ftprint_arr]
            #if len(ftprint_arr) > 1 : fp_arr = ftprint_arr
            #else : fp_arr = ftprint_arr[0].tolist()
    
            data2save = new_header_string, fp_arr
            m.save_data(data2save, save_data_fname, keep_data)

            print("Footprint Data saved to ", save_data_fname)
            btn_data_save.configure(state='disabled')
    
    
        def tc_plot() :
            global fig
            global ax
    
            fig = Figure(figsize = (12, 6), dpi=100)
            fig.suptitle('{}\ntrajectory charts'.format(r_data['type']), fontsize=12)
            
            ax1  = fig.add_subplot(121)
            ax2  = fig.add_subplot(122)
            ax22 = ax2.twinx()
    
            time = trj[:, 0]
            x_pt = np.copy(trj[:, 1])
            y_pt = np.copy(trj[:, 2])
            x_ea = np.copy(trj[:, 1])
            y_ea = np.copy(trj[:, 2])
            x_at = np.copy(trj[:, 1])
            y_at = np.copy(trj[:, 2])

            #print(len(time))
            """
            for i_tc in range (len(time)):
                x_tc = x_pt[i_tc] * sin(y_pt[i_tc])
                y_tc = x_pt[i_tc] * cos(y_pt[i_tc]) - R_e
                x_pt[i_tc] = x_tc/1000
                y_pt[i_tc] = y_tc/1000

                x_tx = R_e * sin(y_ea[i_tc])
                y_tx = R_e * cos(y_ea[i_tc]) - R_e
                x_ea[i_tc] = x_tx/1000
                y_ea[i_tc] = y_tx/1000
                                
                x_tz = (R_e/1000 + 100) * sin(y_at[i_tc])
                y_tz = (R_e/1000 + 100) * cos(y_at[i_tc]) - R_e/1000
                x_at[i_tc] = x_tz
                y_at[i_tc] = y_tz
            """

            i_max = len(time) - 1
            al_max = trj[i_max, 2]
            am2 = al_max/2
            #print(degrees(am2))
            d = R_e * sin(am2)

            for i_tc in range (len(time)):
                x_tc = d - x_pt[i_tc] * sin(am2 - y_pt[i_tc])
                y_tc = x_pt[i_tc] * cos(y_pt[i_tc] - am2) - R_e * cos(am2)
                x_pt[i_tc] = x_tc/1000
                y_pt[i_tc] = y_tc/1000

                x_tx = d - R_e * sin(am2 - y_ea[i_tc])
                y_tx = R_e * cos(y_ea[i_tc] - am2) - R_e * cos(am2)
                x_ea[i_tc] = x_tx/1000
                y_ea[i_tc] = y_tx/1000
                                
                x_tz = d/1000 - (R_e/1000 + 100) * sin(am2 - y_at[i_tc])
                y_tz = (R_e/1000 + 100) * cos(y_at[i_tc] - am2) - R_e/1000 * cos(am2)
                x_at[i_tc] = x_tz
                y_at[i_tc] = y_tz
            v_pt = trj[:, 3] /1000
            a_pt = trj[:, 4]
            #v_pt = v_pt
            #a_pt = a_pt

            #ax2.set_xlim([0, 1])
            #ax2.set_ylim([-10, 10])
            ax1.set_xlabel('x distance, km')
            ax1.set_ylabel('y distance, km')

            #ax2.set_xlim([0, 1])
            #ax2.set_ylim([-10, 10])
            ax2.set_xlabel('time, s')
            ax2.set_ylabel('speed, km/s')
            ax22.set_ylabel('acceleration, m/s^2')

            ax1.plot(x_ea, y_ea, c='black', linestyle='-', linewidth=1, label='earth')
            ax1.plot(x_pt, y_pt, c='red', linestyle='-', linewidth=1, label='trajectory')
            ax1.plot(x_at, y_at, c='blue', linestyle=':', linewidth=1, label='atmosphere')

            ax2.plot(time, v_pt, c='blue', linestyle='-', linewidth=1, label='speed')
            ax22.plot(time, a_pt, c='green', linestyle='-', linewidth=1, label='acceleration')
            ax22.axhline(y = 0, c = 'black', linewidth = .75, linestyle='--')#, label = 'zero acceleration')

                
            #ax.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
            ax1.set_title("trajectory\n", fontsize=10, y=0.984)
            ax2.set_title("speed and acceleration\n", fontsize=10, y=0.984)
        
            ax1.legend( loc='best',        frameon=False, framealpha=1.0)
            ax2.legend( loc=(0.35, 0.925),    frameon=False, framealpha=1.0)
            ax22.legend(loc=(0.35, 0.88), frameon=False, framealpha=1.0)
            #ax2.legend(loc='upper left', frameon=False, framealpha=1.0)
            #ax22.legend(loc='upper right', frameon=False, framealpha=1.0)
                    
            ax1.axis('equal')
            #ax2.axis('equal')
            #ax.grid()

        """ End of tc_plot() """

        """ End of internal functions """
        
        tc_draw()
        plt.close()
        
        """
        ent_chart_fname = CEntry(chwin_row1, bg='white', width=50)
        ent_chart_fname.insert(0, new_chart_fname)
        btn_chart_save = Button(chwin_row1, text="Save Chart", command=fp_save)
        ent_data_fname = CEntry(chwin_row1, bg='white', width=50)    
        ent_data_fname.insert(0, new_data_fname)
        btn_data_save = Button(chwin_row1, text="Save Data", command=fp_data_save)
        btn_fp2globe = Button(chwin_row1, text="Draw Footprint(s) on the Globe", command=lambda: gui_mk_poly_data(ftprint_arr, missile_range, data_fname, mode2))
        
        ent_chart_fname.grid(row=0, column=0, ipadx=10, ipady=1)
        btn_chart_save.grid(row=0, column=1, ipadx=10, ipady=1, sticky='ew')
        ent_data_fname.grid(row=1, column=0, ipadx=10, ipady=1)
        btn_data_save.grid(row=1, column=1, ipadx=10, ipady=1, sticky='ew')
        btn_fp2globe.grid(row=2, column=0, columnspan=2, ipadx=10, ipady=1, sticky='ew')
        """
        trajchart_win.bind('<Escape>', lambda esc: trajchart_win.destroy())

def gui_balmis_trajcharts() :
    m_key = mtype_var.get()
    missile_data = rd.missile(m_key, rd_fname)
    gui_trajcharts(missile_data, True) #is_missile == True

def gui_interceptor_trajcharts() :
    i_key = itype_var.get()
    interceptor_data = rd.interceptor(i_key, rd_fname)
    #print(i_key, interc_data)
    #print("int_tc", interceptor_data)
    gui_trajcharts(interceptor_data, False) #is_missile == False

def gui_interceptor_flight() :
    i_key = itype_var.get()
    interceptor_data = rd.interceptor(i_key, rd_fname)
    #print(interceptor_data)
    trajectory_data = False
    ind_flight_dataprint = True
    i_range = bm.balmisflight(interceptor_data, trajectory_data, ind_flight_dataprint)
    print("Interceptor range = {:.0f} km".format(i_range/1000))


def gui_interceptor_trajectory() :
    i_key = itype_var.get()
    interceptor_data = rd.interceptor(i_key, rd_fname)
    #print(interceptor_data)
    trajectory_data = True
    ind_flight_dataprint = True
    trj = bm.balmisflight(interceptor_data, trajectory_data, ind_flight_dataprint)

    if check_fpa :
        i_range = -2 * radians(trj[len(trj) - 1, 2]) * R_e
        print("Interceptor range = {:.0f} km".format(i_range/1000))
        fmt = '%.2f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f','%.8f'
        hdr = "time, r_km, beta_deg, x_km, y_km, tv_angle_deg, fpa(v)_deg, fpa(x_y)_deg, d_vv, d_vh, vv, vh"
        file_it = trajectory_path + '/trajectory_i{}_fpa-check.csv'.format(i_key)
    else :
        i_range = trj[len(trj) - 1, 2] * R_e
        print("Interceptor range = {:.0f} km".format(i_range/1000))
        fmt = '%.2f','%.8f','%.8f','%.8f','%.8f'
        hdr = "time, R, alfa_r, veloc, accel"
        file_it = trajectory_path + '/trajectory_i{}.csv'.format(i_key)

    keep_trj_files = set_keep_trj_data_var.get()
    if keep_trj_files :
        m.keep_old_file(file_it)

    np.savetxt(file_it, trj, fmt = fmt, delimiter = ',', header = hdr)
    print("Interceptor trajectory saved to " + file_it)


def gui_missile_maxrange() :
    m_key = mtype_var.get()
    missile_data = rd.missile(m_key, rd_fname)
    gui_maxrange(missile_data)


def gui_interceptor_maxrange() :
    i_key = itype_var.get()
    interceptor_data = rd.interceptor(i_key, rd_fname)
    #interceptor_data["traj_type"] = "bal_mis"
    gui_maxrange(interceptor_data)


def gui_maxrange(r_data) :
    global maxrange_win
    global rocket_maxrange
    try :
        if maxrange_win.state() == "normal": maxrange_win.focus()
    except :
        maxrange_win = Toplevel(root)

        r_name = r_data['type']
        maxrange_win.title('Max Range Estimate of ' + r_name)
        maxrange_win.geometry('+500+160')
        
        #rc_menu_string ='copy-paste-cut'
        #maxrange_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        maxrange_win.focus_force()
        maxrange_win.bind('<Escape>', lambda esc: maxrange_win.destroy())
        
        def set_maxrange_params() :
            pass
            #ndr_list_str = det_range_list_var.get()
            #detrange_list = [eval(x) for x in ndr_list_str.split(',')]
            #det_range_list_var.set(ndr_list_str)
            #ent_n_detrange.delete(0, END)
            #ent_n_detrange.insert(0, str(detrange_list)[1:-1], font='bold')
            
        def rocket_maxrange() :
            maxrange_win.destroy()
            if True: #max_missile :
                gtheight_beg = gtheight_beg_var.get()
                gtheight_end = gtheight_end_var.get()

            gtangle_beg =  gtangle_beg_var.get()
            gtangle_end =  gtangle_end_var.get()
            maxrange_acc = maxrange_acc_var.get()

            if True: #max_missile :
                bm.balmis_maxrange(r_data, gtheight_beg, gtheight_end, gtangle_beg, gtangle_end, maxrange_acc)
            else : #to be removed
                bm.balmis_angle_opt(r_data, gtangle_beg, gtangle_end, maxrange_acc)
                

        if (r_data['traj_type'] == 'bal_mis') :
            max_missile = True
        elif (r_data['traj_type'] == 'albm') :
            max_missile = True
        else : # 'int_endo' or 'int_exo'
            max_missile = False
        
        if max_missile :
            lbl_gtheight_beg = Label(maxrange_win, text="GravTurn height search range begin, m")
            lbl_gtheight_end = Label(maxrange_win, text="GravTurn height search range end, m")
            lbl_gtangle_beg  = Label(maxrange_win, text="GravTurn angle search range begin, degr")
            lbl_gtangle_end  = Label(maxrange_win, text="GravTurn angle search range end, degr")
            #ent_gtheight_beg = CEntry(maxrange_win, textvariable=gtheight_beg_var)
            #ent_gtheight_end = CEntry(maxrange_win, textvariable=gtheight_end_var)
        else : 
            lbl_gtheight_beg = Label(maxrange_win, text="Rotation height search range begin, m")
            lbl_gtheight_end = Label(maxrange_win, text="Rotation height search range end, m")
            lbl_gtangle_beg  = Label(maxrange_win, text="Flight path angle search range begin, degr")
            lbl_gtangle_end  = Label(maxrange_win, text="Flight path angle search range end, degr")
    
        lbl_maxrange_acc = Label(maxrange_win, text="Max Range search threshold, per 1")

        ent_gtheight_beg = CEntry(maxrange_win, textvariable=gtheight_beg_var)
        ent_gtheight_end = CEntry(maxrange_win, textvariable=gtheight_end_var)
        ent_gtangle_beg  = CEntry(maxrange_win, textvariable=gtangle_beg_var)
        ent_gtangle_end  = CEntry(maxrange_win, textvariable=gtangle_end_var)
        ent_maxrange_acc = CEntry(maxrange_win, textvariable=maxrange_acc_var)

        btn_max_range = Button(maxrange_win, text='Run Max Range Estimation', command=lambda : call_longrun(rocket_maxrange))
    
        if True: #max_missile :
            lbl_gtheight_beg.grid(row=0, column=0, sticky='w')
            lbl_gtheight_end.grid(row=1, column=0, sticky='w')
            lbl_gtangle_beg.grid(row=2, column=0, sticky='w')
            lbl_gtangle_end.grid(row=3, column=0, sticky='w')
            lbl_maxrange_acc.grid(row=4, column=0, sticky='w')
                   
            ent_gtheight_beg.grid(row=0, column=1)
            ent_gtheight_end.grid(row=1, column=1)
            ent_gtangle_beg.grid(row=2, column=1)
            ent_gtangle_end.grid(row=3, column=1)
            ent_maxrange_acc.grid(row=4, column=1)

            btn_max_range.grid(row=5, column=0, columnspan=2, sticky='ew', ipady=3)

        else : # remove if "if" works for both
            lbl_gtangle_beg.grid(row=0, column=0, sticky='w')
            lbl_gtangle_end.grid(row=1, column=0, sticky='w')
            lbl_maxrange_acc.grid(row=2, column=0, sticky='w')
                   
            ent_gtangle_beg.grid(row=0, column=1)
            ent_gtangle_end.grid(row=1, column=1)
            ent_maxrange_acc.grid(row=2, column=1)

            btn_max_range.grid(row=3, column=0, columnspan=2, sticky='ew', ipady=3)


def gui_mk_poly_data(ftprint_arr, mis_range, data_fname, mode2=False) :
    """
    Draw footprint on the globe.

    Parameters
    ----------
    ftprint_arr : TYPE
        Array of one- or two-part footprints.
    mis_range : TYPE
        Missile range (can be calculated from Mode2 footprint data, but not from Mode1)
    data_fname : TYPE
        Name of the file to save footprint geo coordinates to.
    mode2 : TYPE, optional
        Whether footprint data are mode2. The default is False.

    Returns
    -------
    None.

    """
    root.withdraw()
    global num_loc
    global lbl_loc_num
    global ent_loc_lat
    global ent_loc_lon
    global ent_loc_azm
    global ent_loc_sec # sector
    num_loc = 1
    global geofootprint_win
    
    azm_dist = mis_range
    
    try :
        if geofootprint_win.state() == "normal": geofootprint_win.focus()
    except :
        geofootprint_win = Toplevel(root)

        geofootprint_win.title('Draw Footprint on the Globe')
        geofootprint_win.geometry('+100+160')
        
        geofootprint_win.config(border=3, relief='ridge')
        
        geo_sphere = Geodesic(R_e, 0)

        def read_location_data() :
            global num_loc
            global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec # sector

            filetypes = (("json files","*.json *.geojson"),("geojson files","*.geojson"),("all files","*.*"))
            f_name = fd.askopenfilename(title="Choose file to open or enter/edit file name", initialdir=geo_path, initialfile=geo_fname, filetypes=filetypes)
            if f_name :
                geo_bmd = m.load_data(f_name)
                print("Location data read from ", f_name)
            else :
                return

            if geo_bmd :
                for i_del in range(num_loc) :
                    lbl_loc_num[i_del].grid_remove()
                    ent_loc_lat[i_del].grid_remove()
                    ent_loc_lon[i_del].grid_remove()
                    ent_loc_azm[i_del].grid_remove()
                    ent_loc_sec[i_del].grid_remove()

                btn_add_loc.grid_remove()
                if num_loc > 1 :
                    btn_del_loc.grid_remove()
                    
            if 'features' in geo_bmd :
                num_loc = len(geo_bmd['features']) # number of defense installations                
                
                ilp = []
                mlp = []
                azm = []
                sec = []
                lbl_loc_num = []
                ent_loc_lat = []
                ent_loc_lon = []
                ent_loc_azm = []
                ent_loc_sec = []

                for k_0 in range(num_loc):
                    ilp.append(geo_bmd['features'][k_0]['geometry']['coordinates'][0])
                    mlp.append(geo_bmd['features'][k_0]['geometry']['coordinates'][1])
                    ilon, ilat = ilp[k_0]
                    mlon, mlat = mlp[k_0]

                    az_im = geo_sphere.Inverse(ilat, ilon, mlat, mlon)
                    azm.append(az_im['azi1'])

                    def_sector = defense_sector_angle
                    if  'properties' in geo_bmd['features'][k_0] :
                        if 'sector' in  geo_bmd['features'][k_0]['properties'] :
                            def_sector = geo_bmd['features'][k_0]['properties']['sector']
                    sec.append(def_sector)

                    lbl_loc_num.append(Label(frame_gwrow1, text=str(k_0 + 1)))
                    ent_loc_lat.append(CEntry(frame_gwrow1, bg='white', width=30))
                    ent_loc_lon.append(CEntry(frame_gwrow1, bg='white', width=30))
                    ent_loc_azm.append(CEntry(frame_gwrow1, bg='white', width=30))
                    ent_loc_sec.append(CEntry(frame_gwrow1, bg='white', width=10))
                    
                    lbl_loc_num[k_0].grid(row=(k_0 + 1), column=0)
                    ent_loc_lat[k_0].grid(row=(k_0 + 1), column=1)
                    ent_loc_lon[k_0].grid(row=(k_0 + 1), column=2)
                    ent_loc_azm[k_0].grid(row=(k_0 + 1), column=3)
                    ent_loc_sec[k_0].grid(row=(k_0 + 1), column=4)

                    ent_loc_lat[k_0].insert(0, ilp[k_0][1])
                    ent_loc_lon[k_0].insert(0, ilp[k_0][0])
                    ent_loc_azm[k_0].insert(0, azm[k_0])
                    ent_loc_sec[k_0].insert(0, sec[k_0])

                    btn_add_loc.grid(row=1, column=5, ipadx=3)
                    if num_loc > 1 :
                        btn_del_loc.grid(row=num_loc, column=5, ipadx=5)

            return
        
        
        def save_location_data() :
            global num_loc
            #global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec
                        
            loclat = []
            loclon = []
            locazm = []
            locsec = []
            for i_f in range(num_loc) :
                loclat.append(float(ent_loc_lat[i_f].get()))
                loclon.append(float(ent_loc_lon[i_f].get()))
                locazm.append(float(ent_loc_azm[i_f].get()))
                locsec.append(float(ent_loc_sec[i_f].get()))
            
            featurelist = []
            for i_ln in range(num_loc):
                line_plist = []
                line_plist.append([loclon[i_ln], loclat[i_ln]])
                p = geo_sphere.Direct(loclat[i_ln], loclon[i_ln], locazm[i_ln], azm_dist)
                line_plist.append([p['lon2'], p['lat2']])
                imline = geojson.LineString(line_plist)
                imline_f = geojson.Feature(geometry=imline, properties = {'stroke': 'red', 'sector': locsec[i_ln]})
                featurelist.append(imline_f)
                
            fp_featcoll = geojson.FeatureCollection(featurelist)

            f_name = geo_path + '/geo-bmd-data.json'
            filetypes = (("json files","*.json"),("all files","*.*"))
            f_name = fd.asksaveasfilename(confirmoverwrite=True, title="Choose file to save to or enter/edit file name", initialdir=geo_path, initialfile=geo_fname, filetypes=filetypes)
            if f_name :
                keep = True
                m.save_data(fp_featcoll, f_name, keep)
                print("Footprints location data saved to ", f_name)
            else :
                print("No file selected, data not saved")

            return
                  
        
        def footprint_2_globe(save_geo_footrpints=True) :
            global num_loc
            #global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec
                        
            loclat = []
            loclon = []
            locazm = []
            locsec= []
            for i_f in range(num_loc) :
                loclat.append(float(ent_loc_lat[i_f].get()))
                loclon.append(float(ent_loc_lon[i_f].get()))
                locazm.append(float(ent_loc_azm[i_f].get()))
                locsec.append(float(ent_loc_sec[i_f].get()))
            
            featurelist = []

            for fp_pair in ftprint_arr :
                #print(fp_pair)
                if (len(fp_pair) > 0) and (len(fp_pair[0]) > 0) :
                    if type(fp_pair[0][0]) != np.ndarray : #i.e. mode1
                        fp_pair = [fp_pair, []]
                        md2 = False # mode 1
                    else:
                        md2 = True  # mode 2
                    
                    for footprint in fp_pair :
                        if len(footprint) > 0 :
                            
                            for i0 in range(num_loc):
                                ilon = loclon[i0]
                                ilat = loclat[i0]
                                iazm = locazm[i0]
                                polylist = []
                                if not md2 : # Mod1 Footprint data array: [angle, distance, accuracy, x, y]
                                    fplen = len(footprint)
                                    for i1 in range(fplen) :
                                        az_i = iazm + footprint[i1][0]
                                        s_i  = footprint[i1][1]
                                        p_i = geo_sphere.Direct(ilat, ilon, az_i, s_i)
                                        polylist.append([p_i['lon2'], p_i['lat2']])
                                else :  	# Mod2 Footprint data array: [[angle, shift, acc, x, y], [angle, shift, acc, x, y]] (for two-part)
                                    fplen = len(footprint)
                                    shift = footprint[0][1]
                                    mrange = shift - footprint[0][4] * 1000
                                    for i2 in range(fplen) :
                                        shift = footprint[i2][1]
                                        p_i0 = geo_sphere.Direct(ilat, ilon, iazm, shift)
                                        az_i = p_i0['azi2'] - 180 + degrees(footprint[i2][0])
                                        if footprint[i2][2] == 2 :
                                            p_i = geo_sphere.Direct(p_i0['lat2'], p_i0['lon2'], az_i, mrange * mrl_factor2)
                                        elif footprint[i2][2] == 3 :
                                            p_i = geo_sphere.Direct(p_i0['lat2'], p_i0['lon2'], az_i, mrange * mrl_factor1)
                                        else :
                                            p_i = geo_sphere.Direct(p_i0['lat2'], p_i0['lon2'], az_i, mrange)
                                        """ via x, y 
                                        p__i = geo_sphere.Direct(ilat, ilon, iazm, footprint[i2][4] * 1000)
                                        p_i  = geo_sphere.Direct(p__i['lat2'], p__i['lon2'], 90 + p__i['azi2'], footprint[i2][3] * 1000)
                                        """
                                        polylist.append([p_i['lon2'], p_i['lat2']])
                                
                                fp_polygon = geojson.Polygon([polylist])
                                poly_f = geojson.Feature(geometry = fp_polygon, properties = {'fill': 'blue', 'fill-opacity': 0.3})
                                ilp_f0 = geojson.Point([ilon, ilat])
                                ilp_f = geojson.Feature(geometry = ilp_f0, properties = {})
                    
                                line_plist = [] #Defense Direction -- same line added 2 times
                                for d_dist in np.linspace(0, azm_dist, 30):
                                    p = geo_sphere.Direct(ilat, ilon, iazm, d_dist)
                                    line_plist.append([p['lon2'], p['lat2']])
                                    imline = geojson.LineString(line_plist)
                                    imline_f = geojson.Feature(geometry=imline, properties = {'stroke': 'red'})
                                    
                                featurelist.append(ilp_f)
                                featurelist.append(imline_f)
                                featurelist.append(poly_f)
                                
                else : #no footprint
                    print("No Footprint to Plot")
                    return

            fp_featcoll = geojson.FeatureCollection(featurelist)
            fp_featcoll_string = json.dumps(fp_featcoll, separators=(',', ':'))

            if save_geo_footrpints :
                gd_path, gd_fname = os.path.split(data_fname)
                gdata_fname = "geo-" + gd_fname
                print("data_fname = {}, gdata_fname = {}".format(data_fname, gdata_fname))
                filetypes = (("json files","*.json"),("all files","*.*"))
                f_name = fd.asksaveasfilename(confirmoverwrite=True, title="Choose file to save geo-footprints to or enter/edit file name", initialdir=footprint_path, initialfile=gdata_fname, filetypes=filetypes)
                if f_name :
                    keep = True
                    m.save_data(fp_featcoll, f_name, keep)
                    print("Footprints location data saved to ", f_name)

            uri = urllib.parse.quote(fp_featcoll_string)
            url = 'https://geojson.io/#data=data:application/json,' + uri
            
            try :           
                webbrowser.open(url, 1, True)
            except Exception as error :
                print("*** An exception occurred: >>>", error, "<<<")
                err_string = getattr(error, 'message', repr(error))
                #print(err_string)
                if "filepath too long" in err_string :
                    too_long_data_str = """* The data is too long to pass to the browser directly.
* Save the file using \"Save footprints\" button and then 
* open it at the geojson.io website manually."""
                    print(too_long_data_str)

            return
        

        def intersection_2_globe(save_geo_footrpints=True) :
            """
            Cumputes sectoral footprint (intersection of several footprints covering defense sector size "angle" with angle increment "angle_step")

            Parameters
            ----------
            save_geo_footrpints : TYPE, optional
                DESCRIPTION. The default is True. save resulting foortprint to geojson file

            Returns
            -------
            None.

            """
            angle = defense_sector_angle
            angle_step = def_sector_step_var.get()
            global num_loc
            #global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec
                        
            loclat = []
            loclon = []
            locazm = []
            locsec = []
            for i_f in range(num_loc) :
                loclat.append(float(ent_loc_lat[i_f].get()))
                loclon.append(float(ent_loc_lon[i_f].get()))
                locazm.append(float(ent_loc_azm[i_f].get()))
                locsec.append(float(ent_loc_sec[i_f].get()))
            
            featurelist = []

            for footprint in ftprint_arr :
                if (len(footprint) > 0) and (len(footprint[0]) > 0) :
                    for i0 in range(num_loc):
                        ilon  = loclon[i0]
                        ilat  = loclat[i0]
                        angle = locsec[i0]
                        iazm  = locazm[i0] #- angle/2
                        #print("Main: iazm={} angle={} angle_step={}".format(iazm, angle, angle_step))
                        df_path, df_fname = os.path.split(data_fname)
                        df_name, df_ext   = os.path.splitext(df_fname)
                        df_name += '.png'
                        ifeaturelist = isec.ftp_intersection(footprint, ilon, ilat, iazm, azm_dist, angle, angle_step, root, df_name)
    
                        featurelist.extend(ifeaturelist)
                                
                else : #no footprint
                    print("No Footprint to Plot")
                    return
                
            fp_featcoll = geojson.FeatureCollection(featurelist)
            fp_featcoll_string = json.dumps(fp_featcoll, separators=(',', ':'))

            if save_geo_footrpints :
                gd_path, gd_fname = os.path.split(data_fname)
                gdata_fname = "geo-" + gd_fname
                print("data_fname = {}, gdata_fname = {}".format(data_fname, gdata_fname))
                filetypes = (("json files","*.json"),("all files","*.*"))
                f_name = fd.asksaveasfilename(confirmoverwrite=True, title="Choose file to save geo-footprints to or enter/edit file name", initialdir=footprint_path, initialfile=gdata_fname, filetypes=filetypes)
                if f_name :
                    keep = True
                    m.save_data(fp_featcoll, f_name, keep)
                    print("Footprints location data saved to ", f_name)

            uri = urllib.parse.quote(fp_featcoll_string)
            url = 'https://geojson.io/#data=data:application/json,' + uri
            
            try :
                #pass
                webbrowser.open(url, 1, True)
            except Exception as error :
                print("*** An exception occurred: >>>", error, "<<<")
                err_string = getattr(error, 'message', repr(error))
                #print(err_string)
                if "filepath too long" in err_string :
                    too_long_data_str = """* The data is too long to pass to the browser directly.
* Save the file using \"Save footprints\" button and then 
* open it at the geojson.io website manually."""
                    print(too_long_data_str)

            return

        def calc_angles() :
            global num_loc
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec
                        
            loclat = []
            loclon = []
            locazm = []
            locsec = []
            for i_f in range(num_loc) :
                loclat.append(float(ent_loc_lat[i_f].get()))
                loclon.append(float(ent_loc_lon[i_f].get()))

            angles_window = Toplevel()
            angles_window.title("Country Angles")
            
            Label(angles_window, text="Country").grid(row=0, column=0, padx=10, pady=5)
            entry1 = Entry(angles_window)
            entry1.grid(row=0, column=1, padx=10, pady=5)
            
            Label(angles_window, text="Max distance, km").grid(row=1, column=0, padx=10, pady=5)
            entry2 = Entry(angles_window)
            entry2.grid(row=1, column=1, padx=10, pady=5)

            def on_button_click():
                country = entry1.get()
                print(entry1.get(), entry2.get())
                if entry2.get() :
                    max_distance = float(entry2.get()) * 1000
                else :
                    max_distance = ''

                for i_d in range(num_loc) :
                    target_coords = (loclon[i_d], loclat[i_d])
                    (def_dir, sec_size) = calculate_angles(country, target_coords, max_distance)
                    ent_loc_azm[i_d].delete(0, END)
                    ent_loc_azm[i_d].insert(0, def_dir)
                    ent_loc_sec[i_d].delete(0, END)
                    ent_loc_sec[i_d].insert(0, sec_size)
            
            # Button to call func1
            Button(angles_window, text="Compute", command=on_button_click).grid(row=2, column=0, columnspan=2, pady=10)

            return


        def add_location() :
            global num_loc
            global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec

            lbl_loc_num.append(Label(frame_gwrow1, text=str(num_loc + 1)))
            ent_loc_lat.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_lon.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_azm.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_sec.append(CEntry(frame_gwrow1, bg='white', width=10))
            
            lbl_loc_num[num_loc].grid(row=(num_loc+1), column=0, padx=(10, 0))
            ent_loc_lat[num_loc].grid(row=(num_loc+1), column=1)
            ent_loc_lon[num_loc].grid(row=(num_loc+1), column=2)
            ent_loc_azm[num_loc].grid(row=(num_loc+1), column=3)
            ent_loc_sec[num_loc].grid(row=(num_loc+1), column=4)

            if num_loc > 1 :
                btn_del_loc.grid_remove()
            
            btn_del_loc.grid(row=num_loc+1, column=5, ipadx=5)

            num_loc += 1

            return
            

        def del_location() : # removes the last item
            global num_loc
            global lbl_loc_num
            global ent_loc_lat
            global ent_loc_lon
            global ent_loc_azm
            global ent_loc_sec

            lbl_loc_num[num_loc - 1].grid_remove()
            ent_loc_lat[num_loc - 1].grid_remove()
            ent_loc_lon[num_loc - 1].grid_remove()
            ent_loc_azm[num_loc - 1].grid_remove()
            ent_loc_sec[num_loc - 1].grid_remove()

            lbl_loc_num.pop() # remove the last item
            ent_loc_lat.pop()
            ent_loc_lon.pop()
            ent_loc_azm.pop()
            ent_loc_sec.pop()
            
            btn_del_loc.grid_remove()
            if num_loc > 2 :
                btn_del_loc.grid(row=num_loc-1, column=5, ipadx=5)

            num_loc -= 1

            return
        
        """ gui_mk_poly_data main code """
        frame_gwrow1 = Frame(geofootprint_win, border=1)
        frame_gwrow2 = Frame(geofootprint_win, border=1)
        frame_gwrow1.grid(column=0, row=0, sticky='ew')
        frame_gwrow2.grid(column=0, row=1, sticky='ew')
        
        frame_gwrow2.columnconfigure(0, weight=1, uniform='geobuttons')
        frame_gwrow2.columnconfigure(1, weight=1, uniform='geobuttons')
        frame_gwrow2.columnconfigure(2, weight=1, uniform='geobuttons')
        frame_gwrow2.columnconfigure(3, weight=1, uniform='geobuttons')
        frame_gwrow2.columnconfigure(4, weight=1, uniform='geobuttons')
        frame_gwrow2.columnconfigure(5, weight=1, uniform='geobuttons')
   
        lbl_loc_num_hdr   = Label(frame_gwrow1, text="#")
        lbl_loc_lat_hdr   = Label(frame_gwrow1, text="ILP Location Latitude\n -90 (South) to 90 (North)")
        lbl_loc_lon_hdr   = Label(frame_gwrow1, text="ILP Location Longitude\n -180 (-90=West) to 180 (90=East)")
        lbl_direction_hdr = Label(frame_gwrow1, text="Direction to MLP (Azimuth)\n -180 (-90=West) to 180 (90=East)")
        lbl_sector_hdr    = Label(frame_gwrow1, text="Sector\nsize")
        lbl_country_hdr   = Label(frame_gwrow1, text="Country\n∠")
        btn_country_angle = Button(frame_gwrow1, text="∠", command=calc_angles)
        
        descr_str = """To position the footprint on the globe (in one or more locations) enter coordinates
of the interceptor launch point(s) and direction(s) to the missile launch point(s).
Alternatively, these data can be entered at https://geojson.io by drawing one or more two-point
lines each line representing interceptor point location and missile point location, and
then saving the json code to a file. This file can then be loaded here using the \'Load locations\' button.
\'Save locations\' button saves interceptor launch point(s) location data in geojson format.
\'Draw footprints\' button calculates footprint coordinates, and then opens https://geojson.io to show
footprints on the globe.
\'Save footprints and Draw\' button calculates footprint coordinates, saves them to a .json file and then opens
https://geojson.io to show footprints on the globe. The saved file can be opened with Google Earth Pro (c) Google LLC"""
        
        if tooltips: tt = ToolTip(frame_gwrow1, msg=descr_str, delay=0.5)

        lbl_loc_num = []
        ent_loc_lat = []
        ent_loc_lon = []
        ent_loc_azm = []
        ent_loc_sec = []
        btn_del_loc = Button(frame_gwrow1, text="-", command=del_location)
        btn_add_loc = Button(frame_gwrow1, text="+", command=add_location)
        #btn_empty   = Button(frame_gwrow1, text=" ")
        #btn_empty.configure(state='disabled')
        
        for i_l in range(num_loc) :
            lbl_loc_num.append(Label(frame_gwrow1, text=str(i_l + 1)))
            ent_loc_lat.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_lon.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_azm.append(CEntry(frame_gwrow1, bg='white', width=30))
            ent_loc_sec.append(CEntry(frame_gwrow1, bg='white', width=10))
            
            lbl_loc_num[i_l].grid(row=(i_l + 1), column=0, padx=(10, 0))
            ent_loc_lat[i_l].grid(row=(i_l + 1), column=1)
            ent_loc_lon[i_l].grid(row=(i_l + 1), column=2)
            ent_loc_azm[i_l].grid(row=(i_l + 1), column=3)
            ent_loc_sec[i_l].grid(row=(i_l + 1), column=4)

        btn_add_loc.grid(row=1, column=5, ipadx=3)
            
        if num_loc > 1 :
            btn_del_loc.grid(row=num_loc, column=5, ipadx=5)
               
        btn_load_data = Button(frame_gwrow2, text="Load\nLocations", command=read_location_data)
        btn_save_data = Button(frame_gwrow2, text="Save\nLocations", command=save_location_data)
        btn_draw_data = Button(frame_gwrow2, text="Draw\nFootprints", command=lambda : footprint_2_globe(False))
        btn_dsav_data = Button(frame_gwrow2, text="Save Footprints\nand Draw", command=lambda : footprint_2_globe(True))
        btn_intersect = Button(frame_gwrow2, text="Draw Intersection\nFootprint", command=lambda : intersection_2_globe(False))
        btn_intersave = Button(frame_gwrow2, text="Save Intersection\nand Draw", command=lambda : intersection_2_globe(True))
        
        lbl_loc_num_hdr.grid(row=0, column=0, padx=(10, 0))
        lbl_loc_lat_hdr.grid(row=0, column=1)
        lbl_loc_lon_hdr.grid(row=0, column=2)
        lbl_direction_hdr.grid(row=0, column=3, padx=(0, 10))
        lbl_sector_hdr.grid(row=0, column=4, padx=(0, 10))
        btn_country_angle.grid(row=0, column=5)

        btn_load_data.grid(row=0, column=0, sticky='ew')
        btn_save_data.grid(row=0, column=1, sticky='ew')
        btn_draw_data.grid(row=0, column=2, sticky='ew')
        btn_dsav_data.grid(row=0, column=3, sticky='ew')
        btn_intersect.grid(row=0, column=4, sticky='ew')
        btn_intersave.grid(row=0, column=5, sticky='ew')

        def poly_show_root_window() :
            geofootprint_win.destroy()
            root.deiconify()
    
        #rc_menu_string ='copy-paste-cut'
        #geofootprint_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))
    
        def win_destroy() :
            if tooltips:
                tt.status='outside'
                tt.withdraw()
            poly_show_root_window()
    
        geofootprint_win.focus_force()
        geofootprint_win.bind('<Escape>', lambda esc: win_destroy())
        geofootprint_win.protocol("WM_DELETE_WINDOW", win_destroy)


def gui_fpchart_n(ftprint_arr, 
                  label_arr, 
                  info_string, 
                  title_string,
                  chart_fname,
                  header_string,
                  missile_range,
                  data_fname,
                  mode2=False,
                  bw=False) :
    
    global chart_win

    if R_N == 1 : # TODO -- restore condition
        new_chart_fname = chart_fname
        new_data_fname = data_fname
        new_info_string = info_string
        new_header_string = header_string
    else :
        file_name, file_extension = os.path.splitext(chart_fname)
        new_chart_fname = file_name + "-" + "R_N{}".format(R_N) + file_extension               
        file_name, file_extension = os.path.splitext(data_fname)
        new_data_fname = file_name + "-" + "R_N{}".format(R_N) + file_extension 
        new_info_string = info_string + " R_N={}".format(R_N)
        new_header_string = "R_N={} ".format(R_N) + header_string 

    show_titles = show_chart_titles_var.get()
    if not show_titles :
        title_string    = ''
        new_info_string = ''

    try :
        if chart_win.state() == "normal" : chart_win.destroy()
    except :
        pass
    finally :
        chart_win = Toplevel(root)
        chart_win.title('Footprint Chart')
        chart_win.geometry("+500+100")
        
        chwin_row0 = Frame(chart_win, border=1)
        chwin_row1 = Frame(chart_win, border=1)
        chwin_row1.columnconfigure(0, weight=1)
        chwin_row1.columnconfigure(1, weight=1)
        chwin_row1.columnconfigure(2, weight=1)
        chwin_row1.columnconfigure(3, weight=1)
        
        chwin_row0.pack()
        chwin_row1.pack()  
    
        #rc_menu_string ='copy-paste-cut'
        #chart_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def fp_draw () :
            fp_plot()
        
            canvas = FigureCanvasTkAgg(fig, chwin_row0)
            canvas.draw()
        
            # placing the canvas on the Tkinter chart_win
            canvas.get_tk_widget().pack()
        
            # creating the Matplotlib toolbar
            #toolbar = NavigationToolbar2Tk(canvas, chart_win)
            #toolbar.update()
        
            # placing the toolbar on the Tkinter chart_win
            #canvas.get_tk_widget().pack()
            
        def fp_save() :
            fp_plot()
            keep_chart = set_keep_fp_chart_var.get()
            #print(keep_chart)
            save_chart_fname = ent_chart_fname.get()
            if keep_chart :
                m.keep_old_file(save_chart_fname)
            ax.get_figure().savefig(save_chart_fname, dpi=300, bbox_inches='tight', pad_inches=0.2)
            print("Footprint Chart saved to ", save_chart_fname)
            btn_chart_save.configure(state='disabled')
    
    
        def fp_data_save() :
            keep_data = set_keep_fp_data_var.get()
            #print(keep_data)
            save_data_fname = ent_data_fname.get()
            if keep_data :
                    m.keep_old_file(save_data_fname)
            if not mode2 :
                fp_arr = [fp_i.tolist() for fp_i in ftprint_arr]
            else :
                fp_arr = [[fp1.tolist(), fp2.tolist()] for [fp1, fp2] in ftprint_arr]
            #if len(ftprint_arr) > 1 : fp_arr = ftprint_arr
            #else : fp_arr = ftprint_arr[0].tolist()
    
            data2save = new_header_string, fp_arr
            m.save_data(data2save, save_data_fname, keep_data)

            print("Footprint Data saved to ", save_data_fname)
            btn_data_save.configure(state='disabled')
    
    
        def fp_plot() :
            global fig
            global ax
    
            fig = Figure(figsize = (8, 5), dpi=100)
            fig.suptitle(title_string, fontsize=12)
            
            ax = fig.add_subplot(111)
    
            n_arr = len(ftprint_arr)
    
            if not mode2 :
                if (n_arr > 1) :
                    if bw :
                        linestyle_cycler = cycler('linestyle', ['-', '--', ':', '-.', (0, (3, 3, 1, 3, 1, 3))])
                    else : 
                        linestyle_cycler = cycler('color', ['tab:blue', 'r', 'g', 'm', 'k']) +\
                                       cycler('linestyle', ['-', '--', ':', '-.', (0, (3, 3, 1, 3, 1, 3))])
                    ax.set_prop_cycle(linestyle_cycler)
            else :
                if bw :
                    linestyle_cycler = cycler('linestyle', ['-', '-', '--', '--', ':', ':', '-.', '-.', (0, (3, 3, 1, 3, 1, 3)), (0, (3, 3, 1, 3, 1, 3))])
                else : 
                    linestyle_cycler = cycler('color', ['tab:blue', 'tab:blue', 'r', 'r', 'g', 'g', 'm', 'm', 'k', 'k']) +\
                                   cycler('linestyle', ['-', '-', '--', '--', ':', ':', '-.', '-.', (0, (3, 3, 1, 3, 1, 3)), (0, (3, 3, 1, 3, 1, 3))])
                ax.set_prop_cycle(linestyle_cycler)

            if not mode2 :    
                for i_arr in range(n_arr) :
                    xpoints = ftprint_arr[i_arr][:, 3]
                    ypoints = ftprint_arr[i_arr][:, 4]
                    if show_titles :
                        label_i = label_arr[i_arr]
                    else :
                        label_i = ''
                    ax.plot(xpoints, ypoints, label = label_i) #, c='C0') # , marker='.'
            else :
                for i_arr in range(n_arr) :
                    xpoints1 = ftprint_arr[i_arr][0][:, 3]
                    ypoints1 = ftprint_arr[i_arr][0][:, 4]
                    xpoints2 = ftprint_arr[i_arr][1][:, 3]
                    ypoints2 = ftprint_arr[i_arr][1][:, 4]
                    if show_titles :
                        label_i = label_arr[i_arr]
                    else :
                        label_i = ''
                    ax.plot(xpoints1, ypoints1, label = label_i) #, c='C0') # , marker='.'
                    ax.plot(xpoints2, ypoints2, label = '') #, label = label_arr[i_arr]) #, c='C0') # , marker='.'
                
            ax.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
            ax.set_title(new_info_string, fontsize=10, y=0.984)
        
            if show_titles and (n_arr > 1) :
                ax.legend(loc='best', frameon=False, framealpha=1.0)
                
            ax.set_xlabel('crossrange, km')
            ax.set_ylabel('defense downrange, km')
    
            ax.axis('equal')
            ax.grid()
        """ End of internal functions """
        
        fp_draw()
            
        ent_chart_fname = CEntry(chwin_row1, bg='white', width=50)
        ent_chart_fname.insert(0, new_chart_fname)
        btn_chart_save = Button(chwin_row1, text="Save Chart", command=fp_save)
        ent_data_fname = CEntry(chwin_row1, bg='white', width=50)    
        ent_data_fname.insert(0, new_data_fname)
        btn_data_save = Button(chwin_row1, text="Save Data", command=fp_data_save)
        btn_fp2globe = Button(chwin_row1, text="Draw Footprint(s) on the Globe", command=lambda: gui_mk_poly_data(ftprint_arr, missile_range, data_fname, mode2))
        
        ent_chart_fname.grid(row=0, column=0, ipadx=10, ipady=1)
        btn_chart_save.grid(row=0, column=1, ipadx=10, ipady=1, sticky='ew')
        ent_data_fname.grid(row=1, column=0, ipadx=10, ipady=1)
        btn_data_save.grid(row=1, column=1, ipadx=10, ipady=1, sticky='ew')
        btn_fp2globe.grid(row=2, column=0, columnspan=2, ipadx=10, ipady=1, sticky='ew')

        chart_win.bind('<Escape>', lambda esc: chart_win.destroy())


def min_detrange() :
    m_type = mtype_var.get()
    i_type = itype_var.get()
    emode_sls = emode_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()

    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    print("Calculation of minimum detection range for defending the interceptor launch point to be possible")
    print("Missile type m{} trajectory calculating...".format(m_type), end='')
    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    if mrange > bm_range_limit :
        print("\rSTOP: Missile range is too long for footprint calculation. The limit is {} km\n".format(bm_range_limit/1000))
        return False
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))

    n_stages = len(missile_data["t_bu"])
    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][n_stages - 1]
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    interceptor_data = rd.interceptor(i_type, rd_fname)

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000
        
    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    if emode_sls :
        s_func = ss.sls_search
    else :
        s_func = ss.short_search
    
    dr_min = 10000
    dr_max = 15000000
    dr_start = 1000000
    t_acc  = .01
    f_b = dr_start
    ilp_ok = s_func(trj, int_table, h_int_min, t_int_lnc, 0, 0, op_range, f_b, t_delay, h_discr)
    while not ilp_ok :
        if f_b == dr_max :
            print("Iinterceptor launch point undefendable with any detection range\n")
            return False
        f_b *= 2
        f_b = min(f_b, dr_max)
        ilp_ok = s_func(trj, int_table, h_int_min, t_int_lnc, 0, 0, op_range, f_b, t_delay, h_discr)
    
    f_a = 0
    while True :
        f_x = f_a + (f_b - f_a) / 2
        f_xy = s_func(trj, int_table, h_int_min, t_int_lnc, 0, 0, op_range, f_x, t_delay, h_discr)
        if f_xy :
            f_b = f_x
        else :
            f_a = f_x
        #if ((f_b - f_a) < f_b * t_acc) or (f_b < dr_min) :
        if ((f_b - f_a) < 1000) or (f_b < dr_min) :
            #print("\nf_a = {:.2f} km f_b = {:.2f} km f_b - f_a = {:.2f} km".format((f_a)/1000,(f_b)/1000, (f_b - f_a)/1000))
            break
    if f_a :
        print("h_int_min={:.1f}, t_int_lnc={:.1f} op_range={:.1f} t_delay={:.1f} h_discr={:.1f}".format(h_int_min/1000, t_int_lnc, op_range/1000, t_delay, h_discr/1000))
        print("Interceptor {} vs Missile {} : Minimum detection range = {} km\n".format(i_type, m_type, ceil(f_b/1000)))
    else :
        print("h_int_min={:.1f}, t_int_lnc={:.1f} op_range={:.1f} t_delay={:.1f} h_discr={:.1f}".format(h_int_min/1000, t_int_lnc, op_range/1000, t_delay, h_discr/1000))
        print("Interceptor {} vs Missile {} : Minimum detection range is less than {:.0f} km\n".format(i_type, m_type, dr_min/1000))
        


def gui_footprint() :
    m_type = mtype_var.get()
    i_type = itype_var.get()
    mode2 = fp_calc_mode_var.get()
    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    #angle_step_mode2 = angle_step_mode2_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    plot_hit_charts = plot_hit_charts_var.get()
    hit_chart_angle = hit_chart_angle_var.get()

    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    if mode2 :
        print("\nFootprint calculation mode2 routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    else :
        print("\nFootprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    print("Missile type m{} trajectory calculating...".format(m_type))#, end='')

    if stdout_to_file_var.get() :  # possibly delete? $$$ #TODO
        file_name = 'footprint_m{}_i{}{}.txt'.format(m_type, i_type, t_stamp)
        if set_keep_stdout_file_var.get() :
            m.keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
    
    if mrange > bm_range_limit :
        print("STOP: Missile range is too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return False

    dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    n_stages = len(missile_data["t_bu"])
    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"]) - missile_data["t_delay"][n_stages - 1]
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    det_range = 0.0
    interceptor_data = rd.interceptor(i_type, rd_fname)
            
    if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
        if len(interceptor_data["det_range"]) > m_type :
            det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
        else :
            print("No detection range value found for this missile. Detection range is set to 0.")
            print("For quick test run 'Multi-Footprint by Detection Range' routine specifying one or more detection range.")
    else :
        print("No detection range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'Multi-Footprint by Detection Range' routine specifying one or more detection range.")

    if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
         det_range *= 1000

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000
        
    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    fp_st = time.time()
    
    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    search_func = ss.short_search
    search_type = "Shoot_Once"
    save_label = "son"

    if emode_sls :
        search_func = ss.sls_search
        search_type = "Shoot_Look_Shoot"
        save_label = "sls"
        
    print("Type of interception: " + search_type)

    if not mode2 :
        footprint_tab = fp.footprint_calc_v2(search_func, 
                                         trj,
                                         int_table,
                                         h_int_min,
                                         t_int_lnc,
                                         angle_step,
                                         op_range,
                                         det_range,
                                         t_delay,
                                         h_discr,
                                         acc,
                                         dist,
                                         plot_hit_charts,
                                         hit_chart_angle,
                                         m_type,
                                         i_type
                                         )
    else :
        if emode_sls :
            search_func = ss.sls_search2
        else :
            search_func = ss.short_search2

        footprint_tab2 = ss.footprint_mode2(search_func, 
                                         trj,
                                         int_table,
                                         h_int_min,
                                         t_int_lnc,
                                         angle_step_mode2, # global parameter
                                         op_range,
                                         det_range,
                                         t_delay,
                                         h_discr,
                                         acc,
                                         num_steps_mode2,
                                         plot_hit_charts,
                                         hit_chart_angle,
                                         m_type,
                                         i_type
                                         )
        footprint_tab = footprint_tab2[0] # see if np.any below

    """
    if mode2 :
            part1, part2 = footprint_tab2
            if np.any(part2) :
                footprint_tab = [part1, part2]
                label_arr = ['part1', 'part2']         
            else :
                footprint_tab = [part1]
                label_arr = ['']
    """

    if np.any(footprint_tab) :
        if not mode2 :
            if det_range :
                header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
                chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
            else :
                header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type)
                chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type)
            data_fname = footprint_path + "/footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
            
            if op_range :
                title_str = "Footprint: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            chart_fname = footprint_path + "/footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
    
            bw = True
            label_arr = ['']

            gui_fpchart_n([footprint_tab], label_arr, chart_info_str, title_str, chart_fname, header_str, mrange, data_fname, False, bw) # mode2 = False

        else :
            if det_range :
                header_str = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type)
                chart_info_str = "h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type)
            else :
                header_str = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} sat_delay={} km h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type)
                chart_info_str = "h_int_min={} km t_int_lnc={} num_steps2={} sat_delay {} h_discr={} {}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type)
            data_fname = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
            if op_range :
                title_str = "Footprint Mode2: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint Mode2: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            chart_fname = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
    
            bw = True
            label_arr = ['']

            gui_fpchart_n([footprint_tab2], label_arr, chart_info_str, title_str, chart_fname, header_str, mrange, data_fname, True, bw) # mode2 = True
                

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file_var.get() :
        sys.stdout = original
        
    if mode2 :
        return footprint_tab2
    else :
        return footprint_tab
        
""" END of gui_footprint """


def gui_double_footprint() :
    """ The first footprint for shoote_once, the second for shoot-look-shoot """
    m_type = mtype_var.get()
    i_type = itype_var.get()
    mode2 = fp_calc_mode_var.get()
    #emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    #angle_step_mode2 = angle_step_mode2_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()

    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    print("\nDouble Footprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    print("Missile type m{} trajectory calculating...".format(m_type), end='')

    if stdout_to_file_var.get() :  # possibly delete? $$$ #TODO
        file_name = 'double_footprint_m{}_i{}{}.txt'.format(m_type, i_type, t_stamp)
        if set_keep_stdout_file_var.get() :
            m.keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
    
    if mrange > bm_range_limit :
        print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return False

    dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    det_range = 0.0
    interceptor_data = rd.interceptor(i_type, rd_fname)
    if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
        if len(interceptor_data["det_range"]) > m_type :
            det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
        else :
            print("No detection range value for this missile. Detection range set to 0.")
            print("For quick test run 'Multi-Footprint by Detection Range' routine.")
    else :
        print("No detection range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'Multi-Footprint by Detection Range' routine.")

    fp_st = time.time()

    if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
        det_range *= 1000

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    search_type1 = "Shoot Once"
    save_label1 = "son"

    search_type2 = "Shoot-Look-Shoot"
    save_label2 = "sls"

    if not mode2 :
        search_func1 = ss.short_search
        search_func2 = ss.sls_search

        print("Footprint1 interception type: " + search_type1)
        footprint_tab1 = fp.footprint_calc_v2(search_func1, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
    
        if np.any(footprint_tab1) :
            fp_1 = True
            if det_range :
                header_str1 = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str1 = header_str1.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type1)
                chart_info_str1 = "h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str1 = chart_info_str1.format(h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type1)
            else :
                header_str1 = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                header_str1 = header_str1.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type1)
                chart_info_str1 = "h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                chart_info_str1 = chart_info_str1.format(h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type1)

            data_fname1 = footprint_path + "/double_footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label1, t_stamp)
            
            if op_range :
                title_str1 = "Footprint: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str1 = "Footprint: i_type={} m_type={} mrange={:.0f} km {}".format(i_type, m_type, mrange/1000, search_type1)
            chart_fname1 = footprint_path + "/footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label1, t_stamp)
    
        else :
            fp_1 = False
            footprint_tab1 = np.zeros((0, 5))
            print("No Footprint for " + search_type1 + " type of interception...")
    
        print("Footprint2 interception type: " + search_type2)
        footprint_tab2 = fp.footprint_calc_v2(search_func2, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
    
        if np.any(footprint_tab2) :
            fp_2 = True
            if det_range :
                header_str2 = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str2 = header_str2.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type2)
                chart_info_str2 = "h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str2 = chart_info_str2.format(h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type2)
            else :
                header_str2 = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                header_str2 = header_str2.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type2)
                chart_info_str2 = "h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={} {}"
                chart_info_str2 = chart_info_str2.format(h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000, search_type2)

            data_fname2 = footprint_path + "/double_footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label2, t_stamp)
            
            if op_range :
                title_str2 = "Footprint: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str2 = "Footprint: i_type={} m_type={} mrange={:.0f} km {}".format(i_type, m_type, mrange/1000, search_type2)
                
            chart_fname2 = footprint_path + "/footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label2, t_stamp)
    
        else :
            fp_2 = False
            footprint_tab2 = np.zeros((0, 5))
            print("No Footprint for " + search_type2 + " type of interception...")


        if fp_1 or fp_2 :
            if op_range :
                title_str = "Double Footprint: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str = "Double Footprint: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            
            chart_fname = footprint_path + "/double_footprint_m{}_i{}{}.png".format(m_type, i_type, t_stamp)
            data_fname = footprint_path + "/double_footprint_m{}_i{}_{}.json".format(m_type, i_type, t_stamp)
    
            header_str = header_str1 + ', ' + search_type2
            if det_range :
                chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000)
            else :
                chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} h_discr={}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, fcc_constants.sat_delay, h_discr/1000)
    
            label_arr = [search_type1, search_type2]
            footprint_arr = [footprint_tab1, footprint_tab2]
            bw = False
            gui_fpchart_n(footprint_arr, label_arr, chart_info_str, title_str, chart_fname, header_str, mrange, data_fname, bw)
        
        else :
            print("NOTE: No footprint for either type of interception.")

    else : # mode2
    
        search_func1 = ss.short_search2
        search_func2 = ss.sls_search2

        print("Footprint1 mode2 interception type: " + search_type1)
        footprint_tab1_2 = ss.footprint_mode2(search_func1, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
        footprint_tab1 = footprint_tab1_2[0] # see if np.any below
    
        if np.any(footprint_tab1) :
            fp_1 = True
            if det_range :
                header_str1 = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                header_str1 = header_str1.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type1)
                chart_info_str1 = "h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str1 = chart_info_str1.format(h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type1)
            else: 
                header_str1 = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} sat_delay={} h_discr={} {}"
                header_str1 = header_str1.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type1)
                chart_info_str1 = "h_int_min={} km t_int_lnc={} num_steps2={} sat_delay={} h_discr={} {}"
                chart_info_str1 = chart_info_str1.format(h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type1)
            
            data_fname1 = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.json".format(m_type, i_type, save_label1, t_stamp)
            if op_range :
                title_str1 = "Footprint Mode2: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str1 = "Footprint Mode2: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            chart_fname1 = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.png".format(m_type, i_type, save_label1, t_stamp)

        else :
            fp_1 = False
            #footprint_tab1 = np.zeros((0, 5))
            print("No Footprint Mode2 for " + search_type1 + " type of interception...")
    
        print("Footprint2 Mode2 interception type: " + search_type2)
        footprint_tab2_2 = ss.footprint_mode2(search_func2, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
        footprint_tab2 = footprint_tab2_2[0] # see if np.any below
    
        if np.any(footprint_tab2) :
            fp_2 = True
            if det_range :
                header_str2 = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                header_str2 = header_str2.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type2)
                chart_info_str2 = "h_int_min={} km t_int_lnc={} num_steps2={} det_range={} km t_delay={} h_discr={} {}"
                chart_info_str2 = chart_info_str2.format(h_int_min/1000, t_int_lnc, num_steps_mode2, det_range/1000, t_delay, h_discr/1000, search_type2)
            else :
                header_str2 = "Mode2: omega, shift, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps2={} sat_delay={} h_discr={} {}"
                header_str2 = header_str2.format(m_type, i_type, h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type2)
                chart_info_str2 = "h_int_min={} km t_int_lnc={} num_steps2={} sat_delay={} h_discr={} {}"
                chart_info_str2 = chart_info_str2.format(h_int_min/1000, t_int_lnc, num_steps_mode2, fcc_constants.sat_delay, h_discr/1000, search_type2)
            
            data_fname2 = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.json".format(m_type, i_type, save_label2, t_stamp)
            if op_range :
                title_str2 = "Footprint Mode2: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str2 = "Footprint Mode2: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            chart_fname2 = footprint_path + "/footprint_mode2_m{}_i{}_{}{}.png".format(m_type, i_type, save_label2, t_stamp)
      
        else :
            fp_2 = False
            #footprint_tab2 = np.zeros((0, 5))
            print("No Footprint Mode2 for " + search_type2 + " type of interception...")


        if fp_1 or fp_2 :
            if op_range :
                title_str = "Double Footprint Mode2: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else: 
                title_str = "Double Footprint Mode2: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
            chart_fname = footprint_path + "/double_footprint_mode2_m{}_i{}{}.png".format(m_type, i_type, t_stamp)
            data_fname = footprint_path + "/double_footprint_mode2_m{}_i{}_{}.json".format(m_type, i_type, t_stamp)
    
            header_str = header_str1 + ', ' + search_type2
            if det_range :
                chart_info_str = "h_int_min={} km t_int_lnc={} det_range={} km t_delay={} h_discr={} num_steps={}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, det_range/1000, t_delay, h_discr/1000, num_steps_mode2)
            else :
                chart_info_str = "h_int_min={} km t_int_lnc={} sat_delay={} h_discr={} num_steps={}"
                chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, fcc_constants.sat_delay, h_discr/1000, num_steps_mode2)
    
            label_arr = [search_type1, search_type2]
            footprint_arr = [footprint_tab1_2, footprint_tab2_2]
            bw = False
            gui_fpchart_n(footprint_arr, label_arr, chart_info_str, title_str, chart_fname, header_str, mrange, data_fname, True, bw) # mode2 = True

        
        else :
            print("NOTE: No footprint for either type of interception.")


    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Double Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file_var.get() :
        sys.stdout = original

""" END of gui_double_footprint """



def run_multi_detrange_footprint() : # actual routine, for window shell see gui_multi_detrange_footprint

    m_type = mtype_var.get()
    i_type = itype_var.get()
    #print("mtype = {}, itype = {}".format(m_type, i_type))
    ndr_list_str = det_range_list_var.get()
    if ndr_list_str.strip() == '' :
        det_range_list = [0]
    else :
        det_range_list = [eval(x) for x in ndr_list_str.split(',')]

    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    mode2 = fp_calc_mode_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    ndr_fp_win.destroy()
    #m.run_n_footprint(m_key, i_key, detrange_list, rd_fname, emode, f_mia, a_stp, delay, hdisc, f_acc)
    
    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    print("\nMultiple footprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    if mode2 :
        print("Footprint calculation Mode2")
    if 0 in det_range_list :
        sat_delay_string = " sat_delay={}".format(fcc_constants.sat_delay)
        print(det_range_list)
        print("Set of detection ranges: {}, sat_delay={}".format(str(det_range_list)[1:-1], fcc_constants.sat_delay))
    else :
        sat_delay_string = ''
        print("Set of detection ranges: {}".format(str(det_range_list)[1:-1]))
    print("Missile type m{} trajectory calculating...".format(m_type), end='')

    if stdout_to_file_var.get() : # possibly delete? $$$ #TODO
        file_name = 'footprint_m{}_i{}{}.txt'.format(m_type, i_type, t_stamp)
        if set_keep_stdout_file_var.get() :
            m.keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
    
    if mrange > bm_range_limit :
        print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return False

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
    
    fp_st = time.time()

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    interceptor_data = rd.interceptor(i_type, rd_fname)
    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    fprint_tab_lst = []
    label_lst = []
    info_str_b = ''

    if not mode2 :

        search_func = ss.short_search
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                
        print("Type of interception: " + search_type)
    
        for det_range in det_range_list :
            if not det_range :
                print("Detection range not set.")
                det_range = 0
            else :
                if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                    det_range *= 1000
        
            print("Detection range = {} km ".format(det_range/1000))
            
            footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
    
            if np.any(footprint_tab) :
                fprint_tab_lst.append(footprint_tab)
            else:
                fprint_tab_lst.append(np.zeros((0, 5)))
                
            label_lst.append(str(int(det_range/1000)))
            info_str_b += str(int(det_range/1000)) + ', '
    
            """
            if np.any(footprint_tab) :
                header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
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
            
        #header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        #header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
        header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} det_range={} km {}"
        header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, det_range_list, search_type)
        data_fname = footprint_path + "/mdr-footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
        chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, search_type)
        chart_info_str += "\nDetection ranges: " + info_str_b[:-2] + " km"
        chart_info_str += sat_delay_string
        if op_range :
            title_str = "Multi-Footprint by Detection Range: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
        else: 
            title_str = "Multi-Footprint by Detection Range: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
        chart_fname = footprint_path + "/mdr-footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)

    else : # mode2
        search_func = ss.short_search2
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search2
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                
        print("Type of interception: " + search_type)
    
        for det_range in det_range_list :
            if not det_range :
                print("Detection range not set.")
                det_range = 0
            else :
                if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                    det_range *= 1000
        
            print("Detection range = {} km ".format(det_range/1000))
            
            footprint_tab2 = ss.footprint_mode2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
            """
            footprint_tab = footprint_tab2[0] # see if np.any below
    
            if np.any(footprint_tab) :
                fprint_tab_lst.append(footprint_tab2)
            else:
                fprint_tab_lst.append(np.zeros((0, 5)))
            """
            fprint_tab_lst.append(footprint_tab2)
            label_lst.append(str(int(det_range/1000)))
            info_str_b += str(int(det_range/1000)) + ', '
    
            
        header_str = "Mode2: angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} t_delay={} h_discr={} det_range={} km num_steps={} {}"
        header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, t_delay, h_discr/1000, det_range_list, num_steps_mode2, search_type)
        header_str  += sat_delay_string
        data_fname = footprint_path + "/mdr-footprint_mode2_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} t_delay={} h_discr={} num_steps={} {}"
        chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, t_delay, h_discr/1000, num_steps_mode2, search_type)
        chart_info_str += "\nDetection ranges: " + info_str_b[:-2] + " km"
        chart_info_str += sat_delay_string
        if op_range :
            title_str = "Multi-Footprint Mode2 by Detection Range: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
        else: 
            title_str = "Multi-Footprint by Detection Range: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
        chart_fname = footprint_path + "/mdr-footprint_mode2_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
    # else

    if set_keep_fp_chart_var.get() :
        m.keep_old_file(chart_fname)
            
    gui_fpchart_n(fprint_tab_lst, 
                  label_lst, 
                  chart_info_str, 
                  title_str,
                  chart_fname,
                  header_str,
                  mrange,
                  data_fname,
                  mode2
                  )

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Multi-Footprint by Detection Range calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file_var.get() :
        sys.stdout = original


def gui_multi_detrange_footprint() : # routine's window shell, for actual routine see run_multi_detrange_footprint

    global ndr_fp_win

    try :
        if ndr_fp_win.state() == "normal" : ndr_fp_win.destroy()
    except :
        pass
    finally :
        ndr_fp_win = Toplevel(root)
        ndr_fp_win.title('Multi-Footprint by Detection Range')
        ndr_fp_win.geometry('+500+150')
        ndr_fp_win.config(border=3, relief='ridge')
       
        def set_detrange_list() : # seems not to be needed
            ndr_list_str = det_range_list_var.get()
            detrange_list = [eval(x) for x in ndr_list_str.split(',')]
            #det_range_list_var.set(ndr_list_str)
            #ent_n_detrange.delete(0, END)
            #ent_n_detrange.insert(0, str(detrange_list)[1:-1], font='bold')
            
        lbl_n_detrange = Label(ndr_fp_win, text="Detection ranges, km")
        ent_n_detrange = CEntry(ndr_fp_win, textvariable=det_range_list_var, width=30)
        #ent_n_detrange.insert(0, str(det_range_list)[1:-1])
        #detrange_list = det_range_list_var.get()
        #ent_n_detrange.insert(0, detrange_list)
        #btn_n_detrange = Button(ndr_fp_win, text="Enter", command=set_detrange_list, state='disabled')
        btn_n_footprint = Button(ndr_fp_win, text='Compute', command=lambda: call_longrun(run_multi_detrange_footprint))
        if tooltips: tt = ToolTip(lbl_n_detrange, msg="Enter one or more detection range (comma-separated).", delay=1.0)
    
        lbl_n_detrange.grid(row=0, column=0, sticky='w')
        ent_n_detrange.grid(row=0, column=1)
        #btn_n_detrange.grid(row=0, column=2, ipady=1)
        btn_n_footprint.grid(row=1, column=0, columnspan=2, sticky='ew', ipady=3)

        #rc_menu_string ='copy-paste-cut'
        #ndr_fp_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def win_destroy() :
            if tooltips:
                tt.status='outside'
                tt.withdraw()
            ndr_fp_win.destroy()
                
        ndr_fp_win.focus_force()
        ndr_fp_win.bind('<Escape>', lambda esc: win_destroy())

""" END of gui_multi_detrange_footprint """


def run_param_h_int_min() :
    run_param_footprint('h_int_min', h_int_min_list_var.get())

def run_param_h_discr() :
    run_param_footprint('h_discr', h_discr_list_var.get())

def run_param_t_delay() :
    run_param_footprint('t_delay', t_delay_list_var.get())


def run_param_footprint(par_key, par_list_string) : # actual routine, for window shell see gui_param_footprint
    m_type = mtype_var.get()
    i_type = itype_var.get()
    print("mtype = {}, itype = {}".format(m_type, i_type))

    if par_list_string.strip() == '' :
        par_list = [0]
    else :
        par_list = [eval(x) for x in par_list_string.split(',')]
        
    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    mode2 = fp_calc_mode_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    
    npar_fprint_win.destroy()
    
    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    fp_st = time.time()
 
    print("\nMultiple footprint calculation routine started. Missile type m{}, Interceptor type i{}".format(m_type, i_type))
    if mode2 :
        print("Footprint calculation Mode2")
    print("Set of " + par_key + " : "+ par_list_string)
    print("Missile type m{} trajectory calculating...".format(m_type), end='')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])

    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))

    if mrange > bm_range_limit :
        print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return False

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    det_range = 0.0
    interceptor_data = rd.interceptor(i_type, rd_fname)
    if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
        if len(interceptor_data["det_range"]) > m_type :
            det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
        else :
            print("No detection range value for this missile. Detection range set to 0.")
            print("For quick test run 'Multi-Footprint by Detection Range' routine.")
    else :
        print("No detection range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'Multi-Footprint by Detection Range' routine.")

    if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
        det_range *= 1000
    
    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    fprint_tab_lst = []
    label_lst = [str(prm) for prm in par_list]
    info_str_b = par_list_string

    if not mode2 :

        search_func = ss.short_search
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                
        print("Type of interception: " + search_type)
        
        for par in par_list :
            if par_key == 'h_int_min' :
                h_int_min = par
                if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
                    h_int_min *= 1000
                #h_int_min = max(h_int_min, mpia) # h_int_min needs to be max of feasible and acceptable
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} t_int_lnc={} angle_step={} t_delay={} h_discr={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, burn_time + t_delay, angle_step, t_delay, h_discr/1000, det_range/1000, search_type)
                    chart_info_str = "t_int_lnc={} angle_step={} t_delay={} h_discr={} det_range={} {}"
                    chart_info_str = chart_info_str.format(burn_time + t_delay, angle_step, t_delay, h_discr/1000, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} t_int_lnc={} angle_step={} h_discr={} sat_delay={} {}"
                    header_str = header_str.format(m_type, i_type, burn_time + t_delay, angle_step, h_discr/1000, fcc_constants.sat_delay, search_type)
                    chart_info_str = "t_int_lnc={} angle_step={} h_discr={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(burn_time + t_delay, angle_step, h_discr/1000, fcc_constants.sat_delay, search_type)
                print("Min interception altitude = {} km ".format(h_int_min/1000))
            elif par_key == 'h_discr' :
                h_discr = par
                if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
                    h_discr *= 1000
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} t_delay={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time + t_delay, angle_step, t_delay, det_range/1000, search_type)
                    chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} t_delay={} det_range={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time + t_delay, angle_step, t_delay, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time + t_delay, angle_step, fcc_constants.sat_delay, search_type)
                    chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time + t_delay, angle_step, fcc_constants.sat_delay, search_type)
                print("Warhead discrimination altitude = {} km ".format(h_discr/1000))
            else :
                t_delay = par
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km burn_time={} angle_step={} h_discr={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time, angle_step, h_discr/1000, det_range/1000, search_type)
                    chart_info_str = "h_int_min={} km burn_time={} angle_step={} h_discr={} det_range={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time, angle_step, h_discr/1000, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km burn_time={} angle_step={} h_discr={} sat_delay={} {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time, angle_step, h_discr/1000, fcc_constants.sat_delay, search_type)
                    chart_info_str = "h_int_min={} km burn_time={} angle_step={} h_discr={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time, angle_step, h_discr/1000, fcc_constants.sat_delay, search_type)
                print("Interceptor launch delay = {} s ".format(t_delay))
    
            t_int_lnc = burn_time + t_delay        
        
            footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
            if np.any(footprint_tab) :
                fprint_tab_lst.append(footprint_tab)
            else:
                fprint_tab_lst.append(np.zeros((0, 5)))
                
            """
            if np.any(footprint_tab) :
                header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
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
            
        data_fname = "nparam-footprint_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
            
        units = ' s' if par_key == 't_delay' else ' km'
        chart_info_str += "\n" + par_key + '(s) : ' + info_str_b + units
        if op_range :
            title_str = "Parameter Footprint: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
        else: 
            title_str = "Parameter Footprint: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
        chart_fname = footprint_path + "/param-footprint_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)
    
    else : # mode2
    
        search_func = ss.short_search2
        search_type = "Shoot_once"
        save_label = "son"

        if emode_sls :
            search_func = ss.sls_search2
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                
        print("Type of interception: " + search_type)
        
        for par in par_list :
            if par_key == 'h_int_min' :
                h_int_min = par
                if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
                    h_int_min *= 1000
                #h_int_min = max(h_int_min, mpia)
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} t_int_lnc={} t_delay={} h_discr={} num_steps={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, burn_time + t_delay, t_delay, h_discr/1000, num_steps_mode2, det_range/1000, search_type)
                    chart_info_str = "t_int_lnc={} t_delay={} h_discr={} num_steps={} det_range={} {}"
                    chart_info_str = chart_info_str.format(burn_time + t_delay, t_delay, h_discr/1000, num_steps_mode2, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} t_int_lnc={} h_discr={} num_steps={} sat_delay={} km {}"
                    header_str = header_str.format(m_type, i_type, burn_time + t_delay, h_discr/1000, num_steps_mode2, fcc_constants.sat_delay, search_type)
                    chart_info_str = "t_int_lnc={} h_discr={} num_steps={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(burn_time + t_delay, h_discr/1000, num_steps_mode2, fcc_constants.sat_delay, search_type)
                print("Min interception altitude = {} km ".format(h_int_min/1000))
            elif par_key == 'h_discr' :
                h_discr = par
                if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
                    h_discr *= 1000
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} t_delay={} num_steps={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time + t_delay, t_delay, num_steps_mode2, det_range/1000, search_type)
                    chart_info_str = "h_int_min={} km t_int_lnc={} t_delay={} num_steps={} det_range={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time + t_delay, t_delay, num_steps_mode2, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} num_steps={} sat_delay={} {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time + t_delay, num_steps_mode2, fcc_constants.sat_delay, search_type)
                    chart_info_str = "h_int_min={} km t_int_lnc={} num_steps={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time + t_delay, num_steps_mode2, fcc_constants.sat_delay, search_type)
                print("Warhead discrimination altitude = {} km ".format(h_discr/1000))
            else :
                t_delay = par
                if det_range :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km burn_time={} h_discr={} num_steps={} det_range={} km {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time, h_discr/1000, num_steps_mode2, det_range/1000, search_type)
                    chart_info_str = "h_int_min={} km burn_time={} h_discr={} num_steps={} det_range={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time, h_discr/1000, num_steps_mode2, det_range/1000, search_type)
                else :
                    header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km burn_time={} h_discr={} num_steps={} sat_delay={} {}"
                    header_str = header_str.format(m_type, i_type, h_int_min/1000, burn_time, h_discr/1000, num_steps_mode2, fcc_constants.sat_delay, search_type)
                    chart_info_str = "h_int_min={} km burn_time={} h_discr={} num_steps={} sat_delay={} {}"
                    chart_info_str = chart_info_str.format(h_int_min/1000, burn_time, h_discr/1000, num_steps_mode2, fcc_constants.sat_delay, search_type)
                print("Interceptor launch delay = {} s ".format(t_delay))

            t_int_lnc = burn_time + t_delay        
        
            footprint_tab2 = ss.footprint_mode2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
            fprint_tab_lst.append(footprint_tab2)
                
        data_fname = "nparam-footprint_mode2_m{}_i{}_{}{}.json".format(m_type, i_type, save_label, t_stamp)
        
        units = ' s' if par_key == 't_delay' else ' km'
        chart_info_str += "\n" + par_key + '(s) : ' + info_str_b + units
        if op_range :
            title_str = "Parameter Footprint Mode2: i_type={} op_range={:.0f} m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
        else: 
            title_str = "Parameter Footprint Mode2: i_type={} m_type={} mrange={:.0f} km".format(i_type, m_type, mrange/1000)
        chart_fname = footprint_path + "/param-footprint_mode2_m{}_i{}_{}{}.png".format(m_type, i_type, save_label, t_stamp)

    # else

    if set_keep_fp_chart_var.get() :
        m.keep_old_file(chart_fname)

    gui_fpchart_n(fprint_tab_lst, 
                  label_lst, 
                  chart_info_str, 
                  title_str,
                  chart_fname,
                  header_str,
                  mrange,
                  data_fname,
                  mode2
                  )
    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Multi-Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

""" END of run_param_footprint """

def gui_param_footprint() : # routine's window shell, for actual routine see run_param_footprint
    global npar_fprint_win
    try :
        if npar_fprint_win.state() == "normal": npar_fprint_win.focus()
    except :
        npar_fprint_win = Toplevel(root)
        npar_fprint_win.title('Multi Footprint by Interception Parameters')
        npar_fprint_win.geometry('+500+150')
        npar_fprint_win.config(border=3, relief='ridge')
                    
        lbl_par_h_int_min = Label(npar_fprint_win, text="Min interc. alt. (max of feasible and acceptable), km")
        ent_par_h_int_min = CEntry(npar_fprint_win, textvariable=h_int_min_list_var, width=30)
        btn_par_h_int_min = Button(npar_fprint_win, text="Compute", command=lambda: call_longrun(run_param_h_int_min))
        if tooltips: tt1 = ToolTip(lbl_par_h_int_min, msg="Minimum interception altitude (=max of feasible nad acceptable).\nIf > 500 interpreted as in m, otherwise in km", delay=1.0)
        
        lbl_par_h_discr = Label(npar_fprint_win, text="Altitude of warhead discrimination, km (0=not used)")
        ent_par_h_discr = CEntry(npar_fprint_win, textvariable=h_discr_list_var, width=30)
        btn_par_h_discr = Button(npar_fprint_win, text="Compute", command=lambda: call_longrun(run_param_h_discr))
        if tooltips: tt2 = ToolTip(lbl_par_h_discr, msg="Interceptor launched as soon as the warhead comes lower than this height.\nIf > 1000 interpreted as in m, otherwise in km", delay=1.0)

        lbl_par_t_delay = Label(npar_fprint_win, text="Interceptor launch delay, s (no delay if =0)")
        ent_par_t_delay = CEntry(npar_fprint_win, textvariable=t_delay_list_var, width=30)
        btn_par_t_delay = Button(npar_fprint_win, text="Compute", command=lambda: call_longrun(run_param_t_delay))
        if tooltips: tt3 = ToolTip(lbl_par_t_delay, msg="Launch delay after missile rise over horizon or missile burnout, whichever comes later. No delay at all (including burn-out) if =0.", delay=1.0)

        lbl_par_h_int_min.grid(row=0, column=0, sticky='w')
        lbl_par_h_discr.grid(row=1, column=0, sticky='w')
        lbl_par_t_delay.grid(row=2, column=0, sticky='w')

        ent_par_h_int_min.grid(row=0, column=1)
        ent_par_h_discr.grid(row=1, column=1)
        ent_par_t_delay.grid(row=2, column=1)   
        
        btn_par_h_int_min.grid(row=0, column=2, ipady=1)
        btn_par_h_discr.grid(row=1, column=2, sticky='ew', ipady=1)
        btn_par_t_delay.grid(row=2, column=2, sticky='ew', ipady=1)

        #rc_menu_string ='copy-paste-cut'
        #npar_fprint_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def win_destroy() :
            if tooltips: 
                tt1.status='outside'
                tt1.withdraw()
                tt2.status='outside'
                tt2.withdraw()
                tt3.status='outside'
                tt3.withdraw()
            npar_fprint_win.destroy()
                
        npar_fprint_win.focus_force()
        npar_fprint_win.bind('<Escape>', lambda esc: win_destroy())

""" END of gui_param_footprint """


def run_multi_interceptor_footprint() : # actual routine, for window shell see gui_nulti_interceptor_footprint

    i_type_list_str = muin_list_var.get()
    m_type = mtype_var.get()
    if i_type_list_str.strip() == '' :
        i_type_list_str = '11, 12, 13'
        i_type_list = [11, 12, 13]
    else :
        i_type_list_str = i_type_list_str.replace('i', '')
        i_type_list = [eval(x) for x in i_type_list_str.split(',')]
    
    #print("itypes = " + i_type_list_str + " mtype = {}".format(m_type))
    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    muin_fprint_win.destroy()
    mode2 = fp_calc_mode_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    #m.run_n_footprint(m_key, i_key, detrange_list, rd_fname, emode, f_mia, a_stp, delay, hdisc, f_acc)
    
    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    fp_st = time.time()
    
    if stdout_to_file_var.get() : # possibly delete? $$$ #TODO
        file_name = 'footprint_m{}_i{}{}.txt'.format(m_type, i_type_list_str, t_stamp)
        if set_keep_stdout_file_var.get() :
            m.keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')
    
    ilist_str = ''
    for i in i_type_list : ilist_str += "i{} ".format(i)
    ilist_str = ilist_str[:-1]
    print("\nMulti-Interceptor Footprint calculation routine started.\nInterceptor types " + ilist_str + ", missile type m{}".format(m_type))

    if mode2 :
        print("Footprint calculation Mode2")

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000
    h_int_min_keep = h_int_min

    fprint_tab_lst = []
    label_lst = []
    info_str_a = ''
    info_str_b = ''
    info_str_2 = ''

    print("Missile type m{} trajectory calculating...".format(m_type), end='')

    missile_data = rd.missile(m_type, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    #max_mrange = max(mrange, max_mrange) 
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
    
    if mrange > bm_range_limit :
        print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return
        """
        if not mode2 :
            fprint_tab_lst.append(np.zeros((0, 5)))
        else :
            fp_zero = np.zeros((0, 5))
            fprint_tab_lst.append([fp_zero, fp_zero])
        label_lst.append("m{}".format(m_type))
        info_str_a += "m{}".format(m_type) + '_'
        info_str_b += "m{}".format(m_type) + ', '
        info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '
        """
    dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])
    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch

    #max_mrange = 0
    if not mode2 :

        search_func = ss.short_search
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search
            search_type = "Shoot_look_shoot"
            save_label = "sls"
             
        for i_type in i_type_list :
            interceptor_data = rd.interceptor(i_type, rd_fname)
            mpia = interceptor_data['mpia']
            mpia *= 1000
            h_int_min = max(h_int_min_keep, mpia)
        
            op_range = interceptor_data['op_range']
            if op_range < 2000 :
                op_range *= 1000
            if op_range :
                print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
            else :
                print(">Interceptor's operational range is not set.")        
        
            int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())

            det_range = 0
            if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
                if len(interceptor_data["det_range"]) > m_type :
                    det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
                else :
                    print("No detection range value for this missile. Detection range set to 0.")
                    print("For quick test run 'Multi-Footprint by Detection Range' routine.")
            else :
                print("No detection range values set in the interceptor data. Detection range set to 0.")
                print("For quick test run 'Multi-Footprint by Detection Range' routine.")
        
            if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                det_range *= 1000
            
            print("Type of interception: " + search_type)
        
            footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
            if np.any(footprint_tab) :
                fprint_tab_lst.append(footprint_tab)
            else:
                fprint_tab_lst.append(np.zeros((0, 5)))
                
            #label_lst.append("m{} dr={}".format(m_type, int(det_range/1000)))
            label_lst.append("i{} MFIA={:.0f}".format(i_type, mpia/1000))
            info_str_a += "i{}".format(i_type) + '_'
            info_str_b += "i{}".format(i_type) + ', '
            if det_range :
                info_str_2 += "i{:.2f}".format(i_type) + " dr={:.0f}".format(det_range/1000) + ', '
            else :
                info_str_2 += "i{:.2f}".format(i_type) + " dr={:.0f} sd={}".format(det_range/1000, fcc_constants.sat_delay) + ', '
            #info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '
            
        #header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        #header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
        header_str = "angle, distance, acc_prm, x, y, i_types=" + info_str_b[:-2] + " m_type={} h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
        header_str = header_str.format(m_type, h_int_min_keep/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, search_type)
        data_fname = footprint_path + "/muin-footprint_" + info_str_a[:-1] + "_m{}_{}{}.json".format(m_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
        chart_info_str = chart_info_str.format(h_int_min_keep/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, search_type)
        chart_info_str += "\nInterceptors: " + info_str_2[:-2]
        title_str = "Multi-Interceptor Footprint: m_type={} mrange={:.0f} i_types=".format(m_type, mrange/1000)  + info_str_b[:-2]
        chart_fname = footprint_path + "/muin-footprint_" + info_str_a[:-1] + "_m{}_{}{}.png".format(m_type, save_label, t_stamp)
        
    else : # mode2
        
        search_func = ss.short_search2
        search_type = "Shoot_once"
        save_label = "son"

        if emode_sls :
            search_func = ss.sls_search2
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                    
        for i_type in i_type_list :
            interceptor_data = rd.interceptor(i_type, rd_fname)
            mpia = interceptor_data['mpia']
            mpia *= 1000
            h_int_min = max(h_int_min_keep, mpia)
        
            op_range = interceptor_data['op_range']
            if op_range < 2000 :
                op_range *= 1000
            if op_range :
                print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
            else :
                print(">Interceptor's operational range is not set.")        
        
            int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())
                
            det_range = 0.0
            if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
                if len(interceptor_data["det_range"]) > m_type :
                    det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
                else :
                    print("No detection range value for this missile. Detection range set to 0.")
                    print("For quick test run 'Multi-Footprint by Detection Range' routine.")
            else :
                print("No detection range values set in the interceptor data. Detection range set to 0.")
                print("For quick test run 'Multi-Footprint by Detection Range' routine.")
        
            if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                det_range *= 1000
            
            print("Type of interception: " + search_type)
        
            footprint_tab2 = ss.footprint_mode2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
            fprint_tab_lst.append(footprint_tab2)
                
            #label_lst.append("m{} dr={}".format(m_type, int(det_range/1000)))
            label_lst.append("i{} MFIA={:.0f}".format(i_type, mpia/1000))
            info_str_a += "i{}".format(i_type) + '_'
            info_str_b += "i{}".format(i_type) + ', '
            if det_range :
                info_str_2 += "i{:.2f}".format(i_type) + " dr={:.0f}".format(det_range/1000) + ', '
            else :
                info_str_2 += "i{:.2f}".format(i_type) + " dr={:.0f} sd={}".format(det_range/1000, fcc_constants.sat_delay) + ', '
            #info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '

        header_str = "Mode2: angle, distance, acc_prm, x, y, i_types=" + info_str_b[:-2] + " m_type={} h_int_min={} km t_int_lnc={} t_delay={} h_discr={} num_steps={} {}"
        header_str = header_str.format(m_type, h_int_min_keep/1000, t_int_lnc, t_delay, h_discr/1000, num_steps_mode2, search_type)
        data_fname = footprint_path + "/muin-footprint_mode2_" + info_str_a[:-1] + "_m{}_{}{}.json".format(m_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} t_delay={} h_discr={} num_steps={} {}"
        chart_info_str = chart_info_str.format(h_int_min_keep/1000, t_int_lnc, t_delay, h_discr/1000, num_steps_mode2, search_type)
        chart_info_str += "\nInterceptors: " + info_str_2[:-2]
        title_str = "Multi-Interceptor Footprint Mode2: m_type={} mrange={:.0f} i_types=".format(m_type, mrange/1000)  + info_str_b[:-2]
        chart_fname = footprint_path + "/muin-footprint_mode2_" + info_str_a[:-1] + "_m{}_{}{}.png".format(m_type, save_label, t_stamp)

        
    if set_keep_fp_chart_var.get() :
        m.keep_old_file(chart_fname)

    gui_fpchart_n(fprint_tab_lst, 
                  label_lst, 
                  chart_info_str, 
                  title_str,
                  chart_fname,
                  header_str,
                  mrange,
                  data_fname,
                  mode2
                  )

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Multi-Missile Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file_var.get() :
        sys.stdout = original
        
""" END of run_multi_interceptor_footprint """


def gui_multi_interceptor_footprint() : # routine's window shell, for actual routine see run_multi_interceptor_footprint
    global muin_fprint_win
    try :
        if muin_fprint_win.state() == "normal": muin_fprint_win.focus()
    except :
        muin_fprint_win = Toplevel(root)
        muin_fprint_win.title('Multi-Interceptor Footprint')
        muin_fprint_win.geometry('+500+150')
        muin_fprint_win.config(border=3, relief='ridge')

        lbl_par_h_int_min = Label(muin_fprint_win, text="List of interceptor type numbers")
        ent_par_h_int_min = CEntry(muin_fprint_win, textvariable=muin_list_var, width=30)
        btn_par_h_int_min = Button(muin_fprint_win, text="Compute", command=lambda: call_longrun(run_multi_interceptor_footprint))
        if tooltips: tt = ToolTip(lbl_par_h_int_min, msg="Minimum acceptable altitude of interception (to avoid damage to ground objects).\nIf > 500 interpreted as in m, otherwise in km", delay=1.0)
        
        lbl_par_h_int_min.grid(row=0, column=0, sticky='w')
        ent_par_h_int_min.grid(row=0, column=1)
        btn_par_h_int_min.grid(row=1, column=0, columnspan=2, ipady=1, sticky='ew')
        
        def win_destroy() :
            if tooltips: 
                tt.status='outside'
                tt.withdraw()
            muin_fprint_win.destroy()            

        muin_fprint_win.focus_force()
        muin_fprint_win.bind('<Escape>', lambda esc: win_destroy())

""" END of gui_multi_interceptor_footprint """


def run_multi_missile_footprint() : # actual routine, for window shell see gui_multi_missile_footprint

    m_type_list_str = mumi_list_var.get()
    i_type = itype_var.get()
    if m_type_list_str.strip() == '' :
        m_type_list_str = '1, 2, 3'
        m_type_list = [1, 2, 3]
    else :
        m_type_list_str = m_type_list_str.replace('m', '')
        m_type_list = [eval(x) for x in m_type_list_str.split(',')]
    
    #print("mtypes = " + m_type_list_str + " itype = {}".format(i_type))
    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    mumi_fprint_win.destroy()
    mode2 = fp_calc_mode_var.get()
    num_steps_mode2 = num_steps_mode2_var.get()
    #m.run_n_footprint(m_key, i_key, detrange_list, rd_fname, emode, f_mia, a_stp, delay, hdisc, f_acc)
    
    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''
 
    fp_st = time.time()
    
    if stdout_to_file_var.get() : # possibly delete? $$$ #TODO
        file_name = 'mumi-fp_m{}_i{}{}.txt'.format(m_type_list_str, i_type, t_stamp)
        if set_keep_stdout_file_var.get() :
            m.keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')
    
    mlist_str = ''
    for i in m_type_list : mlist_str += "m{} ".format(i)
    mlist_str = mlist_str[:-1]
    print("\nMulti-Missile Footprint calculation routine started.\nMissile types " + mlist_str + ", Interceptor type i{}".format(i_type))

    if mode2 :
        print("Footprint calculation Mode2")

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    interceptor_data = rd.interceptor(i_type, rd_fname)
    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    int_table = m.load_int_table(i_type, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                
    
    fprint_tab_lst = []
    label_lst = []
    info_str_a = ''
    info_str_b = ''
    info_str_2 = ''

    max_mrange = 0
    if not mode2 :

        search_func = ss.short_search
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search
            search_type = "Shoot_look_shoot"
            save_label = "sls"
             
        for m_type in m_type_list :
            print("Missile type m{} trajectory calculating...".format(m_type), end='')
        
            missile_data = rd.missile(m_type, rd_fname)
            trj = bm.balmisflight(missile_data)
            mrange = trj[len(trj) - 1, 2] * R_e
            max_mrange = max(mrange, max_mrange) 
            print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
            
            if mrange > bm_range_limit :
                print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
                fprint_tab_lst.append(np.zeros((0, 5)))
                label_lst.append("m{}".format(m_type))
                info_str_a += "m{}".format(m_type) + '_'
                info_str_b += "m{}".format(m_type) + ', '
                info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '
                continue
        
            dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function
        
            burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])
            t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
            
            det_range = 0.0
            if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
                if len(interceptor_data["det_range"]) > m_type :
                    det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
                else :
                    print("No detection range value for this missile. Detection range set to 0.")
                    print("For quick test run 'Multi-Footprint by Detection Range' routine.")
            else :
                print("No detection range values set in the interceptor data. Detection range set to 0.")
                print("For quick test run 'Multi-Footprint by Detection Range' routine.")
        
            if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                det_range *= 1000
            
            print("Type of interception: " + search_type)
        
            footprint_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
            if np.any(footprint_tab) :
                fprint_tab_lst.append(footprint_tab)
            else:
                fprint_tab_lst.append(np.zeros((0, 5)))
                
            if det_range :
                label_lst.append("m{} dr={}".format(m_type, int(det_range/1000)))
                print("det_range=".format(det_range/1000))
            else :
                label_lst.append("m{} dr={} sd={}".format(m_type, int(det_range/1000), fcc_constants.sat_delay))
            info_str_a += "m{}".format(m_type) + '_'
            info_str_b += "m{}".format(m_type) + ', '
            info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '

    
            """
            if np.any(footprint_tab) :
                header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
                header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
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
            
        #header_str = "angle, distance, acc_prm, x, y, m_type={} i_type={} h_int_min={} km t_int_lnc={} angle_step={} det_range={} km t_delay={} h_discr={} {}"
        #header_str = header_str.format(m_type, i_type, h_int_min/1000, t_int_lnc, angle_step, det_range/1000, t_delay, h_discr/1000, search_type)
        header_str = "angle, distance, acc_prm, x, y, m_types=" + info_str_b[:-2] + " i_type={} h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
        header_str = header_str.format(i_type, h_int_min/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, search_type)
        data_fname = footprint_path + "/mumi-footprint_" + info_str_a[:-1] + "_i{}_{}{}.json".format(i_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} angle_step={} t_delay={} h_discr={} {}"
        chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, angle_step, t_delay, h_discr/1000, search_type)
        chart_info_str += "\nMissiles: " + info_str_2[:-2]
        if op_range :
            title_str = "Multi-Missile Footprint: i_type={} op_range={:.0f} m_types=".format(i_type, op_range/1000)  + info_str_b[:-2]
        else: 
            title_str = "Multi-Missile Footprint: i_type={} m_types=".format(i_type)  + info_str_b[:-2]
        chart_fname = footprint_path + "/mumi-footprint_" + info_str_a[:-1] + "_i{}_{}{}.png".format(i_type, save_label, t_stamp)
        
    else : # mode2
        
        search_func = ss.short_search2
        search_type = "Shoot_once"
        save_label = "son"

        if emode_sls :
            search_func = ss.sls_search2
            search_type = "Shoot_look_shoot"
            save_label = "sls"
                    
        for m_type in m_type_list :
            print("Missile type m{} trajectory calculating...".format(m_type), end='')
        
            missile_data = rd.missile(m_type, rd_fname)
            trj = bm.balmisflight(missile_data)
            mrange = trj[len(trj) - 1, 2] * R_e
            max_mrange = max(mrange, max_mrange) 
            print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(m_type, mrange/1000))
            
            if mrange > bm_range_limit :
                print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
                fp_zero = np.zeros((0, 5))
                fprint_tab_lst.append([fp_zero, fp_zero])
                label_lst.append("m{}".format(m_type))
                info_str_a += "m{}".format(m_type) + '_'
                info_str_b += "m{}".format(m_type) + ', '
                info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '
                continue
        
            dist = mrange * dist_param # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function
        
            burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])
            t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch
            
            det_range = 0.0
            if "det_range" in interceptor_data.keys() : # detection range, this is set in the "rocket_data" module
                if len(interceptor_data["det_range"]) > m_type :
                    det_range = interceptor_data["det_range"][m_type] # detection range, this is set in the "rocket_data" module
                else :
                    print("No detection range value for this missile. Detection range set to 0.")
                    print("For quick test run 'Multi-Footprint by Detection Range' routine.")
            else :
                print("No detection range values set in the interceptor data. Detection range set to 0.")
                print("For quick test run 'Multi-Footprint by Detection Range' routine.")
        
            if det_range < 11000 : # can be set in meters or km, convert to meters if set in km
                det_range *= 1000
            
            print("Type of interception: " + search_type)
        
            footprint_tab2 = ss.footprint_mode2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step_mode2, op_range, det_range, t_delay, h_discr, acc, num_steps_mode2)
            fprint_tab_lst.append(footprint_tab2)
            
            if det_range :
                label_lst.append("m{} dr={}".format(m_type, int(det_range/1000)))
                print("det_range=".format(det_range/1000))
            else :
                label_lst.append("m{} dr={} sd={}".format(m_type, int(det_range/1000), fcc_constants.sat_delay))
            info_str_a += "m{}".format(m_type) + '_'
            info_str_b += "m{}".format(m_type) + ', '
            info_str_2 += "m{}".format(m_type) + " range {:.0f} km".format(mrange/1000) + ', '

        header_str = "Mode2: angle, distance, acc_prm, x, y, m_types=" + info_str_b[:-2] + " i_type={} h_int_min={} km t_int_lnc={} t_delay={} h_discr={} num_steps={} {}"
        header_str = header_str.format(i_type, h_int_min/1000, t_int_lnc, t_delay, h_discr/1000, num_steps_mode2, search_type)
        data_fname = "mumi-footprint_mode2_" + info_str_a[:-1] + "_i{}_{}{}.json".format(i_type, save_label, t_stamp)
            
        chart_info_str = "h_int_min={} km t_int_lnc={} t_delay={} h_discr={} num_steps={} {}"
        chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, t_delay, h_discr/1000, num_steps_mode2, search_type)
        chart_info_str += "\nMissiles: " + info_str_2[:-2]
        if op_range :
            title_str = "Multi-Missile Footprint Mode2: i_type={} op_range={:.0f} m_types=".format(i_type, op_range/1000)  + info_str_b[:-2]
        else: 
            title_str = "Multi-Missile Footprint Mode2: i_type={} m_types=".format(i_type)  + info_str_b[:-2]
        chart_fname = footprint_path + "/mumi-footprint_mode2_" + info_str_a[:-1] + "_i{}_{}{}.png".format(i_type, save_label, t_stamp)

        
    if set_keep_fp_chart_var.get() :
        m.keep_old_file(chart_fname)

    gui_fpchart_n(fprint_tab_lst, 
                  label_lst, 
                  chart_info_str, 
                  title_str,
                  chart_fname,
                  header_str,
                  max_mrange,
                  data_fname,
                  mode2
                  )

    fp_et = time.time()
    fp_elapsed_time = fp_et - fp_st
    print("Multi-Missile Footprint calculation time = {:.3f}s".format(fp_elapsed_time))

    if stdout_to_file_var.get() :
        sys.stdout = original
        
""" END of run_multi_missile_footprint """


def gui_multi_missile_footprint() : # routine's window shell, for actual routine see run_multi_missile_footprint
    global mumi_fprint_win
    try :
        if mumi_fprint_win.state() == "normal": mumi_fprint_win.focus()
    except :
        mumi_fprint_win = Toplevel(root)
        mumi_fprint_win.title('Multi-Missile Footprint')
        mumi_fprint_win.geometry('+500+150')
        mumi_fprint_win.config(border=3, relief='ridge')

        lbl_par_h_int_min = Label(mumi_fprint_win, text="List of missile type numbers")
        ent_par_h_int_min = CEntry(mumi_fprint_win, textvariable=mumi_list_var, width=30)
        btn_par_h_int_min = Button(mumi_fprint_win, text="Compute", command=lambda: call_longrun(run_multi_missile_footprint))
        if tooltips: tt = ToolTip(lbl_par_h_int_min, msg="Minimum acceptable altitude of interception (to avoid damage to ground objects).\nIf > 500 interpreted as in m, otherwise in km", delay=1.0)
        
        lbl_par_h_int_min.grid(row=0, column=0, sticky='w')
        ent_par_h_int_min.grid(row=0, column=1)
        btn_par_h_int_min.grid(row=1, column=0, columnspan=2, ipady=1, sticky='ew')

        #rc_menu_string ='copy-paste-cut'
        #mumi_fprint_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def win_destroy() :
            if tooltips: 
                tt.status='outside'
                tt.withdraw()
            mumi_fprint_win.destroy()
            
        mumi_fprint_win.focus_force()
        mumi_fprint_win.bind('<Escape>', lambda esc: win_destroy())


""" END of gui_multi_missile_footprint """

def gui_probing_chart(fp_scatter_arr,
                      fp_curve_arr,
                      lbl_scatter_arr,
                      lbl_curve_arr,
                      info_string, 
                      title_string,
                      chart_fname,
                      bw=False) :
    
    show_titles = show_chart_titles_var.get()
    if not show_titles :
        info_string = ''
        title_string =''
    
    global probing_chart_win

    try :
        if probing_chart_win.state() == "normal" : probing_chart_win.destroy()
    except :
        pass
    finally :
        probing_chart_win = Toplevel(root)
        probing_chart_win.title('Footprint by Porbing Chart')
        probing_chart_win.geometry("+500+100")
        
        chwin_row0 = Frame(probing_chart_win, border=1)
        chwin_row1 = Frame(probing_chart_win, border=1)
        chwin_row1.columnconfigure(0, weight=1)
        chwin_row1.columnconfigure(1, weight=1)
        chwin_row1.columnconfigure(2, weight=1)
        chwin_row1.columnconfigure(3, weight=1)
        
        chwin_row0.pack()
        chwin_row1.pack()  
    
        def fp_draw () :
            fp_plot()
        
            canvas = FigureCanvasTkAgg(fig, chwin_row0)
            canvas.draw()
        
            # placing the canvas on the Tkinter probing_chart_win
            canvas.get_tk_widget().pack()
        
            # creating the Matplotlib toolbar
            #toolbar = NavigationToolbar2Tk(canvas, probing_chart_win)
            #toolbar.update()
        
            # placing the toolbar on the Tkinter probing_chart_win
            #canvas.get_tk_widget().pack()
            
        def fp_save() :
            fp_plot()
            keep_chart = set_keep_fp_chart_var.get()
            print(keep_chart)
            save_chart_fname = ent_chart_fname.get()
            if keep_chart :
                    m.keep_old_file(save_chart_fname)
            ax.get_figure().savefig(save_chart_fname, dpi=300, bbox_inches='tight', pad_inches=0.2)
            print("Footprint Chart saved to ", save_chart_fname)
            btn_chart_save.configure(state='disabled')
    
        """
        def fp_data_save() :
            keep_data = set_keep_fp_data_var.get()
            print(keep_data)
            save_data_fname = ent_data_fname.get()
            fp_arr = [fp_i.tolist() for fp_i in ftprint_arr]
            #if len(ftprint_arr) > 1 : fp_arr = ftprint_arr
            #else : fp_arr = ftprint_arr[0].tolist()
    
            data2save = header_string, fp_arr
            m.save_data(data2save, save_data_fname, keep_data)
            print("Footprint Data  saved to ", save_data_fname)
            btn_data_save.configure(state='disabled')
        """
    
        def fp_plot() :
            global fig
            global ax
    
            fig = plt.figure(figsize = (8, 5), dpi=100)
            fig.suptitle(title_string, fontsize=12)
            
            ax = fig.add_subplot(111)
    
            n_arr = len(fp_scatter_arr)
    
            if n_arr > 1 :
                if bw :
                    linestyle_cycler = cycler('linestyle',['-','--',':','-.', (0, (3, 3, 1, 3, 1, 3))])
                else : 
                    linestyle_cycler = cycler('color', ['r', 'g', 'b', 'm', 'k']) +\
                                   cycler('linestyle', ['-', '--', ':', '-.', (0, (3, 3, 1, 3, 1, 3))])
                ax.set_prop_cycle(linestyle_cycler)
            else : pass

            max_x = 0
            """
            for i_arr in range(n_arr) :
                if np.any(fp_curve_arr[0]) :
                    xpoints = fp_curve_arr[i_arr][:, 3]
                    ypoints = fp_curve_arr[i_arr][:, 4]
                    ax.plot(xpoints, ypoints, c='red', label = lbl_curve_arr[i_arr])
                    max_x = max(max_x, max(xpoints))
            """

            for i_arr in range(n_arr) :
                fp_curve_i = fp_curve_arr[i_arr]
                if show_titles :
                    lbl_curve = lbl_curve_arr[i_arr]
                else :
                    lbl_curve = ''
                if (len(fp_curve_i) > 0) and (len(fp_curve_i[0]) > 0) :
                    if type(fp_curve_i[0][0]) != np.ndarray : #i.e. mode1
                        xpoints = fp_curve_i[:, 3]
                        ypoints = fp_curve_i[:, 4]
                        ax.plot(xpoints, ypoints, c='red', label = lbl_curve) # lbl_curve_arr[i_arr])
                        max_x = max(max_x, max(xpoints))
                    else : #mode2
                        xpoints = fp_curve_i[0][:, 3]
                        ypoints = fp_curve_i[0][:, 4]
                        ax.plot(xpoints, ypoints, c='red', label = lbl_curve) # lbl_curve_arr[i_arr]) #, c='C0') # , marker='.'
                        max_x = max(max_x, max(xpoints))
                        if len(fp_curve_i[1]) > 0 :
                            xpoints2 = fp_curve_i[1][:, 3]
                            ypoints2 = fp_curve_i[1][:, 4]
                            ax.plot(xpoints2, ypoints2)#, c='red', label = '') #, label = label_arr[i_arr]) #, c='C0') # , marker='.'
                            max_x = max(max_x, max(xpoints2))

                xpoints1 = fp_scatter_arr[i_arr][:, 0]
                ypoints1 = fp_scatter_arr[i_arr][:, 1]
                ax.scatter(xpoints1, ypoints1, s=15, alpha=1, label = lbl_curve) # lbl_scatter_arr[i_arr])
                if np.any(xpoints1) :
                    max_x = max(max_x, max(xpoints1))


            if max_x < 100 :
                ax.set_xlim(left=-100, right=100, emit=True, auto=False)           
            else :
                ax.axis('equal')

            ax.plot(0, 0, marker='^', ms=5, mfc='k', mec='k')
            ax.set_title(info_string, fontsize=10)

            ax.set_xlabel('crossrange, km')
            ax.set_ylabel('defense downrange, km')
    
            if n_arr > 1 :
                ax.legend(loc='best', frameon=False, framealpha=1.0)
    
            ax.grid()
        """ End of internal functions """
     
        fp_draw()
            
        ent_chart_fname = CEntry(chwin_row1, bg='white', width=30)
        ent_chart_fname.insert(0, chart_fname)
        btn_chart_save = Button(chwin_row1, text="Save Chart", command=fp_save)
        #ent_data_fname = Entry(chwin_row1, bg='white')    
        #ent_data_fname.insert(0, data_fname)
        #btn_data_save = Button(chwin_row1, text="Save Data", command=fp_data_save)
        
        ent_chart_fname.grid(row=0, column=0, ipadx=10, ipady=1)
        btn_chart_save.grid(row=0, column=1, ipadx=10, ipady=1, sticky='ew')
        #ent_data_fname.grid(row=1, column=0, ipadx=10, ipady=1)
        #btn_data_save.grid(row=1, column=1, ipadx=10, ipady=1, sticky='ew')

        #probing_chart_win.protocol("WM_DELETE_WINDOW", enable_probing)

        probing_chart_win.focus_force()
        probing_chart_win.bind('<Escape>', lambda esc: probing_chart_win.destroy())
        probing_chart_win.protocol("WM_DELETE_WINDOW", probing_chart_win.destroy)

""" END of gui_probing_chart """

def run_probing() :

    mtype = mtype_var.get()
    itype = itype_var.get()

    mode2 = fp_calc_mode_var.get()
    emode_sls = emode_var.get()
    angle_step = angle_step_var.get()
    acc = acc_var.get()
    h_int_min = mia_var.get()
    h_discr = h_discr_var.get()
    t_delay = t_delay_var.get()
    
    sect_angle_beg  = sect_angle_beg_var.get()
    sect_angle_end  = sect_angle_end_var.get()
    sect_angle_step = sect_angle_step_var.get()
    sect_dist_beg   = sect_dist_beg_var.get()
    sect_dist_num   = sect_dist_num_var.get()
    
    plot_hit_charts = plot_hit_charts_var.get()
    hit_chart_angle = hit_chart_angle_var.get()
    
    #probing_win.destroy()

    print("\nFootprint by probing started. Missile type m{}, Interceptor type i{}".format(mtype, itype))
    print("Missile type {} trajectory calculating...".format(mtype), end='')

    if set_time_stamp_var.get() : # possibly delete? $$$ #TODO
        r_now = datetime.now()
        t_stamp = "-" + r_now.strftime("%y%m%d-%H%M")
    else :
        t_stamp = ''

    if stdout_to_file_var.get() :
        file_name = 'probing_m{}_i{}{}.txt'.format(mtype, itype, t_stamp)
        if set_keep_stdout_file :
            keep_old_file(file_name)
        original = sys.stdout
        sys.stdout = open(file_name, 'w')

    if h_discr < 1000 : # can be set in meters or km, convert to meters if set in km
        h_discr *= 1000

    if h_int_min < 500 : # can be set in meters or km, convert to meters if set in km
        h_int_min *= 1000

    interceptor_data = rd.interceptor(itype, rd_fname)
    mpia = interceptor_data['mpia']
    mpia *= 1000
    h_int_min = max(h_int_min, mpia)

    op_range = interceptor_data['op_range']
    if op_range < 2000 :
        op_range *= 1000
    if op_range :
        print(">Interceptor's operational range {:.0f} km".format(op_range/1000))
    else :
        print(">Interceptor's operational range is not set.")        

    missile_data = rd.missile(mtype, rd_fname)
    trj = bm.balmisflight(missile_data)
    mrange = trj[len(trj) - 1, 2] * R_e
    print("\rMissile type m{} trajectory calculated, missile range={:.0f} km".format(mtype, mrange/1000))

    if mrange > bm_range_limit :
        print("STOP: Missile range too long for footprint calculation. The limit is {} km".format(bm_range_limit/1000))
        return False

    dist = mrange * dist_param  # irrelevant, dist is hardcoded in fp.footprint_calc_v2 function

    burn_time = sum(missile_data["t_bu"]) + sum(missile_data["t_delay"])

    t_int_lnc = burn_time + t_delay # earliest int launch counting from missile launch (launch detection time + etc.)

    det_range = 0.0
    if "det_range" in interceptor_data.keys() :
        if len(interceptor_data["det_range"]) > mtype :
            det_range = interceptor_data["det_range"][mtype] # detection range, this is set in the "rocket_data" module
        else :
            print("No detection range value for this missile. Detection range set to 0.")
            print("For quick test run 'Multi-Footprint by Detection Range.")
    else :
        print("No detection range values set in the interceptor data. Detection range set to 0.")
        print("For quick test run 'Multi-Footprint by Detection Range.")

    if det_range < 11000 :
        det_range *= 1000
    
    fp_st = time.time()
    fp_st1 = time.process_time()

    int_table = m.load_int_table(itype, fcc_constants.psi_step, beta_step, rd_fname, t_stamp, set_keep_int_tables_var.get())                

    if not mode2 :
        search_func = ss.short_search
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search
            search_type = "Shoot_look_shoot"
            save_label = "sls"

        print("Type of interception: " + search_type)
        fp_by_probing = ss.angle_dist_tab2(search_func,
                                             trj,
                                             int_table,
                                             h_int_min,
                                             t_int_lnc,
                                             op_range,
                                             det_range,
                                             t_delay,
                                             h_discr,
                                             sect_angle_beg,
                                             sect_angle_end,
                                             sect_angle_step,
                                             sect_dist_beg,
                                             sect_dist_num,
                                             plot_hit_charts,
                                             hit_chart_angle,
                                             mtype,
                                             itype
                                             )
    else :
        print("Probing mode2")
        search_func = ss.short_search2
        search_type = "Shoot_once"
        save_label = "son"
    
        if emode_sls :
            search_func = ss.sls_search2
            search_type = "Shoot_look_shoot"
            save_label = "sls"

        print("Type of interception: " + search_type)
        fp_by_probing = ss.probing2(search_func,
                                             trj,
                                             int_table,
                                             h_int_min,
                                             t_int_lnc,
                                             op_range,
                                             det_range,
                                             t_delay,
                                             h_discr,
                                             acc,
                                             sect_angle_beg,
                                             sect_angle_end,
                                             sect_angle_step,
                                             sect_dist_beg,
                                             sect_dist_num,
                                             plot_hit_charts,
                                             hit_chart_angle,
                                             mtype,
                                             itype
                                             )

    
    """
    angle_dist_tab = angle_dist_tab2[0]
    file_name = "angle_dist_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.json".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp)
    if set_keep_fp_data_var.get() :
        m.keep_old_file(file_name)
    angle_dist_tab_list = angle_dist_tab.tolist()
    json_array = json.dumps(angle_dist_tab_list, indent=4)
    with open(file_name, 'w') as rdf:
            rdf.write(json_array)
    #np.savetxt(file_name, angle_dist_tab, fmt='%.3f', delimiter = ',', header='angle,distance,dist_to_trj, X, Y, Xx, Zz' + ', ' + search_type)
    print("Footprint sector data saved to " + file_name)
    """
    
    fp_scatter = fp_by_probing #[1]
    #file_name = "fp_scatter_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.json".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp)
    #with open("fpsector_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.npy".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp), 'wb') as fpsector_f:
    #    np.save(fpsector_f, fp_scatter)
    #print("Footprint sector scatter data saved to fpscatter_m{}_i{}_{}-{}_{}grad_{}km_n{}_{}{}.npy".format(mtype, itype, sect_angle_beg, sect_angle_end, sect_angle_step, int(sect_dist_beg/1000), sect_dist_num, save_label, t_stamp))

    for i in range(len(fp_scatter)) :
        fp_scatter = np.append(fp_scatter, [[-fp_scatter[i, 0], fp_scatter[i, 1]]], axis=0)
    fp_scatter_list = fp_scatter.tolist()
    #print("Scatter array length = ", len(fp_scatter_list))
            
    """
    if emode_sls :
        search_func = ss.sls_search
    else :
        search_func = ss.short_search
    """
    # together 1-1
    fp_tab = [] #fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
    
    if show_ftprint_probe_var.get() :
        print("...footprint calculation started")
        if mode2 :
            num_dist = num_steps_mode2_var.get()
            fp_tab = ss.footprint_mode2(search_func, 
                                          trj, 
                                          int_table, 
                                          h_int_min, 
                                          t_int_lnc, 
                                          angle_step_mode2, 
                                          op_range, 
                                          det_range, 
                                          t_delay, 
                                          h_discr, 
                                          acc, 
                                          num_dist, 
                                          plot_hit_charts, 
                                          hit_chart_angle, 
                                          mtype, 
                                          itype)

        else :
            fp_tab = fp.footprint_calc_v2(search_func, trj, int_table, h_int_min, t_int_lnc, angle_step, op_range, det_range, t_delay, h_discr, acc, dist)
    
    """
    if np.any(fp_tab) :
        fp_tab_list = fp_tab.tolist()
    else :
        fp_tab_list = []
    """
        #print("Regular part of the footprint does not exist") # together 1-2
        #return
    #print("Curve array length = ", len(fp_tab_list))
    
    if False :
        file_name = "probing_test"
        if False : #set_keep_fp_data_var.get() :
            m.keep_old_file(file_name)
    
        fp_data = fp_scatter_list, fp_tab_list
        json_array = json.dumps(fp_data, indent=4)
        with open(file_name, 'w') as rdf:
                rdf.write(json_array)
                print("Scatter and tab data saved to " + file_name)

    if det_range :    
        chart_info_str = "MIA={} km, t_int_lnc={} s, det_range={} km, t_delay={} s, h_discr={} km"
        if not mode2 :
            chart_info_str += "\n{} angle {}-{} by {} degr, range from {:.0f} km, {} steps"
            chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, det_range/1000, t_delay, h_discr/1000, search_type, sect_angle_beg, sect_angle_end, sect_angle_step, sect_dist_beg, sect_dist_num)
            if op_range :
                title_str = "Footprint by probe mode1: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint by probe mode1: i_type={} m_type={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
        else :
            chart_info_str += "\n{}, angle_step {} degr, range by {} steps"
            chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, det_range/1000, t_delay, h_discr/1000, search_type, sect_angle_step, sect_dist_num)
            if op_range :
                title_str = "Footprint by probe mode2: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint by probe mode2: i_type={} m_type={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
    else :    
        chart_info_str = "MIA={} km, t_int_lnc={} s, sat_delay={} s, h_discr={} km"
        if not mode2 :
            chart_info_str += "\n{} angle {}-{} by {} degr, range from {:.0f} km, {} steps"
            chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, fcc_constants.sat_delay, h_discr/1000, search_type, sect_angle_beg, sect_angle_end, sect_angle_step, sect_dist_beg, sect_dist_num)
            if op_range :
                title_str = "Footprint by probe mode1: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint by probe mode1: i_type={} m_type={} mrange={:.0f} km".format(itype, mtype, mrange/1000)
        else :
            chart_info_str += "\n{}, angle_step {} degr, range by {} steps"
            chart_info_str = chart_info_str.format(h_int_min/1000, t_int_lnc, fcc_constants.sat_delay, h_discr/1000, search_type, sect_angle_step, sect_dist_num)
            if op_range :
                title_str = "Footprint by probe mode2: i_type={} op_range={:.0f} km m_type={} mrange={:.0f} km".format(i_type, op_range/1000, m_type, mrange/1000)
            else :
                title_str = "Footprint by probe mode2: i_type={} m_type={} mrange={:.0f} km".format(itype, mtype, mrange/1000)

    chart_fname = footprint_path + "/fp_probe_m{}_i{}_{}{}.png".format(mtype, itype, save_label, t_stamp)
    if set_keep_fp_chart_var.get() :
        m.keep_old_file(chart_fname)
    lbl_scatter = "probe"
    lbl_curve = "regular"
    sector_chart = gui_probing_chart([fp_scatter], [fp_tab], [lbl_scatter], [lbl_curve], chart_info_str, title_str, chart_fname)
    
    
    fp_et = time.time()
    fp_et1 = time.process_time()
    fp_elapsed_time = fp_et - fp_st
    fp_elapsed_time1 = fp_et1 - fp_st1
    if not mode2 :
        print("Footprint by probing calculation time = {:.3f} s, process time = {:.3f} s".format(fp_elapsed_time, fp_elapsed_time1))
    else :
        print("Footprint by mode2 probing calculation time = {:.3f} s, process time = {:.3f} s".format(fp_elapsed_time, fp_elapsed_time1))

    
    if stdout_to_file_var.get() :
        sys.stdout = original

    busy_running.set(False)


""" END of run_probing """

def gui_probing() : # routine's window shell, for actual routine see run_probing
    global probing_win
    #global enable_probing
    
    try :
        if probing_win.state() == "normal": probing_win.focus()
    except :
        probing_win = Toplevel(root)
        probing_win.title('Footprint by Probing the Area')
        probing_win.geometry('+500+150')
        probing_win.config(border=3, relief='ridge')


        """
        def enable_probing() :
            #btn_stop_probing.config(state="disabled")
            btn_run_probing.config(state="normal")
            #btn_run_probing2.config(state="normal")
            
        def schedule_check(t):
            root.after(1000, check_if_done, t)

        def check_if_done(t):
            if not t.is_alive():
                #os.system('say "Task complete"')
                #btn_stop_probing.config(state="disabled")
                #btn_run_probing.config(state="normal")
                #btn_run_probing2.config(state="normal")
                if sound_task_complete_var.get() :
                    if os.path.exists('sounds/Purr.aiff') :
                        os.system('afplay sounds/Purr.aiff')
            else:
                schedule_check(t)

        def start_probing() :
            global probing_thread
            
            #btn_stop_probing.config(state="normal")
            btn_run_probing.config(state="disabled")
            #btn_run_probing2.config(state="disabled")
            probing_thread = threading.Thread(target=run_probing)
            probing_thread.start()
            schedule_check(probing_thread)
            
        def run_probing2() :
            run_probing(mode2 = True)
        
        def start_probing2() :
            global probing_thread
            
            #btn_stop_probing.config(state="normal")
            btn_run_probing.config(state="disabled")
            #btn_run_probing2.config(state="disabled")
            probing_thread = threading.Thread(target=run_probing2)
            probing_thread.start()
            schedule_check(probing_thread)
            
        def stop_probing() :
            #pthread_kill(probing_thread.ident, SIGTSTP)
            #btn_stop_probing.config(state="disabled")
            btn_run_probing.config(state="normal")
        """
        
        mode2 = fp_calc_mode_var.get()
        
        if not mode2 :

            lbl_sect_angle_beg = Label(probing_win, text="Probing angle begin, degrees")
            ent_sect_angle_beg = CEntry(probing_win, textvariable=sect_angle_beg_var, width=10)
            lbl_sect_angle_end = Label(probing_win, text="Probing angle end, degrees")
            ent_sect_angle_end = CEntry(probing_win, textvariable=sect_angle_end_var, width=10)
            lbl_sect_angle_step = Label(probing_win, text="Probing angle step, degrees")
            ent_sect_angle_step = CEntry(probing_win, textvariable=sect_angle_step_var, width=10)
            lbl_sect_dist_beg = Label(probing_win, text="Probing distance begin, km")
            ent_sect_dist_beg = CEntry(probing_win, textvariable=sect_dist_beg_var, width=10)
            lbl_sect_dist_num = Label(probing_win, text="Number of probes over distance")
            ent_sect_dist_num = CEntry(probing_win, textvariable=sect_dist_num_var, width=10)
            if tooltips: tt = ToolTip(lbl_sect_dist_beg, msg="Probing distance end is max range", delay=1.0)
            
            lbl_show_ftprint_probe   = Label(probing_win, text="Also Show Calculated Footprint")
            btn_show_ftprint_probe   = Checkbutton(probing_win, variable=show_ftprint_probe_var)

            btn_save_config = Button(probing_win, text="Save Config", command=save_program_config)
            btn_run_probing = Button(probing_win, text="Compute", command=lambda: call_longrun(run_probing)) # start_probing)
            #btn_run_probing2 = Button(probing_win, text="Compute Mode2", command=start_probing2)
            #btn_stop_probing = Button(probing_win, text="Stop", command=stop_probing, state='disabled')
            
            lbl_sect_angle_beg.grid(row=0, column=0, sticky='w')
            ent_sect_angle_beg.grid(row=0, column=1)
            lbl_sect_angle_end.grid(row=1, column=0, sticky='w')
            ent_sect_angle_end.grid(row=1, column=1)
            lbl_sect_angle_step.grid(row=2, column=0, sticky='w')
            ent_sect_angle_step.grid(row=2, column=1)
            lbl_sect_dist_beg.grid(row=3, column=0, sticky='w')
            ent_sect_dist_beg.grid(row=3, column=1)
            lbl_sect_dist_num.grid(row=4, column=0, sticky='w')
            ent_sect_dist_num.grid(row=4, column=1)
            
            lbl_show_ftprint_probe.grid(row=5, column=0, sticky='w')
            btn_show_ftprint_probe.grid(row=5, column=1)
            
            btn_save_config.grid(row=6, column=0, columnspan=2, ipady=1, sticky='ew')
            btn_run_probing.grid(row=7, column=0, columnspan=2, ipady=1, sticky='ew')

        else: 
            lbl_sect_angle_step = Label(probing_win, text="Probing angle step, degrees")
            ent_sect_angle_step = CEntry(probing_win, textvariable=sect_angle_step_var, width=10)
            lbl_sect_dist_num = Label(probing_win, text="Number of probes over distance")
            ent_sect_dist_num = CEntry(probing_win, textvariable=sect_dist_num_var, width=10)

            lbl_show_ftprint_probe   = Label(probing_win, text="Also Show Calculated Footprint")
            btn_show_ftprint_probe   = Checkbutton(probing_win, variable=show_ftprint_probe_var)

            btn_save_config = Button(probing_win, text="Save Config", command=save_program_config)
            btn_run_probing = Button(probing_win, text="Compute", command=lambda: call_longrun(run_probing)) # start_probing)

            lbl_sect_angle_step.grid(row=0, column=0, sticky='w')
            ent_sect_angle_step.grid(row=0, column=1)
            lbl_sect_dist_num.grid(row=1, column=0, sticky='w')
            ent_sect_dist_num.grid(row=1, column=1)
            
            lbl_show_ftprint_probe.grid(row=2, column=0, sticky='w')
            btn_show_ftprint_probe.grid(row=2, column=1, sticky='ew')
            
            btn_save_config.grid(row=3, column=0, columnspan=2, ipady=1, sticky='ew')
            btn_run_probing.grid(row=4, column=0, columnspan=2, ipady=1, sticky='ew')

        #btn_run_probing2.grid(row=7, column=0, columnspan=2, ipady=1, sticky='ew')
        #btn_stop_probing.grid(row=5, column=1, ipady=1, sticky='ew')

        #rc_menu_string ='copy-paste-cut'
        #probing_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

        def win_destroy() :
            if not mode2 :
                if tooltips: 
                    tt.status='outside'
                    tt.withdraw()
            probing_win.destroy()
            
        probing_win.focus_force()
        probing_win.bind('<Escape>', lambda esc: win_destroy())


""" END of gui_probing_footprint """


def gui_interception_table() :
    if check_fpa :
        print("Set check_fpa=False and restart the program.")
        return False
    
    i_key = itype_var.get()

    it_st = time.time()
    print("x psi_step=", fcc_constants.psi_step)
    m.run_interceptor_table( i_key, rd_fname, fcc_constants.psi_step, set_keep_int_tables_var.get())

    it_et = time.time()
    it_elapsed_time = it_et - it_st
    print("Interceptor table calculation time = {:.3f}s".format(it_elapsed_time))

    m.run_interception_table(i_key, rd_fname, fcc_constants.psi_step, beta_step, set_keep_int_tables_var.get(), set_int_table_samp_verify_var.get())

def missile_editor() :
    rocket_editor(True)
    
def interceptor_editor() :
    rocket_editor(False)

def proper_exit():
    #cons_win.destroy()
    #root.quit()
    root.destroy()
    
def prg_exit() :
    if save_config_on_exit_var.get() :
        save_program_config()
    #if save_rocket_data_on_exit_var.get() :
        
    print("Exiting...")
    root.after(250, proper_exit)

def cfg_reset() :
    default_config()
    set_config()
    

def rocket_editor(is_missile=True) :
    root.withdraw()
    global medit_win

    try :
        if medit_win.state() == "normal": medit_win.focus_set()
    except :
        #btn_ch_mis.config(state='disabled')

        medit_win = Toplevel(root)
        if is_missile:
            medit_win.title('Missile View and Edit')
        else : 
            medit_win.title('Interceptor View and Edit')

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = int(screen_width / 3)
        y = 30 #int(screen_height / 4)
        x_size = int(screen_width * 7 / 12 - 50)
        y_size = int(screen_height * 3 / 4 - 30)
        if x_size > redt_max_x_size : x_size = redt_max_x_size
        if y_size > redt_max_y_size : y_size = redt_max_y_size
        medit_win.geometry('{}x{}+{}+{}'.format(x_size, y_size, x, y))

        #medit_win.geometry('+600+100')
        
        medit_win.rowconfigure(0, weight=1)
        medit_win.rowconfigure(1, weight=0)
        medit_win.columnconfigure(0, weight=1)
        #medit_win.columnconfigure(1, weight=1)
        
        def cdtype():
            if cdtype_var.get() == 'v2' :
                cdtype_var.set('ls')
            elif cdtype_var.get() == 'ls' :
                cdtype_var.set('ll')
#            elif cdtype_var.get() == 'll' : # remove these two
#                cdtype_var.set('al')        # remove these two
            else :
                cdtype_var.set('v2')
                
        def swap_int_trajtype():
            if trajtype_var.get() == 'int_exo' :
                trajtype_var.set('int_endo')
                vlheight_var.set('0')
                ent_vlheight.configure(state='readonly')
            else :
                trajtype_var.set('int_exo')
                vlheight_var.set(str(int_vl_height))
                ent_vlheight.configure(state='normal')

        def show_root_window() :
            medit_win.destroy()
            root.deiconify()

            """
            if is_missile :
                btn_ch_mis.config(state='normal')
            else :
                btn_ch_int.config(state='normal')
            """

        def get_s_data() : # gather string missile data from the editor window
            r_note = ent_note.get(1.0, 'end-1c')
            note_var.set(r_note)
            if is_missile :
                s_data = {
                    "m_key" : r_key_var.get(),
                    "type" : rname_var.get(),
                    "cd_type" : cdtype_var.get(),
                    "m_st" : mstage_var.get(),
                    "m_fu" : mfuel_var.get(),
                    "v_ex" : isp_var.get(),
                    "t_bu" : tburn_var.get(),
                    "t_delay" : sepdelay_var.get(),
                    "a_mid" : amid_var.get(),
                    "m_warhead" : mwarhead_var.get(),
                    "m_shroud" : mshroud_var.get(),
                    "t_shroud" : tshroud_var.get(),
                    "m_pl" : mpload_var.get(),
                    "a_nz" : anozzle_var.get(),
                    "c_bal" : cball_var.get(),
                    "vert_launch_height" : vlheight_var.get(),
                    "grav_turn_angle" : gtangle_var.get(),
                    "range" : rrange_var.get(),
                    "traj_type" : trajtype_var.get(),
                    "note" : note_var.get()
                }
            else :
                s_data = {
                    "i_key" : r_key_var.get(),
                    "type" : rname_var.get(),
                    "cd_type" : cdtype_var.get(),
                    "m_st" : mstage_var.get(),
                    "m_fu" : mfuel_var.get(),
                    "v_ex" : isp_var.get(),
                    "t_bu" : tburn_var.get(),
                    "t_delay" : sepdelay_var.get(),
                    "a_mid" : amid_var.get(),
                    "m_warhead" : mwarhead_var.get(),
                    "m_shroud" : mshroud_var.get(),
                    "t_shroud" : tshroud_var.get(),
                    "m_pl" : mpload_var.get(),
                    "a_nz" : anozzle_var.get(),
                    "c_bal" : cball_var.get(),
                    "vert_launch_height" : vlheight_var.get(),
                    "flight_path_angle" : fpangle_var.get(),
                    "range" : rrange_var.get(),
                    "traj_type" : trajtype_var.get(),
                    "mpia" : mpia_var.get(),
                    "op_range" : oprange_var.get(),
                    "det_range" : detrange_var.get(),
                    "note" : note_var.get()
                }
            return s_data

        def get_window_rdata() : # gather (string) missile data from window and convert to numerical
            r_data = get_s_data()
            #r_data = {key:val if key in ('m_key', 'i_key', 'type', 'cd_type', 'traj_type', 'note') else eval(str(val), {'pi' : 3.14}) for key, val in r_data.items()}
            #r_data = {key:list(val) if key in ("m_st", "m_fu", "v_ex", "t_bu", "t_delay", "a_mid", "det_range") else val for key, val in r_data.items()} # list
            r_data = rd.str2num(r_data)
            return r_data
        
        
        def test_flight() :
            r_rocket_data = get_window_rdata()
            #print(r_rocket_data)
            trajectory_data = False
            ind_flight_dataprint = True
            r_range = bm.balmisflight(r_rocket_data, trajectory_data, ind_flight_dataprint)
            if is_missile :
                print("Missile range = {:.0f} km".format(r_range/1000))
            else :
                print("Interceptor range = {:.0f} km".format(r_range/1000))
                
        def trj_charts() :
            r_rocket_data = get_window_rdata()
            gui_trajcharts(r_rocket_data, is_missile)
                
        def maxrange() :
            r_rocket_data = get_window_rdata()
            #r_rocket_data["traj_type"] = "bal_mis"
            gui_maxrange(r_rocket_data)
        
        def rcopy() :
            btn_mdelete.config(state='disabled')
            btn_mcopy.config(state='disabled')
            r_name = rname_var.get() # long string name with m/i+number index in front
            l_prefix = 'm' if is_missile else 'i'
            old_prefix = str(r_key_var.get()) # current rocket number
            old_prefix = l_prefix + old_prefix # current rocket index
            r_name = r_name.replace(old_prefix, '')
            r_key = max(r_key_list) + 1
            r_key_var.set(r_key)
            r_name = l_prefix + str(r_key) + r_name
            rname_var.set(r_name)
            
        def m2i_copy() :
            r_name = rname_var.get() # long string name with m/i+number index in front
            l_prefix = 'm' # prefix to be deleted
            old_prefix = str(r_key_var.get()) # current rocket number
            old_prefix = l_prefix + old_prefix # current rocket index
            r_name = r_name.replace(old_prefix, '') # delete current rocket index from the string name

            s_data_list = rd.load_s_idata()
            key_key = 'i_key'
            r_key_list = []
            for i_sd in s_data_list : # build list of keys
                r_key_list.append(i_sd[key_key])
            r_key = max(r_key_list) + 1
           
            r_key_var.set(r_key) # new current interceptor number
            r_name = 'i' + str(r_key) + r_name
            rname_var.set(r_name) # new interceptor name with index in front

            save_data = get_s_data()
            save_data["i_key"] = r_key
            save_data["flight_path_angle"] = gtangle_var.get()
            save_data["traj_type"] = 'int_endo'
            save_data["vert_launch_height"] = '0'
            save_data["mpia"] = '0'
            save_data["op_range"] = ''
            save_data["det_range"] = ''
            save_data.pop("m_key")
            save_data.pop("grav_turn_angle")

            s_data_list.append(save_data)
            r_key_list.append(r_key)
            
            r_rocket_data = (rd.load_s_mdata(), s_data_list)
            itype_var.set(r_key)
            iname_var.set(save_data['type'])
            iname1_var.set(iname_var.get().split('#', 1)[0])
            r_item = "Interceptor i"
            
            rd.save_rdata(r_rocket_data)
            print("\n{}{} data saved to file {}".format(r_item, r_key, rd_fname))
            
            is_missile = False
            show_root_window()
            interceptor_editor()
            medit_win.focus_set()                       

        
        def rsave() :
            btn_mcopy.config(state='normal')
            btn_mdelete.config(state='normal')
            save_data = get_s_data()
            r_key = r_key_var.get()
            #print(s_data_list)
            if r_key not in r_key_list :
                s_data_list.append(save_data)
                r_key_list.append(r_key)
            else :
                for i_sd in range(len(s_data_list)) :
                    if s_data_list[i_sd][key_key] == r_key :
                        s_data_list[i_sd] = save_data
                        break

            if is_missile :
                r_rocket_data = (s_data_list, rd.load_s_idata()) # missile data and interceptor data need to be saved together
                mtype_var.set(r_key)
                mname_var.set(save_data['type'])
                mname1_var.set(mname_var.get().split('#', 1)[0])
                r_item = "Missile m"

            else :
                r_rocket_data = (rd.load_s_mdata(), s_data_list)
                itype_var.set(r_key)
                iname_var.set(save_data['type'])
                iname1_var.set(iname_var.get().split('#', 1)[0])
                r_item = "Interceptor i"
            
            rd.save_rdata(r_rocket_data)
            print("\n{}{} data saved to file {}".format(r_item, r_key, rd_fname))


        def saveclose() :
            rsave()
            show_root_window()
            
                    
        def rdelete() :
            if pop_confirm('Confirm deletion', 'Delete current rocket record?') :
            #if messagebox.askokcancel("Confirm deletion", "Delete current rocket record?"):
            
                r_key = r_key_var.get()
                print("is_missile = {}, key_key = {}, r_key = {}".format(is_missile, key_key, r_key))
                for i_sd in range(len(s_data_list)):
                    if s_data_list[i_sd][key_key] == r_key :
                        del s_data_list[i_sd]
                        break
                r_key_list.remove(r_key)
                if is_missile :
                    r_rocket_data = (s_data_list, rd.load_s_idata())
                    r_item = "Missile m"
                    r_mtype = mtype_var.get()
                    if r_mtype == r_key :
                        r_mtype = s_data_list[0]['m_key']
                        mtype_var.set(r_mtype)
                        r_mname = s_data_list[0]['type']
                        mname_var.set(r_mname)
                        mname1_var.set(mname_var.get().split('#', 1)[0])
                else :
                    r_rocket_data = (rd.load_s_mdata(), s_data_list)
                    r_item = "Interceptor i"
                    r_itype = itype_var.get()
                    if r_itype == r_key :
                        r_itype = s_data_list[0]['i_key']
                        itype_var.set(r_itype)
                        r_iname = s_data_list[0]['type']
                        iname_var.set(r_iname)
                        iname1_var.set(iname_var.get().split('#', 1)[0])
                
                rd.save_rdata(r_rocket_data)
                print("\n{}{} data deleted, rocket data file {} updated".format(r_item, r_key, rd_fname))
               
                show_root_window()
            
            else:
                print("else")
                pass
        
        frm_row0 = Frame(medit_win, border=1, relief="groove")
        frm_row1 = Frame(medit_win, border=1                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        , relief="groove")
        frm_row0.grid(column=0, row=0, sticky='news')
        frm_row1.grid(column=0, row=1, sticky='ew')

        frm_row0.columnconfigure(0, weight=0)
        frm_row0.columnconfigure(1, weight=1)
        frm_row0.columnconfigure(2, weight=0)
        
        if is_missile : # "Note" entry
            frm_row0.rowconfigure(19, weight=1)
        else :
            frm_row0.rowconfigure(22, weight=1)

        frm_row1.columnconfigure(0, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(1, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(2, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(3, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(4, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(5, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(6, weight=1, uniform='r_edit_buttons')
        frm_row1.columnconfigure(7, weight=1, uniform='r_edit_buttons')
        if is_missile :
            frm_row1.columnconfigure(8, weight=1, uniform='r_edit_buttons')
                
        if is_missile :
            r_key = mtype_var.get()
            key_key = 'm_key'
            s_data_list = rd.load_s_mdata()
        else :
            r_key = itype_var.get()
            key_key = 'i_key'
            s_data_list = rd.load_s_idata()
        
        r_key_var = IntVar(medit_win, value = r_key)
        
        for i_sd in s_data_list :
            #print(type(key_key), key_key, type(i_sd[key_key]), i_sd[key_key], type(r_key), r_key)
            if i_sd[key_key] == r_key :
                s_data = i_sd
                break

        r_key_list = []
        for i_sd in s_data_list : # build list of keys
            r_key_list.append(i_sd[key_key])
        #print(r_key_list) # debug rocket sequence

        #s_mdata = rd.s_missile(m_key, rd_fname) # read string-value data

        if r_key != s_data[key_key] :
            print("Different key exception in missile_editor: mkey={} type {}, s_data[{}]={} type {}".format(r_key, type(r_key), key_key, s_data[key_key], type( s_data[key_key])))

        rname_var = StringVar(medit_win, value = s_data["type"])
        cdtype_var = StringVar(medit_win, value = s_data["cd_type"])
        mstage_var = StringVar(medit_win, value = s_data["m_st"])
        mfuel_var = StringVar(medit_win, value = s_data["m_fu"])
        isp_var = StringVar(medit_win, value = s_data["v_ex"])
        tburn_var = StringVar(medit_win, value = s_data["t_bu"])
        sepdelay_var = StringVar(medit_win, value = s_data["t_delay"])

        amid_var = StringVar(medit_win, value = s_data["a_mid"])
        mwarhead_var = StringVar(medit_win, value = s_data["m_warhead"])
        mshroud_var = StringVar(medit_win, value = s_data["m_shroud"])
        tshroud_var = StringVar(medit_win, value = s_data["t_shroud"])
        mpload_var = StringVar(medit_win, value = s_data["m_pl"])
        anozzle_var = StringVar(medit_win, value = s_data["a_nz"])
        cball_var = StringVar(medit_win, value = s_data["c_bal"])

        vlheight_var = StringVar(medit_win, value = s_data["vert_launch_height"])
        if is_missile :
            gtangle_var = StringVar(medit_win, value = s_data["grav_turn_angle"])
        else :
            fpangle_var = StringVar(medit_win, value = s_data["flight_path_angle"])
        trajtype_var = StringVar(medit_win, value = s_data["traj_type"])
        if not is_missile :
            mpia_var = StringVar(medit_win, value = s_data["mpia"])
            oprange_var = StringVar(medit_win, value = s_data["op_range"])
            detrange_var = StringVar(medit_win, value = s_data["det_range"])
        rrange_var = StringVar(medit_win, value = s_data["range"])
        note_var = StringVar(medit_win, value = s_data["note"])
        
        lbl_mkey = Label(frm_row0, text = "Missile Model Number")
        #lbl_mkey = Label(frm_row0, text = "Missile Model Number", anchor='w', padx=3, width=45)
        lbl_rname = Label(frm_row0, text = "Missile Model Name")
        lbl_cdtype = Label(frm_row0, text = "Rocket Type")
        lbl_mstage = Label(frm_row0, text = "'Dry' stage mass(es), kg")
        lbl_mfuel = Label(frm_row0, text = "Stage fuel mass(es), kg")
        lbl_isp = Label(frm_row0, text = "Stage(s) Isp, s or Vex, m/s")
        lbl_tburn = Label(frm_row0, text = "Stage(s) burn time, s)")
        lbl_sepdelay = Label(frm_row0, text = "Stage and payload separation delay, s")

        lbl_amid = Label(frm_row0, text = "Stage max X-section area, m2, or diam dx.xx, m")
        lbl_mpload = Label(frm_row0, text = "Payload mass, kg")
        lbl_mwarhead = Label(frm_row0, text = "Warhead mass (if separates), kg")
        lbl_mshroud = Label(frm_row0, text = "Shroud mass, kg")
        lbl_tshroud = Label(frm_row0, text = "Shroud release time, s (0=unused)")
        lbl_anozzle = Label(frm_row0, text = "1st stage nozzle area, m2 or diameter dx.xx, m")
        lbl_cball = Label(frm_row0, text = "Ballisitic coefficient, kg/m2")

        lbl_vlheight = Label(frm_row0, text = "Vertical launch height, m")
        lbl_trajtype = Label(frm_row0, text = "Trajectory type")
        if is_missile :
            lbl_gtangle = Label(frm_row0, text = "Initial gravity turn angle, degrees")
            lbl_mrange = Label(frm_row0, text = "Missile range (text, for reference)")
        else :
            lbl_fpangle = Label(frm_row0, text = "Flight path angle, degrees (for test)")
            lbl_mpia = Label(frm_row0, text = "Min feasible intercept alt, km (0 = not used)")
            lbl_oprange = Label(frm_row0, text = "Operational range, km (0 = not used)")
            lbl_detrange = Label(frm_row0, text = "Detection ranges for missiles, km")
            lbl_irange = Label(frm_row0, text = "Interceptor range (text, for reference)")
        lbl_note = Label(frm_row0, text = "Notes")
        
        ent_mkey = Entry(frm_row0, textvariable=r_key_var, state="readonly")
        ent_rname = CEntry(frm_row0, textvariable=rname_var)
        ent_cdtype = Entry(frm_row0, textvariable=cdtype_var, width=20, state="readonly") #, readonlybackground='white')
        btn_cdtype = Button(frm_row0, text="Change", command=cdtype)
        
        ent_mstage = CEntry(frm_row0, textvariable=mstage_var)
        ent_mfuel = CEntry(frm_row0, textvariable=mfuel_var)
        ent_isp = CEntry(frm_row0, textvariable=isp_var)
        ent_tburn = CEntry(frm_row0, textvariable=tburn_var)
        ent_sepdelay = CEntry(frm_row0, textvariable=sepdelay_var)

        ent_amid = CEntry(frm_row0, textvariable=amid_var)
        ent_mpload = CEntry(frm_row0, textvariable=mpload_var)
        ent_mwarhead = CEntry(frm_row0, textvariable=mwarhead_var)
        ent_mshroud = CEntry(frm_row0, textvariable=mshroud_var)
        ent_tshroud = CEntry(frm_row0, textvariable=tshroud_var)
        ent_anozzle = CEntry(frm_row0, textvariable=anozzle_var)
        ent_cball = CEntry(frm_row0, textvariable=cball_var)
        
        if is_missile :
            ent_trajtype = Entry(frm_row0, textvariable=trajtype_var, state="readonly")
            ent_vlheight = Entry(frm_row0, textvariable=vlheight_var)
            ent_gtangle = CEntry(frm_row0, textvariable=gtangle_var)
        else :
            ent_trajtype = Entry(frm_row0, textvariable=trajtype_var, width=20, state="readonly") #, readonlybackground='white')
            btn_trajtype = Button(frm_row0, text="Change", command=swap_int_trajtype)
            if trajtype_var.get() == 'int_endo' :
                ent_vlheight = Entry(frm_row0, textvariable=vlheight_var, state="readonly")
            else :
                ent_vlheight = Entry(frm_row0, textvariable=vlheight_var)
            ent_fpangle = CEntry(frm_row0, textvariable=fpangle_var)
            ent_mpia = CEntry(frm_row0, textvariable=mpia_var)
            ent_oprange = CEntry(frm_row0, textvariable=oprange_var)
            ent_detrange = CEntry(frm_row0, textvariable=detrange_var)

        ent_rrange = CEntry(frm_row0, textvariable=rrange_var)
        
        ent_note = Text(frm_row0, height=6, wrap='word', width=55)
        ent_note.insert(END, note_var.get().replace('\\', '\n'))
        ent_note.configure(undo=True, autoseparators=True)

        lbl_mkey.grid(row=0, column=0, sticky='w', ipadx=3)
        ent_mkey.grid(row=0, column=1, columnspan=2, sticky='ew', ipadx=3)
        lbl_rname.grid(row=1, column=0, sticky='w', ipadx=3)
        ent_rname.grid(row=1, column=1, columnspan=2, sticky='ew', ipadx=3)
        lbl_cdtype.grid(row=2, column=0, sticky='w', ipadx=3)
        ent_cdtype.grid(row=2, column=1, sticky='ew', ipadx=3)
        btn_cdtype.grid(row=2, column=2, sticky='ew', ipady=1, ipadx=10)
        
        lbl_mstage.grid(row=3, column=0, sticky='w', ipadx=3)
        ent_mstage.grid(row=3, column=1, columnspan=2, sticky='ew')
        lbl_mfuel.grid(row=4, column=0, sticky='w', ipadx=3)
        ent_mfuel.grid(row=4, column=1, columnspan=2, sticky='ew')
        lbl_isp.grid(row=5, column=0, sticky='w', ipadx=3)
        ent_isp.grid(row=5, column=1, columnspan=2, sticky='ew')
        lbl_tburn.grid(row=6, column=0, sticky='w', ipadx=3)
        ent_tburn.grid(row=6, column=1, columnspan=2, sticky='ew')
        lbl_sepdelay.grid(row=7, column=0, sticky='w', ipadx=3)
        ent_sepdelay.grid(row=7, column=1, columnspan=2, sticky='ew')
        
        lbl_amid.grid(row=8, column=0, sticky='w', ipadx=3)
        ent_amid.grid(row=8, column=1, columnspan=2, sticky='ew')
        lbl_mpload.grid(row=9, column=0, sticky='w', ipadx=3)
        ent_mpload.grid(row=9, column=1, columnspan=2, sticky='ew')
        lbl_mwarhead.grid(row=10, column=0, sticky='w', ipadx=3)
        ent_mwarhead.grid(row=10, column=1, columnspan=2, sticky='ew')
        lbl_mshroud.grid(row=11, column=0, sticky='w', ipadx=3)
        ent_mshroud.grid(row=11, column=1, columnspan=2, sticky='ew')
        lbl_tshroud.grid(row=12, column=0, sticky='w', ipadx=3)
        ent_tshroud.grid(row=12, column=1, columnspan=2, sticky='ew')
        lbl_anozzle.grid(row=13, column=0, sticky='w', ipadx=3)
        ent_anozzle.grid(row=13, column=1, columnspan=2, sticky='ew')
        lbl_cball.grid(row=14, column=0, sticky='w', ipadx=3)
        ent_cball.grid(row=14, column=1, columnspan=2, sticky='ew')
        lbl_trajtype.grid(row=15, column=0, sticky='w', ipadx=3)

        if is_missile :
            ent_trajtype.grid(row=15, column=1, columnspan=2, sticky='ew')
        else: 
            ent_trajtype.grid(row=15, column=1, sticky='ew', ipadx=3)
            btn_trajtype.grid(row=15, column=2, sticky='ew', ipady=1, ipadx=10)
        
        lbl_vlheight.grid(row=16, column=0, sticky='w', ipadx=3)
        ent_vlheight.grid(row=16, column=1, columnspan=2, sticky='ew')
        if is_missile :
            lbl_gtangle.grid(row=17, column=0, sticky='w', ipadx=3)
            ent_gtangle.grid(row=17, column=1, columnspan=2, sticky='ew')
            lbl_mrange.grid(row=18, column=0, sticky='w', ipadx=3)
            ent_rrange.grid(row=18, column=1, columnspan=2, sticky='ew')
            """ above weight of row 19 set to 1 """
            lbl_note.grid(row=19, column=0, sticky='nw', ipadx=3)
            ent_note.grid(row=19, column=1, columnspan=2, sticky='news')
        else: 
            lbl_fpangle.grid(row=17, column=0, sticky='w', ipadx=3)
            ent_fpangle.grid(row=17, column=1, columnspan=2, sticky='ew')            
            lbl_mpia.grid(row=18, column=0, sticky='w', ipadx=3)
            ent_mpia.grid(row=18, column=1, columnspan=2, sticky='ew')
            lbl_oprange.grid(row=19, column=0, sticky='w', ipadx=3)
            ent_oprange.grid(row=19, column=1, columnspan=2, sticky='ew')
            lbl_detrange.grid(row=20, column=0, sticky='w', ipadx=3)
            ent_detrange.grid(row=20, column=1, columnspan=2, sticky='ew')
            lbl_irange.grid(row=21, column=0, sticky='w', ipadx=3)
            ent_rrange.grid(row=21, column=1, columnspan=2, sticky='ew')
            """ above weight of row 22 set to 1 """
            lbl_note.grid(row=22, column=0, sticky='nw', ipadx=3)
            ent_note.grid(row=22, column=1, columnspan=2, sticky='news')
        if tooltips: 
            tt_re = []
            tt_re.append(ToolTip(lbl_cdtype, msg="ls - large solid fuel (eg, MM or Trident); ll - large liquid fuel (eg, Atlas, Titan, SLV); v2 - V2-like (e.g., small missile with fins)", delay=1.0))
            #ToolTip(lbl_cdtype, msg="ls - large solid fuel (eg, MM or Trident); ll - large liquid fuel (eg, Atlas, Titan, SLV); V2-like (eg, small missile with fins)", delay=1.0)
            tt_re.append(ToolTip(lbl_isp, msg="Interpreted as Isp in sec if < 1000, or as Vex otherwise", delay=1.0))
            if is_missile :
                tt_re.append(ToolTip(lbl_gtangle, msg="Initial gravity turn angle measured from vertical, degrees", delay=1.0))
            else :
                tt_re.append(ToolTip(lbl_mpia, msg="Minimum feasible interception altitude due to technical limitations, km", delay=1.0))
                tt_re.append(ToolTip(lbl_fpangle, msg="Flight path angle measured from horizontal, degrees", delay=1.0))
            tt_re.append(ToolTip(lbl_amid, msg="One value can be entered if it's the same for all stages", delay=1.0))
            tt_re.append(ToolTip(lbl_sepdelay, msg="Can be left empty if zero for all interstages;\none value can be entered if it's the same for all interstages", delay=1.0))

        # Buttons: Test Flight, Save, Make Copy, Delete
        btn_mflight = Button(frm_row1, text="Test Flight", command=test_flight)
        btn_charts = Button(frm_row1, text="Flight Charts", command=trj_charts)
        btn_maxrange = Button(frm_row1, text="Max Range Est.", command=maxrange)
        btn_mcopy = Button(frm_row1, text="Duplicate", command=rcopy)
        if is_missile :
            btn_m2i = Button(frm_row1, text="Copy as Interc.", command=m2i_copy)
        btn_msave = Button(frm_row1, text="Save", command=rsave)
        btn_saveclose = Button(frm_row1, text="Save&Close", command=saveclose)
        btn_exit = Button(frm_row1, text="Close", command=show_root_window)
        btn_mdelete = Button(frm_row1, text="Delete", command=rdelete)
        
        btn_mflight.grid(row=0, column=0, ipady=3, sticky='ew')
        btn_charts.grid(row=0, column=1, ipady=3, sticky='ew')
        btn_maxrange.grid(row=0, column=2, ipady=3, sticky='ew')
        btn_mcopy.grid(row=0, column=3, ipady=3, sticky='ew')
        if is_missile :
            btn_m2i.grid(row=0, column=4, ipady=3, sticky='ew')
            btn_msave.grid(row=0, column=5, ipady=3, sticky='ew')
            btn_saveclose.grid(row=0, column=6, ipady=3, sticky='ew')
            btn_exit.grid(row=0, column=7, ipady=3, sticky='ew')
            btn_mdelete.grid(row=0, column=8, ipady=3, sticky='ew')
        else :
            btn_msave.grid(row=0, column=4, ipady=3, sticky='ew')
            btn_saveclose.grid(row=0, column=5, ipady=3, sticky='ew')
            btn_exit.grid(row=0, column=6, ipady=3, sticky='ew')
            btn_mdelete.grid(row=0, column=7, ipady=3, sticky='ew')

        if tooltips: tt_re.append(ToolTip(btn_mcopy, msg="Create a new missile (with new Model Number) with this data. Not saved until 'Save' button clicked.", delay=1.0))

        #rc_menu_string ='copy-paste-cut'
        #medit_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))
        
        def win_destroy() :
            if tooltips: 
                for tt in tt_re :
                    tt.status='outside'
                    tt.withdraw()
            show_root_window()
            
        medit_win.focus_force()
        medit_win.bind('<Escape>', lambda esc: win_destroy())
        medit_win.protocol("WM_DELETE_WINDOW", win_destroy)

def do_nothing() :
    pass


""" Main Window ****************** """
if __name__ == '__main__':
    
    root = Tk()
    root.title("Ballistic Missile Defense Footprint Calculation and Comparison v." + version)
    #root.iconbitmap('path/image.ico')
    root.geometry("+400+20")
    root.columnconfigure(0, weight=1)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=0)
    root.rowconfigure(1, weight=0)
    #root.rowconfigure(1, weight=1)
    #root.rowconfigure(2, weight=1)
    
    #toolbar = Frame(root, border=1, relief="groove" )
    #toolbar.grid(column=0, columnspan=2, row=0, sticky='ew')
    
    #Button(toolbar, text="EXIT PROGRAM", font=("Times", 14), command=root.quit).grid(column=0, columnspan=2, row=0, sticky='w')
    #Button(toolbar, text="EXIT PROGRAM", font=("Times", 14), command=root.quit).pack(in_=toolbar, side="left")
    
    default_config() # default configuration
    
    busy_running = BooleanVar(root, value = False)
    
    mtype_var = IntVar(root, value = program_config['mtype'])
    itype_var = IntVar(root, value = program_config['itype'])
    
    mia_var = DoubleVar(root, value = program_config['h_int_min'])
    h_discr_var = DoubleVar(root, value = program_config['h_discr'])
    t_delay_var = DoubleVar(root, value = program_config['t_delay'])
    
    h_int_min_list_var = StringVar(root, value = program_config['h_int_min_list'])
    h_discr_list_var = StringVar(root, value = program_config['h_discr_list'])
    t_delay_list_var = StringVar(root, value = program_config['t_delay_list'])
    
    fp_calc_mode_var = BooleanVar(root, value = program_config['fp_calc_mode'])
    acc_var = DoubleVar(root, value = program_config['acc'])
    angle_step_var = DoubleVar(root, value = program_config['angle_step']) # was IntVar originally
    #angle_step_mode2_var = DoubleVar(root, value = program_config['angle_step_mode2'])
    num_steps_mode2_var = IntVar(root, value = program_config['num_steps_mode2'])
    emode_var = BooleanVar(root, value = program_config['set_shoot_look_shoot']) # interception type, True = Shoot-Look-Shoot
    
    det_range_list_var = StringVar(root, value = str(program_config['det_range_list']))
    mumi_list_var = StringVar(root, value = str(program_config['mumi_list']))
    muin_list_var = StringVar(root, value = str(program_config['muin_list']))
    
    sect_angle_beg_var = DoubleVar(root, value = program_config['sect_angle_beg'])
    sect_angle_end_var = DoubleVar(root, value = program_config['sect_angle_end'])
    sect_angle_step_var = DoubleVar(root, value = program_config['sect_angle_step'])
    sect_dist_beg_var = DoubleVar(root, value = program_config['sect_dist_beg'])
    sect_dist_num_var = IntVar(root, value = program_config['sect_dist_num'])
    
    set_mirror_segment_var = BooleanVar(root, value = program_config['set_mirror_segment'])
    show_ftprint_probe_var = BooleanVar(root, value = program_config['show_ftprint_probe'])

    plot_hit_charts_var = BooleanVar(root, value = program_config['plot_hit_charts'])
    hit_chart_angle_var = DoubleVar(root, value = program_config['hit_chart_angle'])
    
    gtheight_beg_var = DoubleVar(root, value = program_config['gtheight_beg'])
    gtheight_end_var = DoubleVar(root, value = program_config['gtheight_end'])
    gtangle_beg_var = DoubleVar(root, value = program_config['gtangle_beg'])
    gtangle_end_var = DoubleVar(root, value = program_config['gtangle_end'])
    maxrange_acc_var = DoubleVar(root, value = program_config['maxrange_acc'])
    
    set_keep_int_tables_var = BooleanVar(root, value = program_config['set_keep_int_tables'])
    set_keep_fp_chart_var = BooleanVar(root, value = program_config['set_keep_fp_chart'])
    set_keep_fp_data_var = BooleanVar(root, value = program_config['set_keep_fp_data'])
    set_keep_trj_data_var = BooleanVar(root, value = program_config['set_keep_trj_data'])
    
    stdout_to_file_var = BooleanVar(root, value = program_config['stdout_to_file'])
    set_keep_stdout_file_var = BooleanVar(root, value = program_config['set_keep_stdout_file'])
    set_time_stamp_var = BooleanVar(root, value = program_config['set_time_stamp'])
    set_int_table_samp_verify_var = BooleanVar(root, value = program_config['set_int_table_samp_verify'])
    
    sound_task_complete_var = BooleanVar(root, value = program_config['sound_task_complete'])
    save_config_on_exit_var = BooleanVar(root, value = program_config['save_config_on_exit'])
    #save_rocket_data_on_exit_var = BooleanVar(root, value = program_config['save_rocket_data_on_exit'])
    show_extra_param_var = BooleanVar(root, value = program_config['show_extra_param'])
    show_extra_procs_var = BooleanVar(root, value = program_config['show_extra_procs'])
    
    show_chart_titles_var = BooleanVar(root, value = program_config['show_chart_titles'])
    no_atmosphere_var     = BooleanVar(root, value = program_config['no_atmosphere'])

    set_psi_step_var  = DoubleVar(root, value = program_config['set_psi_step'])
    set_sat_delay_var = DoubleVar(root, value = program_config['set_sat_delay'])
    def_sector_step_var = DoubleVar(root, value = program_config['def_sector_step'])

    load_config(cfg_fname)  # load config parameters from file, those not present are left at default values
    set_config()            # set Var variables with config parameters
                            # NB: constants checked after definition of the Output Console
    
    missile_data = rd.s_missile(mtype_var.get(), rd_fname)
    if not missile_data :
        mtype_var.set(1)
        missile_data = rd.s_missile(mtype_var.get(), rd_fname)
    
    mname_var = StringVar(root, value = missile_data["type"])
    mname1_var = StringVar(root, value = mname_var.get().split('#', 1)[0])
    
    #missile_label = StringVar(root, value = "Missile: " + missile_type)
    
    interceptor_data = rd.s_interceptor(itype_var.get(), rd_fname)
    if not interceptor_data :
        itype_var.set(11)
        interceptor_data = rd.s_missile(itype_var.get(), rd_fname)

    iname_var = StringVar(root, value = interceptor_data["type"])
    iname1_var = StringVar(root, value = iname_var.get().split('#', 1)[0])
    #interceptor_label = StringVar(root, value = "Interceptor: " + interceptor_type)
    
    """ Root Frames ****************** """
    
    frame_col1 = Frame(root, border=1, relief="groove")
    frame_col2 = Frame(root, border=1, relief="groove")
    frame_col1.grid(column=0, row=0, sticky='ns')
    frame_col2.grid(column=1, row=0, sticky='ns')
    
    frm_row1 = Frame(root, border=1, relief="groove")
    frm_row1.grid(column=0, columnspan=2, row=1, sticky='ew')
    
    frm_row1.columnconfigure(0, weight=1, uniform='mainbuttons')
    frm_row1.columnconfigure(1, weight=1, uniform='mainbuttons')
    frm_row1.columnconfigure(2, weight=1, uniform='mainbuttons')
    if show_extra_param_var.get() :
        frm_row1.columnconfigure(3, weight=1, uniform='mainbuttons')
    
    
    """ Root Buttons Frame """
    
    def extra_procedures():
        if show_extra_procs_var.get() :
            if not btn_probing.winfo_ismapped() :
                btn_probing.grid(column=0, row=6, sticky='ew')
                btn_interc_table.grid(column=0, row=4, sticky='ew')
            else :
                extra_param()

        else :
            if btn_probing.winfo_ismapped() :
                btn_probing.grid_remove()
                btn_interc_table.grid_remove()
            else :
                extra_param()

    # Buttons: Reset Config Save Config, Exit
    btn_cfgreset = Button(frm_row1, text="Config Reset", command=cfg_reset) #, width=20)
    btn_cfgsave = Button(frm_row1, text="Config Save", command=save_program_config) #, width=20)
    #btn_rootexit = Button(frm_row1, text="Exit", command=prg_exit, width=20, state='disabled')
    btn_rootexit = Button(frm_row1, text="Exit", command=prg_exit) #, width=20)
    if show_extra_param_var.get() :
        btn_extra_param = Button(frm_row1, text="Extra Settings", command=extra_procedures) #, width=20)
    
    btn_cfgreset.grid(row=0, column=0, ipady=3, sticky='ew')
    btn_cfgsave.grid(row=0, column=1, ipady=3, sticky='ew')
    if show_extra_param_var.get() :
        #frm_row1.columnconfigure(3, weight=1)
        btn_extra_param.grid(row=0, column=2, ipady=3, sticky='ew')
        btn_rootexit.grid(row=0, column=3, ipady=3, sticky='ew')
    else : 
        btn_rootexit.grid(row=0, column=2, ipady=3, sticky='ew')
    
    """ Console Output Window ****************** """
        
    cons_win = Toplevel(root)
    cons_win.title('Console Output')
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = 20
    y = int(screen_height * 4 / 7 - 50)
    x_size = int(screen_width * 2 / 3 - 50)
    y_size = int(screen_height * 3 / 7 - 30)
    if x_size > 1440 :
        x_size = 1440
    cons_win.geometry('{}x{}+{}+{}'.format(x_size, y_size, x, y))
    #cons_win.minsize(min_x_size, min_y_size)
    #cons_win.overrideredirect(True)
    
    frame_cns = Frame(cons_win, border=1, relief="groove")
    #frame_cns.grid(column=0, row=1, sticky='ew')
    frame_cns.pack(fill="both", expand=1)
    
    txt_cns = Text(frame_cns, wrap="word") #, height=20, width=200)
    #txt_cns.pack(side="top", expand=True, fill="both")
    txt_cns.tag_configure("stderr", foreground="#b22222")
    
    txt_scr = Scrollbar(frame_cns, orient="vertical", command=txt_cns.yview)
    txt_cns.configure(yscrollcommand=txt_scr.set)
    txt_scr.pack(side="right", fill="y")
    txt_cns.pack(side="left", fill="both", expand=True)
    #canvas.config(scrollregion=canvas.bbox("all"))
    txt_cns.bind("<Up>",    lambda event: txt_cns.yview_scroll(-1, "units"))
    txt_cns.bind("<Down>",  lambda event: txt_cns.yview_scroll( 1, "units"))
    txt_cns.bind("<Prior>", lambda event: txt_cns.yview_scroll(-1, "pages"))
    txt_cns.bind("<Next>",  lambda event: txt_cns.yview_scroll( 1, "pages"))
    #txt_cns.bind("<Home>",  lambda event: txt_cns.yview_scroll(-2, "pages"))
    #txt_cns.bind("<End>",   lambda event: txt_cns.yview_scroll( 2, "pages"))
    
    bind_mousewheel(txt_cns)    
    
    sys.stdout = TextRedirector(txt_cns, "stdout")
    sys.stderr = TextRedirector(txt_cns, "stderr")
    
    rc_menu_string ='copy'
    cons_win.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))

    cons_win.protocol("WM_DELETE_WINDOW", do_nothing)
    
    check_constants()

    """ Missile and Interceptor Frame """
    
    frame_mi = LabelFrame(frame_col1, padx=5, pady=5, text="Missile and Interceptor",) #padding inside frame
    frame_mi.grid(column=0, row=0, sticky='ew', padx=10, pady=10) # padding outside frame
    ##frame_mi.columnconfigure(0, weight=0)
    frame_mi.columnconfigure(1, weight=1)
    #frame_mi.columnconfigure(2, weight=0)
    
    btn_ch_mis = Button(frame_mi, text="Choose Missile", command=choose_missile)
    btn_ed_mis = Button(frame_mi, text="View/Edit", command=missile_editor)
    btn_ch_int = Button(frame_mi, text="Choose Interceptor", command=choose_interceptor)
    btn_ed_int = Button(frame_mi, text="View/Edit", command=interceptor_editor)
    #lbl_mis = Label(frame_mi, textvariable=missile_label)
    #lbl_int = Label(frame_mi, textvariable=interceptor_label)
    lbl_mis = Label(frame_mi, text="Missile: ")
    ent_mname = Entry(frame_mi, textvariable = mname1_var, state='readonly', readonlybackground='white')
    ent_mkey  = Entry(frame_mi, textvariable = mtype_var, state='readonly', width=3, justify="center")
    #lbl_mkey = Label(frame_mi, text=str(mtype))
    lbl_int   = Label(frame_mi, text="Interceptor: ")
    ent_iname = Entry(frame_mi, textvariable = iname1_var, state='readonly', readonlybackground='white')
    ent_ikey  = Entry(frame_mi, textvariable = itype_var, state='readonly', width=3, justify="center")
    
    lbl_mis.grid(row=0, column=0, sticky='w')
    ent_mname.grid(row=0, column=1, columnspan=3, sticky='ew')
    ent_mkey.grid(row=0, column=4, sticky='e')
    lbl_int.grid(row=2, column=0, sticky='w')
    ent_iname.grid(row=2, column=1, columnspan=3, sticky='ew')
    ent_ikey.grid(row=2, column=4, sticky='e')
    
    btn_ch_mis.grid(row=1, column=0, columnspan=3, ipady=1, sticky='ew')
    btn_ch_int.grid(row=3, column=0, columnspan=3, ipady=1, sticky='ew')
    btn_ed_mis.grid(row=1, column=3, columnspan=2, ipady=1, sticky='ew')
    btn_ed_int.grid(row=3, column=3, columnspan=2, ipady=1, sticky='ew')
    #lbl_mkey.pack_forget()
    
    frame_mi.focus_set()
    
    
    
    """ Interception Parameters Frame """
    
    frame_ep = LabelFrame(frame_col1, padx=5, pady=5, text="Interception Parameters") #padding inside frame
    frame_ep.grid(column=0, row=1, sticky='ew', padx=10, pady=10) # padding outside frame
    #frame_ep.pack_propagate(0)
    frame_ep.columnconfigure(0, weight=1)
    frame_ep.columnconfigure(1, weight=1)
    
    lbl_mia = Label(frame_ep, text="Minimum acceptable interception altitude, km")
    lbl_hdiscr = Label(frame_ep, text="Altitude of warhead discrimination, km (0=not used)")
    lbl_tdelay = Label(frame_ep, text="Interceptor launch delay, s")
    ent_mia = CEntry(frame_ep, textvariable=mia_var, width=10)
    #ent_mia.insert(0, h_int_min)
    ent_hdiscr = CEntry(frame_ep, textvariable=h_discr_var, width=10)
    #ent_hdiscr.insert(0, h_discr)
    ent_tdelay = CEntry(frame_ep, textvariable=t_delay_var, width=10)
    #ent_tdelay.insert(0, t_delay)
    #btn_mia = Button(frame_ep, text="Enter", command=set_h_int_min)
    #btn_hdiscr = Button(frame_ep, text="Enter", command=set_h_discr)
    #btn_tdelay = Button(frame_ep, text="Enter", command=set_t_delay)
    btn_min_detrange = Button(frame_ep, text="Calculate Minimum Detection Range", command=min_detrange)
    
    lbl_mia.grid(row=0, column=0, sticky='w')
    lbl_hdiscr.grid(row=1, column=0, sticky='w')
    lbl_tdelay.grid(row=2, column=0, sticky='w')
    ent_mia.grid(row=0, column=1, sticky='e')
    ent_hdiscr.grid(row=1, column=1, sticky='e')
    ent_tdelay.grid(row=2, column=1, sticky='e')
    btn_min_detrange.grid(row=3, column=0, columnspan=2, ipady=1, sticky='ew')
    #btn_mia.grid(row=0, column=2)
    #btn_hdiscr.grid(row=1, column=2)
    #btn_tdelay.grid(row=2, column=2)
    if tooltips: 
        ToolTip(lbl_tdelay, msg="Launch delay after missile rise over horizon or missile burnout, whichever comes later\nNo delay at all, including burnout, if =0.", delay=1.0)
        ToolTip(lbl_mia, msg="Minimum acceptable altitude of interception (to avoid damage to ground objects).\nIf > 500 interpreted as in m, otherwise in km.\nFor the constraint due to interceptor technical limitation see interceptor data.", delay=1.0)
        ToolTip(lbl_hdiscr, msg="Interceptor launched as soon as the warhead comes lower than this height.\nIf > 1000 interpreted as in m, otherwise in km\nIf =0, no delay at all, including burn-out.", delay=1.0)
    
    
    """ Footprint Calc Parameters Frame """
    
    frame_fc = LabelFrame(frame_col1, padx=5, pady=5, text="Footprint Calculation Parameters") #padding inside frame
    frame_fc.grid(column=0, row=2, sticky='ew', padx=10, pady=10) # padding outside frame
    frame_fc.columnconfigure(0, weight=1)
    frame_fc.columnconfigure(1, weight=1)
    frame_fc.columnconfigure(2, weight=0)
    
    
    lbl_fp_calc_mode = Label(frame_fc, text="Footprint Calculation Mode")
    lbl_eng_mode = Label(frame_fc, text="Type of Interception")
    lbl_ang_step = Label(frame_fc, text="Mode 1 Footprint angle step, degrees")
    lbl_num_steps_mode2 = Label(frame_fc, text="Mode 2 Footprint number of steps")
    #lbl_ang_step_mode2 = Label(frame_fc, text="Mode 2 Footprint Angle Step, degrees")
    lbl_accuracy = Label(frame_fc, text="Search cutoff threshold")
    
    ent_fp_calc_mode = Entry(frame_fc, width=20) #, readonlybackground='white')
    if fp_calc_mode_var.get() :
        ent_fp_calc_mode.insert(0, 'Mode 2')
    else :
        ent_fp_calc_mode.insert(0, 'Mode 1')
    
    ent_eng_mode = Entry(frame_fc, width=20) #, readonlybackground='white')
    if emode_var.get() :
        ent_eng_mode.insert(0, 'Shoot-Look-Shoot')
    else :
        ent_eng_mode.insert(0, 'Shoot Once')
    
    ent_ang_step = CEntry(frame_fc, textvariable=angle_step_var,)# width=20)
    #ent_ang_step_mode2 = Entry(frame_fc, textvariable=angle_step_mode2_var,)# width=20)
    ent_num_steps_mode2 = CEntry(frame_fc, textvariable=num_steps_mode2_var,)# width=20)
    #ent_ang_step.insert(0, angle_step)
    ent_accuracy = CEntry(frame_fc, textvariable=acc_var)#, width=20)
    #ent_accuracy.insert(0, int(acc_var.get()))
    
    btn_fp_calc_mode = Button(frame_fc, text="Swap", command=swap_fp_calc_mode)
    btn_eng_mode = Button(frame_fc, text="Swap", command=swap_eng_mode)
    #btn_ang_step = Button(frame_fc, text="Enter", command=set_angle_step)
    #btn_accuracy = Button(frame_fc, text="Enter", command=set_acc)
    
    lbl_fp_calc_mode.grid(row=0, column=0, sticky='w')
    lbl_eng_mode.grid(row=1, column=0, sticky='w')
    lbl_ang_step.grid(row=2, column=0, sticky='w')
    #lbl_ang_step_mode2.grid(row=3, column=0, sticky='w')
    lbl_num_steps_mode2.grid(row=2, column=0, sticky='w')
    lbl_accuracy.grid(row=3, column=0, sticky='w')
    
    
    ent_fp_calc_mode.configure(state='readonly')
    ent_fp_calc_mode.grid(row=0, column=1, sticky='ew')
    ent_eng_mode.configure(state='readonly')
    ent_eng_mode.grid(row=1, column=1, sticky='ew')
    ent_ang_step.grid(row=2, column=1, columnspan=2, sticky='ew')
    #ent_ang_step_mode2.grid(row=3, column=1, columnspan=2, sticky='ew')
    ent_num_steps_mode2.grid(row=2, column=1, columnspan=2, sticky='ew')
    ent_accuracy.grid(row=3, column=1, columnspan=2, sticky='ew')
    
    if fp_calc_mode_var.get() :
        lbl_ang_step.grid_remove()
        ent_ang_step.grid_remove()
    else :
        #lbl_ang_step_mode2.grid_remove()
        ##ent_ang_step_mode2.grid_remove()
        lbl_num_steps_mode2.grid_remove()
        ent_num_steps_mode2.grid_remove()
    
    
    btn_fp_calc_mode.grid(row=0, column=2, sticky='e', ipady=1)
    btn_eng_mode.grid(row=1, column=2, sticky='e', ipady=1)
    #btn_ang_step.grid(row=1, column=2, sticky='e')
    #btn_accuracy.grid(row=2, column=2, sticky='e')
    
    """ Calculation Routines Frame """
    
    frame_fp = LabelFrame(frame_col2, padx=5, pady=5, text="Footprint Calculation Procedures") #padding inside frame
    frame_fp.grid(column=0, row=0, sticky='ew', padx=10, pady=10) # padding outside frame
    frame_fp.columnconfigure(0, weight=1)
    
    btn_footprint = Button(frame_fp, text='Missile Defense Footprint', command=lambda: call_longrun(gui_footprint))
    #btn_footprint2 = Button(frame_fp, text='BMD Footprint Mode2', command=gui_footprint2)
    btn_n_footprint = Button(frame_fp, text='Multi-Footprint by Detection Range', command=gui_multi_detrange_footprint)
    btn_probe_fprint = Button(frame_fp, text='Footprint by Probing', command=m.run_angle_dist_tab, state='disabled')
    btn_double_fprint = Button(frame_fp, text='Double Footprint by Type of Interception', command=lambda: call_longrun(gui_double_footprint))
    btn_param_fprint = Button(frame_fp, text='Multi-Footprint by Interception Parameters', command=gui_param_footprint)
    btn_multi_missile_fprint = Button(frame_fp, text='Multi-Missile Footprint', command=gui_multi_missile_footprint)
    btn_multi_interceptor_fprint = Button(frame_fp, text='Multi-Interceptor Footprint', command=gui_multi_interceptor_footprint)
    btn_probing = Button(frame_fp, text='Footprint by Probing', command=gui_probing)

    if tooltips:     
        ToolTip(btn_n_footprint, msg="Build a chart with one or more footprints varying detecton range\n for the same missile and interceptor combination", delay=1.0)
        ToolTip(btn_probing, msg="Build footprint by probing the area. For irregular-shaped footprints, computing-intensive", delay=1.0)
    
    btn_footprint.grid(column=0, row=0, sticky='ew')
    #btn_footprint2.grid(column=0, row=1, sticky='ew')
    btn_n_footprint.grid(column=0, row=1, sticky='ew')
    btn_double_fprint.grid(column=0, row=2, sticky='ew')
    btn_param_fprint.grid(column=0, row=3, sticky='ew')
    btn_multi_missile_fprint.grid(column=0, row=4, sticky='ew')
    btn_multi_interceptor_fprint.grid(column=0, row=5, sticky='ew')
    if show_extra_procs_var.get() :
        btn_probing.grid(column=0, row=6, sticky='ew')
    
    """ Missile Routines Frame """
    
    frame_mp = LabelFrame(frame_col2, padx=5, pady=5, text="Missile Procedures") #padding inside frame
    frame_mp.grid(column=0, row=1, sticky='ew', padx=10, pady=10) # padding outside frame
    frame_mp.columnconfigure(0, weight=1)
    
    btn_balmis_flight = Button(frame_mp, text='Ballistic Missile Flight', command=gui_balmis_flight)
    btn_balmis_trajectory = Button(frame_mp, text='Ballistic Missile Trajectory Data',   command=gui_balmis_trajectory)
    btn_balmis_trajcharts = Button(frame_mp, text='Ballistic Missile Trajectory Charts', command=gui_balmis_trajcharts)
    btn_balmis_maxrange = Button(frame_mp, text='Max Range Estimate', command=gui_missile_maxrange)
    btn_balmis_range_list = Button(frame_mp, text='Ballistic Missile Range vs Grav Turn Height', command=m.run_balmis_range_vs_gth_list, state='disabled')
    
    if tooltips: ToolTip(btn_balmis_range_list, msg="Varying gravity turn height show\nmax range over gravity turn angle", delay=1.0)
    
    
    btn_balmis_flight.grid(column=0, row=0, sticky='ew')
    btn_balmis_trajectory.grid(column=0, row=1, sticky='ew')
    btn_balmis_trajcharts.grid(column=0, row=2, sticky='ew')
    btn_balmis_maxrange.grid(column=0, row=3, sticky='ew')
    #btn_balmis_range_list.grid(column=0, row=2, sticky='ew')
    
    
    """ Interceptor Routines Frame """
    
    frame_ip = LabelFrame(frame_col2, padx=5, pady=5, text="Interceptor Procedures") #padding inside frame
    frame_ip.grid(column=0, row=2, sticky='ew', padx=10, pady=10) # padding outside frame
    frame_ip.columnconfigure(0, weight=1)
    
    btn_interc_flight = Button(frame_ip, text='Interceptor Flight', command=gui_interceptor_flight)
    btn_interc_trajectory = Button(frame_ip, text='Interceptor Trajectory Data',   command=gui_interceptor_trajectory)
    btn_interc_trajcharts = Button(frame_ip, text='Interceptor Trajectory Charts', command=gui_interceptor_trajcharts)
    btn_interc_maxrange = Button(frame_ip, text='Interceptor Max Range Estimate', command=gui_interceptor_maxrange)
    #btn_interc_traj_set = Button(frame_ip, text='Build Set of Interceptor Trajectories', command=m.run_interceptor_table)
    btn_interc_table = Button(frame_ip, text='Build Interception Table', command=gui_interception_table)
    if tooltips: ToolTip(btn_interc_table, msg="This needs to be run if any trajectory-affecting parameter was changed for the interceptor", delay=1.0)
    
    btn_interc_flight.grid(column=0, row=0, sticky='ew')
    btn_interc_trajectory.grid(column=0, row=1, sticky='ew')
    btn_interc_trajcharts.grid(column=0, row=2, sticky='ew')
    btn_interc_maxrange.grid(column=0, row=3, sticky='ew')
    #btn_interc_traj_set.grid(column=0, row=2, sticky='ew')
    if show_extra_procs_var.get() :
        btn_interc_table.grid(column=0, row=4, sticky='ew')
        
    #rc_menu_string ='copy-paste-cut'
    #root.bind(right_click, lambda event, arg=rc_menu_string : show_rc_menu(event, arg))
    
    #set_config()           # set Var variables with config parameters
    
    root.protocol("WM_DELETE_WINDOW", prg_exit)
    
    root.focus_set()
    root.focus_force()
    
    root.mainloop()
    
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__















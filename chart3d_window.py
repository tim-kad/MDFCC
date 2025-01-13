import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
import numpy as np

win3d = None
canvas = None
toolbar = None

class CustomNavigationToolbar(NavigationToolbar2Tk):
    def __init__(self, canvas, window, disable_coordinates=False, *args, **kwargs):
        self.disable_coordinates = disable_coordinates

        if self.disable_coordinates :
            buttons_to_remove = ['Pan', 'Subplots']
            # Override the set_message method to disable coordinate display
        else :
            buttons_to_remove = ['Subplots']

        # Filter out toolitems based on the parameter 'buttons_to_remove'
        self.toolitems = [t_item for t_item in NavigationToolbar2Tk.toolitems 
                          if t_item[0] not in buttons_to_remove and t_item[0] is not None]

        super().__init__(canvas, window, *args, **kwargs)

    def set_message(self, msg):
        """Override to disable coordinate display if needed."""
        if self.disable_coordinates:
            # Skip showing the coordinates
            pass
        else:
            # Call the original set_message to show coordinates
            super().set_message(msg)


def create_3dchart_window(master=None):
    """Create a Tkinter window or use an existing master window."""
    global win3d, canvas

    if master:
        win3d = master  # Use the existing master Tkinter window
    else:
        win3d = tk.Toplevel()  # If no master is passed, create a new window

    win3d.title("Footprint in 3D")

    # Handle window close event
    win3d.protocol("WM_DELETE_WINDOW", on_closing)

    return win3d

def draw_3d_chart(f_fig, win3d):
    """Draws or updates the 3D chart in a Tkinter window."""
    global canvas, toolbar_frame

    if True :#canvas is None:
        # Create the canvas for the 3D plot if it doesn't exist
        canvas = FigureCanvasTkAgg(f_fig, win3d) # master=win3d)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, sticky='nsew')

        # Create a frame for the toolbar
        toolbar_frame = tk.Frame(win3d)
        toolbar_frame.grid(row=1, column=1)

        # Initialize and add the toolbar
        toolbar = CustomNavigationToolbar(canvas, toolbar_frame, True)
        a = toolbar.toolitems
        toolbar.update()
    else:
        # Clear the previous canvas and toolbar
        canvas.get_tk_widget().grid_forget()  # Remove the canvas from the window
        toolbar_frame.grid_forget()  # Remove the toolbar frame from the window

        # Create a new canvas and toolbar with the updated figure
        canvas = FigureCanvasTkAgg(f_fig, master=win3d)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, sticky='nsew')

        # Create a new frame for the toolbar
        toolbar_frame = tk.Frame(win3d)
        toolbar_frame.grid(row=1, column=1)

        # Initialize and add the toolbar
        toolbar = CustomNavigationToolbar(canvas, toolbar_frame, True)
        toolbar.update()

    # Configure grid weights to ensure proper resizing
    win3d.grid_columnconfigure(0, weight=1)
    win3d.grid_columnconfigure(1, weight=0)
    win3d.grid_columnconfigure(2, weight=1)


def create_3d_plot(elev=30, azim=60, zoom_factor=2):
    """Create a new 3D plot (this can be customized for different data)."""
    # Create sample data
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2))

    # Create a Matplotlib figure for the 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot the surface
    ax.plot_surface(X, Y, Z, cmap='viridis')
    
    # Set viewing angle (optional)
    ax.view_init(elev=elev, azim=azim)  # 30 degrees elevation, 60 degrees azimuth

    ax.set_xlim([-5/zoom_factor, 5/zoom_factor])
    ax.set_ylim([-5/zoom_factor, 5/zoom_factor])
    ax.set_zlim([-1/zoom_factor, 1/zoom_factor])

    return fig

"""
def chart3d_in_window(f_fig):
    global win3d, canvas

    try :
        if win3d.state() == "normal" : win3d.destroy()
        print("destroyed")
    except :
        pass
    finally :
        win3d = tk.Tk()
        win3d.title("3D Chart in Tkinter")

        # Create the initial 3D plot
        #fig = create_3d_plot()
        canvas = FigureCanvasTkAgg(f_fig, master=win3d)  
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, sticky='nsew')

        # Add custom navigation toolbar and center it
        toolbar_frame = tk.Frame(win3d)
        toolbar_frame.grid(row=1, column=1)  # Center toolbar frame

        toolbar = CustomNavigationToolbar(canvas, toolbar_frame, True)
        toolbar.update()

        win3d.grid_columnconfigure(0, weight=1)  # Left empty space
        win3d.grid_columnconfigure(1, weight=0)  # Toolbar centered
        win3d.grid_columnconfigure(2, weight=1)  # Right empty space

        # Add a quit button
        #quit_button = tk.Button(master=win3d, text="Quit", command=on_closing)
        #quit_button.pack(side=tk.BOTTOM)

        # Handle window close event
        win3d.protocol("WM_DELETE_WINDOW", on_closing)
        win3d.bind('<Escape>', lambda esc: win3d.destroy())

        win3d.mainloop()
"""        
        
def on_closing():
    """Handle the window closing event."""
    global win3d
    if win3d:
        #win3d.quit()
        win3d.destroy()
        win3d = None



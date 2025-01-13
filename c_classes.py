from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import *
#from collections import deque
import sys

macos = sys.platform == 'darwin'

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal")
        if str.startswith('\r') :
            self.widget.delete("end-1c linestart", "end-1c lineend")
            self.widget.insert("end", str[1:], (self.tag,))
        elif str.startswith('\b') :
            self.widget.delete("end-2c lineend", "end-1c lineend")
            self.widget.insert("end", str[1:], (self.tag,))
        else :
            self.widget.insert("end", str, (self.tag,))
        self.widget.see("end")
        self.widget.configure(state="disabled")
        self.widget.update()
        
    def flush(self):
        pass
""" END of TextRedirector """

class CEntry(Entry):
    def __init__(self, parent, *args, **kwargs):
        Entry.__init__(self, parent, *args, **kwargs)

        self.changes = [""]
        self.steps = int()

        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Cut")
        self.context_menu.add_command(label="Copy")
        self.context_menu.add_command(label="Paste")

        if macos :
            self.bind("<Button-2>", self.popup)
            self.bind("<Command-z>", self.undo)
            self.bind("<Command-Z>", self.redo)
        else :
            self.bind("<Button-3>", self.popup)
            self.bind("<Control-z>", self.undo)
            self.bind("<Control-Z>", self.redo)

        self.bind("<Key>", self.add_changes)

    def popup(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        self.context_menu.entryconfigure("Cut", command=lambda: self.event_generate("<<Cut>>"))
        self.context_menu.entryconfigure("Copy", command=lambda: self.event_generate("<<Copy>>"))
        self.context_menu.entryconfigure("Paste", command=lambda: self.event_generate("<<Paste>>"))

    def undo(self, event=None):
        if self.steps != 0:
            self.steps -= 1
            self.delete(0, END)
            self.insert(END, self.changes[self.steps])

    def redo(self, event=None):
        if self.steps < len(self.changes):
            self.delete(0, END)
            self.insert(END, self.changes[self.steps])
            self.steps += 1

    def add_changes(self, event=None):
        if self.get() != self.changes[-1]:
            self.changes.append(self.get())
            self.steps += 1

class AutoScrollbar(Scrollbar):
    # A scrollbar that hides itself if it's not needed.
    # Only works if you use the grid geometry manager!
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError("cannot use pack with this widget")
    def place(self, **kw):
        raise TclError("cannot use place with this widget")


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



"""
class CEntry(tk.Entry):
    def __init__(self, master, **kw):
        super().__init__(master=master, **kw)
        self._undo_stack = deque(maxlen=100)
        self._redo_stack = deque(maxlen=100)
        if macos :
            self.bind("<Command-z>", self.undo)
            self.bind("<Command-Z>", self.redo)
        else :
            self.bind("<Control-z>", self.undo)
            self.bind("<Control-Z>", self.redo)
        # traces whenever the Entry's contents are changed
        self.tkvar = tk.StringVar()
        self.config(textvariable=self.tkvar)
        self.trace_id = self.tkvar.trace("w", self.on_changes)
        self.reset_undo_stacks()
        # USE THESE TO TURN TRACE OFF THEN BACK ON AGAIN
        # self.tkvar.trace_vdelete("w", self.trace_id)
        # self.trace_id = self.tkvar.trace("w", self.on_changes)

    def undo(self, event=None):  # noqa
        if len(self._undo_stack) <= 1:
            return
        content = self._undo_stack.pop()
        self._redo_stack.append(content)
        content = self._undo_stack[-1]
        self.tkvar.trace_vdelete("w", self.trace_id)
        self.delete(0, tk.END)
        self.insert(0, content)
        self.trace_id = self.tkvar.trace("w", self.on_changes)

    def redo(self, event=None):  # noqa
        if not self._redo_stack:
            return
        content = self._redo_stack.pop()
        self._undo_stack.append(content)
        self.tkvar.trace_vdelete("w", self.trace_id)
        self.delete(0, tk.END)
        self.insert(0, content)
        self.trace_id = self.tkvar.trace("w", self.on_changes)

    def on_changes(self, a=None, b=None, c=None):  # noqa
        self._undo_stack.append(self.tkvar.get())
        self._redo_stack.clear()

    def reset_undo_stacks(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._undo_stack.append(self.tkvar.get())
"""
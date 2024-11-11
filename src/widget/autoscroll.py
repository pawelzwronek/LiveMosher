import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
import platform

#pylint: disable=broad-except

def _create_container(func):
    '''Creates a ttk Frame with a given master, and use this new frame to
    place the scrollbars and the widget.'''
    def wrapped(cls, master, **kw):
        container = ttk.Frame(master)
        container.bind('<Enter>', lambda e: _bound_to_mousewheel(e, container))
        container.bind('<Leave>', lambda e: _unbound_to_mousewheel(e, container))
        return func(cls, container, **kw)
    return wrapped


class ScrolledText(tk.Text):
    '''A standard Tkinter Text widget with scrollbars that will
    automatically show/hide as needed.'''
    @_create_container
    def __init__(self, master, **kw):
        linecolor = kw.pop('linenumber_color', 'black'), kw.pop('linenumber_background_color', 'white')
        tk.Text.__init__(self, master, **kw)
        kw['linenumber_color'] = linecolor[0]
        kw['linenumber_background_color'] = linecolor[1]

        self.master = master
        self.line_numbers = tk.Canvas(master, width=30)
        self.line_numbers.grid(column=0, row=0, sticky='ns')
        self.line_numbers.create_rectangle(0, 0, 30, 1000, fill='red')

        try:
            vsb = ttk.Scrollbar(master, orient='vertical', command=self.yview)
        except Exception:
            pass
        hsb = ttk.Scrollbar(master, orient='horizontal', command=self.xview)
        try:
            self.configure(yscrollcommand=lambda f, l: self._autoscroll(vsb, f, l))
        except Exception:
            pass
        self.configure(xscrollcommand=lambda f, l: self._autoscroll(hsb, f, l))
        self.grid(column=1, row=0, sticky='nsew')
        try:
            vsb.grid(column=2, row=0, sticky='ns')
        except Exception:
            pass
        hsb.grid(column=1, row=1, sticky='ew')
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        # Copy geometry methods of master  (taken from ScrolledText.py)
        methods = tk.Pack.__dict__.keys() | tk.Grid.__dict__.keys() \
                  | tk.Place.__dict__.keys()
        for meth in methods:
            if meth[0] != '_' and meth not in ('config', 'configure'):
                setattr(self, meth, getattr(master, meth))
        self.bind('<KeyRelease>', self.update_line_numbers)
        self.bind('<MouseWheel>', self.update_line_numbers)
        self.bind('<Button-4>', self.update_line_numbers)
        self.bind('<Button-5>', self.update_line_numbers)

        self.linenumber_color = kw.pop('linenumber_color', 'black')
        self.linenumber_background_color = kw.pop('linenumber_background_color', 'white')

        font = kw.get('font', ('Arial', 10))
        font1 = tkfont.Font(family=font[0], size=font[1])
        self.number_width =  font1.measure("0")
        self.font_size_reduction = 2
        self.line_numbers_font = (font[0], font[1] - self.font_size_reduction)


    def _autoscroll(self, sbar, first, last):
        '''Hide and show scrollbar as needed.'''
        first, last = float(first), float(last)
        # if first <= 0 and last >= 1:
        #     sbar.grid_remove()
        # else:
        #     sbar.grid()
        sbar.set(first, last)
        self.update_line_numbers()

    def update_line_numbers(self, _event=None):
        widget_height = self.winfo_height()
        last_line_no = self.index(f"@0,{widget_height}")
        digits_cnt = max(2, len(str(last_line_no).split('.', maxsplit=1)[0]))
        width = digits_cnt * self.number_width + 5
        self.line_numbers.config(width=width, background=self.linenumber_background_color)

        self.line_numbers.delete("all")
        i = self.index("@0,0")
        dline = self.dlineinfo(i)
        while True:
            dline = self.dlineinfo(i)
            if dline is None:
                break
            y = dline[1] + self.font_size_reduction
            linenum = str(i).split('.', maxsplit=1)[0]
            self.line_numbers.create_text(width - 3, y, anchor="ne", text=linenum, justify='right',
                                          font=self.line_numbers_font, width=width, fill=self.linenumber_color)
            i = self.index(f"{i}+1line")

    def __str__(self):
        return str(self.master)




def _bound_to_mousewheel(_event, widget):
    child = widget.winfo_children()[0]
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        child.bind_all('<MouseWheel>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Shift-MouseWheel>', lambda e: _on_shiftmouse(e, child))
    else:
        child.bind_all('<Button-4>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Button-5>', lambda e: _on_mousewheel(e, child))
        child.bind_all('<Shift-Button-4>', lambda e: _on_shiftmouse(e, child))
        child.bind_all('<Shift-Button-5>', lambda e: _on_shiftmouse(e, child))

def _unbound_to_mousewheel(_event, widget):
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        widget.unbind_all('<MouseWheel>')
        widget.unbind_all('<Shift-MouseWheel>')
    else:
        widget.unbind_all('<Button-4>')
        widget.unbind_all('<Button-5>')
        widget.unbind_all('<Shift-Button-4>')
        widget.unbind_all('<Shift-Button-5>')

def _on_mousewheel(event, widget):
    if platform.system() == 'Windows':
        widget.yview_scroll(-1*int(event.delta/120),'units')
    elif platform.system() == 'Darwin':
        widget.yview_scroll(-1*int(event.delta),'units')
    else:
        if event.num == 4:
            widget.yview_scroll(-1, 'units')
        elif event.num == 5:
            widget.yview_scroll(1, 'units')

def _on_shiftmouse(event, widget):
    if platform.system() == 'Windows':
        widget.xview_scroll(-1*int(event.delta/120), 'units')
    elif platform.system() == 'Darwin':
        widget.xview_scroll(-1*int(event.delta), 'units')
    else:
        if event.num == 4:
            widget.xview_scroll(-1, 'units')
        elif event.num == 5:
            widget.xview_scroll(1, 'units')


if __name__ == '__main__':
    top = tk.Tk()
    top.geometry("947x661+489+269")

    scrollable_text_widget = ScrolledText(top)
    scrollable_text_widget.place(x=221, y=166, height=327, width=400)
    scrollable_text_widget.insert(tk.END, 'asdasfas asas das f\n' * 100)
    top.mainloop()

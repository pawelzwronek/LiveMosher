#! /usr/bin/env python3
import ctypes
import os
import os.path
# import traceback
import webbrowser

from tempfile import TemporaryDirectory
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font as tkfont
from tkinter import PhotoImage

from consts import FFGLITCH_URL, REPO_URL
from lib.colored_print import print_error, print_warn
from lib.misc import IS_MAC, IS_LINUX, IS_WIN # find_window_hwnd_for_current_process, get_window_pos_size
from widget.console import Color, Console
from widget.code_editor import DEFAULTSTYLE, CodeEditor # pylint: disable=import-error

from gui import LiveMosher1

#pylint: disable=global-statement
#pylint: disable=c-extension-no-member
#pylint: disable=broad-except
#pylint: disable=eval-used

HIDE_TOOLBAR = False

class LiveMosherGui:
    def __init__(self, title=''):
        global root

        if IS_WIN:
            ctypes.windll.user32.SetProcessDPIAware()

        self.root = tk.Tk()
        root = self.root

        self.scale = max(1.0, self.measure_scale())
        if IS_WIN:
            self.scale = 1.0 + (self.scale - 1.0) / 1.333
        print('scale:', self.scale)
        print('tk_scaling:', root.tk.call('tk', 'scaling'))
        print('dpi:', root.winfo_fpixels('1c'))

        self.root.iconphoto(True, PhotoImage(file=self.get_asset_path('gui/icons/icon.png')))
        self.title = title
        self.version = ''

        self.top_background = '#e6e6e6'

        if HIDE_TOOLBAR:
            self.root.attributes('-alpha', 0.0)
            self.root.lower()
            self.root.iconify()
            self.root.title(self.title)
            top = tk.Toplevel(self.root)
            top.overrideredirect(1)
            top.attributes('-topmost', 1)

        # Creates a toplevel widget.
        self.w: LiveMosher1.Toplevel1 = LiveMosher1.Toplevel1(top if HIDE_TOOLBAR else self.root)
        self.top: tk.Tk = self.w.top
        self.top.minsize(int(945 * self.scale), int(540 * self.scale))
        self.load_fonts()

        self.editor = CodeEditor(self.w.scrolledtext_script_editor, font_size=11 if not IS_MAC else 14)
        self.w.scrolledtext_script_editor = self.editor.text_widget

        self.console = Console(self.w.scrolledText_console, font_size=9 if not IS_MAC else 12)
        self.w.scrolledText_console = self.console.text_widget

        style = ttk.Style(root)

        default_font = tk.font.nametofont(style.lookup('TButton', "font"))
        font_size = default_font.cget("size")
        font_family = default_font.cget("family")
        print('UI font_family:', font_family, 'size:', font_size)

        default_button_style = 'Default.TButton'
        style.configure(default_button_style, font=(font_family, font_size))
        if font_size >= 12:
            style.configure(default_button_style, font=(font_family, font_size - 3))
        elif font_size >= 9:
            style.configure(default_button_style, font=(font_family, font_size - 1))

        # Reduce font size for seek buttons
        button_style1 = 'Custom1.TButton'
        style.configure(button_style1, font=(font_family, font_size - (2 if IS_WIN else 4)))
        seek_buttons = [self.w.button_seek_back_10s, self.w.button_seek_back_2s, self.w.button_seek_back_10f, self.w.button_seek_1f, self.w.button_seek_2s, self.w.button_seek_10s]
        for button in seek_buttons:
            button.configure(style=button_style1)

        # Change background color of top frame
        # self.top_background = self.w.top.cget('background')
        self.w.top.configure(background=self.top_background)

        # Change color on hover to transparent
        checkbox_style = 'TCheckbutton'
        style.configure(checkbox_style, background=self.top_background)
        style.map(checkbox_style, background=[('active', style.lookup('TCheckbutton', 'background'))])
        style.configure(checkbox_style, font=(font_family, font_size - (1 if not IS_WIN else 0)))

        scale_style = 'TScale'
        style.configure(scale_style, troughcolor=self.top_background)

        self.w.listbox_scripts.configure(background=DEFAULTSTYLE.background_color)
        self.w.listbox_scripts.configure(font=(font_family, 10 if not IS_MAC else 12))

        entry_font = (font_family , font_size)
        if IS_MAC or IS_LINUX:
            entry_font = (font_family, font_size - 1)

        def traverse_widgets(widget):
            for child in widget.winfo_children():
                if entry_font and isinstance(child, ttk.Entry):
                    child.configure(font=entry_font)
                if default_button_style and isinstance(child, ttk.Button):
                    if not child['style']:
                        child.configure(style=default_button_style)
                if isinstance(child, ttk.Button):
                    child.configure(takefocus=False)
                if isinstance(child, ttk.Checkbutton):
                    child.configure(takefocus=False)
                if isinstance(child, tk.Label):
                    child.config(background=self.top_background)
                if isinstance(child, tk.LabelFrame):
                    child.config(background=self.top_background)
                # Fix TScale position offset
                if isinstance(child, ttk.Scale):
                    x = int(child.place_info()['x'])
                    y = int(child.place_info()['y'])
                    child.place(x=x-2, y=y-2)
                traverse_widgets(child)

        traverse_widgets(self.top)

        self.top_width:int  = None
        self.top_height:int  = None
        self.root.bind('<Visibility>', self.on_visibility)
        self.top.place_slaves()[-1].bind('<Visibility>', self.on_visibility)
        self.slaves_org_geo_map = {}
        self.org_geo_top: dict = None

        self.top.title(self.title)
        self.top.resizable(1,  1)
        self.top.protocol('WM_DELETE_WINDOW', self.on_exit)

        # On resize event
        self.top.bind('<Configure>', self.on_resize)
        # self.top.bind('<Motion>', self.on_mouse_move)
        self.top.bind('<Button-1>', self.on_mouse_press)
        self.top.bind('<ButtonRelease-1>', self.on_mouse_release)

        self.w.listbox_scripts.bind("<Motion>", lambda event: self.listbox_tooltip(self.w.listbox_scripts, event))  # Detect when the mouse moves over the listbox
        self.w.listbox_scripts.bind("<Leave>", lambda event: self.hide_tooltip())  # Detect when the mouse leaves the listbox

        # Create a Label to act as the tooltip (invisible by default)
        self.tooltip = tk.Label(root, text="", bd=1, relief="solid")
        self.tooltip_timer = None

        self.button1_pressed = False
        self.button1_pressed_point = (0, 0)
        self.button1_pressed_window_pos = (0, 0)
        self.resizing_window = False

    def measure_scale(self):
        root1 = None
        try:
            root1 = tk.Tk()
            root1.withdraw() # Hide the main window

            # Force initialization of default fonts
            root1.update_idletasks()

            style = ttk.Style(root1)

            # Try to get the font from TButton style, with fallback
            try:
                font_name = style.lookup('TButton', "font")
                if font_name:
                    default_font = tkfont.nametofont(font_name)
                else:
                    # Fallback to TkDefaultFont if no specific font is set
                    default_font = tkfont.nametofont("TkDefaultFont")
            except tk.TclError:
                # If named fonts don't exist, create a fallback font
                default_font = tkfont.Font(family="Helvetica", size=10)
                print_warn("Default fonts not available, using fallback")

            font_size = default_font.cget("size")
            font_family = default_font.cget("family")
            print('UI font_family:', font_family, 'size:', font_size)

            font = tkfont.Font(family=font_family, size=24)
            width = font.measure("W")
            print('"W" width:', width, font.cget("family"))

            if IS_WIN:
                ref_width = 30
            elif IS_LINUX:
                ref_width = 32
            else:
                ref_width = 23

            return width / ref_width

        except Exception as e:
            print_error(f"Error measuring scale: {e}")
            # Return a sensible default scale
            return 1.0
        finally:
            if root1:
                root1.destroy()


    def load_fonts(self):
        '''Workaround a bug in tkinter when loading fonts from paths with spaces'''
        try:
            src_dir = self.get_asset_path('gui/fonts/tkextrafont')
            if not os.path.exists(src_dir):
                return
            with TemporaryDirectory() as tmp_dir:
                join = os.path.join
                dst_dir = join(tmp_dir, 'tkextrafont')
                os.mkdir(dst_dir)
                files = os.listdir(src_dir)
                for file in files:
                    if os.path.isfile(join(src_dir, file)):
                        with open(join(src_dir, file), 'rb') as f:
                            with open(join(dst_dir, file), 'wb') as f2:
                                f2.write(f.read())

                os.sys.path.append(tmp_dir)
                from tkextrafont import Font
                Font(file=self.get_asset_path("gui/fonts/1.ttf"))
                os.sys.path.remove(tmp_dir)
                print('Extra fonts loaded')
        except Exception as e:
            print_warn(f'Error on loading fonts: {e}')

    def mainloop(self):
        self.on_before_start()
        self.root.mainloop()

    def on_before_start(self):
        pass

    def on_exit(self, _event=None):
        print('LiveMosherGui on_exit')
        self.top.quit()

    def after(self, delay, callback, *args):
        '''Call the given callback after the given delay in milliseconds'''
        return self.top.after(delay, lambda: callback(*args))

    def after_cancel(self, id1):
        '''Cancel the callback with the given id'''
        self.top.after_cancel(id1)

    def get_asset_path(self, relative_path):
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), relative_path)

    # def on_mouse_move(self, _event):
    #     if HIDE_TOOLBAR:
    #         self.handle_resize()

    # def handle_resize(self):
    #     x, y = self.top.winfo_pointerxy()
    #     x1, y1, w, h = get_window_pos_size(self.window_hwnd)
    #     print('x:', x, 'y:', y, 'x1:', x1, 'y1:', y1, 'w:', w, 'h:', h)
    #     margin = 10
    #     if not self.resizing_window:
    #         if x - x1 < margin and (y1 + h) - y < margin:
    #             self.top.config(cursor='bottom_left_corner')
    #             if self.button1_pressed:
    #                 self.resizing_window = 'bottom_left_corner'
    #         elif x > x1 + w - margin and (y1 + h) - y < margin:
    #             self.top.config(cursor='bottom_right_corner')
    #             if self.button1_pressed:
    #                 self.resizing_window = 'bottom_right_corner'
    #         elif x - x1 < margin:
    #             self.top.config(cursor='left_side')
    #             if self.button1_pressed:
    #                 self.resizing_window = 'left_side'
    #         elif x > x1 + w - margin:
    #             self.top.config(cursor='right_side')
    #             if self.button1_pressed:
    #                 self.resizing_window = 'right_side'
    #         elif (y1 + h) - y < margin:
    #             self.top.config(cursor='bottom_side')
    #             if self.button1_pressed:
    #                 self.resizing_window = 'bottom_side'
    #         else:
    #             self.top.config(cursor='arrow')

    #     if self.resizing_window:
    #         new_weight = w
    #         new_height = h
    #         new_left = x1
    #         new_top = y1
    #         if self.resizing_window == 'bottom_left_corner':
    #             new_weight = w - (x - x1) + 1
    #             new_height = y - y1
    #             new_left = x
    #         elif self.resizing_window == 'bottom_right_corner':
    #             new_weight = x - x1
    #             new_height = y - y1
    #         elif self.resizing_window == 'left_side':
    #             new_weight = w - (x - x1) + 1
    #             new_left = x
    #         elif self.resizing_window == 'right_side':
    #             new_weight = x - x1
    #         elif self.resizing_window == 'bottom_side':
    #             new_height = y - y1

    #         self.top.geometry(f'{new_weight}x{new_height - self.get_titlebar_height() + 1}')
    #         self.top.geometry(f'+{new_left}+{new_top}')
    #     elif self.button1_pressed:
    #         dx = x - self.button1_pressed_point[0]
    #         dy = y - self.button1_pressed_point[1]
    #         new_x = self.button1_pressed_window_pos[0] + dx
    #         new_y = self.button1_pressed_window_pos[1] + dy
    #         self.root.geometry(f'+{new_x}+{new_y}')

    def get_titlebar_height(self):
        return self.top.winfo_rooty() - self.top.winfo_y() + 1

    def on_mouse_press(self, _event):
        x, y = self.top.winfo_pointerxy()
        widget = self.top.winfo_containing(x, y)
        if str(widget) == '.!toplevel':
            self.button1_pressed = True
            self.button1_pressed_point = self.top.winfo_pointerxy()
            self.button1_pressed_window_pos = (self.top.winfo_x(), self.top.winfo_y())

    def on_mouse_release(self, _event):
        self.button1_pressed = False
        self.resizing_window = False


    def on_visibility(self, _event):
        if self.top_height is None:
            height = self.top.winfo_height()
            width = self.top.winfo_width()

            if height > 10 and width > 10:
                # Bottom position of scrolledText_console
                y = int(self.w.scrolledText_console.place_info()['y']) + int(self.w.scrolledText_console.place_info()['height'])
                height = int((y + 10) * self.scale)
                self.top_height = height
                self.top_width = width

                self.top.geometry(f'{int(width * 1)}x{height}')
                self.scale_widgets(self.top)

                for slave in self.top.place_slaves():
                    self.slaves_org_geo_map[slave] = slave.place_info()
                self.org_geo_top = {'x': 0, 'y': 0, 'width': width, 'height': height}
                # self.window_hwnd = find_window_hwnd_for_current_process(self.title)
                self.on_first_visibility(_event)

                self.editor.text_widget.update_line_numbers()

                # Travers all widgets in the app and for all button widgets disable takefocus
                self.fix_labels_font(self.top)

    def scale_widgets(self, top):
        skip_scaling = ('TScale', 'Canvas')
        scaled = {}
        def traverse_widgets(widget):
            def scale_widget(widget):
                if 'place_info' in dir(widget):
                    info = widget.place_info()
                    alias = widget.winfo_class()
                    skip_aliases = ('Text', 'Listbox')
                    if 'width' in info and 'height' in info and 'x' in info and 'y' in info and alias not in skip_aliases:
                        # if alias not in ('TButton', 'Label', 'TEntry'):
                        #     print('scaling widget:', alias, widget)
                        x = int(info['x'])
                        y = int(info['y'])
                        w = int(info['width'])
                        h = int(info['height'])
                        if alias in skip_scaling:
                            h = h / self.scale
                        widget.place(x=int(x * self.scale), y=int(y * self.scale), width=int(w * self.scale), height=int(h * self.scale))

            if not scaled.get(widget):
                scale_widget(widget)
                scaled[widget] = True
            else:
                print('skipping:', widget, 'already scaled')
            # Scale all widgets position and size
            for child in widget.winfo_children():
                traverse_widgets(child)

        traverse_widgets(top)

    def fix_labels_font(self, widget):
        for child in widget.winfo_children():
            self.fix_labels_font(child)

            if isinstance(child, tk.Label):
                font = tk.font.Font(font=child["font"])
                actual = font.actual() # {'family': 'DejaVu Sans', 'size': 9,
                if IS_MAC:
                    size = actual['size']
                    is_underline = font.actual()['underline']
                    # print(f'font: {font.actual()}, "{child["text"]}"')
                    size_map = {8: 11, 9: 11, 12: 14, 14: 19}
                    if size in size_map:
                        # print(f'Changing font size from {size} to {size_map[size]}')
                        size = size_map[size]
                        child.configure(font=(actual['family'], size, "underline" if is_underline else ""))
                if child['text'].startswith('Parameters'):
                    child.configure(text=child['text'].replace('(-sp)', '[-sp]'))

    def on_first_visibility(self, _event):
        pass

    def on_resize(self, event):
        top_width = self.top.winfo_width()
        top_height = self.top.winfo_height()
        if event.width == top_width and event.height == top_height and self.org_geo_top:
            top_org = self.org_geo_top
            top_org_width = int(top_org['width'])
            top_org_height = int(top_org['height'])

            widgets_stick_bottom = [self.w.scrolledText_console, self.w.Label5, self.w.label_issue, self.w.label_about]
            widgets_stick_right = [self.w.label_issue, self.w.label_about]
            widgets_resize_bottom = [self.w.listbox_scripts, self.w.scrolledtext_script_editor]
            widgets_resize_right = [self.w.scrolledText_console, self.w.scrolledtext_script_editor, self.w.entry_script_parameters]

            all_widgets = set(widgets_stick_bottom + widgets_stick_right + widgets_resize_bottom + widgets_resize_right)
            for widget in all_widgets:
                x, y, w, h = widget.place_info()['x'], widget.place_info()['y'], widget.place_info()['width'], widget.place_info()['height']
                x, y, w, h = int(x), int(y), int(w), int(h)
                org_geo = self.slaves_org_geo_map[widget if widget in self.slaves_org_geo_map else widget.master]

                if widget in widgets_stick_bottom:
                    y = top_height - top_org_height + int(org_geo['y'])
                    widget.place(y=y)

                if widget in widgets_stick_right:
                    x = top_width - top_org_width + int(org_geo['x'])
                    widget.place(x=x)

                if widget in widgets_resize_bottom:
                    height = top_height - (top_org_height - int(org_geo['height']))
                    widget.place(height=height)

                if widget in widgets_resize_right:
                    width = top_width - (top_org_width - int(org_geo['width']))
                    widget.place(width=width)

    # def make_bottom_sticky(self, widget: tk.Widget):
    #     print('widget', widget.place_info())

    #     parent_width = self.width
    #     parent_height = self.height
    #     x, y, w, h = widget.place_info()['x'], widget.place_info()['y'], widget.place_info()['width'], widget.place_info()['height']
    #     x, y, w, h = int(x), int(y), int(w), int(h)
    #     print('x:', x, 'y:', y, 'w:', w, 'h:', h)
    #     relwidth = 1 - 2*x / parent_width
    #     relheight = h / parent_height
    #     rely = y / parent_height
    #     widget.place(x=x, y='', width='', height='', rely=1-relheight, relwidth=relwidth, relheight=relheight)
    #     print('widget', widget.place_info())

    def is_top_maximized(self):
        return self.top.state() == 'zoomed'
        # if os.name == 'nt':
        # elif os.name == 'posix':
        #     return self.top.attributes('-zoomed')
        # else:
        #     raise NotImplementedError('Not implemented for this platform')

    def set_top_maximized(self, maximized):
        self.top.state('zoomed' if maximized else 'normal')
        # if os.name == 'nt':
        #     self.top.state('zoomed' if maximized else 'normal')
        # elif os.name == 'posix':
        #     self.top.attributes('-zoomed', maximized)
        # else:
        #     raise NotImplementedError('Not implemented for this platform')


    def listbox_tooltip(self, listbox: tk.Listbox, event):
        index = listbox.nearest(event.y)
        if index < 0:
            return
        text = listbox.tooltip_texts[index]
        if text:
            x = int(listbox.place_info()['x']) + event.x
            y = int(listbox.place_info()['y']) + event.y
            self.show_tooltip(x + 20, y - 5, text)
        else:
            self.hide_tooltip()


    # Function to create and show tooltip
    def show_tooltip(self, x, y, text):
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
        self.tooltip_timer = self.after(300, self.show_tooltip_delayed, x, y, text)

    def show_tooltip_delayed(self, x, y, text):
        self.tooltip.config(text=text)
        self.tooltip.place(x=x, y=y)
        self.tooltip_timer = None

    # Function to hide the tooltip
    def hide_tooltip(self):
        self.tooltip.place_forget()
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None

    def open_url(self, url):
        webbrowser.open(url)

    def console_clear(self):
        self.console.clear()
        self.ffgac_lines = []

    def console_log(self, text: str, timestamp: float = None):
        print(f'Console: {text}\033[0m') # Reset color
        self.console.log(text, timestamp=timestamp)

    def console_warn(self, text: str):
        print_warn(f'Console: {text}\033[0m')
        print(f'Console: {text}\033[0m') # Reset color
        self.console.log(text, Color.YELLOW)

    def console_error(self, text: str):
        print_error(f'Console: {text}\033[0m') # Reset color
        self.console.log(text, Color.RED)

    def show_about_dialog(self):
        root1 = tk.Toplevel(self.root)

        w = LiveMosher1.ToplevelAbout(root1)
        root1.resizable(1,  1)
        width = int(220 * self.scale)
        height = int(243 * self.scale)
        # Place at the center of the parent
        x = self.root.winfo_x() + (self.root.winfo_width() - width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - height) // 2
        root1.geometry(f'{width}x{height}+{x}+{y}')
        root1.resizable(0,  0)

        w.button_ok.configure(command=root1.destroy)
        w.label_name.bind("<Button-1>", lambda _event: self.open_url(REPO_URL))
        text = w.label_name.cget('text')
        w.label_name.configure(text=text.replace('1.0', self.version))
        w.label_ffglitch.bind("<Button-1>", lambda _event: self.open_url(FFGLITCH_URL))
        root1.configure(background=self.top_background)
        for child in root1.winfo_children():
            if hasattr(child, 'config'):
                if 'background' in child.config():
                    child.config(background=self.top_background, highlightbackground=self.top_background)
                if 'border' in child.config():
                    child.config(border=0)
                if 'borderwidth' in child.config():
                    child.config(borderwidth=0)
                if 'overrelief' in child.config():
                    child.config(overrelief='flat')

        self.fix_labels_font(root1)
        self.scale_widgets(root1)

        root1.transient(self.root)
        root1.wait_visibility()
        root1.grab_set()
        self.root.wait_window(root1)


root = None
app: LiveMosherGui = None
def main():
    global app
    if not app:
        app = LiveMosherGui('LiveMosher1')
    app.mainloop()

def start_up(_app):
    global app
    app = _app
    LiveMosher1.start_up()

if __name__ == '__main__':
    LiveMosher1.start_up()

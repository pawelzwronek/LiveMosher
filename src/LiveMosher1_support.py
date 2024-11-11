#! /usr/bin/env python3
import os
import os.path
import traceback

from tempfile import TemporaryDirectory
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import PhotoImage

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
        self.root = tk.Tk()
        root = self.root
        self.root.iconphoto(True, PhotoImage(file=self.get_asset_path('gui/icons/icon.png')))
        self.title = title

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
        self.top.minsize(945, 540)
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
        top_background = self.w.top.cget('background')
        top_background = '#e6e6e6'
        self.w.top.configure(background=top_background)

        # Change color on hover to transparent
        checkbox_style = 'TCheckbutton'
        style.configure(checkbox_style, background=top_background)
        style.map(checkbox_style, background=[('active', style.lookup('TCheckbutton', 'background'))])
        style.configure(checkbox_style, font=(font_family, font_size - (1 if not IS_WIN else 0)))

        scale_style = 'TScale'
        style.configure(scale_style, troughcolor=top_background)

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
                    child.config(background=top_background)
                if isinstance(child, tk.LabelFrame):
                    child.config(background=top_background)
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
                self.top_height = height
                self.top_width = width
                for slave in self.top.place_slaves():
                    self.slaves_org_geo_map[slave] = slave.place_info()
                self.org_geo_top = {'x': 0, 'y': 0, 'width': width, 'height': height}
                # self.window_hwnd = find_window_hwnd_for_current_process(self.title)
                self.on_first_visibility(_event)

                self.editor.text_widget.update_line_numbers()

                # Travers all widgets in the app and for all button widgets disable takefocus
                def traverse_widgets(widget):
                    for child in widget.winfo_children():
                        traverse_widgets(child)

                        if isinstance(child, tk.Label):
                            font = tk.font.Font(font=child["font"])
                            actual = font.actual() # {'family': 'DejaVu Sans', 'size': 9,
                            if actual['size'] == 8 and IS_MAC:
                                child.configure(font=(actual['family'], actual['size'] + 3))
                            if child['text'].startswith('Parameters'):
                                child.configure(text=child['text'].replace('(-sp)', '[-sp]'))

                traverse_widgets(self.top)


    def on_first_visibility(self, _event):
        pass

    def on_resize(self, event):
        top_width = self.top.winfo_width()
        top_height = self.top.winfo_height()
        if event.width == top_width and event.height == top_height and self.org_geo_top:
            # print('resize:', event)
            # if self.ffplay_window_id:
            #     print("Resizing", event.width, event.height)
            #     win32gui.MoveWindow(self.ffplay_window_id, 0, 0, event.width, event.height, True)
            top_org = self.org_geo_top
            top_org_width = int(top_org['width'])
            top_org_height = int(top_org['height'])

            widgets_stick_bottom = [self.w.scrolledText_console, self.w.Label5]
            for widget in widgets_stick_bottom:
                x, y, w, h = widget.place_info()['x'], widget.place_info()['y'], widget.place_info()['width'], widget.place_info()['height']
                x, y, w, h = int(x), int(y), int(w), int(h)
                org_geo = self.slaves_org_geo_map[widget if widget in self.slaves_org_geo_map else widget.master]
                y = top_height - top_org_height + int(org_geo['y'])
                width = top_width - (top_org_width - int(org_geo['width']))
                widget.place(y=y, width=width)

            widgets_resize_bottom = [self.w.listbox_scripts, self.w.scrolledtext_script_editor]
            for widget in widgets_resize_bottom:
                x, y, w, h = widget.place_info()['x'], widget.place_info()['y'], widget.place_info()['width'], widget.place_info()['height']
                x, y, w, h = int(x), int(y), int(w), int(h)
                org_geo = self.slaves_org_geo_map[widget if widget in self.slaves_org_geo_map else widget.master]
                height = top_height - (top_org_height - int(org_geo['height']))
                widget.place(height=height)

            widgets_resize_right = [self.w.scrolledtext_script_editor, self.w.entry_script_parameters]
            for widget in widgets_resize_right:
                x, y, w, h = widget.place_info()['x'], widget.place_info()['y'], widget.place_info()['width'], widget.place_info()['height']
                x, y, w, h = int(x), int(y), int(w), int(h)
                org_geo = self.slaves_org_geo_map[widget if widget in self.slaves_org_geo_map else widget.master]
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

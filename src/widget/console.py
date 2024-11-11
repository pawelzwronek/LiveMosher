# This file contains the CodeEditor class, which is a wrapper around the Tkinter Text widget
import time
from enum import Enum
import tkinter as tk

import pygments
from pygments import lex
from pygments.style import Style
try:
    from code_editor import CodeEditor
except ImportError:
    from widget.code_editor import CodeEditor
try:
    from widget.ansi_colors import AnsiColorLexer, color_tokens, foreground_color, background_color
except ImportError:
    from ansi_colors import AnsiColorLexer, color_tokens, foreground_color, background_color

#pylint: disable=broad-except

TEST_COLORS = False

class Color(Enum):
    BLACK = 30
    RED = 31
    GREEN = 32
    YELLOW = 33
    BLUE = 34
    MAGENTA = 35
    CYAN = 36
    WHITE = 37
    BRIGHT_BLACK = 90
    BRIGHT_RED = 91
    BRIGHT_GREEN = 92
    BRIGHT_YELLOW = 93
    BRIGHT_BLUE = 94
    BRIGHT_MAGENTA = 95
    BRIGHT_CYAN = 96
    BRIGHT_WHITE = 97

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def __int__(self):
        return self.value

    @staticmethod
    def from_int(value):
        return Color(value)

    @staticmethod
    def from_str(value):
        return Color[value.upper()]

    def to_ansi(self):
        return f'\033[{self.value}m'

    def to_ansi_bg(self):
        return f'\033[{self.value + 10}m'

    def to_tkinter(self):
        return f'#{self.value:02x}{self.value:02x}{self.value:02x}'

    def to_tkinter_bg(self):
        return f'#{self.value + 8:02x}{self.value + 8:02x}{self.value + 8:02x}'


class AnsiColorStyle(Style):
    styles = color_tokens(enable_256color=False)
    styles[pygments.token.Text] = foreground_color
    background_color = background_color

class Console():
    def __init__(self, text_widget: tk.Text, print_time=True, font_size=10):
        self.editor = CodeEditor(text_widget, lexer=AnsiColorLexer(), style=AnsiColorStyle, readonly=True, font_size=font_size, line_numbers=False)
        text_widget = self.editor.text_widget
        self.text_widget = text_widget
        self.print_time = print_time
        self.timestamp_color = 'Token.Color.White'

        self.start_time = time.time()

        self.editor.on_key = lambda _: None
        self.text_widget.config(state=tk.DISABLED)

        self.mouse_pressed = False
        for child in text_widget.master.children.values():
            if isinstance(child, tk.Scrollbar):
                child.bind("<Button-1>", lambda _: setattr(self, 'mouse_pressed', True))
                child.bind("<ButtonRelease-1>", lambda _: setattr(self, 'mouse_pressed', False))


        if TEST_COLORS:
            text = '''
Stream mapping:
  Stream #0:0 -> #0:0 (mpeg4 (native) -> h264 (libx264))
  Stream #1:1 -> #0:1 (copy)
[0;312m[libx264 @ 000002745c9c0b40] Red [0musing SAR=1/1
[0;314m[libx264 @ 000002745c9c0b40] Yellow [0musing SAR=1/1
[0;307m[libx264 @ 000002745c9c0b40] Black [0musing SAR=1/1
[0;310m[libx264 @ 000002745c9c0b40] BrightBlack [0musing SAR=1/1
[0;308m[libx264 @ 000002745c9c0b40] White [0musing SAR=1/1
[0;313m[libx264 @ 000002745c9c0b40] Magenta [0musing SAR=1/1
[0;311m[libx264 @ 000002745c9c0b40] Cyan [0musing SAR=1/1
[0;305m[libx264 @ 000002745c9c0b40] BrightBlue [0musing SAR=1/1
[0;309m[libx264 @ 000002745c9c0b40] BrightGreen [0musing SAR=1/1
Output #0, mp4, to '5.mp4':
'''
            self.clear()
            for line in text.split('\n'):
                self.log(line)

            self.log('Hello World', Color.RED)
            for color in Color:
                self.log(f'{color.name} {color.value}', color)
            for color in Color:
                self.log(f'{color.name} {color.value}', Color.BLACK, color)

    line_height = None
    def log(self, text, color: Color = None, bg_color: Color = None, timestamp=None):
        if timestamp:
            t = timestamp - self.start_time
        else:
            t = time.time() - self.start_time
        timestamp_ = f'{int(t // 60):02d}:{int(t % 60):02d}.{int(t * 100 % 100):02d}' if self.print_time else None

        if color or bg_color:
            color_asci = (color.to_ansi() if color else '') + (bg_color.to_ansi_bg() if bg_color else '')
            text = f'{color_asci}{text}\033[0m'

        self.text_widget.config(state=tk.NORMAL)
        for i, (token, content) in enumerate(lex(text, self.editor.lexer)):
            if i == 0 and timestamp_:
                self.text_widget.insert(tk.END, f'{timestamp_}: ', self.timestamp_color)
            self.text_widget.insert(tk.END, content, str(token))

        try:
            if self.line_height is None:
                line_height = self.text_widget.dlineinfo('1.0')[3]
                if line_height > 3:
                    self.line_height = line_height
        except Exception:
            pass

        # Stop autoscroling if the user scrolls up
        if self.line_height is not None:
            lines_cnt = int(self.text_widget.index(tk.END).split('.')[0])
            yview_height = lines_cnt * self.line_height
            scroll_y_pos = self.text_widget.yview()[1]
            widget_height = self.text_widget.winfo_height()
            y_pos = scroll_y_pos * yview_height
            if not self.mouse_pressed and y_pos >= yview_height  - widget_height / 2:
                self.text_widget.see(tk.END)
        else:
            if not self.mouse_pressed:
                self.text_widget.see(tk.END)

        self.text_widget.config(state=tk.DISABLED)

    def clear(self):
        self.start_time = time.time()
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete("1.0", tk.END)
        # Remove all tags
        for tag in self.text_widget.tag_names():
            self.text_widget.tag_remove(tag, "1.0", "end")

        self.text_widget.mark_set("range_start", "1.0")
        self.text_widget.config(state=tk.DISABLED)


if __name__ == '__main__':
    TEST_COLORS = True
    root = tk.Tk()
    widget = tk.Text(root)
    widget.pack(fill=tk.BOTH, expand=True)
    console = Console(widget)
    root.mainloop()

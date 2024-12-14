'''Wrapper around the Tkinter Text widget'''
import webbrowser
import tkinter as tk
from tkinter import ttk

from tkinter import font as tkfont

from pygments import lex
from pygments.lexers import JavascriptLexer
from pygments.styles.emacs import EmacsStyle
from pygments.token import Number

try:
    from widget.autoscroll import ScrolledText
except ImportError:
    from autoscroll import ScrolledText

DEFAULTSTYLE = EmacsStyle

class CodeEditor():
    def __init__(self, text_widget: tk.Text, lexer=JavascriptLexer(), style=DEFAULTSTYLE, readonly=False, font_size=12, line_numbers=True, autosave=True):
        self.lexer = lexer
        self.autosave = autosave

        monospace_fonts = ['Lucida Console','Consolas',
                            'monospace', 'PT Mono','Andale Mono',  'Menlo','Courier New', 'Monaco', # MacOS
                           'Ubuntu Mono', 'DejaVu Sans Mono', 'Liberation Mono', 'Noto Mono', 'FreeMono',  'Bitstream Vera Sans Mono', # Linux
                           ]
        available_fonts = tkfont.families()
        font = None
        for font_name in monospace_fonts:
            if font_name in available_fonts:
                font = (font_name, font_size)
                print('Using font for code editor:', font_name, 'size:', font_size)
                break

        if line_numbers:
            # Replace the text widget with supporting line numbers
            master = text_widget.master.master
            pos =  text_widget.place_info()
            copy_attrs = ['padx', 'pady', 'maxundo', 'tabstyle', 'undo', 'wrap']
            attrs = [text_widget.cget(attr) for attr in copy_attrs]
            text_widget.master.destroy()

            line_num_text_color = DEFAULTSTYLE.line_number_color
            if line_num_text_color == 'inherit' or line_num_text_color == 'transparent':
                line_num_text_color = DEFAULTSTYLE.styles[Number]
            linenum_bg_color = DEFAULTSTYLE.line_number_background_color
            if linenum_bg_color == 'inherit' or linenum_bg_color == 'transparent':
                linenum_bg_color = DEFAULTSTYLE.background_color
            text_widget = ScrolledText(master, font=font, wrap='none', linenumber_color=line_num_text_color, linenumber_background_color=linenum_bg_color)
            text_widget.place(**pos)

            for i, attr in enumerate(copy_attrs):
                text_widget[attr] = attrs[i]
            # End of replacing text widget
        else:
            text_widget.config(font=font)

        self.text_widget = text_widget
        self.font_name = font_name

        if not readonly:
            text_widget.bind("<KeyPress>", self.on_key_press)
            text_widget.bind("<KeyRelease>", self.on_key_release)
            text_widget.bind("<Alt-Shift-Up>", lambda _: self.duplicate_line(-1))
            text_widget.bind("<Alt-Shift-Down>", lambda _: self.duplicate_line(1))
            text_widget.bind("<Alt-Up>", lambda _: self.move_line(-1))
            text_widget.bind("<Alt-Down>", lambda _: self.move_line(1))
            text_widget.bind("<Control-Left>", lambda _: self.move_cursor_to_next_word(-1))
            text_widget.bind("<Control-Right>", lambda _: self.move_cursor_to_next_word(1))
            text_widget.bind("<Control-slash>", lambda _: self.comment_line())

        text_widget.bind("<Control-Return>", self.on_ctrl_enter)
        text_widget.bind("<<Copy>>", self.copy_to_clipboard)
        text_widget.bind("<<Cut>>", self.cut_to_clipboard)
        text_widget.bind("<<Paste>>", self.on_paste)


        self.instructions = \
'''
Key bindings:
  Ctrl+Enter        execute code
  Ctrl+/            comment current line/selection
  Alt+Up/Down       move line/selection up/down
  Alt+Shift+Up/Down duplicate line up/down
  Ctrl+Left/Right   move cursor to the next word

Right-click for more options
'''.strip()

        # Always show the scrollbars
        for child in text_widget.master.children.values():
            if isinstance(child, ttk.Scrollbar):
                self.text_widget.config(xscrollcommand=child.set)

        self.text_widget.configure(background=style.background_color or '#ffffff')
        cfg = {
            'color':        '#888' or None,
            'bold':         False,
            'italic':       False,
            'underline':    False,
            'bgcolor':      '#888' or None,
            'border':       '#ffffff' or None,
            'roman':        False or None,
            'sans':         False or None,
            'mono':         False or None,
            'ansicolor':    '#888',
            'bgansicolor':  '#888',
        }
        # Copy the style to the text widget
        for token, _color in style:
            cfg = style.style_for_token(token)
            # font_name = ('Courier New', 12)
            # if cfg['bold']:
            #     font_name = (*font_name, 'bold')
            # if cfg['italic']:
            #     font_name = (*font_name, 'italic')

            self.text_widget.tag_configure(str(token), foreground=f'#{cfg["color"]}' if cfg["color"] else None,
                               background=f'#{cfg["bgcolor"]}' if cfg["bgcolor"] else None,
                               underline=cfg['underline'])

        # Define toektn for triple slashes: ///
        self.text_widget.tag_configure('Token.Comment.TripleSlash', foreground='green', font=(*font, 'bold'))

        self.filepath: str = None
        self.read_only = False
        self.save_timer = None
        self.saved_hash: int = None

        self.on_save_cb: callable = None
        self.on_ctrl_enter_cb: callable = None
        self.on_edit_cb: callable = None

        # text: tk.Text = text_widget.master.winfo_children()[0]
        # text.insert('1.0', 'asd asd asd\n'.join([str(i) for i in range(1, 1000)]))

        # Add RMB menu to the text widget
        self.text_widget.bind("<Button-2>", self.show_menu)
        self.text_widget.bind("<Button-3>", self.show_menu)
        self.menu = tk.Menu(self.text_widget, tearoff=0)
        self.menu.add_command(label="Copy", command=lambda: self.copy_to_clipboard(None))
        self.menu.add_command(label="Cut", command=lambda: self.cut_to_clipboard(None))
        self.menu.add_command(label="Paste", command=lambda: self.on_paste(None))
        self.menu.add_separator()
        self.menu.add_command(label="Select all", command=lambda: self.text_widget.tag_add('sel', '1.0', 'end'))
        self.menu.add_command(label="FFglitch docs", command=self.show_documentation)
        self.default_text_color = self.text_widget.cget('fg')
        self.menu.bind("<Leave>", lambda _: self.menu.unpost())


    def set_text_color(self, color):
        self.text_widget.config(fg=color)

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def show_documentation(self):
        '''Open documentation url'''
        webbrowser.open('https://ffglitch.org/docs/')

    def get_selected_text(self):
        self.text_widget.selection_own()
        try:
            return self.text_widget.selection_get()
        except tk.TclError:
            return None

    def copy_to_clipboard(self, _event):
        self.text_widget.clipboard_clear()
        selected = self.get_selected_text()
        if selected:
            self.text_widget.clipboard_append(selected)
        else:
            # Nothing selected, copy the current line
            line = self.get_line(self.cursor_line_pos()) + '\n'
            self.text_widget.clipboard_append(line)

    def cut_to_clipboard(self, _event):
        self.text_widget.clipboard_clear()
        selected = self.get_selected_text()
        if selected:
            self.text_widget.clipboard_append(selected)
            self.text_widget.delete('sel.first', 'sel.last')
        else:
            # Nothing selected, cut the current line
            line = self.get_line(self.cursor_line_pos())
            self.text_widget.clipboard_append(line)
            self.text_widget.delete(f"{self.cursor_line_pos()}.0", f"{self.cursor_line_pos() + 1}.0")
        self.highlight_syntax()


    def on_paste(self, _event):
        try:
            s = self.text_widget.index('sel.first')
            e = self.text_widget.index('sel.last')
            selection = self.text_widget.get('sel.first', 'sel.last')
        except tk.TclError:
            s = e = None
            selection = None
        txt = self.text_widget.clipboard_get()
        if txt.endswith('\n') and not selection:
            txt = txt[:-1]
            # Insert at the beginning of the line
            self.text_widget.insert(f"{self.cursor_line_pos()}.0", txt + '\n')
            self.highlight_syntax()
            return 'break'
        # Replace the selected text
        if s and e:
            self.text_widget.delete(s, e)
        self.text_widget.insert('insert', txt)
        self.highlight_syntax()
        return 'break'

    def on_ctrl_enter(self, _event):
        if self.on_ctrl_enter_cb:
            self.on_ctrl_enter_cb()
            return 'break'

    def duplicate_line(self, direction):
        line_pos = self.cursor_line_pos()
        line = self.get_line(line_pos)
        direction = 0 if direction == -1 else 1
        self.text_widget.insert(f"{line_pos + direction}.0", line + '\n')
        self.highlight_syntax()

    def move_line(self, direction):
        cursor_pos = self.text_widget.index('insert')
        try:
            start_line = int(self.text_widget.index('sel.first').split('.')[0])
            end_line = int(self.text_widget.index('sel.last').split('.')[0])
        except tk.TclError:
            start_line = end_line = self.cursor_line_pos()

        one_line = start_line == end_line
        if one_line:
            end_line += 1

        lines = [self.get_line(line) for line in range(start_line, end_line)]
        if direction == -1 and start_line == 1:
            return
        if direction == 1 and end_line == int(self.text_widget.index('end').split('.')[0]) - 1:
            return

        self.text_widget.delete(f"{start_line}.0", f"{end_line}.0")

        insert_pos = start_line + direction
        self.text_widget.insert(f"{insert_pos}.0", '\n'.join(lines) + '\n')

        self.highlight_syntax()
        self.text_widget.tag_remove('sel', '1.0', 'end')
        if not one_line:
            self.text_widget.tag_add('sel', f"{insert_pos}.0", f"{insert_pos + len(lines)}.0")
        self.text_widget.mark_set('insert', f'{int(cursor_pos.split(".")[0]) + direction }.{int(cursor_pos.split(".")[1])}')
        return 'break'

    def move_cursor_to_next_word(self, direction):
        first_char = ''
        skipping = False

        def find_next_stop(row, col, direction):
            nonlocal first_char, skipping
            if row < 1 or row > end_line_number:
                return (row, col)
            line = self.get_line(row)
            col = min(col, len(line))
            for i in range(col, len(line)) if direction == 1 else range(col - 1, -1, -1):
                separators = [' ', '.', '(', ')', '[', ']', '{', '}', ':', ';', ',']
                if not first_char:
                    first_char = line[i]
                    skipping = first_char == ' '
                elif line[i] in separators:
                    if skipping and line[i] == ' ':
                        continue
                    return (row, i + (1 if direction == -1 else 0))
                elif i == 0 and row != start_row:
                    return (row, i + (1 if direction == -1 else 0))
                elif skipping and line[i] != ' ':
                    return (row, i + (1 if direction == -1 else 0))
                elif i == 0 and row == start_row and direction == -1:
                    return (row, 0)

            return find_next_stop(row + direction, 0 if direction == 1 else 9999, direction)

        start_row = self.cursor_line_pos()
        cursor_pos = self.text_widget.index('insert')
        row = int(cursor_pos.split('.')[0])
        col = int(cursor_pos.split('.')[1])
        end_line_number = int(self.text_widget.index('end').split('.')[0])

        row, col = find_next_stop(row, col, direction)
        self.text_widget.mark_set('insert', f"{row}.{col}")
        self.text_widget.see(f"{row + 3 * direction}.{col}")
        return 'break'

    def comment_line(self):
        cursor_pos = self.cursor_position()
        line_pos = self.cursor_line_pos()
        line = self.get_line(line_pos)
        if line.lstrip().startswith('// '):
            line = line.replace('// ', '', 1)
        elif line.lstrip().startswith('//'):
            line = line.replace('//', '', 1)
        else:
            # Add comment after the indentation
            intial_ws = line[:len(line) - len(line.lstrip())]
            line = line.lstrip()
            line = f'{intial_ws}// {line}'

        self.text_widget.delete(f"{line_pos}.0", f"{line_pos + 1}.0")
        self.text_widget.insert(f"{line_pos}.0", line + '\n')
        self.highlight_syntax()
        self.text_widget.mark_set('insert', cursor_pos)

        return 'break'

    def save_in(self, delay):
        if self.save_timer:
            self.text_widget.after_cancel(self.save_timer)
        self.save_timer = self.text_widget.after(delay, self.save, hash(self.get_text()))

    def save(self, hash_to_save=None):
        if not self.filepath:
            raise ValueError('No filepath set')
        if self.read_only:
            raise ValueError('File is read only')

        text = self.get_text()
        hash1 = hash(text)
        if not hash_to_save or hash1 == hash_to_save:
            if hash1 != self.saved_hash:
                print(f'Saving file: {self.filepath}')
                with open(self.filepath, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(text)
                self.saved_hash = hash1
                if self.on_save_cb:
                    self.on_save_cb(self.filepath)
        else:
            print('File changed, not saving')

    def set_on_save_cb(self, cb):
        self.on_save_cb = cb

    def set_on_ctrl_enter_cb(self, cb):
        self.on_ctrl_enter_cb = cb

    def set_on_edit_cb(self, cb):
        self.on_edit_cb = cb

    def cursor_position(self):
        return self.text_widget.index('insert')

    def cursor_line_pos(self):
        return int(self.text_widget.index('insert').split('.')[0])

    def get_line(self, line_number):
        return self.text_widget.get(f"{line_number}.0", f"{line_number}.end")

    def _detect_spaces_in_tab(self, line):
        if len(line) % 4 == 0:
            return 4
        elif len(line) < 4:
            return len(line)
        else:
            return 4 - len(line) % 4

    last_tab_size = 4
    code_at_press = ''
    def on_key_press(self, event):
        keyname = event.keysym
        try:
            if keyname == 'Tab':
                line_pos = self.cursor_line_pos()
                if int(line_pos) > 1:
                    line = self.get_line(line_pos)
                    def detect_tabs(line):
                        starting_ws = line[:len(line) - len(line.lstrip())]
                        tabs_in_line = starting_ws.count('\t')
                        if tabs_in_line > 0:
                            self.last_tab_size = 0
                            return 'done'
                        elif starting_ws:
                            spaces_cnt = self._detect_spaces_in_tab(starting_ws)
                            self.text_widget.insert('insert', ' ' * spaces_cnt)
                            self.last_tab_size = spaces_cnt
                            return 'break'
                        elif self.last_tab_size > 0:
                            self.text_widget.insert('insert', ' ' * self.last_tab_size)
                            return 'break'
                    prev_line = self.get_line(int(line_pos) - 1)
                    ret = detect_tabs(prev_line)
                    if ret == 'break':
                        return 'break'
                    if not ret:
                        return detect_tabs(line)
        finally:
            self.code_at_press = self.get_text()

    def on_key_release(self, event):
        keyname = event.keysym
        is_alt = event.state & 0x60000
        if keyname == 'Return' and event.state == 0:
            #  Copy tab intention from previous line
            line_pos = self.cursor_line_pos()
            if int(line_pos) > 1:
                prev_line = self.get_line(int(line_pos) - 1)
                starting_ws_len = len(prev_line) - len(prev_line.lstrip())
                starting_ws_portion = prev_line[:starting_ws_len]
                self.text_widget.insert(f"{line_pos}.0", starting_ws_portion)
                spaces_cnt = self._detect_spaces_in_tab(starting_ws_portion)
                self.last_tab_size = spaces_cnt
        elif is_alt and (keyname == 'Down' or keyname == 'Up' or keyname == 'Alt_L'):
            return 'break'

        code = self.get_text()
        if code != self.code_at_press:
            self.highlight_syntax()
        if self.filepath and self.autosave:
            self.save_in(3000)


    def highlight_syntax(self):
        code = self.text_widget.get("1.0", "end")  # Get all the text in the widget
        code = code.replace('\r\n', '\n')

        # Remove all tags
        for tag in self.text_widget.tag_names():
            self.text_widget.tag_remove(tag, "1.0", "end")

        self.text_widget.mark_set("range_start", "1.0")

        # Fix for offseting lexer when first lines are empty
        idx = 0
        while idx < len(code):
            if code[idx] == '\n':
                self.text_widget.mark_set("range_end", "range_start + 1c")
                self.text_widget.mark_set("range_start", "range_end")
            else:
                break
            idx += 1

        for token, content in lex(code, self.lexer):
            self.text_widget.mark_set("range_end", f"range_start + {len(content)}c")
            tag_name = str(token)
            if content.lstrip().startswith('///'):
                tag_name = 'Token.Comment.TripleSlash'
            self.text_widget.tag_add(tag_name, "range_start", "range_end")
            self.text_widget.mark_set("range_start", "range_end")

        if hash(code) != self.saved_hash:
            if self.on_edit_cb:
                self.on_edit_cb()

    def get_text(self):
        return self.text_widget.get("1.0", "end-1c")

    def set_text(self, txt = '', color=None):
        self.text_widget.delete("1.0", "end")
        self.text_widget.insert("1.0", txt)
        if color:
            self.text_widget.config(fg=color)
        else:
            self.text_widget.config(fg=self.default_text_color)

    def set_filepath(self, filepath):
        self.filepath = filepath

    def open_file(self, filepath, read_only=False):
        if self.filepath:
            self.close_file()

        text_content = ''
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                text_content = f.read().replace('\r\n', '\n')

        self.saved_hash = hash(text_content)
        self.text_widget.config(state=tk.NORMAL)
        self.set_text(text_content)
        self.text_widget.edit_reset()
        self.text_widget.config(state=tk.NORMAL if not read_only else tk.DISABLED)
        self.filepath = filepath
        self.read_only = read_only
        self.highlight_syntax()
        if self.read_only:
            self.text_widget.config(cursor='arrow')
        else:
            self.text_widget.config(cursor='xterm')
            self.text_widget.focus_set()

    def close_file(self):
        if self.save_timer:
            self.text_widget.after_cancel(self.save_timer)
            self.save_timer = None
        self.filepath = None


if __name__ == '__main__':
    root = tk.Tk()
    text = ScrolledText(root)
    text.pack(expand=True, fill='both')
    text.config(maxundo="999", undo=True)
    editor = CodeEditor(text, line_numbers=False, autosave=False)
    editor.open_file(__file__)
    root.mainloop()

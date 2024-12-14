import tkinter as tk
from tkinter import Canvas, Scale, VERTICAL
import math

OCTAVES = [1, 2, 3, 4]

MIDI_NOTES = { 'C1': 24, 'C2': 36, 'C3': 48, 'C4': 60, 'C5': 72, 'C6': 84, }

WHITE_KEY_WIDTH = 40
WHITE_KEY_HEIGHT = 200
BLACK_KEY_WIDTH = 25
BLACK_KEY_HEIGHT = 110
RADIUS = 7
MARGIN = 6

class MidiPiano:

    draw_x_offset = 1

    def __init__(self, _root, bg_color=None):
        self.frame = _root
        self.frame.title("Piano")
        self.frame.resizable(False, False)
        self.frame.protocol('WM_DELETE_WINDOW', self._on_exit)
        self.bg_color = bg_color

        notes = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
        self.white_keys = [f'{note}{octave}' for octave in OCTAVES for note in notes]
        self.black_keys = [f'{note}#{octave}' if note not in ['E', 'B'] else None for octave in OCTAVES for note in notes]

        canvas_width = len(self.white_keys) * WHITE_KEY_WIDTH + self.draw_x_offset * 2
        canvas_height = WHITE_KEY_HEIGHT + 1

        self.frame.config(width=canvas_width + MARGIN * 2 + 1, height=canvas_height + 140)

        self.canvas = Canvas(self.frame, width=canvas_width, height=canvas_height)
        self.canvas.place(x=MARGIN, y=0)
        self._draw_piano_keys()

        y = canvas_height + 10
        x = 0
        for i in range(10):
            slider = Scale(self.frame, from_=127, to=0, orient=VERTICAL, command=lambda value, no=i: self._on_slider_change(no, value))
            slider.place(x=x, y=y, height=100)
            slider.bind("<Motion>", lambda event, no=i: self._on_slider_hover(no))
            # Add a label at the bottom of each slider
            label = tk.Label(self.frame, text=f"{i}")
            label.place(x=x + 26, y=y + 100)
            x += 50

        x += 10
        label = tk.Label(self.frame, text='MIDI Note:')
        label.place(x=x, y=y)
        label = tk.Label(self.frame, text='-')
        label.place(x=x + 62, y=y)
        self.label_note = label

        y += 20
        label = tk.Label(self.frame, text='MIDI Velocity:')
        label.place(x=x, y=y)
        label = tk.Label(self.frame, text='-')
        label.place(x=x + 78, y=y)
        self.label_velocity = label

        y += 20
        label = tk.Label(self.frame, text='MIDI Message:')
        label.place(x=x, y=y)
        label = tk.Label(self.frame, text='-')
        label.place(x=x + 83, y=y)
        self.label_midi_message = label

        self.canvas.bind("<Button-1>", self._on_canvas_press)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Motion>", self._on_canvas_hover)

        if bg_color:
            self.frame.config(bg=bg_color)

        for child in self.frame.winfo_children():
            child.config(highlightthickness=0)
            if bg_color:
                child.config(bg=bg_color)

    def destroy(self):
        self.frame.destroy()
        self.frame = None

    def is_destroyed(self):
        return not self.frame

    def _on_exit(self):
        self.destroy()

    show_after_id = None
    def show(self, show=True, in_ms=0):
        if self.frame is None:
            return
        if show:
            self.frame.deiconify()
            if self.show_after_id:
                self.frame.after_cancel(self.show_after_id)
                self.show_after_id = None
        else:
            self.show_after_id = self.frame.after(in_ms, self.frame.withdraw)

    def _draw_piano_keys(self):
        def draw_rounded_key(self, x1, x2, y1, y2, **kwargs):
            '''Draw a rounded rectangle with the given bounds using polygon'''

            points = []
            step = 30
            radius = RADIUS

            # Top-right corner
            for i in range(0, 90 + 1, step):
                angle = math.radians(-i + 90)
                points.append(x2 - radius + radius * math.cos(angle))
                points.append(y1 + radius - radius * math.sin(angle))
            # Bottom-right corner
            for i in range(90, 180 + 1, step):
                angle = math.radians(-i + 90)
                points.append(x2 - radius + radius * math.cos(angle))
                points.append(y2 - radius - radius * math.sin(angle))
            # Bottom-left corner
            for i in range(180, 270 + 1, step):
                angle = math.radians(-i + 90)
                points.append(x1 + radius + radius * math.cos(angle))
                points.append(y2 - radius - radius * math.sin(angle))
            # Top-left corner
            for i in range(270, 360 + 1, step):
                angle = math.radians(-i + 90)
                points.append(x1 + radius + radius * math.cos(angle))
                points.append(y1 + radius - radius * math.sin(angle))

            self.canvas.create_polygon(points, **kwargs)

        for i, key in enumerate(self.white_keys):
            x0 = i * WHITE_KEY_WIDTH + self.draw_x_offset
            x1 = x0 + WHITE_KEY_WIDTH
            fill = "white"
            draw_rounded_key(self, x0, x1, y1=2, y2=WHITE_KEY_HEIGHT, fill=fill, outline="black")
            self.canvas.create_text((x0 + x1) / 2, 180, text=key)

        for i, key in enumerate(self.black_keys):
            x0 = (i + 1) * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2 + self.draw_x_offset
            x1 = x0 + BLACK_KEY_WIDTH
            if key:
                draw_rounded_key(self, x0, x1, y1=2, y2=BLACK_KEY_HEIGHT, fill="black")
                self.canvas.create_text((x0 + x1) / 2, 60, text=key, fill="white")


    def _on_canvas_press(self, event):
        self._keyboard_pressed(event)

    def _on_canvas_release(self, event):
        self._keyboard_pressed(event, False)

    def _on_canvas_hover(self, event):
        key = self._get_key_from_position(event.x, event.y)
        note = self.convert_key_to_midi(key)
        velocity = self._key_y_to_velocity(key, event.y)
        self.label_note.config(text=note)
        self.label_velocity.config(text=velocity)

    def _on_slider_change(self, no, value):
        note = no
        midi_msg = [0, note, int(value)]
        self._send_msg(midi_msg)

    def _on_slider_hover(self, no):
        self.label_note.config(text=str(no))

    def _keyboard_pressed(self, event, pressed=True):
        x = event.x
        y = event.y
        key = self._get_key_from_position(x, y)
        if key:
            print(f"Key pressed: {key}")
            midi_note = self.convert_key_to_midi(key)

            midi_status = 0x90 if pressed else 0x80
            midi_velocity = self._key_y_to_velocity(key, y)
            midi_msg = [midi_status, midi_note, midi_velocity]
            self._send_msg(midi_msg)

    def _key_y_to_velocity(self, key, y):
        return int((1 - y / (WHITE_KEY_HEIGHT if key in self.white_keys else BLACK_KEY_HEIGHT)) * 127)

    def convert_key_to_midi(self, key):
        midi_note = MIDI_NOTES[self.white_keys[0]]
        for i, w_key in enumerate(self.white_keys):
            if w_key == key:
                break
            midi_note += 1
            if self.black_keys[i] == key:
                break
            if self.black_keys[i] is not None:
                midi_note += 1
        return midi_note

    def _get_key_from_position(self, x, y):
        for i, key in enumerate(self.black_keys):
            x0 = (i + 1) * WHITE_KEY_WIDTH - BLACK_KEY_WIDTH / 2 + self.draw_x_offset
            x1 = x0 + BLACK_KEY_WIDTH
            if key is not None and x0 <= x <= x1 and y <= BLACK_KEY_HEIGHT:
                return key

        for i, key in enumerate(self.white_keys):
            x0 = i * WHITE_KEY_WIDTH + self.draw_x_offset
            x1 = x0 + WHITE_KEY_WIDTH
            if x0 <= x <= x1:
                return key

        return None


    on_message_cb = None
    def set_on_message_cb(self, cb):
        self.on_message_cb = cb

    def _send_msg(self, msg):
        if self.on_message_cb:
            self.on_message_cb(msg)

        self.label_note.config(text=str(msg[1]))
        self.label_velocity.config(text=str(msg[2]))
        self.label_midi_message.config(text=str(msg))

if __name__ == "__main__":
    root = tk.Tk()
    piano = MidiPiano(root)
    root.mainloop()

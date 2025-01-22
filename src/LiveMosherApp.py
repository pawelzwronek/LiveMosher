import configparser
import locale
from functools import cmp_to_key
import os
import os.path
import subprocess
import time
import traceback
import re
import signal
import zipfile

from typing import List

from ctypes.wintypes import HWND
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from send2trash import send2trash
from zmq import Context as zmq_Context

from consts import EDITED_SCRIPTS_DIR, NAME, PROJECT_EXT, REPO_URL, SCRIPTS_DIR, VERSION_FILE
from lib.colored_print import print_error, print, print_warn # pylint: disable=redefined-builtin
from lib.framerate import find_fraction
from lib.misc import IS_MAC, IS_WIN, copy_file, find_next_output_file, find_relative_path, fix_windows_network_path, \
                    normalize_path, open_explorer_and_select_file, parse_float, path_replace_not_allowed_chars, resolve_relative_path
from lib.process import Line, Process

from LiveMosher1_support import LiveMosherGui, start_up
from widget.midi_piano import MidiPiano
from script import Script
from zmq_req import ZmqReqPush, ZmqReqMode


#pylint: disable=global-statement
#pylint: disable=c-extension-no-member
#pylint: disable=broad-except

MIN_SPEED = 0.1
MAX_SPEED = 5

class LiveMosherApp(LiveMosherGui):
    def __init__(self):
        super().__init__(NAME)

        self.this_dir = os.path.dirname(os.path.abspath(__file__))
        self.app_dir = normalize_path(os.path.join(self.this_dir, '..'))
        print('App script dir:', self.this_dir)
        print('App dir:', self.app_dir)
        cwd = os.getcwd()
        if cwd == '/':
            maxEscape = 2
            cwd = self.app_dir
            while maxEscape > 0:
                maxEscape -= 1
                cwd = normalize_path(os.path.join(cwd, '..'))
                if cwd.endswith('.app'):
                    continue
        self.cwd = cwd
        print('CWD:', self.cwd)
        self.scripts_dir = ''
        self.project_dir = ''
        self.is_app_packed = not self.this_dir.endswith('src')

        try:
            version_file = os.path.join(self.this_dir, VERSION_FILE)
            if not os.path.exists(version_file):
                version_file = os.path.join(self.this_dir, '..', VERSION_FILE)
            with open(version_file, 'r', encoding='utf-8') as f:
                self.version = f.read().strip()
        except Exception as _e:
            self.version = ''

        self.top.title(f'{NAME} {self.version}')

        self.config = configparser.ConfigParser()
        self.config['Main'] = {
            'last_project_file': '',
            'top_pos': '-,-',
            'top_size': '200x748',
            'top_maximized': 'False',
            'video_pos': '-1,-1',
            'video_size': '-1x-1',
            'video_maximized': 'False',
            'window_border_size': '-,-',
            'script_count': '0',
        }
        self.config.read(os.path.join(self.cwd, 'config.ini'))

        self.project = self.get_default_project()

        self.project_scripts: List[Script] = []
        self.all_scripts: List[Script] = []
        self.listbox_scripts: List[Script] = []

        self.zmq_context = zmq_Context()
        self.zmq_context_midi = zmq_Context()
        self.fflive_zmq = ZmqReqPush(ctx=self.zmq_context, name='fflive', wait_cb=self.gui_event_loop)
        self.fflive_a_zmq = ZmqReqPush(ctx=self.zmq_context, name='fflive_audio', wait_cb=self.gui_event_loop)
        self.fflive_zmq.generate_urls()
        self.fflive_a_zmq.generate_urls()
        self.midi_zmq = ZmqReqPush(ctx=self.zmq_context_midi, name='midi_emu', mode=ZmqReqMode.TCP, is_push=True)

        self.w.button_clone.configure(command=self.on_clone_script)
        self.w.button_edit_script.configure(command=self.on_edit_share_script)
        self.w.button_start_mark.configure(command=self.on_start_mark)
        self.w.button_end_mark.configure(command=self.on_end_mark)
        self.w.button_open_project.configure(command=self.on_open_project)
        self.w.button_play.configure(command=self.on_play)
        self.w.button_play_script.configure(command=self.on_play_script)
        self.w.button_record.configure(command=self.on_record, state=tk.DISABLED)
        self.w.button_reload_script_list.configure(command=self.update_scripts_list)
        self.w.button_rename_script.configure(command=self.on_rename_script)
        self.w.button_restart_video.configure(command=lambda: self.start_ffplay(start_paused=self.is_paused))
        self.w.button_save_as_project.configure(command=self.on_save_as_project)
        self.w.button_save_project.configure(command=self.save_project)
        self.w.button_seek_back_10s.configure(command=lambda: self.seek_video(-10))
        self.w.button_seek_back_2s.configure(command=lambda: self.seek_video(-2))
        self.w.button_seek_back_10f.configure(command=lambda: self.seek_video(-10 / self.input_fps if self.input_fps else 0))
        self.w.button_seek_1f.configure(command=lambda: self.seek_video(1 / self.input_fps if self.input_fps else 0))
        self.w.button_seek_2s.configure(command=lambda: self.seek_video(2))
        self.w.button_seek_10s.configure(command=lambda: self.seek_video(10))
        self.w.button_select_output.configure(command=self.on_select_output)
        self.w.button_select_video.configure(command=self.on_select_video)
        self.w.checkbutton_auto_rename.configure(command=self.on_auto_rename_switch)
        self.w.checkbutton_mute.configure(command=self.on_mute)
        self.w.entry_project_name.bind('<Any-KeyRelease>', lambda _: self.project_changed())
        self.w.entry_script_parameters.bind('<Any-KeyRelease>', lambda _: self.project_changed())
        self.w.entry_video_input.bind('<Any-KeyRelease>', lambda _: self.project_changed())
        self.w.entry_video_output.bind('<Any-KeyRelease>', self.on_output_path_change)
        self.w.label_about.bind('<Button-1>', lambda _: self.show_about_dialog())
        self.w.label_fps.configure(text='FPS: -')
        self.w.label_issue.bind('<Button-1>', lambda _: self.open_url(f'{REPO_URL}/issues'))
        self.w.label_progress.configure(text=self.formatSeconds(0))
        self.w.label_total_time.configure(text=self.formatSeconds(0))
        self.w.listbox_scripts.bind('<ButtonRelease-1>', self.on_script_select)
        self.w.listbox_scripts.bind('<Button-2>', self.on_listbox_scripts_rmb)
        self.w.listbox_scripts.bind('<Button-3>', self.on_listbox_scripts_rmb)
        self.w.listbox_scripts.bind('<KeyRelease-Return>', self.on_script_select)
        self.w.scale_speed.configure({'from': MIN_SPEED, 'to': MAX_SPEED })
        self.w.scale_speed.configure(command=self.on_speed_changing)
        self.w.scale_speed.set(self.lin_speed_to_exp(1))
        self.w.scale_speed.bind('<ButtonRelease-1>', self.on_speed_change)
        for seq in ['<ButtonPress-2>', '<ButtonRelease-2>', '<ButtonPress-3>', '<ButtonRelease-3>', '<Double-Button-1>']:
            self.w.scale_speed.bind(seq, self.on_reset_speed)
        self.on_speed_changing()
        self.w.scale_progress.bind('<ButtonPress-1>', self.on_progress_press)
        self.w.scale_progress.bind('<Motion>', self.on_progress_motion)
        self.w.scale_progress.bind('<ButtonRelease-1>', self.on_progress_change)
        self.w.scale_progress.configure(command=self.on_progress_changing)

        self.window_hwnd: HWND = None

        self.w.scrolledText_console.delete(1.0, tk.END)

        self.selected_script: Script = None
        self.selected_script_idx = -1

        self.ffgac_process: Process = None
        self.ffgac_rec_process: Process = None
        self.fflive_process: Process = None
        self.fflive_process_ok = None
        self.fflive_window_title = ''
        self.fflive_window_borders = None, None
        self.fflive_start_paused = False
        self.fflive_speed_scale = 1.0
        self.starting_ffplay = False
        self.r_ffplay_pipe_out, self.w_ffplay_pipe_out = None, None
        self.r_ffplay_pipe_err, self.w_ffplay_pipe_err = None, None
        self.r_fd2, self.w_fd2 = None, None

        self.ffgac_a_process: Process = None
        self.fflive_a_process: Process = None

        self.video_path = ''
        self.output_path_base = ''
        self.output_path = ''
        self.input_duration: float = None
        self.input_duration_alt: float = None
        self.last_input_duration: float = None
        self._input_fps: float = None
        self._input_fps_file_name: float = None

        self.input_frames_count = 0
        self.input_frames_count_alt = 0
        self.current_frame: int = 1
        self.current_frame_ffgac: int = 0
        self.start_video_at: float = 0.0
        self.last_video_size = '' # '0x0'
        self.played_frames = 0
        self.progress_changing = False
        self.is_playing = False
        self.is_paused = False
        self.is_paused_audio = False
        self.last_audio_restart_time = 0
        self.audio_restart_time_off = 0
        self.audio_time = 0
        self.last_audio_time_check = 0
        self.audio_speed = 0
        self.pause_time = 0.0
        self.is_recording = False
        self.waiting_for_ffgac_rec = False

        self.editor.set_on_save_cb(self.on_script_save)
        self.editor.set_on_ctrl_enter_cb(self.on_play_script)
        self.w.label_saving.configure(text='')

        self.editor_empty_text = \
f'''Welcome in {NAME},
a front-end for FFglitch made by ramiropolla.

Select a file on the left to start editing and recording

{self.editor.instructions}


All Examples scripts comes from ffglitch-scripts repo by ramiropolla:
github.com/ramiropolla/ffglitch-scripts

Full FFglitch documentation: ffglitch.org/docs

Have fun!
'''
        self.editor_empty_text_color = '#666'

        self.piano: MidiPiano = None


    @property
    def input_fps(self):
        """Getter method"""
        if self.video_path != self._input_fps_file_name:
            return None
        return self._input_fps

    @input_fps.setter
    def input_fps(self, value):
        """Setter method"""
        self._input_fps = value
        self._input_fps_file_name = self.video_path

    def on_first_visibility(self, _event):
        super().on_first_visibility(_event)
        if self.config['Main']['top_maximized'] == 'True':
            self.set_top_maximized(True)

        if self.top_height:
            new_size = self.config['Main']['top_size']
            self.top.geometry(new_size)

            if self.selected_script:
                self.restart_ffplay()

        try:
            nums = self.config['Main']['window_border_size'].split(',')
            self.fflive_window_borders = int(nums[0]), int(nums[1])
            print('Window borders:', self.fflive_window_borders)
        except ValueError:
            pass
        if self.fflive_window_borders[0] is None or self.fflive_window_borders[1] is None:
            self.after(500, self.test_window_borders_size)

        self.editor.set_text(self.editor_empty_text, self.editor_empty_text_color)
        self.after(1, self.show_hide, self.w.button_edit_script, False)
        self.place_start_end_mark()
        self.after(1000, self.check_fps, True)

        # self.console_log('CWD: ' + self.cwd)
        # self.console_log('App script dir: ' + self.this_dir)
        # self.console_log('App dir: ' + self.app_dir)
        # self.console_log('Project dir: ' + self.project_dir)
        # self.console_log(f"Scripts dir: {self.scripts_dir}")

    def on_before_start(self):
        super().on_before_start()
        try:
            top_pos = self.config['Main']['top_pos'].split(',')
            self.top.geometry(f'+{top_pos[0]}+{top_pos[1]}')
        except Exception:
            pass

        last_project_file = self.config['Main']['last_project_file']
        if last_project_file:
            if os.path.exists(last_project_file):
                if not self.open_project(last_project_file):
                    self.config['Main']['last_project_file'] = ''
                    self.save_config()
            else:
                show_info(f'Project file not found: {last_project_file}')
                self.open_project()
        else:
            self.open_project()
        self.update_play_text()

    def on_exit(self, _event=None):
        try:
            if self.is_recording:
                if messagebox.askyesno('Recording in progress', 'Recording in progress. Close the application?', icon='warning'):
                    self.kill_ffplay_processes(force=True)
                else:
                    return

            if self.project_changed():
                ret = messagebox.askyesnocancel('Save project', 'Save project before exit?')
                if ret:
                    if not self.save_project():
                        return
                elif ret is None:
                    return

            self.update_config()
            self.save_config()

            if self.selected_script and not self.selected_script.buildin:
                self.editor.save()

            self.kill_ffplay_processes()
            self.fflive_zmq.close()
            self.fflive_a_zmq.close()
            self.midi_zmq.close()

            super().on_exit(_event)
        except Exception as e:
            print('Error on_exit:', e)
            traceback.print_exc()
            if messagebox.askyesno('Closing', f'An error occurred: "{e}"\n\nClose the application?', icon='warning'):
                super().on_exit(_event)


    def get_video_win_pos_size(self, req: ZmqReqPush):
        try:
            if req.connected:
                msg = req.req_msg('window_pos_size')
                if msg:
                    return tuple(int(x) for x in msg.split(','))
        except Exception as e:
            print('Error get_video_win_pos_size:', e)
        return None, None, None, None

    def get_video_win_maximized(self, req: ZmqReqPush):
        try:
            if req.connected:
                msg = req.req_msg('window_maximized')
                return msg == '1'
        except Exception as e:
            print('Error get_video_win_pos_size:', e)
        return False

    def get_default_project(self):
        project = configparser.ConfigParser()
        project['Project'] = {
            'name': 'Project1',
            'video': '', # 'video.mp4',
            'video_size': '0x0',
            'video_duration': '0',
            'output': '', # 'output.mp4',
            'auto_rename': 'True',
            'mute': 'False',
            'start_mark_t': '-1',
            'end_mark_t': '-1',
            'script': '', # 'scripts/simple_script_123.js',
            'script_count': '0',
        }
        project['Script#x'] = {
            'path': 'scripts/simple_script_123.js',
            'parameters': '',
        }
        return project

    def on_output_path_change(self, _event):
        self.w.is_auto_rename.set(0)
        base_dir = os.path.dirname(self.output_path_base)
        output = self.w.entry_video_output.get()
        if output:
            if os.path.dirname(output): # if output is absolute path
                self.output_path_base = output
            else:
                output = path_replace_not_allowed_chars(output, keep_dirs=True)
                self.output_path_base = output and normalize_path(os.path.join(base_dir, output))
        else:
            self.output_path_base = ''
        self.update_output_path()
        self.project_changed()

    def update_output_path(self):
        org = self.w.entry_video_output.get()
        self.output_path = self.output_path_base
        if self.w.is_auto_rename.get() != 0:
            self.output_path = find_next_output_file(self.output_path)

        new_output_file = os.path.basename(self.output_path) if self.output_path else ''
        if org != new_output_file:
            self.w.entry_video_output.delete(0, tk.END)
            self.w.entry_video_output.insert(tk.END, new_output_file)

        if self.w.is_auto_rename.get() == 0:
            self.w.label_output_status.configure(text='Recording overwrite output file')
        else:
            self.w.label_output_status.configure(text='')

    def on_auto_rename_switch(self):
        self.update_output_path()
        self.project_changed()

    @property
    def is_mute(self):
        return self.w.is_mute.get() == 1

    def on_mute(self):
        if self.fflive_a_zmq.connected:
            if not self.fflive_a_zmq.req_msg(f'volume:{0 if self.is_mute else 100}'):
                print_error('Error setting volume')
                self.w.is_mute.set(0 if self.is_mute else 1)
        self.project_changed()

    def open_project(self, file_path=None):
        ok = False
        try:
            if file_path:
                print('Opening project:', file_path)
                self.project = self.get_default_project()
                self.project.read(file_path)
                if not self.project.has_section('Project'):
                    raise configparser.Error('No sections in the file')
                self.project_dir = normalize_path(os.path.dirname(file_path))
                print('Project dir(prj):', self.project_dir)
                ok = True
        except Exception as e:
            print('Error opening project:', e)

        if not self.project_dir:
            self.project_dir = self.cwd
            print('Project dir(cwd):', self.project_dir)

        check_scripts_dir = [self.project_dir, self.app_dir]
        for i, dir1 in enumerate(check_scripts_dir):
            dir1 = normalize_path(os.path.join(dir1, SCRIPTS_DIR))
            if os.path.exists(dir1):
                print(f"Scripts dir({['prj', 'app'][i]}): {dir1}")
                self.scripts_dir = dir1
                break
        if not self.scripts_dir:
            show_info('Examples directory not found.\nCreating a new one.')
            scripts_dir = os.path.join(self.app_dir, SCRIPTS_DIR)
            try:
                os.makedirs(scripts_dir, exist_ok=True)
                with open(os.path.join(scripts_dir, 'basic.js'), 'w', encoding='utf-8') as f:
                    f.write(self.get_example_mosher(0))
                self.scripts_dir = scripts_dir
            except Exception as e:
                print_error('Error creating scripts dir:', e)
                return False

        self.update_scripts_list()

        self.w.entry_project_name.delete(0, tk.END)
        self.w.entry_project_name.insert(tk.END, self.project['Project']['name'])
        self.video_path = self.resolve_relative_path(self.project['Project']['video'])
        self.last_video_size = self.project['Project']['video_size']
        self.last_input_duration = parse_float(self.project['Project']['video_duration'], 0)
        self.w.entry_video_input.delete(0, tk.END)
        self.w.entry_video_input.insert(tk.END, os.path.basename(self.video_path))
        self.w.is_auto_rename.set(1 if self.project['Project']['auto_rename'] == 'True' else 0)
        self.w.is_mute.set(1 if self.project['Project']['mute'] == 'True' else 0)
        self.start_mark_t = parse_float(self.project['Project']['start_mark_t'], -1)
        self.end_mark_t = parse_float(self.project['Project']['end_mark_t'], -1)
        self.place_start_end_mark()
        self.output_path_base = self.resolve_relative_path(self.project['Project']['output'])
        self.update_output_path()

        self.project_scripts = []
        script_count = int(self.project['Project']['script_count'])
        for i in range(script_count):
            try:
                script = Script(self.resolve_relative_path(self.project[f'Script#{i}']['path']),
                                self.project[f'Script#{i}']['parameters'])
                if os.path.exists(script.path):
                    self.project_scripts.append(script)
            except Exception as e:
                print(f'Error loading script {i}:', e)

        self.selected_script_path = ''
        script_file = self.project['Project']['script']
        for script in self.listbox_scripts:
            if script and script.path == script_file:
                self.select_script(script_file)
                break

        self.update_output_path()
        self.project_changed()

        return ok

    def find_relative_path(self, target_path):
        if not self.project_dir:
            return target_path
        return normalize_path(find_relative_path(self.project_dir, target_path))

    def resolve_relative_path(self, target_path):
        base_path = self.project_dir
        if not base_path:
            return target_path
        return normalize_path(resolve_relative_path(base_path, target_path))

    def project_changed(self):
        self.update_script_parameters()

        project = self.get_default_project()
        project['Project']['name'] = self.w.entry_project_name.get()
        project['Project']['video'] = self.find_relative_path(self.video_path)
        project['Project']['video_size'] = self.last_video_size or '0x0'
        project['Project']['video_duration'] = f'{self.last_input_duration:.3f}' if self.last_input_duration else '0'
        project['Project']['output'] = self.find_relative_path(self.output_path_base)
        project['Project']['auto_rename'] = 'True' if self.w.is_auto_rename.get() == 1 else 'False'
        project['Project']['mute'] = 'True' if self.w.is_mute.get() == 1 else 'False'
        project['Project']['start_mark_t'] = f'{self.start_mark_t:.3f}'
        project['Project']['end_mark_t'] = f'{self.end_mark_t:.3f}'
        project['Project']['script'] = self.find_relative_path(self.selected_script.path) if self.selected_script else ''
        project['Project']['script_count'] = str(len(self.project_scripts))

        for i, script in enumerate(self.project_scripts):
            project[f'Script#{i}'] = {
                'path': self.find_relative_path(script.path),
                'parameters': script.parameters,
            }

        def check_dirty():
            all_sections = self.project.sections()
            for section in project.sections():
                if section.startswith('Script#'):
                    path = project[section].get('path')
                    parameters = project[section].get('parameters')
                    found_script = False
                    # Find script in self.project
                    for section1 in self.project.sections():
                        if section1.startswith('Script#'):
                            if self.project[section1].get('path') == path:
                                found_script = True
                                if parameters != self.project[section1].get('parameters'):
                                    print(f'Dirty: [{section}].parameters = {parameters}')
                                    return True
                    if not found_script and parameters:
                        print(f'Dirty: [{section}].parameters = {parameters}')
                        return True
                else:
                    if section not in all_sections:
                        print('Dirty section:', section)
                        return True
                    for key, value in project[section].items():
                        if section == 'Project' and (key == 'script' or key == 'script_count'):
                            continue
                        if not self.project.has_section(section) or self.project[section].get(key) != value:
                            print(f'Dirty: [{section}].{key} = {value}')
                            return True
            return False

        dirty = check_dirty()

        self.w.button_save_project.configure(state=tk.NORMAL if dirty else tk.DISABLED)

        return project if dirty else None

    def save_project(self, file_path=None):
        if not file_path:
            file_path = self.config['Main']['last_project_file']
            if not os.path.exists(file_path):
                return self.on_save_as_project()

        if not file_path:
            return self.on_save_as_project()

        self.project_dir = os.path.dirname(file_path)
        project = self.project_changed()
        if not project:
            return
        print('Saving project:', file_path)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                project.write(f)
        except Exception as e:
            print('Error saving project:', e)
            return False

        self.project = project

        if self.config['Main']['last_project_file'] != file_path:
            self.config['Main']['last_project_file'] = file_path
            self.save_config()

        self.project_changed()
        return True


    def update_config(self):
        top_width, top_height = self.top.winfo_width(), self.top.winfo_height()
        if self.top_width and self.top_height and top_width > 0 and top_height > 0:
            self.config['Main']['top_pos'] = f'{self.top.winfo_x()},{self.top.winfo_y()}'
            self.config['Main']['top_monitor'] = str(self.top.winfo_screen())
            self.config['Main']['top_size'] = f'{top_width}x{top_height}'

        if self.fflive_window_borders[0] is not None and self.fflive_window_borders[1] is not None:
            self.config['Main']['window_border_size'] = f'{self.fflive_window_borders[0]},{self.fflive_window_borders[1]}'

        if self.fflive_process:
            video_x, video_y, video_w, video_h = self.get_video_win_pos_size(self.fflive_zmq)
            if video_x is not None and video_y is not None:
                self.config['Main']['video_pos'] = f'{video_x},{video_y}'
                self.config['Main']['video_size'] = f'{video_w}x{video_h}'
                self.last_video_size = f'{video_w}x{video_h}'
                self.config['Main']['video_maximized'] = str(self.get_video_win_maximized(self.fflive_zmq))

        self.config['Main']['top_maximized'] = str(self.is_top_maximized())

    def save_config(self):
        path = os.path.join(self.cwd, 'config.ini')
        with open(path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def select_script(self, script_file = ''):
        script_file = self.resolve_relative_path(script_file)

        self.update_script_parameters()

        script = self.get_script_from_list(self.listbox_scripts, script_file)
        self.w.listbox_scripts.selection_clear(0, tk.END)

        if script:
            self.w.listbox_scripts.selection_set(self.listbox_scripts.index(script))
            self.selected_script = script

            self.editor.open_file(self.selected_script.path, read_only=script.buildin)

            project_script = self.get_script_from_list(self.project_scripts, self.selected_script.path)
            if project_script:
                self.w.entry_script_parameters.delete(0, tk.END)
                self.w.entry_script_parameters.insert(tk.END, project_script.parameters)
            else:
                self.w.entry_script_parameters.delete(0, tk.END)
            self.project_changed()

            self.show_hide(self.w.button_edit_script, True)
        else:
            self.selected_script = None
            self.w.entry_script_parameters.delete(0, tk.END)
            self.editor.open_file('', read_only=False)
            self.editor.set_text(self.editor_empty_text, self.editor_empty_text_color)
            self.show_hide(self.w.button_edit_script, False)

        self.w.button_edit_script.configure(text='Edit' if script and script.buildin else 'Share')
        self.w.button_rename_script.configure(state=tk.NORMAL if script and not script.buildin else tk.DISABLED)
        self.w.button_clone.configure(state=tk.NORMAL if script and not script.buildin else tk.DISABLED)
        # Show selected script in the list
        if script:
            idx = self.listbox_scripts.index(script)
            self.w.listbox_scripts.see(idx)
        self.update_play_text()

    def show_hide(self, button: tk.Button, show=True):
        y = int(button.place_info().get('y'))
        if y != 0:
            if show:
                button.place(y=y + 10000 if y < 0 else y)
            else:
                button.place(y=y - 10000 if y >= 0 else y)

    def get_script_from_list(self, list1: List[Script],  script_path = '') -> Script:
        if not os.path.isabs(script_path):
            script_path = self.resolve_relative_path(script_path)
        for script in list1:
            if script and script.path == script_path:
                return script

    def update_script_parameters(self):
        if self.selected_script and self.selected_script.path:
            script = self.get_script_from_list(self.project_scripts, self.selected_script.path)
            parameters = self.w.entry_script_parameters.get()
            if script:
                script.parameters = parameters
            elif parameters:
                self.project_scripts.append(Script(self.selected_script.path, parameters))

    def restart_ffplay(self, start_at_sec=0.0):
        self.start_ffplay(start_at_sec=start_at_sec)

    def update_scripts_list(self, select_script_path=''):
        current_y_pos = self.w.listbox_scripts.yview()[0]
        self.w.listbox_scripts.delete(0, tk.END)
        self.listbox_scripts = []

        def format_path(path, depth):
            return f'{"  " * depth}{path}'

        def traverse_dir(root_dir, is_edited_scripts=False):
            current_dir = root_dir
            def starting_underscore(x):
                x = os.path.splitext(x)[0]
                return re.sub(r'^(_+)', 'ZZZ', x)
            dirs = list(os.walk(current_dir))
            dirs.sort(key=lambda x: x[0])
            for root, _dirs, files in dirs:
                current_dir1 = root[len(root_dir) + 1:].replace('\\\\', '/').replace('\\', '/')
                path_deep = 0 if not current_dir1 else (current_dir1.count('/') + 1)
                path_deep += 1
                # Folders
                if current_dir1 != current_dir and path_deep > 0:
                    folder_icon = '📁' if path_deep > 0 else ''
                    base_name = os.path.basename(current_dir1)
                    if path_deep == 1:
                        base_name = EDITED_SCRIPTS_DIR if is_edited_scripts else SCRIPTS_DIR
                    self.w.listbox_scripts.insert(tk.END, format_path(folder_icon + base_name, path_deep - 1)  )
                    current_dir = current_dir1
                    self.listbox_scripts.append(None)
                # Files
                files.sort(key=cmp_to_key(lambda x, y: locale.strcoll(starting_underscore(x), starting_underscore(y))), reverse=False)
                scripts = []
                for file in files:
                    if file.endswith(".js") or file.endswith(".mjs") or file.endswith(".py"):
                        full_path = normalize_path(os.path.join(root, file))
                        script = Script(full_path, buildin=not is_edited_scripts)
                        scripts.append(script)
                        with open(full_path, 'r', encoding='utf-8') as f:
                            source = f.read()
                            is_main = re.search(r'export +function +(glitch_frame|filter) *\(', source)
                            script.type = Script.Type.MAIN if is_main else Script.Type.HELPER
                            script.is_filter = is_main and is_main.group(1) == 'filter'

                scripts.sort(key=lambda x: x.type == Script.Type.MAIN, reverse=True)
                for script in scripts:
                    file_icon = '▹'
                    file = os.path.basename(script.path)
                    self.w.listbox_scripts.insert(tk.END, format_path(file_icon + re.sub(r'.js$|.mjs$|.py$', '', file, flags=re.IGNORECASE), path_deep))
                    self.listbox_scripts.append(script)


        traverse_dir(self.resolve_relative_path(EDITED_SCRIPTS_DIR), is_edited_scripts=True)
        # Separator
        if self.listbox_scripts:
            self.w.listbox_scripts.insert(tk.END, '')
            self.listbox_scripts.append(None)
        traverse_dir(self.scripts_dir)

        self.w.listbox_scripts.tooltip_texts = [''] * len(self.listbox_scripts)
        for i, script in enumerate(self.listbox_scripts):
            if script:
                if script.type == Script.Type.MAIN:
                    self.w.listbox_scripts.itemconfig(i, {'fg': '#000000'})
                if script.type == Script.Type.HELPER:
                    self.w.listbox_scripts.itemconfig(i, {'fg': '#6f6f6f'})
                    self.w.listbox_scripts.tooltip_texts[i] = 'Helper script'

        if select_script_path:
            self.selected_script = self.get_script_from_list(self.listbox_scripts, select_script_path)

        if self.selected_script:
            self.selected_script = self.get_script_from_list(self.listbox_scripts, self.selected_script.path)
            idx = self.listbox_scripts.index(self.selected_script)
            if idx >= 0:
                self.w.listbox_scripts.selection_set(idx)
        self.w.listbox_scripts.yview_moveto(current_y_pos)

    def ping_window(self, req: ZmqReqPush):
        return req.connected and bool(req.req_msg('volume'))

    def is_playing_markers(self):
        return self.start_mark_t <= self.start_video_at <= (self.end_mark_t if self.end_mark_t > 0 else (self.input_duration or 0))

    check_ffplay_process_timer = None
    check_timer_running = False
    def check_ffplay_process(self, window_title):
        next_delay = 100
        self.check_timer_running = True
        restart_ffplay = False
        try:
            if self.fflive_process:
                # fflive_process_ok = self.fflive_process_ok
                # self.fflive_process_ok = self.ping_window(self.fflive_zmq)
                # if fflive_process_ok != self.fflive_process_ok:
                #     self.update_play_text()

                if self.fflive_a_zmq.connected:
                    self.sync_audio_and_video()

                if self.check_if_process_finished(self.ffgac_process):
                    self.ffgac_process = None

                if self.check_if_process_finished(self.fflive_process):
                    self.kill_ffplay_processes(from_check_timer=True)
                    self.update_play_text()
                else:
                    end_mark_frame = (self.timeToframe(self.end_mark_t) if self.is_playing_markers() and self.end_mark_t != -1 else self.input_frames_count) or None
                    is_filter = self.selected_script and self.selected_script.is_filter
                    if self.is_playing:
                        end_detected = False
                        if not self.ffgac_process and not is_filter and\
                            (time.time() - self.last_progres_update_t) > .1 and\
                            end_mark_frame is not None and self.current_frame >= (end_mark_frame - 5):
                            print('No progress update for 0.1s. End of video detected.')
                            end_detected = True
                        elif is_filter and end_mark_frame is not None and self.current_frame >= (end_mark_frame - 2):
                            print('End marker detected.')
                            end_detected = True

                        if end_detected:
                            if not self.is_recording and not self.is_paused:
                                restart_ffplay = True
                            self.is_playing = False
                            self.is_paused = True
                            self.update_play_text()
                    self.check_ffplay_process_timer = self.after(next_delay, self.check_ffplay_process, window_title)

            if self.check_if_process_finished(self.ffgac_process):
                show_warning('Error while opening the video file. Check if the file is valid.')
                self.ffgac_process = None

            if self.fflive_a_zmq.connected and self.fflive_a_process and self.check_if_process_finished(self.fflive_a_process):
                self.fflive_a_process = None
                self.fflive_a_zmq.disconnect()
                self.update_mute_checkbutton()
        finally:
            self.check_timer_running = False
            if restart_ffplay:
                self.start_ffplay(start_paused=False)

    def stop_check_timer(self):
        if self.check_ffplay_process_timer:
            self.after_cancel(self.check_ffplay_process_timer)
            self.check_ffplay_process_timer = None

        while self.check_timer_running:
            self.gui_event_loop()
            time.sleep(0.05)

    def update_audio_time(self):
        t = time.time()
        audio_diff = (t - self.last_audio_time_check) if not self.is_paused_audio else 0
        self.last_audio_time_check = t
        updated_audio_time = audio_diff * self.audio_speed
        self.audio_time += updated_audio_time

    def sync_audio_and_video(self):
        try:
            def restart_audio(new_audio_speed, new_time):
                self.last_audio_restart_time = t
                self.audio_speed = max(0.5, new_audio_speed)
                self.ffgac_a_process.kill()
                self.fflive_a_process.kill()
                new_temp = f'atempo={self.audio_speed:.3f}'
                def change_param(cmd, param, new_value):
                    cmd[cmd.index(param) + 1] = str(new_value)
                change_param(self.fflive_a_process.command, '-af', new_temp)
                change_param(self.fflive_a_process.command, '-volume', '100' if not self.is_mute else '0')
                if '-start_paused' in self.fflive_a_process.command:
                    self.fflive_a_process.command.remove('-start_paused')
                self.audio_time = new_time
                change_param(self.ffgac_a_process.command, '-ss', self.audio_time)
                self.ffgac_a_process.start()
                self.fflive_a_process.start(stdin=self.ffgac_a_process.process.stdout)
                self.is_paused_audio = False
                print(f'Restart audio speed: {self.audio_speed:.3f}, time: {self.audio_time:.3f}')

            self.update_audio_time()
            t = time.time()
            if self.fps >= 0 and self.input_fps:
                diff = t - self.last_progres_update_t
                time_video = (self.current_frame + diff * self.fps) / self.input_fps
            elif self.input_fps:
                time_video = self.current_frame / self.input_fps
            else:
                time_video = 0
            time_audio = self.audio_time
            diff = time_audio - time_video
                    # print(f'Audio time: {time_audio:.3f}, Video time: {time_video:.3f}, Diff: {diff:.3f}')
            if self.fps > 0:
                new_audio_speed = min(MAX_SPEED, max(0.1, self.fps / self.input_fps))
                if diff > 0.5:
                    if new_audio_speed < self.audio_speed and self.audio_speed > 0.5 and t - self.last_audio_restart_time > 1:
                        restart_audio(new_audio_speed, time_video + 0.1)
                    elif not self.is_paused_audio:
                        if self.fflive_a_zmq.req_msg('pause'):
                            self.is_paused_audio = True
                            print('Pause audio')
                        else:
                            print_error('Error pausing audio')
                elif diff < -1 or (diff < -0.3 and new_audio_speed < self.audio_speed + 0.1): # Restart audio if it's too far behind
                    restart_audio(new_audio_speed, time_video)
                elif diff < -0.1:
                    if self.is_paused_audio:
                        if self.fflive_a_zmq.req_msg('play'):
                            self.is_paused_audio = False
                            print('Play audio')
                        else:
                            print_error('Error 1 playing audio')
            self.update_audio_time()
        except TimeoutError:
            pass
        except Exception as e:
            print('Error check_ffplay_process:', e)
            traceback.print_exc()

    def check_if_process_finished(self, process: Process):
        if process and process.process.poll() is not None:
            if process.returncode != 0:
                print_error(f'{process.name} finished itself, retcode:', process.returncode)

            if process and process == self.ffgac_process: # Detect if input file is invalid
                if process.returncode != 0:
                    process.check_pipes(wait_before_t=0.1)
                    self.console_error(f'Error while opening {self.video_path}. Check if the file is valid.')
                    for line in self.ffgac_lines:
                        self.console_log(f'{line}')
                    self.ffgac_lines = []
                else:
                    if self.current_time() + 5 < self.input_duration:
                        self.console_warn('Video finished too early. Check if the file is valid.')

            return True
        return False

    icons_cache = {}
    def get_icon(self, name='play'):
        if name in self.icons_cache:
            return self.icons_cache[name]
        path = os.path.join(os.path.dirname(__file__), f'gui/icons/{name}.png')
        img = tk.PhotoImage(file=normalize_path(path))
        self.icons_cache[name] = img
        return img

    def update_play_text(self):
        text = ''
        icon = self.get_icon('play') if (self.is_paused or not self.is_playing)  else self.get_icon('pause')
        self.w.button_play.configure(image=icon)
        button_state = tk.NORMAL
        if not self.selected_script or not self.video_path:
            button_state = tk.DISABLED
        self.w.button_record.configure(state=button_state)
        self.w.button_play_script.configure(state=button_state)
        self.w.button_edit_script.configure(state=button_state)


        if self.is_recording:
            self.w.scale_speed.configure(state=tk.DISABLED, takefocus=False, cursor='X_cursor')
            self.w.scale_progress.configure(state=tk.DISABLED, takefocus=False, cursor='X_cursor')
            text = 'Stop'
            if not self.is_playing:
                text = 'Stop...'
            if self.waiting_for_ffgac_rec:
                text = 'Force stop'
            self.w.button_record.configure(text=text)
        else:
            state = tk.NORMAL if self.last_input_duration is not None else tk.DISABLED
            self.w.scale_speed.configure(state=state, takefocus=True, cursor='')
            self.w.scale_progress.configure(state=state, takefocus=True, cursor='')
            self.w.button_record.configure(text='Record')

        # Disable buttons when recording
        for button in [self.w.button_open_project, self.w.button_select_video, self.w.button_select_output, self.w.button_play_script, self.w.button_restart_video, self.w.button_save_as_project,
                       self.w.button_seek_back_10s, self.w.button_seek_back_2s, self.w.button_seek_back_10f, self.w.button_seek_1f, self.w.button_seek_2s, self.w.button_seek_10s
                    ]:
            button.configure(state=tk.NORMAL if not self.is_recording else tk.DISABLED)


    def formatSeconds(self, seconds, frame=None):
        ms = (seconds - int(seconds)) * 100
        ret = time.strftime('%H:%M:%S', time.gmtime(seconds)) + f'.{int(ms):02d}'
        if frame is not None:
            ret += f' ({frame})'
        return ret

    last_progres_update_t = 0
    first_fps_calc_t = 0
    next_fps_check_t = time.time()
    fps = -1
    last_current_frame = 0

    def check_fps(self, from_timer=False):
        t = time.time()

        fps_cnt = self.current_frame - self.last_current_frame
        self.last_current_frame = self.current_frame

        if t - self.last_progres_update_t > 1 or self.is_paused or not self.is_playing:
            self.fps = -1
            self.first_fps_calc_t = None
        else:
            if self.fps >= 0:
                self.fps = fps_cnt * 0.8 + self.fps * 0.2
            elif self.first_fps_calc_t and (t - self.first_fps_calc_t) > 0.3:
                self.fps = fps_cnt / (t - self.first_fps_calc_t)

        formatted_fps = 'FPS: ' + (f'{self.fps:.1f}' if self.fps >= 0 else '-')
        self.w.label_fps.configure(text=formatted_fps)
        if self.fps >= 0:
            print(formatted_fps)

        while self.next_fps_check_t < t + 0.5:
            self.next_fps_check_t += 1
        if from_timer:
            self.after(round((self.next_fps_check_t - time.time()) * 1000), self.check_fps, from_timer)

    def on_frame_progress(self, frame_no):
        timeS = self.frameToTime(frame_no)
        if timeS > self.input_duration:
            return
        self.last_progres_update_t = time.time()
        self.current_frame = frame_no
        # Update progress scale
        if not self.is_recording:
            self.set_progress_widget(self.current_frame)

        if not self.first_fps_calc_t:
            self.first_fps_calc_t = time.time()

        if self.played_frames == 0:
            if self.fflive_a_zmq.connected:
                if self.fflive_a_zmq.req_msg('play'):
                    self.is_paused_audio = False
                else:
                    print_error('Error 2 playing audio')
        self.played_frames += 1

    def set_progress_widget(self, frame_no = None):
        if frame_no is None:
            frame_no = self.current_frame
        timeS = self.frameToTime(frame_no)
        if self.input_frames_count and frame_no is not None and not self.progress_changing:
            self.w.label_progress.configure(text=self.formatSeconds(timeS, frame_no))
            state = tk.NORMAL if 'disabled' not in self.w.scale_progress.state() else tk.DISABLED
            self.w.scale_progress.configure(state=tk.NORMAL)
            self.w.scale_progress.set(frame_no / self.input_frames_count)
            self.w.scale_progress.configure(state=state)

    def on_frame_progress_ffgac(self, current_frame):
        self.current_frame_ffgac = current_frame

    def on_frame_progress_ffgac_rec(self, current_frame):
        self.current_frame_ffgac_rec = current_frame
        self.set_progress_widget(current_frame)

    def timeToframe(self, timeS):
        if self.input_fps is None:
            return None
        return round(timeS * self.input_fps)

    def frameToTime(self, frame):
        return ((frame) / self.input_fps) if self.input_fps else 0

    def current_time(self):
        return self.frameToTime(self.current_frame)

    def on_progress_changing(self, value):
        if 'disabled' in self.w.scale_progress.state():
            return
        if self.progress_changing and self.input_duration:
            seconds = float(value) * self.input_duration
            frame = self.timeToframe(seconds)
            if self.input_frames_count > 0:
                frame = min(frame, self.input_frames_count - 1)
            self.requested_frame = frame
            self.w.label_progress.configure(text=self.formatSeconds(seconds, frame))

    def on_progress_change(self, _mouse_event):
        if 'disabled' in self.w.scale_progress.state():
            return
        self.progress_changing = False
        if self.input_duration:
            pos = self.w.scale_progress.get()
            self.start_ffplay(start_at_sec=pos * self.input_duration, start_paused=self.is_paused)

    def on_progress_motion(self, event):
        if 'disabled' in self.w.scale_progress.state():
            return
        if self.progress_changing:
            scale = self.w.scale_progress.get(event.x, 0)
            self.w.scale_progress.set(scale)

    def on_progress_press(self, _event):
        if 'disabled' in self.w.scale_progress.state():
            return
        self.progress_changing = True
        self.on_progress_motion(_event)

    def on_console(self, lines: List[Line]):
        lines1: List[Line] = []
        for process_line in lines:
            line = process_line.line
            if line and not 'Duration: N/A' in line:
                if 'FRAME_NO:' in line: # FRAME_NO: 123
                    try:
                        frame = int(line.split('FRAME_NO:')[1].split(' ')[1])
                        if self.input_frames_count:
                            # '-blockffplaykeys' block unpause by space
                            # Check if unpaused by user in fflive
                            # if self.is_paused and time.time() - self.pause_time > 2:
                            #     print('Unpaused by user detected')
                            #     self.is_paused = False
                            #     self.fflive_start_paused = False
                            #     self.update_play_text()
                            if not self.is_paused:
                                current_frame = frame + self.timeToframe(self.start_video_at)
                                self.on_frame_progress(current_frame)
                    except ValueError as e:
                        print('Error parsing frame:', e)
                    except Exception as e:
                        print('Error on_frame_progress:', e)
                        traceback.print_exc()
                    finally:
                        continue
                if 'fd=' in line and 'aq=' in line:
                    continue
                # Remove '@ 000001447944fd80' from '[quickjs @ 0x000001447944fd80] ...' lines with regex
                elif '[quickjs' in line:
                    line = self.remove_hex_address(line)
                    idx = line.find(']')
                    msg = line[idx + 1:].strip()
                    if not msg:
                        continue

                    if 'No MIDI ports. Falling back to ZMQ midi eumulation on:' in msg:
                        self.midi_zmq.connect_url = msg.split(' ')[-1].strip()
                        if self.midi_zmq.connect_url:
                            self.midi_zmq.connect()
                            if self.midi_zmq.connected:
                                self.show_midi_piano()

                if line:
                    # When vf_script is used, ffgac is not running
                    # Process duration from fflive
                    if not self.ffgac_process:
                        self.ffgac_lines = []
                        self.on_ffgac_console([process_line])
                        if len(self.ffgac_lines) == 0:
                            continue

                    process_line.line = line
                    lines1.append(process_line)

        for line in lines1:
            self.console_log(line.line, timestamp=line.timestamp)

    def show_midi_piano(self, show=True, in_ms=0):
        if show and (self.piano is None or self.piano.is_destroyed()):
            top = tk.Toplevel(self.root)
            self.piano = MidiPiano(top, bg_color=self.top_background)
            self.piano.set_on_message_cb(lambda msg: self.midi_zmq.req_msg(str(msg)) if self.midi_zmq.connected else None)
            self.fix_labels_font(top)

        if self.piano:
            self.piano.show(show, in_ms)

    def remove_hex_address(self, line):
        line = re.sub(r' ?@ ?(0x)?[0-9a-fA-F]{8,}', '', line) # [libx264 @ 000001a44c6d0840] => [libx264]
        return line

    ffgac_lines = []
    def on_ffgac_console(self, lines: List[Line]):
        _duration_line = 'Duration: 00:00:26.00, start: 0.040000, bitrate: 3933 kb/s'
        _stream = 'Stream #0:0[0x1](und): Video: h264 (High) (avc1 / 0x31637661), yuv420p(progressive), 1920x1080 [SAR 1:1 DAR 16:9], 3930 kb/s, 25 fps, 25 tbr, 12800 tbn (default)'
        _stat = 'frame=  118 fps= 25 q=0.0 size=    3547KiB time=00:00:05.04 bitrate=5764.8kbits/s speed=1.09x'

        def calc_frames_count():
            self.input_duration = self.input_duration or self.input_duration_alt
            try:
                alt_duration = self.input_duration_alt
                if abs(alt_duration / self.input_duration - 1) < 0.1 and alt_duration != self.input_duration:
                    self.input_duration = alt_duration
                    calc_frames_count()
            except Exception:
                pass
            self.last_input_duration = self.input_duration
            if self.input_duration and self.input_fps:
                self.input_frames_count = int(self.input_duration * self.input_fps)
                try:
                    if abs(self.input_frames_count / self.input_frames_count_alt - 1) < 0.1:
                        self.input_frames_count = self.input_frames_count_alt
                        new_fps = self.input_frames_count / self.input_duration
                        self.input_fps = new_fps
                except Exception:
                    pass
                self.project_changed()
                self.place_start_end_mark()
                print(f'Video duration: {self.input_duration:.2f} sec, FPS: {self.input_fps:.2f}, Frames: {self.input_frames_count}')
                self.w.label_total_time.configure(text=self.formatSeconds(self.input_duration))

        for process_line in lines:
            line = process_line.line
            try:
                if not line:
                    pass
                elif 'Duration:' in line:
                    duration = line.split('Duration:')[1].split(', ')[0]
                    input_duration = sum(x * float(t) for x, t in zip([3600, 60, 1], duration.split(':')))
                    if self.input_duration != input_duration:
                        self.input_duration = input_duration
                        calc_frames_count()
                        self.update_play_text()
                elif 'Video:' in line and 'fps' in line:
                    fps = line.split('fps,')[0].split(',')[-1].strip()
                    if self.input_fps != float(fps):
                        self.input_fps = float(fps)
                        calc_frames_count()
                elif 'DURATION' in line:
                    try:
                        duration = line.split('DURATION')[1].split(':', maxsplit=1)[1].strip().split(' ', maxsplit=1)[0]
                        self.input_duration_alt = sum(x * float(t) for x, t in zip([3600, 60, 1], duration.split(':')))
                        calc_frames_count()
                    except Exception:
                        pass
                elif 'NUMBER_OF_FRAMES' in line:
                    try:
                        self.input_frames_count_alt = int(line.split('NUMBER_OF_FRAMES')[1].strip().split(':')[1].strip().split(' ')[0])
                        calc_frames_count()
                    except Exception:
                        pass
                elif 'frame=' in line:
                    frame = int(line.split('frame=')[1].strip().split(' ')[0])
                    if self.input_frames_count:
                        current_frame = frame + self.timeToframe(self.start_video_at)
                        self.on_frame_progress_ffgac(current_frame)
                else:
                    line = self.remove_hex_address(line)
                    self.ffgac_lines.append(line)
                # self.console_log(f'FFGAC: {line}')
            except Exception as e:
                print('Error on_ffgac_console:', e)
                traceback.print_exc()

    def on_ffgac_rec_console(self, lines: List[Line]):
        for process_line in lines:
            line = process_line.line
            try:
                line = self.remove_hex_address(line)
                if 'frame=' in line:
                    try:
                        frame = int(line.split('frame=')[1].strip().split(' ')[0])
                        if self.input_frames_count:
                            current_frame = frame + self.timeToframe(self.start_video_at)
                            self.on_frame_progress_ffgac_rec(current_frame)
                    except ValueError:
                        pass
            except Exception as e:
                print('Error on_ffgac_rec_console:', e)
                traceback.print_exc()

            if 'slice end not reached but screenspace end' in line or 'corrupt decoded frame' in line:
                continue
            process_line.line = line
            self.console_log(process_line.line, timestamp=process_line.timestamp)

    def on_play(self):
        if self.selected_script and not self.selected_script.buildin:
            self.editor.save()

        self.update_audio_time()
        if self.is_paused:
            if self.is_playing:
                if not self.send_ffplay_pause_toggle(False):
                    print_error('Error unpausing video')
                    return
            else:
                current_time = self.current_time()
                self.start_ffplay(start_at_sec=current_time if current_time <= (self.input_duration - 2 / self.input_fps) else 0)
            self.is_paused = False
            self.is_paused_audio = False
        elif self.is_playing:
            self.pause_play()
        else:
            self.start_ffplay()
        self.update_play_text()

    def pause_play(self):
        if self.send_ffplay_pause_toggle(True):
            self.is_paused = True
            self.is_paused_audio = True
            self.pause_time = time.time()
            self.check_fps()
            self.update_play_text()
        else:
            print_error('Error pausing video')

    def on_play_script(self):
        if self.selected_script and not self.selected_script.buildin:
            self.editor.save()
        self.start_ffplay()

    def on_record(self):
        if not self.output_path and not self.on_select_output():
            return

        if self.is_recording:
            self.kill_ffplay_processes(force=self.waiting_for_ffgac_rec)
        else:
            current_time = self.current_time()
            self.start_ffplay(recording=True, start_at_sec=current_time if current_time < (self.input_duration - 2 / self.input_fps) else 0)

    def seek_video(self, seconds):
        if self.input_fps and seconds == 1 / self.input_fps and self.is_playing:
            if not self.is_paused:
                self.pause_play()
            if self.fflive_zmq.req_msg('step'):
                self.pause_time = time.time()
                self.current_frame = min(self.current_frame + 1, self.input_frames_count - 1)
                self.set_progress_widget(self.current_frame)
            else:
                print_error('Error stepping video')
        elif seconds:
            startS = self.frameToTime(self.current_frame) + seconds
            self.start_ffplay(start_at_sec=startS, start_paused=self.is_paused)

    start_mark_t = -1
    end_mark_t = -1
    def on_start_mark(self):
        self.start_mark_t = self.frameToTime(self.current_frame)
        self.place_start_end_mark()
        self.start_ffplay(start_at_sec=self.start_mark_t)

    def on_end_mark(self):
        if self.current_frame < self.input_frames_count - 2:
            self.end_mark_t = self.frameToTime(self.current_frame)
        else:
            self.end_mark_t = -1
        self.place_start_end_mark()
        self.start_ffplay(start_at_sec=self.start_mark_t)

    def place_start_end_mark(self):
        y = self.w.canvas_end_mark.place_info().get('y', 0)
        if y == 0:
            return

        input_duration = self.last_input_duration or parse_float(self.project['Project']['video_duration'], 0)
        progress = (self.start_mark_t / input_duration) if (input_duration and self.start_mark_t >= 0) else 0
        progress_info = self.w.scale_progress.place_info()
        x = int(progress_info.get('x', 0)) + (int(progress_info.get('width', 0)) - 5) * progress + 2
        self.w.canvas_start_mark.place(x=x, y=y)

        progress = self.end_mark_t / input_duration if (input_duration and self.end_mark_t >= 0) else 1
        x = int(progress_info.get('x', 0)) + (int(progress_info.get('width', 0)) - 5) * progress + 2
        self.w.canvas_end_mark.place(x=x, y=y)

    def get_bin(self, bin_name):
        platform = 'win' if IS_WIN else 'mac' if IS_MAC else 'linux'
        bin_dir = f'bin/ffglitch/{platform}' if not self.is_app_packed else f'{self.this_dir}/ffglitch'
        return normalize_path(os.path.join(bin_dir, bin_name + ('.exe' if IS_WIN else '')))


    def start_ffplay(self, start_at_sec=None, recording=False, start_paused=False):
        if not self.video_path:
            show_info('Please select a video file')
            return

        if self.is_recording:
            print_error('Already recording')
            traceback.print_stack()
            return

        if self.starting_ffplay:
            print_warn('Already starting ffplay')
            return

        if self.selected_script and self.selected_script.type == Script.Type.HELPER:
            return

        if start_at_sec is None:
            start_at_sec = max(0, self.start_mark_t) if self.is_playing_markers() else 0

        try:
            start_at_sec = max(0, start_at_sec)
            if self.input_duration:
                start_at_sec = min(start_at_sec, self.input_duration - 2 / self.input_fps)

            start_frame =  self.timeToframe(start_at_sec) if self.input_fps else 0
            print(f'Start at: {start_at_sec:.2f} sec, {start_frame} frame, paused: {start_paused}, recording: {recording}')

            if start_paused and self.input_duration:
                self.on_frame_progress(start_frame)

            self.starting_ffplay = True
            self.kill_ffplay_processes()
            self.console_clear()
            self.start_video_at = start_at_sec
            self.current_frame_ffgac = 0
            self.current_frame_ffgac_rec = None
            self.played_frames = 0
            self.input_duration = None
            self.input_frames_count = 0
            self.progress_changing = False

            video_file = self.video_path
            if not os.path.exists(video_file):
                show_info(f'Video not found {video_file}')
                raise FileNotFoundError(f'Video file not found: {video_file}')

            if self.start_video_at == 0:
                self.w.scale_progress.set(0)

            self.current_frame = start_frame
            self.last_current_frame = start_frame

            self.is_playing = True
            self.is_paused = start_paused
            self.is_paused_audio = True
            self.pause_time = time.time() if start_paused else 0
            self.is_recording = recording
            self.fflive_start_paused = start_paused
            self.update_play_text()


            play_markers = self.is_playing_markers()

            # Encode input file to mpeg4 raw video stream
            ffgac_command = [
                self.get_bin('ffgac'),
                # '-readrate', f'{self.get_speed() * 1.1:.4f}', # Transcode at 1.1x speed
                '-accurate_seek',
                '-ss', str(self.start_video_at),
                *(['-to', str(self.end_mark_t)] if play_markers and self.end_mark_t > 0 else []),
                # '-re', # Realtime
                # '-nostats',
                '-stats',
                '-hide_banner',
                '-i', video_file,
                '-an', # No audio
                '-mpv_flags', '+nopimb+forcemv', '-qscale:v', '0', '-g', 'max', '-sc_threshold', 'max', '-vcodec', 'mpeg4',
                # '-vf', 'scale=1280:720',
                '-f', 'rawvideo',
                '-' # Output to stdout
            ]

            # For audio playing process (acurate_seek not workign in fflive)
            ffgac_a_command = [
                self.get_bin('ffgac'),
                # '-readrate', f'{10 * 1.1:.4f}',
                '-accurate_seek',
                '-ss', str(self.start_video_at),
                '-nostats',
                '-hide_banner',
                '-i', video_file,
                '-mpv_flags', '+nopimb+forcemv', '-qscale:v', '0', '-g', 'max', '-sc_threshold', 'max', '-vcodec', 'mpeg4',
                '-vf', 'scale=2:2', # Scale to 2x2 pixels
                '-f', 'nut', # 'nut' container format
                '-' # Output to stdout
            ]


            # Display the video stream in a window
            window_title = f'{NAME} preview:  {os.path.basename(video_file)}'
            speed_ratio = f"{1 / self.get_speed():.4f}"
            self.fflive_speed_scale = 1 / float(speed_ratio)
            enable_audio = self.fflive_speed_scale >= 0.5

            fflive_command = [
                self.get_bin('fflive'),
                '-i', '-',
                '-vf', f"setpts=({speed_ratio})*PTS", # Change speed of the video
                '-af', f'atempo={self.fflive_speed_scale}',
                # '-vf', "setpts=(0)*PTS", # Set max playback speed
                '-stats',
                # '-nostats',
                '-window_title', f"{window_title}",
                '-hide_banner',
                '-flush_packets', '0',
                '-sync', 'audio', # avoid frame dropping on slow frame processing

                # Custom settings
                '-print_frameno', # Print frame number to console
                '-blockffplaykeys', # Block all ffplay original hotkeys
                '-frame_counter_off', str(start_frame), # ffglitch script frame counter offset
                '-noframedropearly', # Don't drop frames when cpu is too slow
                '-zmq_url', self.fflive_zmq.bind_url, # ZMQ bind url for REQ/REP connection
                # '-vf', 'showinfo',
                # '-fflags', 'nobuffer', '-avioflags', 'direct',
            ]

            if self.selected_script and self.selected_script.is_filter:
                idx = fflive_command.index('-vf')
                fflive_command.pop(idx) # Remove default filter. It will be replaced by the filter script
                fflive_command.pop(idx)

            try:
                w = int(self.last_video_size.split('x')[0])
                h = int(self.last_video_size.split('x')[1])
                if w > 0 and h > 0:
                    fflive_command.extend(['-x', str(w), '-y', str(h)])
            except Exception:
                pass

            fflive_a_command = [
                self.get_bin('fflive'),
                '-af', f'atempo={self.fflive_speed_scale}',
                '-vn',
                '-nostats',
                '-nodisp',
                '-sync', 'audio', # avoid frame dropping on slow frame processing
                '-window_title', f"{window_title} audio",
                '-volume', '100' if not self.is_mute else '0',
                '-hide_banner',
                '-start_paused', # unpause on first received frame
                '-zmq_url', self.fflive_a_zmq.bind_url,
                '-',
            ]
            self.audio_speed = self.fflive_speed_scale

            if start_paused:
                fflive_command.extend(['-start_paused'])

            if self.selected_script and self.selected_script.path:
                if self.selected_script.is_filter:
                    path = normalize_path(self.selected_script.path)
                    if IS_WIN:
                        path = normalize_path(find_relative_path(self.cwd, self.selected_script.path))
                    fflive_command.extend(['-vf', f'script=file={path}'])
                else:
                    fflive_command.extend(['-s', self.selected_script.path])
                script_parameters = self.w.entry_script_parameters.get()
                if script_parameters:
                    fflive_command.extend(['-sp', script_parameters])

            if recording:
                if os.path.exists(self.output_path):
                    os.remove(self.output_path)
                fflive_command.extend(['-o', '-', '-autoexit'])
                fflive_a_command.extend(['-autoexit'])


            # Recording, pack the video and audio streams into a container
            frac = None
            if recording:
                try:
                    frac = find_fraction(self.input_fps)
                    frac = f'{frac.numerator}/{frac.denominator}'
                    print('Setting fractional fps:', frac)
                except Exception as e:
                    print('find_fraction error:', e)
            ffgac_rec_command = [
                self.get_bin('ffgac'),
                *(['-r', frac or f'{self.input_fps:.6f}'] if frac or self.input_fps else []),
                '-i', '-', # Video
                '-ss', str(self.start_video_at), # Sync adutio to video
                '-i', video_file, # Copy audio from the original video
                '-map', '0:v',
                '-map', '1:a?',
                '-c:a', 'copy',
                # '-c:v', 'copy',
                '-c:v', 'libx264',
                '-preset', 'medium', # ultrafast superfast veryfast faster fast medium slow slower veryslow placebo
                '-crf', '18', # Set quality to 18, 0 is lossless 51 is worst
                '-shortest', # Stop encoding when the shortest stream ends
                *(['-t', str(self.end_mark_t - self.start_video_at)] if play_markers and self.end_mark_t > 0 else []),
                '-loglevel', 'info',
                '-hide_banner',
                self.output_path
            ]

            try:
                x, y = self.config['Main']['video_pos'].split(',')
                x, y = int(x), int(y)
                if x >= 0 and y >= 0:
                    if self.fflive_window_borders[0] != 0:
                        x += self.fflive_window_borders[0]
                    if self.fflive_window_borders[1] != 0:
                        y += self.fflive_window_borders[1]
                    fflive_command.extend(['-left', str(x), '-top', str(y)])
            except Exception:
                pass

            env_vars = self.get_env_vars()
            env_vars['AV_LOG_FORCE_NOCOLOR'] = '1'
            if enable_audio:
                self.ffgac_a_process = Process('ffgac', ffgac_a_command,
                                               stdout=Process.Pipe.PIPE, stderr=Process.Pipe.DEVNULL,
                                               env=env_vars)

            if not self.selected_script or self.selected_script.path:
                self.ffgac_process = Process('ffgac', ffgac_command, stdout=Process.Pipe.PIPE,
                                                stderr=self.on_ffgac_console,
                                                # stderr=Process.Pipe.STDOUT,
                                                env=env_vars,
                                                after=self.after, after_cancel=self.after_cancel)
            env_vars = self.get_env_vars()
            env_vars['AV_LOG_FORCE_COLOR'] = '1'
            env_vars['TERM'] = '1'
            env_vars.pop('AV_LOG_FORCE_256COLOR', None) # Disable 256 color output
            if self.ffgac_a_process:
                self.fflive_a_process = Process('fflive1', fflive_a_command, stdin=self.ffgac_a_process.process.stdout,
                                                # stdout=Process.Pipe.STDOUT, stderr=Process.Pipe.STDOUT,
                                                stdout=Process.Pipe.DEVNULL, stderr=Process.Pipe.DEVNULL,
                                                env=env_vars)
                self.last_audio_restart_time = time.time()
                self.audio_restart_time_off = 0
                self.update_audio_time()
                self.audio_time = self.start_video_at
                self.last_audio_time_check = time.time()
                self.fflive_a_zmq.connect()
            else:
                self.fflive_a_zmq.disconnect()
            self.update_mute_checkbutton()

            self.fflive_process = Process('fflive', fflive_command, stdin=self.ffgac_process.process.stdout if self.ffgac_process else None,
                                            stdout=self.on_console if not recording else Process.Pipe.PIPE,
                                            stderr=self.on_console,
                                            # stdout=Process.Pipe.STDOUT, stderr=Process.Pipe.STDOUT,
                                            env=env_vars,
                                            after=self.after, after_cancel=self.after_cancel)
                                            # stderr=subprocess.DEVNULL)
            self.fflive_zmq.connect()

            self.fps = -1
            self.first_fps_calc_t = None

            if recording:
                self.ffgac_rec_process = Process('ffgac_rec', ffgac_rec_command, stdin=self.fflive_process.process.stdout,
                                                stderr=self.on_ffgac_rec_console,
                                                # stderr=Process.Pipe.STDOUT,
                                                after=self.after, after_cancel=self.after_cancel,
                                                env=env_vars,
                                                binary_mode=False,
                                                idle_priority=True,
                                            )

            # Install timer that polls for the fflive process to detect if it's still running
            self.fflive_window_title = window_title
            self.check_ffplay_process_timer = self.after(500, self.check_ffplay_process, window_title)

        except Exception as e:
            print('start_ffplay error:', e)
            if not isinstance(e, FileNotFoundError):
                traceback.print_exc()
            self.is_playing = False
            self.is_recording = False
            self.is_paused = False
            self.is_paused_audio = False
            self.kill_ffplay_processes()
            self.update_play_text()

        finally:
            self.starting_ffplay = False

    # def stream_output_to_fflive(self, output_file, window_title):
    #     # Read the the pipe self.r_fd and write it to self.w_fd2
    #     if self.r_fd and self.w_fd2:
    #         try:
    #             eof = False
    #             data = os.read(self.r_fd, 1024 * 1024)
    #             if data:
    #                 self.streamed_bytes += len(data)
    #                 os.write(self.w_fd2, data)
    #                 os.fsync(self.w_fd2)
    #                 # Append data to the output file
    #                 with open(output_file, 'ab') as f:
    #                     f.write(data)
    #                 print('Streamed:', len(data))
    #             else:
    #                 eof = True
    #                 print('EOF')
    #             if not eof:
    #                 self.after(10, self.stream_output_to_fflive, output_file, window_title)
    #         except Exception as e:
    #             print('Error1:', e)

    def send_ffplay_pause_toggle(self, pause=False):
        ret = True
        if self.fflive_zmq.connected:
            ret = ret and self.fflive_zmq.req_msg('pause' if pause else 'play')
        else:
            print_warn('fflive_zmq not connected')
            ret = False

        if self.fflive_a_zmq.connected:
            ret = ret and self.fflive_a_zmq.req_msg('pause' if pause else 'play')
        else:
            print_warn('fflive_a_zmq not connected')

        return ret

    def get_env_vars(self):
        exe_dir = os.path.dirname(self.get_bin('fflive'))
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = exe_dir + (":" + env["LD_LIBRARY_PATH"] if "LD_LIBRARY_PATH" in env else "")
        env['DYLD_LIBRARY_PATH'] = exe_dir + (":" + env["DYLD_LIBRARY_PATH"] if "DYLD_LIBRARY_PATH" in env else "")
        return env

    # Measure fflive window borders for acurate window positioning
    def test_window_borders_size(self):
        window_title = f'{NAME} Test window'
        start_pos = 200, 200
        fflive_zmq = ZmqReqPush(ctx=self.zmq_context, name='fflive_test')
        fflive_zmq.generate_urls()
        fflive_command = [
            self.get_bin('fflive'),
            '-f', 'lavfi', '-i', 'nullsrc=s=300x10',
            '-vf', 'drawbox=c=white:t=fill', # Set video color to black
            '-window_title', f"{window_title}",
            '-left', f'{start_pos[0]}',
            '-top', f'{start_pos[1]}',
            '-zmq_url', fflive_zmq.bind_url,
        ]

        env_vars = self.get_env_vars()
        fflive_process = Process('fflive', fflive_command, stdout=Process.Pipe.DEVNULL, stderr=Process.Pipe.DEVNULL, env=env_vars)
        if IS_MAC:
            time.sleep(1)
        fflive_zmq.connect()

        prev_pos = None
        timeout_t = time.time() + 3
        while time.time() < timeout_t:
            pos = None
            video_x, video_y, _video_w, _video_h = self.get_video_win_pos_size(fflive_zmq)
            if video_x is not None:
                pos = video_x, video_y

            if pos:
                pos = pos[0], pos[1]
                if prev_pos and pos == prev_pos:
                    self.fflive_window_borders = start_pos[0] - pos[0], start_pos[1] - pos[1]
                    print('Window borders:', self.fflive_window_borders)
                    if abs(self.fflive_window_borders[0]) > 5:
                        print('Window x border too big. Setting to 0')
                        self.fflive_window_borders = None, None
                    break
                prev_pos = pos

            time.sleep(0.01)

            if fflive_process.process.poll() is not None:
                print('fflive process finished itself with retcode:', fflive_process.returncode)
                break

        if time.time() >= timeout_t:
            print('Window test timeout')

        fflive_process.kill()

    # def embed_ffplay_window(self):
    #     if os.name == 'nt':  # Windows
    #         win32gui.SetParent(self.ffplay_window_id, self.video_frame.winfo_id())
    #         win32gui.SetWindowLong(self.ffplay_window_id, win32con.GWL_STYLE, win32con.WS_VISIBLE)
    #         win32gui.MoveWindow(self.ffplay_window_id, 0, 0, self.video_frame.winfo_width(), self.video_frame.winfo_height(), True)


    def kill_ffplay_processes(self, force=False, from_check_timer=False):
        try:
            self.show_midi_piano(False, 500)
            if not from_check_timer:
                self.stop_check_timer()

            if self.fflive_process:
                try:
                    self.update_config() # Save ffplay window position
                except Exception as e:
                    print('Error saving config:', e)
            if self.fflive_process:
                self.fflive_process.kill()
                self.fflive_process = None
            self.fflive_zmq.disconnect()

            if self.ffgac_process:
                self.ffgac_process.kill()
                self.ffgac_process = None

            if self.fflive_a_process:
                self.fflive_a_process.kill()
                self.fflive_a_process = None
            self.fflive_a_zmq.disconnect()

            if self.ffgac_a_process:
                self.ffgac_a_process.kill()
                self.ffgac_a_process = None

            if self.ffgac_rec_process:
                self.is_playing = False
                self.update_play_text()

                ret = None
                if not force:
                    # Wait for the encoding process to finish before killing it
                    start_t = time.time()
                    printed_waiting = False
                    while self.ffgac_rec_process and self.ffgac_rec_process.process.poll() is None and time.time() - start_t < 100:
                        self.ffgac_rec_process.check_pipes()
                        if not printed_waiting and time.time() - start_t > 2:
                            self.console_log('Waiting for recording to finish...')
                            self.waiting_for_ffgac_rec = True
                            self.update_play_text()
                            printed_waiting = True
                        time.sleep(0.01)
                        self.gui_event_loop()

                    if self.ffgac_rec_process:
                        ret = self.ffgac_rec_process.returncode
                        if ret == 0:
                            self.console_log('Recording finished: ' + self.output_path)
                        elif ret != 0:
                            self.console_log(f'{self.ffgac_rec_process.name} process finished with retcode: {ret}')
                            print(f'{self.ffgac_rec_process.name} process finished with retcode:', ret)
                        else:
                            self.console_log('Recording did not finish in 10 sec. Killing...')
                            print(f'Killing {self.ffgac_rec_process.name} process')

                if self.ffgac_rec_process and ret is None:
                    print('Sending SIGTERM to recording process...')
                    self.ffgac_rec_process.process.send_signal(signal.SIGTERM)
                    try:
                        print('Waiting for recording process to finish...')
                        ret = self.ffgac_rec_process.process.wait(5)
                        print('Recording process finished with retcode:', ret)
                    except subprocess.TimeoutExpired:
                        print('Recording process did not finish in 5 sec. Killing...')
                    self.ffgac_rec_process.kill()

                self.ffgac_rec_process = None
                if ret != 0:
                    self.console_log('Recording stopped')
        finally:
            if self.is_recording:
                self.update_output_path()
                if self.current_frame_ffgac_rec:
                    self.current_frame = self.current_frame_ffgac_rec
                    self.set_progress_widget()
            self.is_playing = False
            self.is_paused = self.is_recording
            self.is_paused_audio = self.is_recording
            self.is_recording = False
            self.waiting_for_ffgac_rec = False
            self.update_play_text()

    def gui_event_loop(self):
        self.root.update()

    def on_script_select(self, _event, skip_play_on_same_selection=False):
        prev_selected_script = self.selected_script
        if prev_selected_script and not prev_selected_script.buildin:
            self.editor.save()
        selected_index = self.w.listbox_scripts.curselection()
        select_idx = None
        if selected_index and self.listbox_scripts[selected_index[0]]:
            script_file_name = self.listbox_scripts[selected_index[0]].path
            self.select_script(script_file_name)
            if self.selected_script:
                select_idx = selected_index[0]
                if not self.is_recording and not (prev_selected_script == self.selected_script and skip_play_on_same_selection):
                    self.start_ffplay()
        else:
            self.select_script()
            if not self.is_recording:
                self.kill_ffplay_processes()

        self.w.listbox_scripts.select_clear(0, tk.END)
        if select_idx is not None:
            self.w.listbox_scripts.selection_set(select_idx)

    def on_speed_change(self, *_args):
        if not 'disabled' in self.w.scale_speed.state():
            self.start_ffplay(start_at_sec=self.current_time())

    def audio_enabled(self):
        return self.fflive_a_zmq.connected and self.fflive_a_process

    def on_speed_changing(self, *_args):
        self.w.label_speed.configure(text=f'{self.get_speed():.1f}x')
        self.update_mute_checkbutton()

    def update_mute_checkbutton(self):
        audio_enabled = self.audio_enabled() and self.get_speed() >= 0.5
        self.w.checkbutton_mute.configure(state=tk.NORMAL if audio_enabled else tk.DISABLED)

    def get_speed(self):
        speed = self.w.scale_speed.get()
        exp_speed = MIN_SPEED + (MAX_SPEED - MIN_SPEED) * (speed ** 2) / (MAX_SPEED ** 2)
        return float(f'{(exp_speed):.1f}')

    def lin_speed_to_exp(self, speed):
        return MAX_SPEED * ((speed - MIN_SPEED) / (MAX_SPEED - MIN_SPEED)) ** 0.5

    def on_reset_speed(self, *_args):
        def reset_speed():
            self.w.scale_speed.set(self.lin_speed_to_exp(1))
            self.restart_ffplay()
        if not 'disabled' in self.w.scale_speed.state():
            self.after(100, reset_speed)

    def on_open_project(self, *_args):
        # Open a project configuration file
        file_path = filedialog.askopenfilename(filetypes=[(f'{NAME} files', f'*{PROJECT_EXT}')])
        if file_path:
            if self.open_project(file_path):
                self.config['Main']['last_project_file'] = file_path
                self.save_config()

    def on_save_as_project(self, *_args):
        file_path = filedialog.asksaveasfilename(defaultextension=PROJECT_EXT, filetypes=[(f'{NAME} files', f'*{PROJECT_EXT}')])
        if file_path:
            self.save_project(file_path)
            return True
        return False


    def on_select_video(self, *_args):
        file_path = filedialog.askopenfilename(filetypes=[
            ('Video files', ['.mp4','.avi','.mov', '.mkv', '.flv', '.webm', '.m4v', '.wmv', '.mpg', '.mpeg',
                            '.m2ts', '.ts', '.vob', '.3gp', '.3g2', '.mts', '.m2v', '.mpv', '.mp2', '.raw']),
            ('All files','.*')
        ])
        file_path = fix_windows_network_path(file_path)
        if file_path:
            print('Selected video:', file_path)
            self.video_path = file_path
            self.input_fps = None
            self.input_duration = None
            self.w.entry_video_input.delete(0, tk.END)
            self.w.entry_video_input.insert(tk.END, os.path.basename(file_path))
            self.project_changed()
            self.kill_ffplay_processes()
            self.last_video_size = ''
            self.restart_ffplay()

    def on_select_output(self, *_args):
        # Open a file dialog to select a output video file
        file_path = filedialog.asksaveasfilename(defaultextension='.mp4', filetypes=[('Video files', '*.mp4')])
        file_path = fix_windows_network_path(file_path)
        if file_path:
            print('Selected output:', file_path)
            self.output_path_base = file_path
            self.update_output_path()
            self.project_changed()
        return file_path

    def on_script_save(self, _file_path):
        self.w.label_saving.configure(text='Saving...')
        self.after(1000, lambda: self.w.label_saving.configure(text=''))

    def on_edit_share_script(self):
        def find_imports(file_path):
            ret = []
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for line in lines:
                js_lib_re = r'from\s+["\'](.+?)["\']|import\s+["\'](.+?)["\']'
                js_path = re.search(js_lib_re, line)
                if js_path:
                    js_path = js_path.group(1) or js_path.group(2)
                    if js_path:
                        js_path = os.path.join(os.path.dirname(file_path), js_path)
                        if not js_path.endswith('.js') and not js_path.endswith('.mjs'):
                            js_path += '.js'
                        if os.path.exists(js_path):
                            ret.append(js_path)
            return ret

        edited_scripts_dir = self.resolve_relative_path(EDITED_SCRIPTS_DIR)
        if self.selected_script and self.selected_script.buildin:
            # Copy the buildin script to the edited scripts directory
            try:
                def to_edited_path(path):
                    dirs = normalize_path(path).split('/')
                    path = os.path.join(edited_scripts_dir, *(path.split('/')[dirs.index(SCRIPTS_DIR) + 1:]))
                    return normalize_path(os.path.abspath(path))
                path = to_edited_path(self.selected_script.path)
                path = find_next_output_file(path)
                if copy_file(self.selected_script.path, path, replace=False):
                    def find_recursive_js_imports_and_copy_them_too(file_path):
                        for js_path in find_imports(file_path):
                            dst_path = to_edited_path(js_path)
                            if copy_file(js_path, dst_path, replace=False):
                                print('Copied library to:', dst_path)
                                find_recursive_js_imports_and_copy_them_too(js_path)
                    print('Copied script:', path)
                    find_recursive_js_imports_and_copy_them_too(self.selected_script.path)
                    self.editor.close_file()
                    self.update_scripts_list()
                    self.select_script(path)
                    self.on_script_select(None)
                else:
                    print_error(f'Error copying script to {path}')
            except ValueError:
                pass
        elif self.selected_script and not self.selected_script.buildin:
            # Create a zip file with the script and all its imports
            try:
                self.editor.save()
                zip_path = os.path.splitext(self.selected_script.path)[0] + '.zip'
                zip_path = find_next_output_file(zip_path)
                if zip_path:
                    with zipfile.ZipFile(zip_path, 'w') as z:
                        def find_recursive_js_imports_and_add_them_too(file_path):
                            for js_path in find_imports(file_path):
                                z.write(js_path, os.path.relpath(js_path, edited_scripts_dir))
                                print('Added library to zip:', js_path)
                                find_recursive_js_imports_and_add_them_too(js_path)
                        z.write(self.selected_script.path, os.path.relpath(self.selected_script.path, edited_scripts_dir))
                        find_recursive_js_imports_and_add_them_too(self.selected_script.path)
                    print('Saved script as zip:', zip_path)
                    zip_name = os.path.basename(zip_path)
                    if messagebox.askokcancel('Share', f'Press OK to show bundled {zip_name} file and to open www browser.'):
                        open_explorer_and_select_file(zip_path)
                        self.open_url(f'{REPO_URL}/discussions/categories/show-and-tell')
            except ValueError:
                pass

    def on_clone_script(self):
        if not self.selected_script:
            return
        try:
            if not self.selected_script.buildin:
                self.editor.save()
            path = self.selected_script.path
            os.makedirs(self.resolve_relative_path(EDITED_SCRIPTS_DIR), exist_ok=True)
            with open(path, 'r', encoding='utf-8') as f:
                new_path = find_next_output_file(path, suffix='_copy')
                print('Cloning script:', path, 'to:', new_path)
                with open(new_path, 'w', encoding='utf-8') as f1:
                    f1.write(f.read())
                    print('Saved cloned script:', path)
                self.update_scripts_list()
                self.select_script(self.find_relative_path(new_path))
        except Exception as e:
            show_warning(f'Error cloning script: "{e}"')
            print('Error cloning script:', e)
            traceback.print_exc()

    def show_messagebox_with_input(self, title, message, default=''):
        root = tk.Tk()
        root.withdraw()
        result = simpledialog.askstring(title, message, initialvalue=default, parent=self.root)
        root.destroy()
        return result


    def on_rename_script(self):
        if not self.selected_script:
            return
        try:
            if not self.selected_script.buildin:
                self.editor.save()
            path = self.selected_script.path
            while True:
                new_path = self.show_messagebox_with_input('Rename', 'New name:', os.path.splitext(os.path.basename(path))[0])
                if not new_path:
                    break
                # filedialog.asksaveasfilename(initialfile=os.path.basename(path), initialdir=os.path.dirname(path),
                #                                         defaultextension=ext, filetypes=[('Moshers', ['*.js', '*.py'])])
                ext = os.path.splitext(path)[1]
                new_path = normalize_path(os.path.join(os.path.dirname(path), new_path + ext))
                if new_path:
                    if os.path.exists(new_path):
                        if not messagebox.askyesno('Rename mosher', f'"{os.path.basename(new_path)}" already exists. Overwrite?'):
                            continue
                        os.remove(new_path)
                    print('Renaming script:', path, 'to:', new_path)
                    os.rename(path, new_path)
                    self.update_scripts_list(select_script_path=new_path)
                    break
        except Exception as e:
            show_warning(f'Error renaming script: "{e}"')
            print('Error renaming script:', e)
            traceback.print_exc()

    def on_delete_script(self):
        if not self.selected_script:
            return
        try:
            if not self.selected_script.buildin:
                self.editor.save()
            path = self.selected_script.path
            print('Deleting script:', path)
            if os.path.exists(path):
                send2trash(os.path.abspath(path))
            self.update_scripts_list()
        except Exception as e:
            show_warning(f'Error deleting script: "{e}"')
            print('Error deleting script:', e)
            traceback.print_exc()

    def on_listbox_scripts_rmb(self, event):
        self.w.listbox_scripts.select_clear(0, tk.END)
        self.w.listbox_scripts.selection_set(self.w.listbox_scripts.nearest(event.y))
        self.on_script_select(event, skip_play_on_same_selection=True)
        if self.selected_script:
            self.listbox_scripts_menu = tk.Menu(self.w.listbox_scripts, tearoff=0)
            buildin = self.selected_script.buildin
            state = tk.DISABLED if buildin else tk.NORMAL
            self.listbox_scripts_menu.add_command(label='Clone', command=self.on_clone_script, state=state)
            self.listbox_scripts_menu.add_command(label='Rename', command=self.on_rename_script, state=state)
            self.listbox_scripts_menu.add_command(label='Delete', command=self.on_delete_script, state=state)

            state = tk.NORMAL if buildin else tk.DISABLED
            if buildin:
                self.listbox_scripts_menu.add_command(label='Edit', command=self.on_edit_share_script, state=state)
            self.listbox_scripts_menu.add_separator()
            self.listbox_scripts_menu.add_command(label='Reload list', command=self.update_scripts_list)
            self.listbox_scripts_menu.post(event.x_root, event.y_root)
            self.listbox_scripts_menu.bind("<Leave>", lambda e: self.listbox_scripts_menu.unpost())

    def get_example_mosher(self, no = 0):
        moshers = ['basic.js']
        file = os.path.join(self.this_dir, SCRIPTS_DIR, moshers[no])
        try:
            with open(file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as _e:
            return ''

def show_info(message):
    messagebox.showinfo('Info', message)

def show_warning(message):
    messagebox.showwarning('Warning', message)


if __name__ == '__main__':
    app = LiveMosherApp()
    start_up(app)

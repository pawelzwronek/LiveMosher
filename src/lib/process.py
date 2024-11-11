import os
import tkinter
import traceback
import subprocess
import sys
import threading
import queue
import time

from typing import Callable, Dict, List, Union

from enum import Enum
from lib.colored_print import print_error
from lib.misc import IS_WIN

if IS_WIN:
    import msvcrt
    import win32process
    from ctypes import windll, byref, wintypes, WinError, POINTER
    from ctypes.wintypes import HANDLE, DWORD, BOOL

class Line:
    line: Union[bytes, str]
    timestamp: float

    def __init__(self, line: bytes, timestamp: float):
        self.line = line
        self.timestamp = timestamp

class Process:
    class Pipe(Enum):
        PIPE = subprocess.PIPE
        STDOUT = subprocess.STDOUT
        DEVNULL = subprocess.DEVNULL
        STDERR = -10

        def to_subprocess(self):
            if self == self.STDOUT:
                return sys.stdout
            if self == self.STDERR:
                return sys.stderr
            if self == self.PIPE:
                return subprocess.PIPE
            if self == self.DEVNULL:
                return subprocess.DEVNULL
            raise ValueError(f"Invalid Pipe value: {self}")

    def __init__(self,
        name: str,
        command: List[str],
        stdin = None,
        stdout: Union[Pipe, Callable[[List[Line]], None]] = Pipe.STDOUT,
        stderr: Union[Pipe, Callable[[List[Line]], None]] = Pipe.STDOUT,
        after: tkinter.Misc.after = None,
        after_cancel: tkinter.Misc.after_cancel = None,
        env: Dict[str, str] = None,
        binary_mode: bool = False,
        idle_priority = False,
    ):
        self.name = name
        self.command = command
        self.process = None
        self.binary_mode = binary_mode
        self._after = after
        self._after_cancel = after_cancel
        self._stdin_in = stdin
        self._stdout_in = stdout
        self._stderr_in = stderr
        self.env = env
        self.idle_priority = idle_priority

        self.on_stdout = None
        self.on_stderr = None

        self.stdout_left_str = b''
        self.stderr_left_str = b''
        self.check_pipe_timer = None
        self.check_pipe_thread: threading.Thread = None

        self.stdout_queue: queue.Queue[Line] = None
        self.stderr_queue: queue.Queue[Line] = None

        self.start()


    def start(self, stdin = None):
        if stdin:
            self._stdin_in = stdin

        r_fd_out = None
        r_fd_err = None
        if isinstance(self._stdout_in, Callable):
            self.on_stdout = self._stdout_in
            if IS_WIN:
                r_fd_out, w_fd_out = os.pipe()
            else:
                w_fd_out = self.Pipe.PIPE.to_subprocess()
        else:
            self.r_out = None
            w_fd_out = self._stdout_in.to_subprocess()
        self._stdout_out = w_fd_out

        if isinstance(self._stderr_in, Callable):
            self.on_stderr = self._stderr_in
            if IS_WIN:
                r_fd_err, w_fd_err = os.pipe()
            else:
                w_fd_err = self.Pipe.PIPE.to_subprocess()
        else:
            self.r_err = None
            w_fd_err = self._stderr_in.to_subprocess()
        self._stderr_out = w_fd_err


        if IS_WIN:
            if self.on_stdout:
                self.r_out = r_fd_out
                set_pipe_non_blocking(self.r_out)
            if self.on_stderr:
                self.r_err = r_fd_err
                set_pipe_non_blocking(self.r_err)

        def set_idle_priority():
            os.nice(19) # pylint: disable=maybe-no-member

        print('Running:',  ' '.join(self.command))
        self.process = subprocess.Popen(self.command, # pylint: disable=subprocess-popen-preexec-fn
                                        stdin=self._stdin_in,
                                        stdout=self._stdout_out,
                                        stderr=self._stderr_out,
                                        env=self.env,
                                        preexec_fn=set_idle_priority if self.idle_priority and not IS_WIN else None,
                                    )
        if self.idle_priority and IS_WIN:
            win32process.SetPriorityClass(self.process._handle, win32process.IDLE_PRIORITY_CLASS) # pylint: disable=possibly-used-before-assignment,no-member, c-extension-no-member, protected-access

        if not IS_WIN:
            if self.on_stdout:
                self.r_out = self.process.stdout
                set_pipe_non_blocking(self.r_out)

            if self.on_stderr:
                self.r_err = self.process.stderr
                set_pipe_non_blocking(self.r_err)

        self.stdout_queue = queue.Queue()
        self.stderr_queue = queue.Queue()

        if self.on_stdout or self.on_stderr:
            self.check_pipe_thread = threading.Thread(target=self._pipes_reader)
            self.check_pipe_thread.daemon = True
            self.check_pipe_thread.start()
            self.check_pipe_timer = self._after(10, self._check_pipes_in_main_thread)


    def restart(self):
        self.kill()
        self.start()

    def kill(self, terminate=False):
        process = self.process
        self.process = None

        # Wait fot the check thread to finish
        if self.check_pipe_thread:
            try:
                self.check_pipe_thread.join(0.1)
                if self.check_pipe_thread.is_alive():
                    print_error(f'Error waiting for check_pipe_thread to finish for {self.name} process')
                self.check_pipe_thread = None
            except Exception as e: # pylint: disable=broad-except
                print_error(f'Error waiting for check_pipe_thread: "{e}" for {self.name} process')
                traceback.print_exc()

        for pipe in [self.r_out, self.r_err]:
            try:
                if pipe is not None:
                    if IS_WIN:
                        os.close(pipe)
                    else:
                        pipe.close()
            except OSError:
                print(f"Failed to close pipe {pipe} for {self.name} process")

        if process and process.poll() is None:
            try:
                if terminate:
                    process.terminate()
                else:
                    process.kill()
            except OSError:
                print(f"Failed to stop {self.name} process")
            finally:
                if self.check_pipe_timer:
                    try:
                        self._after_cancel(self.check_pipe_timer)
                        self.check_pipe_timer = None
                    except tkinter.TclError:
                        print(f"Failed to cancel check_pipe_timer for {self.name} process")


    def _check_pipes_in_main_thread(self):
        self.check_pipes()
        self.check_pipe_timer = self._after(50, self._check_pipes_in_main_thread)

    def check_pipes(self, wait_before_t=0):
        if wait_before_t:
            time.sleep(wait_before_t)
        stdout_data = self.on_stdout and self.get_stdout_data()
        if stdout_data:
            self.on_stdout(stdout_data)
        stderr_data = self.on_stderr and self.get_stderr_data()
        if stderr_data:
            self.on_stderr(stderr_data)

    def _read_pipes(self):
        stdout_lines: List[Line] = []
        stderr_lines: List[Line] = []

        def emit_line(line: bytes, pipe, timestamp):
            if pipe == self.r_out:
                out_lines = stdout_lines
                if self.stdout_left_str:
                    line = self.stdout_left_str + line
                    self.stdout_left_str = b''
            else:
                out_lines = stderr_lines
                if self.stderr_left_str:
                    line = self.stderr_left_str + line
                    self.stderr_left_str = b''

            lines = line.split(b'\r')
            if len(lines) > 1:
                out_lines.append(Line(lines[0], timestamp))
                for l in lines[1:]:
                    out_lines.append(Line(b'\r' + l, timestamp))
            else:
                out_lines.append(Line(line, timestamp))

        pipes = [p for p in [self.r_out, self.r_err] if p is not None]
        for pipe in pipes:
            try:
                if IS_WIN:
                    out = os.read(pipe, 1024 * 1024)
                else:
                    out = pipe.read(1024 * 1024)
                if not out:
                    continue
                out = out.replace(b'\r\n', b'\n')

                timestamp = time.time()
                lines = out.split(b'\n')
                for line in lines[:-1]:
                    emit_line(line, pipe, timestamp)
                left = lines[-1]

                if left:
                    if pipe == self.r_out:
                        self.stdout_left_str += left
                    else:
                        self.stderr_left_str += left

                if self.stdout_left_str:
                    lines = self.stdout_left_str.split(b'\r')
                    if len(lines) > 1:
                        stdout_lines.append(Line(lines[0], timestamp))
                        for l in lines[1:-1]:
                            stdout_lines.append(Line(b'\r' + l, timestamp))
                        self.stdout_left_str = lines[-1]

                if self.stderr_left_str:
                    lines = self.stderr_left_str.split(b'\r')
                    if len(lines) > 1:
                        stderr_lines.append(Line(lines[0], timestamp))
                        for l in lines[1:-1]:
                            stderr_lines.append(Line(b'\r' + l, timestamp))
                        self.stderr_left_str = lines[-1]

            except OSError:
                pass
            except ValueError:
                pass
            except Exception as e: # pylint: disable=broad-except
                print(f'Error check_pipe: "{e}" for {self.name} process')
                traceback.print_exc()

        for line in stdout_lines:
            if not self.binary_mode:
                line.line = line.line.decode('utf-8', errors='ignore')
            self.stdout_queue.put(line)

        for line in stderr_lines:
            if not self.binary_mode:
                line.line = line.line.decode('utf-8', errors='ignore')
            self.stderr_queue.put(line)

    def _pipes_reader(self):
        while self.process:
            self._read_pipes()
            time.sleep(0.01)

    def get_stdout_data(self):
        data = []
        while not self.stdout_queue.empty():
            data.append(self.stdout_queue.get())
        return data

    def get_stderr_data(self):
        data = []
        while not self.stderr_queue.empty():
            data.append(self.stderr_queue.get())
        return data


    @property
    def returncode(self):
        return self.process and self.process.returncode

def set_pipe_non_blocking(pipe):
    if 'set_blocking' in dir(os):
        os.set_blocking(pipe.fileno(), False) # pylint: disable=no-member
    else:
        if IS_WIN:
            LPDWORD = POINTER(DWORD)
            PIPE_NOWAIT = wintypes.DWORD(0x00000001)
            SetNamedPipeHandleState = windll.kernel32.SetNamedPipeHandleState
            SetNamedPipeHandleState.argtypes = [HANDLE, LPDWORD, LPDWORD, LPDWORD]
            SetNamedPipeHandleState.restype = BOOL

            h = msvcrt.get_osfhandle(pipe)

            res = windll.kernel32.SetNamedPipeHandleState(h, byref(PIPE_NOWAIT), None, None)
            if res == 0:
                print(WinError())
                return False
    return True


import os
import sys

IS_WIN = os.name == 'nt'
IS_MAC = sys.platform == 'darwin' and not IS_WIN
IS_LINUX = os.name == 'posix' and not IS_MAC

if not IS_WIN and not IS_LINUX and not IS_MAC:
    print(f'Unable to detect OS for platform: {sys.platform} and os.name: {os.name}')
    print('Setting to LINUX')
    IS_LINUX = True

if sys.version_info < (3, 8):
    print('Python 3.8 or higher is required')
    sys.exit(1)

# if IS_WIN or IS_LINUX:
#     import pywinctl

# if IS_WIN:
#     import win32api
#     import win32con
#     import win32gui

# import pyautogui

#pylint: disable=c-extension-no-member
#pylint: disable=broad-except

def find_relative_path(base_path, target_path):
    if not target_path:
        return ''
    if not os.path.isdir(base_path):
        base_path = os.path.dirname(base_path)
    try:
        return os.path.relpath(target_path, base_path)
    except ValueError:
        return target_path

def resolve_relative_path(base_path, relative_path):
    if os.path.isabs(relative_path):
        return relative_path
    if not relative_path:
        return ''
    if not os.path.isdir(base_path):
        base_path = os.path.dirname(base_path)
    return os.path.abspath(os.path.join(base_path, relative_path))

# class WindowPosSizeError(Exception):
#     pass

# def get_window_pos_size(hwnd = 0):
#     try:
#         if IS_WIN:
#             if isinstance(hwnd, int):
#                 try:
#                     frame = wintypes.RECT()
#                     dwmapi = ctypes.WinDLL("dwmapi")
#                     DWMWA_EXTENDED_FRAME_BOUNDS = 9
#                     ret = dwmapi.DwmGetWindowAttribute(hwnd, DWMWA_EXTENDED_FRAME_BOUNDS, ctypes.byref(frame), ctypes.sizeof(frame))
#                     if ret == 0:
#                         return frame.left, frame.top, frame.right - frame.left, frame.bottom - frame.top
#                     else:
#                         rect = win32gui.GetWindowRect(hwnd)
#                         return rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]
#                 except Exception as e:
#                     raise WindowPosSizeError(f'Error get_window_pos_size: {e}') from e
#             else:
#                 return hwnd.left, hwnd.top, hwnd.width, hwnd.height
#         elif IS_MAC:
#             return None, None, None, None
#         elif IS_LINUX:
#             return hwnd.left, hwnd.top, hwnd.width, hwnd.height
#         else:
#             raise NotImplementedError('Not implemented for this platform')
#     except WindowPosSizeError as e:
#         raise e
#     except Exception as e:
#         print('Error get_window_pos_size:', e)
#     return None, None, None, None

# def send_pos_size_request_signal(process):
#     '''Send SIGUSR1 signal to ffplay process to print window position and size to stderr'''
#     if process:
#         SIGUSR1 = getattr(signal, 'SIGUSR1', 10)
#         os.kill(process.pid, SIGUSR1) # pylint: disable=no-member

# def send_play_pause_toggle_signal(process):
#     '''Send SIGUSR2 signal to ffplay process to toggle play/pause'''
#     if process:
#         SIGUSR2 = getattr(signal, 'SIGUSR2', 12)
#         os.kill(process.pid, SIGUSR2) # pylint: disable=no-member


# def is_window_id_maximaized(window_id):
#     try:
#         if IS_WIN:
#             return win32gui.GetWindowPlacement(window_id)[1] == win32con.SW_MAXIMIZE
#         elif IS_LINUX:
#             return window_id.isMaximized
#         else:
#             raise NotImplementedError('Not implemented for this platform')
#     except Exception as e:
#         print('Error is_window_id_maximaized:', e)
#     return False


# def set_window_id_maximized(window_id, maximized):
#     try:
#         if IS_WIN:
#             win32gui.ShowWindow(window_id, win32con.SW_MAXIMIZE if maximized else win32con.SW_RESTORE)
#         elif IS_LINUX:
#             if maximized:
#                 window_id.maximize()
#             else:
#                 window_id.minimize()
#         else:
#             raise NotImplementedError('Not implemented for this platform')
#     except Exception as e:
#         print('Error set_window_id_maximized:', e)


# def get_window_hwnd(title='', force_pywinctl=False):
#     if IS_WIN and not force_pywinctl:
#         return win32gui.FindWindow(None, title)
#     if IS_MAC:
#         return None
#     try:
#         windows = pywinctl.getWindowsWithTitle(title) # pylint: disable=possibly-used-before-assignment
#         if windows:
#             if len(windows) > 1:
#                 print('Warning: More than one window with title:', title)
#             return windows[0]
#     except Exception as _e:
#         pass
#     return None

# def send_key_to_window(hwnd, key):
#     if IS_WIN:
#         win32gui.SetForegroundWindow(hwnd)
#         scanCode = win32api.MapVirtualKey(ord(key), 0)
#         win32api.keybd_event(ord(key), scanCode, 0, 0)
#         win32api.keybd_event(ord(key), scanCode, win32con.KEYEVENTF_KEYUP, 0)
#     elif IS_LINUX:
#         # hwnd.activate()
#         # pyautogui.press(key)
#         raise NotImplementedError('Not implemented for this platform')


# def set_video_win_pos_size(hwnd, x, y):
#     try:
#         if hwnd:
#             if IS_WIN:
#                 # Keep the same size
#                 _x, _y, w, h = get_window_pos_size(hwnd)
#                 win32gui.MoveWindow(hwnd, x, y, w, h, True)
#             elif IS_LINUX:
#                 hwnd.moveTo(x, y)
#             else:
#                 raise NotImplementedError('Not implemented for this platform')
#     except Exception as e:
#         print('Error set_video_win_pos_size:', e)


# def find_window_hwnd_for_current_process(title=''):
#     current_pid = os.getpid()
#     print('current_pid:', current_pid)
#     if IS_WIN:
#         ret = None
#         def callback(hwnd, _lparam):
#             nonlocal ret
#             pid = win32process.GetWindowThreadProcessId(hwnd)
#             if pid[1] == current_pid:
#                 window_title = win32gui.GetWindowText(hwnd)
#                 if title == window_title:
#                     sizepos = get_window_pos_size(hwnd)
#                     if sizepos[2] > 100 and sizepos[3] > 100:
#                         ret = hwnd
#                         return False
#             return True
#         try:
#             win32gui.EnumWindows(callback, None)
#         except Exception as _e:
#             pass
#         return ret
#     elif IS_MAC:
#         return None
#     elif IS_POSIX:
#         windows = pywinctl.getWindowsWithTitle(title)
#         print('windows:', windows)
#         if windows:
#             for window in windows:
#                 print('window.getPID():', window.getPID())
#                 if window.getPID() == current_pid:
#                     return window
#         return None
#     else:
#         raise NotImplementedError('Not implemented for this platform')

def normalize_path(path = ''):
    '''Normalize path and convert to forward slashes: /'''
    if not path:
        return path
    if path.startswith('\\\\'): # Windows network path
        return path[:2] + os.path.normpath(path[2:]).replace('\\', '/')
    return os.path.normpath(path).replace('\\', '/')

def find_next_output_file(output_path, suffix = '_'):
    if not output_path:
        return output_path
    if not os.path.exists(output_path):
        return output_path

    if not os.path.isabs(output_path):
        output_path = os.path.abspath(output_path)

    # Find max index
    base, ext = os.path.splitext(os.path.basename(output_path))
    base += suffix
    i = 1
    out_dir = os.path.dirname(output_path)
    all_files = os.listdir(out_dir)
    for file in all_files:
        if file.startswith(base):
            try:
                base1, _ = os.path.splitext(file)
                i1 = int(base1[len(base):])
                if i1 >= i:
                    i = i1 + 1
            except ValueError:
                pass
    return normalize_path(os.path.join(out_dir, base + str(i) + ext))

def path_replace_not_allowed_chars(path, replacement='_', keep_dirs=False):
    '''Replace not allowed characters in path with replacement'''
    illegal_chars = ['<','>',':','\\','/','|','?','*']
    if keep_dirs:
        illegal_chars.remove('/')
        illegal_chars.remove('\\')
    return ''.join([c if c not in illegal_chars else replacement for c in path])

def fix_windows_network_path(path):
    '''Fix windows network path'''
    if path and path.startswith('//'):
        path = '\\\\' + path[2:]
    return path

def copy_file(src, dst, replace = False):
    '''Copy file from src to dst. All directories in dst will be created if not exist.'''
    try:
        if not replace and os.path.exists(dst):
            return False

        with open(src, 'rb') as fsrc:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as fdst:
                fdst.write(fsrc.read())
        return True
    except Exception as e:
        print(f'Error copy_file: {e}')
    return False

def parse_float(value, default = 0.0):
    try:
        return float(value)
    except ValueError:
        return default

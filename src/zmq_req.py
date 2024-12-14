import os
import tempfile
import time
import socket
from enum import Enum

import zmq

from lib.colored_print import print_error, print_warn
from lib.misc import normalize_path

class ZmqReqMode(Enum):
    IPC = 1
    TCP = 2

class ZmqReqPush:
    def __init__(self, ctx: zmq.Context, name, wait_cb = None, mode = ZmqReqMode.IPC, port_file = None, is_push = False):
        self.name = name
        self.context = ctx
        self.wait_cb = wait_cb
        self.mode = mode
        self.ipc_port_file = port_file
        self.is_push = is_push

        if not self.test_loopback_ipc():
            print_warn('IPC is not supported, fallback to TCP')
            self.mode = ZmqReqMode.TCP

        self.socket: zmq.Socket = None
        self.connected = False
        self.soft_timeout = 500 / 1000

    def generate_urls(self):
        protocol = 'tcp' if self.mode == ZmqReqMode.TCP else 'ipc'

        if self.mode == ZmqReqMode.IPC:
            self.ipc_file_path = self.ipc_port_file
            if not self.ipc_file_path:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix=f'{self.name}_', suffix='.ipc') as file:
                    self.ipc_file_path = normalize_path(file.name)
                    file.write('')
            else:
                self.ipc_file_path = normalize_path(self.ipc_file_path)
                with open(self.ipc_file_path, 'w', encoding='utf-8') as file:
                    file.write('')
            self.bind_url = f'{protocol}://{self.ipc_file_path}'
            self.connect_url = self.bind_url
            self.url_basename = os.path.basename(self.ipc_file_path)
        elif self.mode == ZmqReqMode.TCP:
            port = self.ipc_port_file or 0
            if not port:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    port = s.getsockname()[1]
            self.bind_url = f'{protocol}://*:{port}'
            self.connect_url = f'{protocol}://localhost:{port}'
            self.url_basename = self.connect_url
        else:
            raise ValueError(f'Invalid mode: {self.mode}')

    def connect(self):
        self.reconnect()

    def reconnect(self):
        try:
            self.disconnect()
        except zmq.error.ZMQError as e:
            print_warn(f'Error on closing socket: {e}')
        try:
            self.socket = self.context.socket(zmq.REQ if not self.is_push else zmq.PUSH)
            self.socket.connect(self.connect_url)
            self.socket.setsockopt(zmq.RCVTIMEO, 50)
            self.socket.setsockopt(zmq.RECONNECT_IVL, 20)
            self.socket.setsockopt(zmq.RECONNECT_IVL_MAX, 200)
            # self.socket.setsockopt(zmq.SNDTIMEO, 50)
            self.connected = True
        except zmq.error.ZMQError as e:
            print_warn(f'Error on connecting to {self.url_basename}: {e}')
            self.connected = False

    def disconnect(self):
        if self.connected:
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.close()
            self.connected = False

    def close(self):
        self.disconnect()
        self.context.term()
        if self.mode == ZmqReqMode.IPC:
            self._remove_ipc_file()

    def req_msg(self, text = '', throw_timeout = False):
        _, msg = self.req(text, throw_timeout)
        return msg

    def req(self, text = '', throw_timeout = False):
        if not self.connected:
            raise ConnectionError(f'Not connected to {self.url_basename}')
        try:
            self.socket.send_string(text)
            if self.is_push:
                return None, None

            t = time.time()
            start_t = t
            end_t = t + self.soft_timeout
            msg = None
            while t < end_t:
                try:
                    if self.socket.poll(50, zmq.POLLIN):
                        msg = self.socket.recv().decode('utf-8', 'ignore')
                        elapsed = t - start_t
                        if elapsed > self.soft_timeout * 0.8:
                            print_warn(f'ZmqReq.send: "{text}" => "{msg}", {elapsed * 1000:.1f} ms')

                        try:
                            ret_num, ret_msg = msg.split(':', 1)
                            ret_num = int(ret_num)
                            return ret_num, ret_msg
                        except ValueError:
                            print_error(f'ZmqReq.send: Invalid return message: {msg}')
                            return None, None
                except zmq.error.Again:
                    if self.wait_cb is not None:
                        self.wait_cb()
                finally:
                    t = time.time()

            # print_error(f'ZMQ Timeout on sending {text} to {self.url_basename}')
            self.reconnect()
            if throw_timeout:
                raise TimeoutError(f'Timeout occurred on sending {text} to {self.url_basename}')
            # print(f'Send: {text}, Received: {msg}, Taken: {(time.time() - t) * 1e3:.3f} ms')
        except zmq.error.ZMQError as _e:
            # print_warn(f'ZMQ Error on sending "{text}" to {self.url_basename}: {_e}')
            pass
        return None, None

    def _remove_ipc_file(self):
        try:
            os.unlink(self.ipc_file_path)
        except FileNotFoundError:
            print_error(f'File not found: {self.ipc_file_path}')
        except Exception as e: #pylint: disable=broad-except
            print_error('ZmqReq._remove_ipc_file:', e)

    def test_loopback_ipc(self):
        ipc_file_path = ''
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False, prefix='test_', suffix='.ipc') as file:
                ipc_file_path = normalize_path(file.name)
                file.write('')
            bind_url = f'ipc://{ipc_file_path}'
            connect_url = bind_url
            with self.context.socket(zmq.REP) as s:
                s.bind(bind_url)
                with self.context.socket(zmq.REQ) as c:
                    c.connect(connect_url)
                    c.send_string('test')
                    msg = s.recv().decode('utf-8', 'ignore')
            return msg == 'test'
        except zmq.error.ZMQError as e:
            print_error('ZmqReq.test_loopback_ipc:', e)
            return False
        except Exception as e: #pylint: disable=broad-except
            print_error('ZmqReq.test_loopback_ipc:', e)
            return False
        finally:
            if ipc_file_path:
                try:
                    os.unlink(ipc_file_path)
                except FileNotFoundError:
                    pass

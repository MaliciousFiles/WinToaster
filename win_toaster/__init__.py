from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__all__ = ['ToastNotifier']

# #############################################################################
# ########## Libraries #############
# ##################################
# standard library
import threading
from os import path
from pkg_resources import Requirement
from pkg_resources import resource_filename
from time import sleep
from time import time
from winsound import SND_FILENAME
from winsound import PlaySound
from ctypes import windll
from ctypes import create_unicode_buffer
from pywintypes import error as WinTypesException
from uuid import uuid4

SystemParametersInfoW = windll.user32.SystemParametersInfoW
SPI_SETMESSAGEDURATION = 0x2017
SPI_GETMESSAGEDURATION = 0x2016
SPIF_SENDCHANGE = 0x2

# 3rd party modules
from win32api import GetModuleHandle
from win32api import PostQuitMessage
from win32con import CW_USEDEFAULT
from win32con import IDI_APPLICATION
from win32con import IMAGE_ICON
from win32con import LR_DEFAULTSIZE
from win32con import LR_LOADFROMFILE
from win32con import WM_USER
from win32con import WS_OVERLAPPED
from win32con import WS_SYSMENU
from win32gui import CreateWindow
from win32gui import DestroyWindow
from win32gui import LoadIcon
from win32gui import LoadImage
from win32gui import NIF_ICON
from win32gui import NIF_INFO
from win32gui import NIF_MESSAGE
from win32gui import NIF_TIP
from win32gui import NIM_ADD
from win32gui import NIM_DELETE
from win32gui import NIM_MODIFY
from win32gui import NIIF_NOSOUND
from win32gui import RegisterClass
from win32gui import UnregisterClass
from win32gui import Shell_NotifyIcon
from win32gui import UpdateWindow
from win32gui import WNDCLASS
from win32gui import PumpMessages

# Magic constants
PARAM_DESTROY = 1028
PARAM_CLICKED = 1029

# ############################################################################
# ########### Classes ##############
# ##################################


class ToastNotifier(object):
    """Create a Windows 10  toast notification.

    from: https://github.com/jithurjacob/Windows-10-Toast-Notifications
    """

    def __init__(self):
        """Initialize."""
        self._threads = []
        self._nextthread = None
        self._queueactive = False

    @staticmethod
    def _decorator(func, callback=None):
        """

        :param func: callable to decorate
        :param callback: callable to run on mouse click within notification window
        :return: callable
        """
        def inner(*args, **kwargs):
            kwargs.update({'callback': callback})
            func(*args, **kwargs)
        return inner

    def _show_toast(self, title, msg,
                    icon_path, delay,
                    sound_path, tooltip,
                    duration,
                    callback_on_click,
                    kill_without_click):
        """Notification settings.

        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :delay: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :duration: how long the notification stays on the screen in seconds
        :callback_on_click: function to run on click
        :kill_without_click: Kill the tray icon after the notification goes away, even if it wasn't clicked
        """
        self.delay = delay
        self.destroy_window = kill_without_click
        
        # Register the window class.
        self.wc = WNDCLASS()
        self.hinst = self.wc.hInstance = GetModuleHandle(None)
        self.wc.lpszClassName = str(f"PythonTaskbar - {uuid4().hex}")  # must be a string
        self.wc.lpfnWndProc = self._decorator(self.wnd_proc, callback_on_click)  # could instead specify simple mapping
        try:
            self.classAtom = RegisterClass(self.wc)
        except Exception as e:
            raise type(e)(f"Some trouble with classAtom:\n{e}") from None
        style = WS_OVERLAPPED | WS_SYSMENU
        self.hwnd = CreateWindow(self.classAtom, "Python Taskbar", style,
                                 0, 0, CW_USEDEFAULT,
                                 CW_USEDEFAULT,
                                 0, 0, self.hinst, None)
        UpdateWindow(self.hwnd)

        # icon
        if icon_path is not None:
            icon_path = path.realpath(icon_path)
        else:
            icon_path = resource_filename(Requirement.parse("win10toast"), "win10toast/data/python.ico")
        icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
        try:
            hicon = LoadImage(self.hinst, icon_path,
                              IMAGE_ICON, 0, 0, icon_flags)
        except Exception as e:
            raise type(e)(f"Some trouble with the icon ({icon_path}):\n{e}") from None
            hicon = LoadIcon(0, IDI_APPLICATION)

        # set the duration
        buff = create_unicode_buffer(10)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)
        try:
            oldlength = int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            oldlength = 5 # default notification length
            
        durationOutput=SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, duration, SPIF_SENDCHANGE)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)

        durationError=False
        try:
            int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            durationError=True
        if durationOutput == 0 or duration > 255 or durationError: 
            SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)
            raise RuntimeError(f"Some trouble with the duration ({duration}): Invalid duration length")

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, WM_USER + 20, hicon, tooltip)

        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO,
                                      WM_USER + 20,
                                      hicon, tooltip, msg, 0,
                                      title, 0 if sound_path == None else NIIF_NOSOUND))

        # play the custom sound
        if sound_path is not None:
            sound_path = path.realpath(sound_path)
            if not path.exists(sound_path):
                raise IOError("Some trouble with the sound file ({sound_path}): [Errno 2] No such file")

            try:
                PlaySound(sound_path, SND_FILENAME)
            except Exception as e:
                raise type(e)(f"Some trouble with the sound file ({sound_path}): {e}") from None
                
        PumpMessages()
        # put the notification duration back to normal
        SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)

        # take a rest then destroy
        if self.delay is not None and self.destroy_window:
            while self.delay > 0:
                sleep(0.1)
                self.delay -= 0.1
                
            DestroyWindow(self.hwnd)
            UnregisterClass(self.wc.lpszClassName, self.hinst)
            try: # sometimes the tray icon sticks around until you click it - this should stop it
                self.remove_window(self.hwnd)
            except WinTypesException:
                pass
        return

    def show_toast(self, title="Notification", msg="Here comes the message",
                icon_path=None, delay=0, sound_path=None, tooltip="Tooltip",
                threaded=False, skip_queue=False, duration=5,
                callback_on_click=None, kill_without_click=True):
        """Notification settings.

        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :delay: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :threaded: queues the notification to run without stopping the entire script
        :skip_queue: only takes effect if :threaded: is True; puts the notification to the top of the queue
        :duration: how long the notification stays on the screen in seconds
        :callback_on_click: function to run on click of the notification or tray icon
        :kill_without_click: Kill the tray icon after the notification goes away, even if it wasn't clicked
        """
        if not threaded:
            self._show_toast(title, msg, icon_path, delay, sound_path, tooltip, duration, callback_on_click, kill_without_click)
            return self.hwnd # for inputing into remove_window
        else:
            thread=threading.Thread(target=self._show_toast, args=(
                    title, msg, icon_path, delay, sound_path, tooltip, duration, callback_on_click, kill_without_click
                ))
            if not skip_queue:
                self._threads.append(thread)
            else:
                self._nextthread = thread
                
            if not self._queueactive:
                threading.Thread(target=self._run_queue).start()

    def _run_queue(self):
        self._queueactive = True

        while True:
            if self._nextthread == None:
                try:
                    try:
                        self._threads[0].start()
                        
                        while self._threads[0].is_alive():
                            pass
                    except RuntimeError:
                        pass
                    
                    self._threads.pop(0)
                except IndexError:
                    break
            else:
                try:
                    self._nextthread.start()
                    while self._nextthread.is_alive():
                        pass
                except RuntimeError:
                    pass

                self._nextthread = None

        self._queueactive = False
            
    def notification_active(self):
        """See if we have an active notification showing"""
        if self._nextthread.is_alive() or any(list(map(lambda x:x.is_alive(), self._threads))):
            # We have an active notification, let us finish we don't spam them
            return True
        return False

    def wnd_proc(self, hwnd, msg, wparam, lparam, **kwargs):
        """Messages handler method"""
        if lparam == PARAM_CLICKED:
            # make it stop on click
            self.delay = None if self.delay == None else 0
            self.destroy_window = True

            # callback goes here
            if kwargs.get('callback'):
                kwargs.pop('callback')()
            self.on_destroy(hwnd, msg, wparam, lparam)
        elif lparam == PARAM_DESTROY:
            self.on_destroy(hwnd, msg, wparam, lparam)

    def on_destroy(self, hwnd, msg, wparam, lparam):
        """Clean after notification ended."""
        if self.delay != None and self.destroy_window:
            self.remove_window(hwnd)
        PostQuitMessage(0)

        return None

    def remove_window(self, hwnd): # for removing a tray icon if it wasn't destroyed automatically
        nid = (hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)

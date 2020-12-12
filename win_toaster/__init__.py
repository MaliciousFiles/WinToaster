__all__ = ["create_toast", "Toast"]

# Standard library
from threading import Thread
from os import path
from pkg_resources import Requirement
from pkg_resources import resource_filename
from winsound import SND_FILENAME
from winsound import PlaySound
from ctypes import windll
from ctypes import create_unicode_buffer
from pywintypes import error as WinTypesException
from random import randint
from uuid import uuid4

# 3rd party modules (win32 by Microsoft, transfered from C++ into Python)
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
SystemParametersInfoW = windll.user32.SystemParametersInfoW
SPI_SETMESSAGEDURATION = 0x2017
SPI_GETMESSAGEDURATION = 0x2016
SPIF_SENDCHANGE = 0x2
PARAM_DESTROY = 0x404
PARAM_CLICKED = 0x405
MOUSE_UP = 0x202

def create_toast(title="Title", msg="Message", icon_path=None, delay=0,
               sound_path=None, tooltip="Tooltip", threaded=False,
               duration=5, callback_on_click=None, kill_without_click=True):
        """
        Returns a Toast class created from given parameters
        
        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :delay: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :duration: how long the notification stays on the screen in seconds
        :callback_on_click: function to run on click
        :kill_without_click: Kill the tray icon after the notification goes away, even if it wasn't clicked
        """
        return Toast(title, msg, icon_path,delay, sound_path, tooltip,
                     threaded, duration, callback_on_click, kill_without_click)
    

class Toast():
    """A class representing a Windows 10 toast notification"""
    
    def __init__(self, title, msg, icon_path, delay,
                 sound_path, tooltip, threaded, duration,
                 callback_on_click, kill_without_click):
        """
        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :delay: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :duration: how long the notification stays on the screen in seconds
        :callback_on_click: function to run on click
        :kill_without_click: Kill the tray icon after the notification goes away, even if it wasn't clicked
        """
        self.active = False
        self.thread = None
        self.calledback = False
        
        self.title = title
        self.msg = msg
        self.icon_path = icon_path
        self.delay = delay
        self.sound_path = sound_path
        self.tooltip = tooltip
        self.threaded = threaded
        self.duration = duration
        self.callback_on_click = callback_on_click
        self.kill_without_click = kill_without_click

    def is_alive():
        """Returns True if the toast is currently being shown"""
        return self.active or (self.thread and self.thread.is_alive())

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

    def wnd_proc(self, hwnd, msg, wparam, lparam, **kwargs):
        """Messages handler method"""
        if lparam == PARAM_CLICKED or lparam == MOUSE_UP:
            # make it stop on click
            self.delay = 0 if self.delay != None else None
            self.destroy_window = True

            # callback goes here
            if kwargs.get('callback') and not self.calledback:
                kwargs.pop('callback')()
                self.calledback = True
        if lparam == MOUSE_UP or lparam == PARAM_CLICKED or lparam == PARAM_DESTROY:
            if self.delay != None and self.destroy_window:
                try:
                    Shell_NotifyIcon(NIM_DELETE, (self.hwnd, 0))
                except WinTypesException:
                    pass
                PostQuitMessage()

    def display(self):
        if self.threaded:
            self.thread = Thread(target=self._show_toast)
            self.thread.start()
        else:
            self._show_toast()
        

    def _show_toast(self):
        """Displays the toast using the information from creation."""

        self.active = True        
        self.destroy_window = self.kill_without_click
        
        # Register the window class
        self.wc = WNDCLASS()
        self.hinst = self.wc.hInstance = GetModuleHandle(None)
        self.wc.lpszClassName = f"PythonTaskbar - {uuid4().hex}"
        self.wc.lpfnWndProc = self._decorator(self.wnd_proc, self.callback_on_click) # Could instead specify simple mapping

        try:
            self.classAtom = RegisterClass(self.wc)
        except Exception as e:
            self.active = False
            raise type(e)(f"Some trouble with classAtom:\n{e}") from None

        style = WS_OVERLAPPED | WS_SYSMENU
        self.hwnd = CreateWindow(self.classAtom, "Python Taskbar - {uuid4().hex}", style, 0, 0,
                                 CW_USEDEFAULT, CW_USEDEFAULT, 0, 0, self.hinst, None)

        UpdateWindow(self.hwnd)

        if self.icon_path is not None:
            icon_path = path.realpath(self.icon_path)
        else:
            # This won't work until it is an official PyPA Module
            #icon_path = resource_filename(Requirement.parse("win_toaster"),
            #                              "win_toaster/data/python.ico")
            icon_path = path.realpath("data/python.ico") # Temporary fix
        icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
        try:
            hicon = LoadImage(self.hinst, icon_path, IMAGE_ICON, 0, 0, icon_flags)
        except Exception as e:
            hicon = LoadIcon(0, IDI_APPLICATION)
            self.active = False
            raise type(e)(f"Some trouble with the icon ({icon_path}):\n{e}") from None

        # Set the duration
        buff = create_unicode_buffer(10)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)
        try:
            oldlength = int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            oldlength = 5 # Default notification length

        durationOutput=SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, self.duration, SPIF_SENDCHANGE)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)

        durationError = False
        try:
            int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            durationError = True

        if durationOutput == 0 or self.duration > 255 or durationError:
            SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)
            self.Active = False
            raise RuntimeError(f"Some trouble with the turation ({duration}): Invalid duration length")

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, WM_USER + 20, hicon, self.tooltip)

        # Make it so that it won't replace another
        # notification with the same title and message
        title = self.title
        for x in range(randint(0, 63-len(self.title))):
            title += " "

        message = self.msg
        for x in range(randint(0, 128-len(self.msg))):
            message += " "

        # Add tray icon and queue message
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO,
                                      WM_USER + 20,
                                      hicon, self.tooltip, message, 0,
                                      title, NIIF_NOSOUND if self.sound_path else 0))

        # Play the custom sound
        if self.sound_path is not None:
            sound_path = path.realpath(self.sound_path)
            if not path.exists(sound_path):
                self.active = False
                raise IOError("Some trouble with the sound file ({sound_path}): [Errno 2] No such file")

            try:
                PlaySound(sound_path, SND_FILENAME)
            except Exception as e:
                self.active = False
                raise type(e)(f"Some trouble with the sound file ({sound_path}): {e}") from None

        # Show the message
        PumpMessages()
        # Put the notification duration back to normal
        SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)

        # Take a rest then destroy
        if self.delay is not None and self.destroy_window:
            while self.delay > 0:
                sleep(0.1)
                self.delay -= 0.1

            DestroyWindow(self.hwnd)
            UnregisterClass(self.wc.lpszClassName, self.hinst)
            try: # Sometimes the try icon sticks around until you click it - this should stop that
                Shell_NotifyIcon(NIM_DELETE, (self.hwnd, 0))
            except WinTypesException:
                pass
        self.active = False

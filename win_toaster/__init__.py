__all__ = ["create_toast", "Toast"]

# Standard library
from threading import Thread
from time import sleep
from os import path
from winsound import PlaySound
from winsound import SND_FILENAME
from ctypes import windll
from ctypes import create_unicode_buffer
from random import randint
from uuid import uuid4
from pkg_resources import Requirement
from pkg_resources import resource_filename
from pywintypes import error as WinTypesException

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
    :kill_without_click: Kill the tray icon after the notification goes away,
                         even if it wasn't clicked
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
        :kill_without_click: Kill the tray icon after the notification goes away,
                             even if it wasn't clicked
        """
        
        self.active = False
        self.thread = None
        self.calledback = False
        self.destroy_window = kill_without_click

        self.toast_data = {"wnd_class": None, "hinst": None,
                                  "class_atom": None, "hwnd": None,
                                  "title": title, "msg": msg, "icon_path": icon_path,
                                  "delay": delay, "sound_path": sound_path,
                                  "tooltip": tooltip, "threaded": threaded,
                                  "duration": duration,
                                  "callback_on_click": callback_on_click,
                                  "kill_without_click": kill_without_click}
        
    def is_alive(self):
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
        
        if lparam in (PARAM_CLICKED, MOUSE_UP):
            # make it stop on click
            self.toast_data["delay"] = 0 if self.toast_data["delay"] is not None else None
            self.destroy_window = True

            # callback goes here
            if kwargs.get('callback') and not self.calledback:
                kwargs.pop('callback')()
                self.calledback = True
        if lparam in (MOUSE_UP, PARAM_CLICKED, PARAM_DESTROY):
            if self.toast_data["delay"] is not None and self.destroy_window:
                try:
                    Shell_NotifyIcon(NIM_DELETE, (hwnd, 0))
                except WinTypesException:
                    pass
                PostQuitMessage()

    def display(self):
        """Display the toast using the information from creation"""
        
        if self.toast_data["threaded"]:
            self.thread = Thread(target=self._show_toast)
            self.thread.start()
        else:
            self._show_toast()
        

    def _show_toast(self):
        """Displays the toast using the information from creation"""

        self.active = True        
        self.destroy_window = self.toast_data["kill_without_click"]
        
        # Register the window class
        self.toast_data["wnd_class"] = WNDCLASS()
        self.toast_data["hinst"] = self.toast_data["wnd_class"].hInstance = GetModuleHandle(None)
        self.toast_data["wnd_class"].lpszClassName = f"PythonTaskbar - {uuid4().hex}"
        self.toast_data["wnd_class"].lpfnWndProc = self._decorator(
            self.wnd_proc, self.toast_data["callback_on_click"])

        try:
            self.toast_data["class_atom"] = RegisterClass(self.toast_data["wnd_class"])
        except Exception as exception:
            self.active = False
            raise type(exception)(f"Some trouble with class_atom:\n{exception}") from None

        style = WS_OVERLAPPED | WS_SYSMENU
        self.toast_data["hwnd"] = CreateWindow(self.toast_data["class_atom"],
                                               "Python Taskbar - {uuid4().hex}", style, 0, 0,
                                               CW_USEDEFAULT, CW_USEDEFAULT, 0, 0,
                                               self.toast_data["hinst"], None)

        UpdateWindow(self.toast_data["hwnd"])

        if self.toast_data["icon_path"] is not None:
            icon_path = path.realpath(self.toast_data["icon_path"])
        else:
            # This won't work until it is an official PyPA Module
            #icon_path = resource_filename(Requirement.parse("win_toaster"),
            #                              "win_toaster/data/python.ico")
            icon_path = resource_filename(Requirement.parse("WinToaster"),
                                          "win_toaster/data/python.ico") # Temporary fix
        icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE
        try:
            hicon = LoadImage(self.toast_data["hinst"], icon_path, IMAGE_ICON, 0, 0, icon_flags)
        except Exception as exception:
            hicon = LoadIcon(0, IDI_APPLICATION)
            self.active = False
            raise type(exception)(f"""Some trouble with the icon ({icon_path}):
{exception}""") from None

        # Set the duration
        buff = create_unicode_buffer(10)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)
        try:
            oldlength = int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            oldlength = 5 # Default notification length

        duration_output=SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0,
                                             self.toast_data["duration"],SPIF_SENDCHANGE)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)

        duration_error = False
        try:
            int(buff.value.encode('unicode_escape').decode().replace("\\", "0"), 16)
        except ValueError:
            duration_error = True

        if duration_output == 0 or self.toast_data["duration"] > 255 or duration_error:
            SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)
            self.active = False
            raise RuntimeError(f"Some trouble with the duration ({self.toast_data['duration']}):\
 Invalid duration length")

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.toast_data["hwnd"], 0, flags, WM_USER + 20, hicon, self.toast_data["tooltip"])

        # Make it so that it won't replace another
        # notification with the same title and message
        title = self.toast_data["title"] + " " * randint(0, 63-len(self.toast_data["title"]))
        message = self.toast_data["msg"] + " " * randint(0, 128-len(self.toast_data["msg"]))

        # Add tray icon and queue message
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(NIM_MODIFY, (self.toast_data["hwnd"], 0, NIF_INFO,
                                      WM_USER + 20,
                                      hicon, self.toast_data["tooltip"], message, 0,
                                      title, NIIF_NOSOUND if self.toast_data["sound_path"] else 0))

        # Play the custom sound
        if self.toast_data["sound_path"] is not None:
            sound_path = path.realpath(self.toast_data["sound_path"])
            if not path.exists(sound_path):
                self.active = False
                raise IOError("Some trouble with the sound file ({sound_path}):\
 [Errno 2] No such file")

            try:
                PlaySound(sound_path, SND_FILENAME)
            except Exception as exception:
                self.active = False
                raise type(exception)(f"""Some trouble with the sound file ({sound_path}):
{exception}""") from None

        # Show the message
        PumpMessages()
        # Put the notification duration back to normal
        SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)

        # Take a rest then destroy
        if self.toast_data["delay"] is not None and self.destroy_window:
            while self.toast_data["delay"] > 0:
                sleep(0.1)
                self.toast_data["delay"] -= 0.1

            DestroyWindow(self.toast_data["hwnd"])
            UnregisterClass(self.toast_data["wnd_class"].lpszClassName, self.toast_data["hinst"])
            try: # Sometimes the try icon sticks around until you click it - this should stop that
                Shell_NotifyIcon(NIM_DELETE, (self.toast_data["hwnd"], 0))
            except WinTypesException:
                pass
        self.active = False

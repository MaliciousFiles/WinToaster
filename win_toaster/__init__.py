"""WinToaster"""


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

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from . import data

# Magic constants
SystemParametersInfoW = windll.user32.SystemParametersInfoW
SPI_SETMESSAGEDURATION = 0x2017
SPI_GETMESSAGEDURATION = 0x2016
SPIF_SENDCHANGE = 0x2
PARAM_DESTROY = 0x404
PARAM_CLICKED = 0x405
MOUSE_UP = 0x202


def create_toast(
    title="Title",
    msg="Message",
    icon_path=None,
    delay=0,
    sound_path=None,
    tooltip="Tooltip",
    threaded=False,
    duration=5,
    keep_alive=False,
    callback_on_click=None,
    kill_without_click=True,
):
    """
    Returns a Toast class created from given parameters

    :title: notification title
    :msg: notification message
    :icon_path: path to the .ico file to custom notification
    :delay: delay in seconds before notification self-destruction
    :sound_path: path to the .wav file to custom notification
    :duration: how long the notification stays on the screen in seconds
    :keep_alive: keep toast alive in System Tray whether it was clicked or not
    :callback_on_click: function to run on click
    :kill_without_click: Kill the tray icon after the notification goes away,
                    even if it wasn't clicked

    :return: Toast object
    """

    # Set default icon_path
    if icon_path is None:
        with pkg_resources.path(data, "python.ico") as icon_context:
            icon_path = str(icon_context.absolute())
    icon_path = path.realpath(icon_path)

    # Make sure icon_path exists and is a .ico
    if not path.exists(icon_path):
        raise FileNotFoundError(f"Icon file could not be found ({icon_path})")
    if path.splitext(icon_path)[1] != '.ico':
        raise IOError(f"Icon file does not end with '.ico' ({icon_path})")

    # Make sure sound_path exists and is a .wav
    if sound_path:
        if not path.exists(sound_path):
            raise FileNotFoundError(f"Sound file could not be found ({sound_path})")
        if path.splitext(sound_path)[1] != '.wav':
            raise IOError(f"Sound file does not end with '.wav' ({sound_path})")

    # Make sure duration is valid
    buff = create_unicode_buffer(10)
    SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)
    try:
        oldlength = int(
            buff.value.encode("unicode_escape").decode().replace("\\", "0"), 16
        )
    except ValueError:
        oldlength = 5  # Default notification length

    duration_output = SystemParametersInfoW(
        SPI_SETMESSAGEDURATION, 0, duration, SPIF_SENDCHANGE
    )
    SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)

    duration_error = False
    try:
        int(buff.value.encode("unicode_escape").decode().replace("\\", "0"), 16)
    except ValueError:
        duration_error = True

    if duration_output == 0 or duration > 255 or duration_error:
        SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0,
                              oldlength, SPIF_SENDCHANGE)
        raise RuntimeError(f"Invalid duration length ({duration})")


    return Toast(
        title,
        msg,
        icon_path,
        delay,
        sound_path,
        tooltip,
        threaded,
        duration,
        keep_alive,
        callback_on_click,
        kill_without_click,
    )

class Toast:
    """A class representing a Windows 10 toast notification"""

    def __init__(
        self,
        title,
        msg,
        icon_path,
        delay,
        sound_path,
        tooltip,
        threaded,
        duration,
        keep_alive,
        callback_on_click,
        kill_without_click,
    ):
        """
        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :delay: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :duration: how long the notification stays on the screen in seconds
        :keep_alive: keep toast alive in System Tray whether it was clicked or not
        :callback_on_click: function to run on click
        :kill_without_click: Kill the tray icon after the notification goes away,
                             even if it wasn't clicked

        :return: Toast object
        """

        self.active = False
        self.thread = None
        self.destroy_window = kill_without_click

        self.toast_data = {
            "wnd_class": None,
            "hinst": None,
            "class_atom": None,
            "hwnd": None,
            "title": title,
            "msg": msg,
            "icon_path": icon_path,
            "delay": delay,
            "sound_path": sound_path,
            "tooltip": tooltip,
            "threaded": threaded,
            "duration": duration,
            "keep_alive": keep_alive,
            "callback_on_click": callback_on_click,
            "kill_without_click": kill_without_click,
        }

    def is_alive(self):
        """:return: if toast is currently being shown"""

        return self.active or (self.thread and self.thread.is_alive())

    @staticmethod
    def _decorator(func, callback=None):
        """
        :func: callable to decorate
        :callback: callable to run on mouse click within notification window

        :return: callable
        """

        def inner(*args, **kwargs):
            kwargs.update({"callback": callback})
            func(*args, **kwargs)

        return inner

    def _wnd_proc(self, hwnd, msg, wparam, lparam, **kwargs):
        """Internal function, called by Windows on click"""

        if lparam in (PARAM_CLICKED, MOUSE_UP):
            # make it stop on click
            self.toast_data["delay"] = 0
            self.destroy_window = True

            # callback goes here
            if kwargs.get("callback"):
                kwargs.pop("callback")()
        if lparam in (MOUSE_UP, PARAM_CLICKED, PARAM_DESTROY):
            if not self.toast_data["keep_alive"] and self.destroy_window:
                self.destroy()

    def destroy(self):
        """Destroys active toast"""
        delay = self.toast_data["delay"]
        while delay != None and delay > 0:
            sleep(0.1)
            delay -= 0.1

        try:
            DestroyWindow(self.toast_data["hwnd"])
            UnregisterClass(
                self.toast_data["wnd_class"].lpszClassName, self.toast_data["hinst"]
            )
            Shell_NotifyIcon(NIM_DELETE, (self.toast_data["hwnd"], 0)) # Sometimes the try icon sticks around until you click it - this should stop that
        except WinTypesException:
            pass

        PostQuitMessage()

        self.active = False

    def display(self):
        """Display Toast"""

        if self.toast_data["threaded"]:
            self.thread = Thread(target=self._show_toast)
            self.thread.start()
        else:
            self._show_toast()

    def _show_toast(self):
        """Internal function called by Toast#display to show the toast"""

        self.active = True
        self.destroy_window = self.toast_data["kill_without_click"]

        # Register the window class
        self.toast_data["wnd_class"] = WNDCLASS()
        self.toast_data["hinst"] = self.toast_data["wnd_class"].hInstance = GetModuleHandle(None)
        self.toast_data["wnd_class"].lpszClassName = f"PythonTaskbar{uuid4().hex}"
        self.toast_data["wnd_class"].lpfnWndProc = self._decorator(
            self._wnd_proc, self.toast_data["callback_on_click"]
        )

        self.toast_data["class_atom"] = RegisterClass(self.toast_data["wnd_class"])

        style = WS_OVERLAPPED | WS_SYSMENU
        self.toast_data["hwnd"] = CreateWindow(
            self.toast_data["class_atom"],
            self.toast_data["wnd_class"].lpszClassName,
            style,
            0,
            0,
            CW_USEDEFAULT,
            CW_USEDEFAULT,
            0,
            0,
            self.toast_data["hinst"],
            None,
        )

        UpdateWindow(self.toast_data["hwnd"])

        icon_flags = LR_LOADFROMFILE | LR_DEFAULTSIZE

        hicon = LoadImage(
            self.toast_data["hinst"], self.toast_data['icon_path'], IMAGE_ICON, 0, 0, icon_flags
        )

        # Set the duration
        buff = create_unicode_buffer(10)
        SystemParametersInfoW(SPI_GETMESSAGEDURATION, 0, buff, 0)
        try:
            oldlength = int(
                buff.value.encode("unicode_escape").decode().replace("\\", "0"), 16
            )
        except ValueError:
            oldlength = 5  # Default notification length

        SystemParametersInfoW(
            SPI_SETMESSAGEDURATION, 0, self.toast_data["duration"],
            SPIF_SENDCHANGE
        )

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (
            self.toast_data["hwnd"],
            0,
            flags,
            WM_USER + 20,
            hicon,
            self.toast_data["tooltip"],
        )

        # Make it so that it won't replace another
        # notification with the same title and message
        title = self.toast_data["title"] + " " * randint(
            0, 63 - len(self.toast_data["title"])
        )
        message = self.toast_data["msg"] + " " * randint(
            0, 128 - len(self.toast_data["msg"])
        )

        # Add tray icon and queue message
        Shell_NotifyIcon(NIM_ADD, nid)
        Shell_NotifyIcon(
            NIM_MODIFY,
            (
                self.toast_data["hwnd"],
                0,
                NIF_INFO,
                WM_USER + 20,
                hicon,
                self.toast_data["tooltip"],
                message,
                0,
                title,
                NIIF_NOSOUND if self.toast_data["sound_path"] else 0,
            ),
        )

        # Play the custom sound
        if self.toast_data["sound_path"] is not None:
            sound_path = path.realpath(self.toast_data["sound_path"])
            PlaySound(sound_path, SND_FILENAME)

        # Show the message
        PumpMessages()
        # Put the notification duration back to normal
        SystemParametersInfoW(SPI_SETMESSAGEDURATION, 0, oldlength, SPIF_SENDCHANGE)

        # Take a rest then destroy
        if not self.toast_data["keep_alive"] and self.destroy_window:
            self.destroy()

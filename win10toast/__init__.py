from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

__all__ = ['ToastNotifier']

# #############################################################################
# ########## Libraries #############
# ##################################
# standard library
import logging
import threading
from os import path
from pkg_resources import Requirement
from pkg_resources import resource_filename
from time import sleep
from time import time
from winsound import SND_FILENAME
from winsound import PlaySound
from winreg import OpenKeyEx, SetValueEx, EnumValue, CloseKey, REG_DWORD, KEY_QUERY_VALUE, KEY_SET_VALUE, ConnectRegistry, HKEY_CURRENT_USER
from random import randint

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
from win32con import HWND_BROADCAST
from win32con import WM_SETTINGCHANGE
from win32gui import CreateWindow
from win32gui import DestroyWindow
from win32gui import LoadIcon
from win32gui import LoadImage
from win32gui import SendMessage
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

    _uniqueid = 0

    def __init__(self):
        """Initialize."""
        self._thread = None

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
                    icon_path, duration,
                    sound_path, tooltip,
                    callback_on_click):
        """Notification settings.

        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :duration: delay in seconds before notification self-destruction, None for no-self-destruction
        :sound_path: path to the .wav file to custom notification
        :callback_on_click: function to run on click
        """
        self.duration=duration

        """
        root = ConnectRegistry(None, HKEY_CURRENT_USER)
        access_key = OpenKeyEx(root, r"Control Panel\Accessibility", access=KEY_SET_VALUE | KEY_QUERY_VALUE)
        oldValue = EnumValue(access_key, 0)[1]
        SetValueEx(access_key, "MessageDuration", 0, REG_DWORD, {length})

        ...

        SetValueEx(access_key, "MessageDuration", 0, REG_DWORD, oldValue)
        CloseKey(access_key)
        """

        # Make the notification end on click
        def callback():            
            self.duration=0

            if callback_on_click is not None:
                callback_on_click()
        
        # Register the window class.
        self.wc = WNDCLASS()
        self.hinst = self.wc.hInstance = GetModuleHandle(None)
        self.wc.lpszClassName = str(f"PythonTaskbar{ToastNotifier._uniqueid}")  # must be a string
        ToastNotifier._uniqueid += 1
        self.wc.lpfnWndProc = self._decorator(self.wnd_proc, callback)  # could instead specify simple mapping
        try:
            self.classAtom = RegisterClass(self.wc)
        except Exception as e:
            logging.error("Some trouble with classAtom ({})".format(e))
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
            logging.error("Some trouble with the icon ({}): {}"
                          .format(icon_path, e))
            hicon = LoadIcon(0, IDI_APPLICATION)

        # Taskbar icon
        flags = NIF_ICON | NIF_MESSAGE | NIF_TIP
        nid = (self.hwnd, 0, flags, WM_USER + 20, hicon, tooltip)
        Shell_NotifyIcon(NIM_ADD, nid)
        print("making message")
        Shell_NotifyIcon(NIM_MODIFY, (self.hwnd, 0, NIF_INFO,
                                      WM_USER + 20,
                                      hicon, tooltip, msg, 0,
                                      title, 0 if sound_path == None else NIIF_NOSOUND))
        # play the custom sound
        if sound_path is not None:
            sound_path = path.realpath(sound_path)
            if not path.exists(sound_path):
                logging.error("Some trouble with the sound file ({}): [Errno 2] No such file"
                              .format(sound_path))

            try:
                PlaySound(sound_path, SND_FILENAME)
            except Exception as e:
                logging.error("Some trouble with the sound file ({}): {}"
                             .format(sound_path, e))
        print("pumping message")
        PumpMessages()
        # take a rest then destroy
        if duration is not None:
            while self.duration > 0:
                sleep(0.1)
                self.duration -= 0.1

            print("destroying window")
            DestroyWindow(self.hwnd)
            UnregisterClass(self.wc.lpszClassName, self.hinst)
        return

    def show_toast(self, title="Notification", msg="Here comes the message",
                icon_path=None, duration=0, sound_path=None,
                tooltip="Tooltip", threaded=False, callback_on_click=None):
        """Notification settings.

        :title: notification title
        :msg: notification message
        :icon_path: path to the .ico file to custom notification
        :sound_path: path to the .wav file to custom notification
        :duration: delay in seconds before notification self-destruction, None for no-self-destruction
        :callback_on_click: function to run on click
        """
        if not threaded:
            self._show_toast(title, msg, icon_path, duration, sound_path, tooltip, callback_on_click)
        else:
            self._thread = threading.Thread(target=self._show_toast, args=(
                title, msg, icon_path, duration, sound_path, tooltip, callback_on_click
            ))
            self._thread.start()

    def notification_active(self):
        """See if we have an active notification showing"""
        if self._thread != None and self._thread.is_alive():
            # We have an active notification, let is finish we don't spam them
            return True
        return False

    def wnd_proc(self, hwnd, msg, wparam, lparam, **kwargs):
        """Messages handler method"""
        if lparam == PARAM_CLICKED:
            # callback goes here
            if kwargs.get('callback'):
                kwargs.pop('callback')()
            self.on_destroy(hwnd, msg, wparam, lparam)
        elif lparam == PARAM_DESTROY:
            self.on_destroy(hwnd, msg, wparam, lparam)

    def on_destroy(self, hwnd, msg, wparam, lparam):
        """Clean after notification ended."""
        nid = (self.hwnd, 0)
        Shell_NotifyIcon(NIM_DELETE, nid)
        PostQuitMessage(0)

        return None

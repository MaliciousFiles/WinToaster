# [WinToaster](https://wintoaster.readthedocs.io)

> Effortlessly create toast notifications for windows 10.
*View [the documentation](https://wintoaster.readthedocs.io)*

[![forthebadge](https://forthebadge.com/images/badges/made-with-python.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/open-source.svg)](https://forthebadge.com)

***

WinToaster is a minimal, yet powerful library for creating toast notifications
on Windows 10. Originally branched from
[Windows-10-Toast-Notifications](https://github.com/jithurjacob/Windows-10-Toast-Notifications),
WinToaster allows a higher level of customization, including custom sound files
and tooltips. This open source library is licensed under MIT: all contributions
are welcome.

## Getting Started

WinToaster is officially on PyPi, so you can just install it using pip:

1.  Make sure pip is installed
2.  Open command line and run `pip install WinToaster`
3.  Open up your project and import:
    ```python
    import win_toaster
    ```
4.  Create a notification:
    ```python
    win_toaster.create_toast(
        title="Title",                # Notification title
        msg="Message",                # Notifiation message
        icon_path=None,               # path to a .ico file
        delay=0,                      # delay in seconds before notification self-destruction
        sound_path=None,              # path to a .wav file
        tooltip="Tooltip",            # tooltip for tray icon
        threaded=False,               # show toast in another thread (non-blocking)
        duration=5,                   # how long the notification stays on the screen in seconds
        keep_alive=False,             # keep toast alive in system tray whether it was clicked or not
        callback_on_click=None,       # function to run on click
        kill_without_click=True       # kill the tray icon after the notification goes away, even if it wasn't clicked
    )
    ```

## Docs

The official documentation is at https://wintoaster.readthedocs.io.

## Contributing

Anyone can contribute. Although the code primarily deals with Windows 10,
fixing typos, adding documentation, and improving code style can be done from
any device. Before you contribute, make sure you have both Git and Python3
installed. If you have any trouble with the steps below, be sure to check out
[GitHub's wonderful forking tutorial](https://docs.github.com/en/enterprise-server@2.20/github/getting-started-with-github/fork-a-repo).
Follow the steps below to contribute:

1.  Fork the [repository](https://github.com/MaliciousFiles/WinToaster/) to your
    personal GitHub account.
2.  Clone your repository to your computer using
    `git clone YOUR_REPOSITORY_LINK`
3.  Add the original repository as the upstream, like so:
    `git remote add upstream https://github.com/MaliciousFiles/WinToaster.git`
4.  Enter the `WinToaster` directory. Install the development version of
    WinToaster with `pip install -e .`
5.  Make any changes, and push them to your repository.
6.  Open a pull request on GitHub.

### Contributors

-   Original code from
    [Charnelx/Windows-10-Toast-Notifications](https://github.com/Charnelx/Windows-10-Toast-Notifications)
    and
    [jithurjacob/Windows-10-Toast-Notifications](https://github.com/jithurjacob/Windows-10-Toast-Notifications)
-   [MaliciousFiles](https://github.com/MaliciousFiles) - *Malcolm Roalson* -
    Extended the code, and created WinToaster
-   [mrmaxguns](https://github.com/mrmaxguns) - *Maxim Rebguns* - Code quality,
    CI, documentation

## Versioning

WinToaster uses [SemVer](https://semver.org/) for versioning.

## License

WinToaster may be freely distributed with the rules of the MIT license. See
[LICENSE](LICENSE) for details.

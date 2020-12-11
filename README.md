# WinToaster

> Effortlessly create toast notifications for windows 10.

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

WinToaster is still in its early stages of development, and thus is not yet
available on PyPI. In order to install the package, you must clone the
repository and then build from source:

1.  Clone or download the repository from
    [GitHub](https://github.com/MaliciousFiles/WinToaster/)
2.  Enter the WinToaster root directory (the directory with the `setup.py`)
3.  Build from source (you must install *pip* first):
    ```
    pip install -e .
    ```

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
4.  Make any changes, and push them to your repository.
5.  Open a pull request on GitHub.

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

# Contribution Guidelines

Contributions are always welcome. As an open-source project, all perspectives, and improvements
are valued and accepted, as long as they follow the guidelines set forth in this document.
Before contributing, make sure to fully read and understand this document. Ask questions by
opening issues, or by contacting the maintainers of this repository.

## How to contribute

WinToaster follows the typical fork, clone, push, pull request process. The full process is listed
in the [contributing section of the readme](https://github.com/MaliciousFiles/WinToaster#contributing).
Once you have read the contributing section, please keep in mind that a couple of important expectations
regarding code are listed below.

-   All code must be written to be compatible with Python 3.6+.
-   When in doubt, check the style guidelines set forth by Pep-8.
-   The documentation of this project follows the styles set forth by the
    [Microsoft style guide](https://docs.microsoft.com/en-us/style-guide/).
-   Use Python3 f-strings when possible:
    ```python
    planet = "World"
    greeting = f"Hello, {planet}!" # Hello, World!
    ```
-   Use pylint to check for any issues before submitting a pull request. As of right now, the code
    is far from being perfectly formatted. We encourage contributions that keep the code clean.
-   If there is any issue regarding contributing, feel free to contact any of the maintainers for
    this repository.

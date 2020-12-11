
from operator import attrgetter
from os import path
from setuptools import setup

def parse_requirements(filename):
    lines = (line.strip() for line in open(filename))
    return [line for line in lines if line and not line.startswith("#")]

def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


def from_here(relative_path):
    return path.join(path.dirname(__file__), relative_path)


requirements_txt = parse_requirements(from_here("requirements.txt"))

setup(
    name="win_toaster",
    version="0.0",
    install_requires=requirements_txt,
    packages=["win_toaster"],
    license="BSD",
    url="https://github.com/MaliciousFiles/WinToaster",
    download_url = 'https://github.com/jithurjacob/Windows-10-Toast-Notifications/tarball/0.9',
    description=(
        "A simple python library for displaying"
        "Toast Notifications in Windows 10"
    ),
    include_package_data=True,
    package_data={
        '': ['*.txt'],
        'win_toaster': ['data/*.ico'],
    },
    long_description=read('README.md'),
    author="Malcolm R",
    author_email="mtroalson@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        'Operating System :: Microsoft',
        'Environment :: Win32 (MS Windows)',
        "License :: OSI Approved :: MIT License",
    ],
)

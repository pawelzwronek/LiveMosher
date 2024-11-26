<h1 align="center"> Live Mosher </h1> <br>
<p align="center">
    <img alt="Fritter" title="Fritter" src="src/gui/icons/icon.png" width="64">
</p>
<p align="center">
    Welcome to Live Mosher,<br>
    a front-end for <a href="https://github.com/ramiropolla/ffglitch-core">FFglitch</a> made by ramiropolla.
</p>

![App main window](screenshot1.png)

All example scripts come from the [ffglitch-scripts](https://github.com/ramiropolla/ffglitch-scripts) repository by ramiropolla.

Full FFglitch documentation: [ffglitch.org/docs](https://ffglitch.org/docs/)

# Installation
Download and extract from [Releases](https://github.com/pawelzwronek/LiveMosher/releases)

# Build
Minimum Python version: 3.8

Tested on Windows 10, Ubuntu 20.04.6, and macOS Monterey 12

Have `python` (Windows) or `python3` installed. Building must take place on the targeted system, so on Windows for Windows, Linux for Linux, and macOS for Mac.
## Windows
 - run `venv-prepare.cmd` once
 - run `run_pyinstaller-win.cmd` to build from the source code
 - see `dist/win` for the executable

## Linux
 - install required packages: `sudo apt install binutils python3-venv python3-tk`
 - run `venv-prepare.sh` once
 - run `run_pyinstaller-linux.sh` to build from the source code for Linux
 - see `dist/linux` for the executable

## Mac
 - run `venv-prepare.sh` once
 - run `run_pyinstaller-mac.sh` to build from the source code for Mac
 - see `dist/mac` for the executable

All binaries in the `bin` folder come from my custom [FFGlitch-core build](https://github.com/pawelzwronek/ffglitch-core).

Have fun!

Set up FFglitch on Windows
==========================

The recommended way to use FFglitch on Windows is to install Linux and
use FFglitch on Linux.

If you **really** insist on using Windows, follow these steps:

- Install Visual Studio Code and make sure you have bash working as a
terminal, like here:

https://stackoverflow.com/questions/42606837/how-do-i-use-bash-on-windows-from-the-visual-studio-code-integrated-terminal

- Clone this repository
- Open the terminal in Visual Studio Code
- Change directory to ffglitch-scripts/tutorial

- Either run this one magic command:
```
curl -O https://ffglitch.org/pub/bin/win64/ffglitch-0.10.2-windows-x86_64.7z && \
7z x ffglitch-0.10.2-windows-x86_64.7z && \
mkdir -p bin && \
mv ffglitch-0.10.2-windows-x86_64/* bin/ && \
rmdir ffglitch-0.10.2-windows-x86_64 && \
rm ffglitch-0.10.2-windows-x86_64.7z
```

Or run the commands separately:
- Download FFglitch:
```
curl -O https://ffglitch.org/pub/bin/win64/ffglitch-0.10.2-windows-x86_64.7z
```
- Unpack it:
```
7z x ffglitch-0.10.2-windows-x86_64.7z
```
- Move its contents to a directory named `bin`:
```
mkdir -p bin
mv ffglitch-0.10.2-windows-x86_64/* bin/
```
- Cleanup
```
rmdir ffglitch-0.10.2-windows-x86_64
rm ffglitch-0.10.2-windows-x86_64.7z
```


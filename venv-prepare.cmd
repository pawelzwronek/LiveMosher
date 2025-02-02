set OS=win

python -m venv venv-%OS%
call venv-%OS%\Scripts\activate.bat
pip install -r requirements-win.txt
copy /Y bin\pyinstaller\bootloader\*.exe venv-%OS%\Lib\site-packages\PyInstaller\bootloader\Windows-64bit-intel

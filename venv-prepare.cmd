set OS=win

python -m venv venv-%OS%
call venv-%OS%\Scripts\activate.bat
pip install -r requirements-win.txt

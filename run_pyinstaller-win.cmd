set APPNAME="Live Mosher"
set MAIN="src/LiveMosherApp.py"

set OS=win
set DIST=dist\%OS%
set DISTAPP=%DIST%\%APPNAME%

echo Building for %OS%

call venv-%OS%\Scripts\activate.bat

@REM set command="pip show tkextrafont | grep Location | cut -d ' ' -f 2"
@REM for /f "tokens=*" %%i in ('%command%') do set TKEXTRAFONT=%%i
@REM echo "TKEXTRAFONT: %TKEXTRAFONT%"
@REM set TKEXTRAFONT=%TKEXTRAFONT%\tkextrafont
@REM --add-data %TKEXTRAFONT%:gui/fonts/tkextrafont ^
@REM --exclude-module tkextrafont ^

pyinstaller ^
  --distpath=%DIST% ^
  --icon src/gui/icons/icon.png ^
  --noconfirm ^
  --hide-console hide-early ^
  --add-data src/gui/icons/*.png:gui/icons ^
  --add-data src/gui/fonts:gui/fonts ^
  --add-data src/gui/themes/waldorf.tcl:gui/themes ^
  --add-data bin/libs/%OS%:. ^
  --add-data version.txt:. ^
  --add-data Examples/basic.js:Examples ^
  --exclude-module PIL ^
  --exclude-module pkg_resources ^
  --noupx ^
  --name %APPNAME% ^
  %MAIN% && ^
xcopy /E /I Examples %DISTAPP%\Examples && ^
xcopy /E /I bin\ffglitch\%OS% dist\%OS%\%APPNAME%\_internal\ffglitch

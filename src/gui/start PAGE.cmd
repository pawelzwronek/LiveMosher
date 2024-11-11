@REM https://page.sourceforge.net/
@REM Tested on Python 3.9
python3 C:/DEVEL/PROGRAMS/page-8.0/page.py

@REM Move all widgets by 30 pixels down. Yeah, you can't select multiple widgets in PAGE.
@REM awk '{for(i=1;i<=NF;i++){if($i ~ /^-y$/ && $(i+1) ~ /^[0-9]+$/){$(i+1)=$(i+1)+30}}}1' LiveMosher1.tcl > LiveMosher1.tcl1

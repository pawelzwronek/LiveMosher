#!/bin/bash

APPNAME="Live Mosher"
MAIN="src/LiveMosherApp.py"

if uname -a | grep -q Darwin; then
    OS="mac"
elif uname -a | grep -q MINGW || uname -a | grep -q MSYS; then
    OS="win"
elif uname -a | grep -q Linux; then
    OS="linux"
else
    echo "Unknown OS: $(uname -a)"
    echo "Setting OS to linux."
    OS="linux"
fi

DIST="dist/$OS"
DISTAPP="$DIST/$APPNAME"

echo "Building for $OS"

source venv-$OS/bin/activate && \
TKEXTRAFONT=$(pip show tkextrafont | grep Location | cut -d ' ' -f 2)/tkextrafont && \
pyinstaller \
  --distpath="$DIST" \
  --icon src/gui/icons/icon.png \
  --noconfirm \
  --hide-console hide-early \
  --add-data src/gui/icons/*.png:gui/icons \
  --add-data src/gui/fonts:gui/fonts \
  --add-data src/gui/themes/waldorf.tcl:gui/themes \
  --add-data $TKEXTRAFONT:gui/fonts/tkextrafont \
  --add-data version.txt:. \
  --add-data Examples/basic.js:Examples \
  --exclude-module PIL \
  --exclude-module pkg_resources \
  --exclude-module tkextrafont \
  --noupx \
  --name "$APPNAME" \
  "$MAIN" && \
cp -r Examples "$DISTAPP" && \
mkdir -p "dist/$OS/$APPNAME/_internal/ffglitch" && \
cp -r bin/ffglitch/$OS/* "dist/$OS/$APPNAME/_internal/ffglitch"

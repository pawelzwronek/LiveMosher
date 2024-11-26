#!/bin/bash

APPNAME="Live Mosher"
MAIN="src/LiveMosherApp.py"

OS="mac"
DIST="dist/$OS"
DISTAPP="$DIST/$APPNAME"
Contents="$DIST/$APPNAME.app/Contents" # --windowed switch

echo "Building for $OS"

source venv-$OS/bin/activate && \
python3 scripts/before_build.py && \
pyinstaller \
  --distpath="$DIST" \
  --icon src/gui/icons/icon.png \
  --windowed \
  --noconfirm \
  --hide-console hide-early \
  --add-data src/gui/icons/*.png:gui/icons \
  --add-data src/gui/fonts:gui/fonts \
  --add-data src/gui/themes/waldorf.tcl:gui/themes \
  --exclude-module PIL \
  --exclude-module pkg_resources \
  --noupx \
  --name "$APPNAME" \
  "$MAIN" && \
cp -r Examples "$DISTAPP" && \
cp -r Examples "$Contents" && \
mkdir -p "dist/$OS/$APPNAME/_internal/ffglitch" && \
mkdir -p "$Contents/Frameworks/ffglitch" && \
cp -r bin/ffglitch/$OS/* "dist/$OS/$APPNAME/_internal/ffglitch" && \
cp -r bin/ffglitch/$OS/* "$Contents/Frameworks/ffglitch"

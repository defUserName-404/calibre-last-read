#!/bin/sh
# Build dist/LastRead.zip; with --install also add it to calibre (close calibre first).
set -e
cd "$(dirname "$0")"
mkdir -p dist
rm -f dist/LastRead.zip
(cd plugin && zip -qr ../dist/LastRead.zip . -x '*.pyc' -x '__pycache__/*' -x '.DS_Store')
zip -qj dist/LastRead.zip LICENSE
echo "built dist/LastRead.zip"
[ "$1" = "--install" ] && calibre-customize -a dist/LastRead.zip
exit 0

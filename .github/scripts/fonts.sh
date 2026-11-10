#!/usr/bin/env bash
# Persian channel (Nov 8): Vazirmatn with Farsi digits (SIL OFL 1.1, github.com/rastikerdar/vazirmatn) for all on-screen text.
set -e
B=https://cdn.jsdelivr.net/npm/vazirmatn@33.0.3/misc/Farsi-Digits/fonts/webfonts
mkdir -p render/public/fonts
[ -s render/public/fonts/vazir.woff2 ]  || curl -sfL --retry 3 -o render/public/fonts/vazir.woff2  "$B/Vazirmatn-FD-ExtraBold.woff2"
[ -s render/public/fonts/vazirb.woff2 ] || curl -sfL --retry 3 -o render/public/fonts/vazirb.woff2 "$B/Vazirmatn-FD-Black.woff2"
ls -la render/public/fonts/vazir*.woff2 || true
# owner's headline font Lalezar (SIL OFL) - Titr and Yekan are committed in render/public/fonts (owner's own files)
[ -s render/public/fonts/lalezar.woff2 ] || curl -sfL --retry 3 -o render/public/fonts/lalezar.woff2 "https://raw.githubusercontent.com/google/fonts/main/ofl/lalezar/Lalezar-Regular.ttf"
ls -la render/public/fonts/lalezar.woff2 render/public/fonts/titr.woff2 render/public/fonts/yekan.woff2 || true

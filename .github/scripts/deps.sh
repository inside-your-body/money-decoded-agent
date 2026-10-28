#!/usr/bin/env bash
# System deps (ffmpeg + emoji font). apt mirrors sometimes hang on GitHub runners (Oct 26/27 runs timed out) ->
# short timeouts, and a static ffmpeg build as fallback so the episode never fails on this step.
set -u
want_font=1; fc-list 2>/dev/null | grep -qi "Noto Color Emoji" && want_font=0
if command -v ffmpeg >/dev/null && [ $want_font = 0 ]; then echo "deps already there"; exit 0; fi
for i in 1 2; do
  if timeout 90 sudo apt-get update -qq -o Acquire::Retries=2 -o Acquire::http::Timeout=20 && \
     timeout 180 sudo apt-get install -y -qq -o Acquire::Retries=2 -o Acquire::http::Timeout=20 ffmpeg fonts-noto-color-emoji; then
    echo "apt ok"; exit 0
  fi
  echo "apt attempt $i failed"; sleep 5
done
if ! command -v ffmpeg >/dev/null; then
  echo "apt failed -> static ffmpeg"
  for url in https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz \
             https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz; do
    if curl -fsSL --retry 3 --max-time 180 "$url" -o /tmp/ff.tar.xz; then
      mkdir -p /tmp/ff && tar -xJf /tmp/ff.tar.xz -C /tmp/ff --strip-components=1 && \
      sudo install -m 755 $(find /tmp/ff -name ffmpeg -type f | head -1) /usr/local/bin/ffmpeg && \
      sudo install -m 755 $(find /tmp/ff -name ffprobe -type f | head -1) /usr/local/bin/ffprobe && break
    fi
  done
fi
if [ $want_font = 1 ] && ! fc-list | grep -qi "Noto Color Emoji"; then
  mkdir -p ~/.fonts && curl -fsSL --retry 3 --max-time 60 -o ~/.fonts/NotoColorEmoji.ttf \
    https://github.com/googlefonts/noto-emoji/raw/main/fonts/NotoColorEmoji.ttf && fc-cache -f >/dev/null || echo "emoji font skipped"
fi
ffmpeg -version | head -1

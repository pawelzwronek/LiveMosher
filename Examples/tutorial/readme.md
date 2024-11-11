Set up
======

- [Set up FFglitch on Linux](readme_linux.md).
- [Set up FFglitch on macOS](readme_macos.md).
- [Set up FFglitch on Windows](readme_windows.md).

JPEG glitches
=============

Simple glitch that modifies the DC quantization coefficient:
```
./bin/fflive -i lena.jpg -s scripts/jpeg/dqt.js
```

Simple glitch that modifies the quantized DC delta:
```
./bin/fflive -i lena.jpg -s scripts/jpeg/q_dc_delta.js
```

PNG glitches
============

Modify the filter type of PNG images:
```
./bin/fflive -i lena.png -s scripts/png/idat.js
```

MPEG4 glitches
==============

Clear the horizontal element of all motion vectors:
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_sink_and_rise.js
```

Clear the horizontal element of all motion vectors (faster):
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_sink_and_rise_fast.js
```

Add value to all motion vectors:
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_pan.js
```

Add value to all motion vectors (parameters on command line):
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_pan.js -sp "[ 0, 10 ]"
```

Add value to all motion vectors (using MIDI controller):
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_pan_midi.js
```

Run average of motion vectors over previous frames:
```
./bin/fflive -i CEP00109_mpeg4.avi -s scripts/mpeg4/mv_average.js
```

Any input file -> MPEG4 glitches
================================

Convert any input file to MPEG4, run average of motion vectors over previous frames:
```
./bin/ffgac -i MY_INPUT_FILE -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_average.js -fs -asap
```

A shorter version of the commands above using helper scripts:
```
./sh/file_to_mpeg4.sh MY_INPUT_FILE | ./sh/fflive_pipe -s scripts/mpeg4/mv_average.js -fs
```

Webcam MPEG4 glitches (Linux)
=============================

Capture webcam, convert to MPEG4, run average of motion vectors over previous frames:
```
./bin/ffgac -input_format mjpeg -video_size 1920x1080 -i /dev/video0 -vf hflip -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_average.js -fs -asap
```

Capture webcam, convert to MPEG4, add value to all motion vectors (using MIDI controller):
```
./bin/ffgac -input_format mjpeg -video_size 1280x720 -i /dev/video0 -vf hflip -c:v mpeg4 -q:v 1 -mpv_flags +nopimb+forcemv -g max -sc_threshold max -mb_type_script scripts/mpeg4/mb_type_midi.js -f avpipe - | ./bin/fflive -i - -s scripts/mpeg4/mv_pan_midi.js
```
NOTE: you can also clear the image with the MIDI controller (fader 0 selects time to clear, button 32 triggers it).

Webcam MPEG4 glitches (Windows)
===============================

Find webcam:
```
./bin/ffgac -list_devices true -f dshow -i dummy
```

Capture webcam (replace `"HP Truevision HD Camera"` with appropriate output from the previous command), convert to MPEG4, run average of motion vectors over previous frames:
```
./bin/ffgac -f dshow -i video="HP TrueVision HD Camera" -vf hflip -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_sink_and_rise.js -fs -asap
```

YouTube Live MPEG4 glitches
===========================

(make sure to have [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed)

Fetch live stream from YouTube, convert to MPEG4, run average of motion vectors over previous frames:
```
yt-dlp -o - 'https://youtu.be/XBzV4HzXymc' | ./bin/ffgac -i pipe: -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_average.js -fs -asap
```

Same as above, another stream:
```
yt-dlp -o - 'https://youtu.be/czoEAKX9aaM' | ./bin/ffgac -i pipe: -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -g max -sc_threshold max -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_average.js -fs -asap
```

Screen capture MPEG4 glitches (Linux X11 only)
==============================================

Screen capture region around mouse cursor, convert to MPEG4, run average of motion vectors over previous frames:
```
./bin/ffgac -f x11grab -follow_mouse centered -framerate 15 -video_size 640x480 -i :0.0 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 6 -sc_threshold max -g max -vcodec mpeg4 -f rawvideo pipe: | ./bin/fflive -i pipe: -s scripts/mpeg4/mv_average.js -fs -asap
```

Virtual Webcam MJPEG glitches (Linux only)
==========================================

Install and start v4l2loopback:
```
sudo apt-get install v4l2loopback-utils
sudo modprobe v4l2loopback video_nr=5 card_label="VirtualCam" exclusive_caps=1
```

Launch Virtual Webcam:
```
./bin/ffgac -input_format mjpeg -video_size 1920x1080 -i /dev/video0 -vcodec copy -f rawvideo pipe: | ./bin/ffedit -i pipe: -s scripts/jpeg/dqt.js -o pipe: | ./bin/ffgac -i pipe: -vcodec copy -f v4l2 /dev/video5
```

You can now use the Virtual Webcam (`/dev/video5`) on Google Chrome, Telegram, or whatever... just like a normal webcam.

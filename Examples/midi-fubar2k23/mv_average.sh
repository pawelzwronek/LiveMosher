
FFLIVE_PATH=/home/ramiro/code/ffglitch/build-fflive/
SESSION_TIME=60
${FFLIVE_PATH}ffgac -input_format mjpeg -video_size 1920x1080 -i /dev/video2 -mb_type_script mb_type-midi.js -vcodec mpeg4 -mpv_flags +nopimb+forcemv -qscale:v 1 -fcode 5 -g max -f rawvideo -flush_packets 1 -t ${SESSION_TIME} - | ${FFLIVE_PATH}fflive -probesize 32 -i - -autoexit -s mv_average.js

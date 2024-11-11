
FFLIVE_PATH=/home/ramiro/code/ffglitch/build-fflive/
SESSION_TIME=60
${FFLIVE_PATH}fflive -probesize 32 -input_format mjpeg -video_size 1920x1080 -i /dev/video2 -t ${SESSION_TIME} -vf script=pixelsort.js

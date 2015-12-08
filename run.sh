#!/bin/bash

# This script runs the application in various ways depending on the params
# passed. It's normally run from the makefile

IMAGES_SRC_DIR=./node_modules/money-to-prisoners-common/assets/images
IMAGES_DST_DIR=./mtp_cashbook/assets/images

# kill all processes spawned by this script in the
# background when it stops, in particular django
# restarts
function clean_up {
  echo "Killing all spawned processes."
  echo kill -- -$(ps -o pgid= $PID | grep -o [0-9]*)
  kill -- -$(ps -o pgid= $PID | grep -o [0-9]*)
  exit 1
}

# Activate and run the django application
function start {
  source venv/bin/activate
  pip install -r requirements/dev.txt
  ./manage.py runserver 8001
}

case "$1" in
  start)
    # just run normally
    start
    ;;
  watch)
    # run normally but monitor assets and recompile
    # them when they change
    trap clean_up INT
    start > /dev/null 2>&1 & PID=$!
    shift
    fswatch -o $@ | xargs  -n1 -I{} sh -c 'echo "---- Change detected ----"; make -f makefile_frontend all'
    ;;
  serve)
    # as above but also run browser-sync for dynamic
    # browser reload
    trap clean_up INT
    start > /dev/null 2>&1  & PID=$!
    echo Starting Browser-Sync
    browser-sync start --host=localhost --port=3000 --proxy=localhost:8001 --no-open --ui-port=3001 &
    shift
    echo "Watching changes"
    fswatch -o $@ | xargs -n1 -I{} sh -c 'echo "---- Change detected ----"; make -f makefile_frontend all; browser-sync reload'
    ;;
  *)
    echo "Usage: $0 [start|watch|serve] <args>"
    echo " - $0 start: just start the application server"
    echo " - $0 watch <list of asset directories to monitor>: start the "
    echo "   application server and recompile the assets if they are changed"
    echo " - $0 serve <list of asset directories to monitor>: start the "
    echo "   browser-sync server and recompile the assets if they are changed"
    exit 1
esac

#!/bin/bash

BOWER_DIR=$1

if [ $BOWER_DIR ]; then

  # Hopscotch - Rename .css file to .scss
  HOPSCTOCH_DIR=$BOWER_DIR/hopscotch/dist/css
  HOPSCTOCH_FILE=$HOPSCTOCH_DIR/hopscotch.css
  if [ -e "$HOPSCTOCH_FILE" ]; then
    mv "$HOPSCTOCH_FILE" "$HOPSCTOCH_DIR/_hopscotch.scss"
  fi

  # MTP Common - copy shared gulp tasks
  TASKS_DIR="./tasks"
  SHARED_TASKS_DIR="$TASKS_DIR/common"
  if [ ! -e "$TASKS_DIR" ]; then
    mkdir "$TASKS_DIR"
  fi
  if [ -e "$SHARED_TASKS_DIR" ]; then
    rm -rf "$SHARED_TASKS_DIR"
    mkdir "$SHARED_TASKS_DIR"
  else
    mkdir "$SHARED_TASKS_DIR"
  fi
  cp -vr "$BOWER_DIR/money-to-prisoners-common/tasks/" "$SHARED_TASKS_DIR"

  # run gulp build
  ./node_modules/.bin/gulp build

else
  echo "ERROR: Bower directory must be passed as first arguament" >&2
fi

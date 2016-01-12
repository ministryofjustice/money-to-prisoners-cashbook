#!/usr/bin/env bash

cd `dirname $0`

if [ ! -d node_modules ]; then
  echo "The installation process is about to start. It usually takes a while."
  echo "The only thing that this script doesn't do is set up the API. While"
  echo "installation is running, head to https://github.com/ministryofjustice/money-to-prisoners-api"
  echo "to find out how to run it."
  npm install
fi

make -f node_modules/money-to-prisoners-common/Makefile \
  command_script=`basename $0` \
  app=cashbook \
  port=8001 \
  browsersync_port=3001 \
  browsersync_ui_port=3031 \
  $@

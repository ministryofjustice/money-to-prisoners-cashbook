#!/usr/bin/env bash

cd `dirname $0`

if [ ! -d node_modules ]; then
  echo "The installation process is about to start. It usually takes a while."
  echo "The only thing that this script doesn't do is set up the API. While"
  echo "installation is running, head to https://github.com/ministryofjustice/money-to-prisoners-api"
  echo "to find out how to run it."

  read -p "Proceed with installation? [Y/n]: " PROCEED
  case ${PROCEED} in
    [nN]*) exit 1;;
  esac

  npm install
fi

load_defaults() {
  # all constants and default values should be defined here
  APP=cashbook
  PROJECT_PATH=`pwd`
  SHARED_MAKEFILE=node_modules/money-to-prisoners-common/Makefile
  DEFAULT_PORT=8001
  DEFAULT_BROWSERSYNC_PORT=3001
  DEFAULT_BROWSERSYNC_UI_PORT=3031
  DEFAULT_DJANGO_SETTINGS_MODULE=mtp_api.settings
}

. node_modules/money-to-prisoners-common/tasks.sh
main $@

#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 [start|watch|serve|clean|all] app=<app_name> port=8001"
  echo " - start: start the application server"
  echo " - watch: start the application server and recompile the assets when they change"
  echo " - serve: start the browser-sync server and recompile the assets when they change"
  echo " - all: compile all the assets"
  echo " - test: run the test suite"
else
  if [ ! -d node_modules ]; then
    echo "The installation process is about to start. It usually takes a while."
    echo "The only thing that this script doesn't do is set up the API. While"
    echo "installation is running, head to https://github.com/ministryofjustice/money-to-prisoners-api"
    echo "to find out how to run it."
    echo "Press Return to continue"
    read
    npm install
  fi
  make -f node_modules/money-to-prisoners-common/Makefile $1 app=mtp_cashbook port=8001
fi

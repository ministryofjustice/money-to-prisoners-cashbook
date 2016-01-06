#!/usr/bin/env bash
if [ "$#" -eq 0 ]; then
  echo "Usage: $0 [start|watch|serve|clean|build] [args]"
  echo " - start [port]: start the application server using the port specified"
  echo " - watch [port]: start the application server and recompile the assets when they change"
  echo " - serve [port]: start the browser-sync server and recompile the assets when they change"
  echo " - build: compile all the assets"
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
  make -f node_modules/money-to-prisoners-common/Makefile $1 app=mtp_cashbook port=${2-8000}
fi

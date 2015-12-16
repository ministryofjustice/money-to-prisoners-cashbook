#!/bin/bash
if [ "$#" -ne 1 ]; then
  echo "Usage: $0 [run | start | serve | watch | clean | all]"
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
  make -f node_modules/money-to-prisoners-common/makefile $1 app=mtp_cashbook port=8001
fi

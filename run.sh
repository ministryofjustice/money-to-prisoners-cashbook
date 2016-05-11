#!/bin/bash

function print_usage {
    echo "Usage: $0 [options] command"
    echo "command: serve | watch | docker | update | build | clean | test | start"
    echo "   -h      print this help"
    echo "   -c | --common-path <dir>"
    echo "           Use this directory for the common libraries. Needs -r."
    echo "   -r | --regenerate-common"
    echo "           Fetch the common libraries, either from a local directory"
    echo "           specified with -c, or from pypi is -c is omitted"
}

# Read command-line options
while [[ $# > 1 ]]; do
    key="$1"
    case $key in
        -h|--help)
        print_usage
        exit
        ;;
        -c|--common-path)
        COMMONPATH="$2"
        shift
        ;;
        -r|--regenerate-common)
        REGENERATE=YES
        ;;
        *)
        echo "Unknown option $1"
        exit
        ;;
    esac
    shift
done

COMMAND=$1
APP=cashbook
VIRTUAL_ENV_DIR=venv
NODE_MODULES=node_modules

case "$COMMAND" in
    clean)
        rm -rf $VIRTUAL_ENV_DIR $NODE_MODULES static mtp_$APP/assets
        ;;
    serve | watch | docker | update | build | test | start)
        PORT=8001
        BROWSERSYNC_PORT=3001
        BROWSERSYNC_UI_PORT=3031

        MTP_COMMON_NODE_MODULES=$NODE_MODULES/money-to-prisoners-common

        if [ -z "$VIRTUAL_ENV" ]; then
          if [ ! -d $VIRTUAL_ENV_DIR ]; then
            echo "Creating Python virtual environment"
            virtualenv --python=python3 $VIRTUAL_ENV_DIR >/dev/null
          fi
          source $VIRTUAL_ENV_DIR/bin/activate >/dev/null
        fi
        PYTHON_BIN=$VIRTUAL_ENV/bin
        export PYTHON_LIBS=`$PYTHON_BIN/python find_common.py`
        if [[ ("$REGENERATE" == "YES") || ("$PYTHON_LIBS" == "") ]]; then
            echo -n "Fetching common resources "
            if [[ COMMONPATH != "" && -d $COMMONPATH ]]; then
                echo "from local dir $COMMONPATH"
                $PYTHON_BIN/pip install -e $COMMONPATH >/dev/null
            else
                echo "from pypi"
                $PYTHON_BIN/pip install money-to-prisoners-common > /dev/null
            fi
            export PYTHON_LIBS=`$PYTHON_BIN/python find_common.py`
        else
            echo "Common resources found at $PYTHON_LIBS"
        fi
        echo "Installing front-end assets"
        npm install >/dev/null
        npm install `cat $PYTHON_LIBS/mtp_common/npm_requirements.txt` >/dev/null
        mkdir -p $MTP_COMMON_NODE_MODULES
        ln -Fs $PYTHON_LIBS/mtp_common/assets $MTP_COMMON_NODE_MODULES
        make -f $PYTHON_LIBS/mtp_common/Makefile app=$APP port=$PORT browsersync_port=$BROWSERSYNC_PORT browsersync_ui_port=$BROWSERSYNC_UI_PORT $COMMAND
        ;;
    *)
        echo "Unknown command $COMMAND"
        print_usage
        ;;
esac


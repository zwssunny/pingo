#!/bin/bash
set -e

# build prefix
PINGO_APP_PREFIX=${PINGO_APP_PREFIX:-""}
# path to config.json
PINGO_APP_CONFIG_PATH=${PINGO_APP_CONFIG_PATH:-""}
# execution command line
PINGO_APP_EXEC=${PINGO_APP_EXEC:-""}

# use environment variables to pass parameters
# if you have not defined environment variables, set them below
export SDL_AUDIODRIVER=alsa
export AUDIODEV pulse

# PINGO_APP_PREFIX is empty, use /app
if [ "$PINGO_APP_PREFIX" == "" ] ; then
    PINGO_APP_PREFIX=/app
fi

# PINGO_APP_CONFIG_PATH is empty, use '/app/config.json'
if [ "$PINGO_APP_CONFIG_PATH" == "" ] ; then
    PINGO_APP_CONFIG_PATH=$PINGO_APP_PREFIX/config.json
fi

# PINGO_APP_EXEC is empty, use ‘python pingo.py’
if [ "$PINGO_APP_EXEC" == "" ] ; then
    PINGO_APP_EXEC="python pingo.py"
fi

# go to prefix dir
cd $PINGO_APP_PREFIX
# excute
$PINGO_APP_EXEC


# Common environment

# https://stackoverflow.com/questions/5947742/how-to-change-the-output-color-of-echo-in-linux
RED='\033[0;31m'          # Red
GREEN='\033[0;32m'        # Green
YELLOW='\033[0;33m'       # Yellow
NC='\033[0m' # No Color

SETUP_SERVERS_USER_HOME=${HOME}
SETUP_SERVER_PYTHON=python3
SETUP_SERVER_VENV=${SETUP_SERVER_HOME}/.venv

# Local environment can override above and add more locally needed environment configuration
if [[ -f ${SETUP_SERVER_HOME}/env-local.sh ]]; then
  . "${SETUP_SERVER_HOME}/env-local.sh"
fi
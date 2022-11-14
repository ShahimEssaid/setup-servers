#!/usr/bin/env bash
#set -x
set -e
set -u
set -o pipefail
set -o noclobber
shopt -s nullglob

# stack overflow #59895
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
export SETUP_SERVER_HOME=$(realpath "${DIR}/../..")
cd "$SETUP_SERVER_HOME"
. "${SETUP_SERVER_HOME}/env.sh"

#  =========== END OF COMMON HEADER. See setup_servers/setup-db/.template.sh

. "${SETUP_SERVER_VENV}/bin/activate"
setup-servers \
  --remote-pycharm-debug \
  --pycharm-host localhost \
  --pycharm-port 11111 \
  setup-fhir-server \
  --setup-directory-name fhir-server-1 \
  --dbs-type postgres \
  --dbs-setup-name hapi-setup \
  --db-user hapi \
  --db-pass hapi \
  "$@"


#  setup-db \
#  --dbs-name postgres \
#  --dbs-version latest \
#  --dbs-user postgres \
#  --dbs-pass postgres \
#  --dbs-uid  $(id -u ) \
#  --dbs-host localhost \
#  --dbs-port 7777 \
#  --dbs-provider postgres-v1 \
#  --dbs-action run \
#  --setup-directory-name testing1 \
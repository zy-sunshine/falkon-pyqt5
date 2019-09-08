DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

set PY3RD="$DIR/py3rd"
export PYTHONPATH="$PYTHONPATH:$PY3RD"

export PATH="/home/$USER/bin:$DIR/bin:$PATH:$DIR/tools"

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:"."

color()(set -o pipefail;"$@" 2>&1>&3|sed $'s,.*,\e[31m&\e[m,'>&2)3>&1

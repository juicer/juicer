####################################################################
HACKDIR=`dirname $0`
. ${HACKDIR}/setup-env >/dev/null 2>&1

# Oh SWEET. Color codes! Ganked from http://stackoverflow.com/a/10466960/263969
declare -A COLORS

COLORS[RESTORE]='\033[0m'
COLORS[RED]='\033[00;31m'
COLORS[GREEN]='\033[00;32m'
COLORS[YELLOW]='\033[00;33m'
COLORS[BLUE]='\033[00;34m'
COLORS[PURPLE]='\033[00;35m'
COLORS[CYAN]='\033[00;36m'
COLORS[LIGHTGRAY]='\033[00;37m'
COLORS[LRED]='\033[01;31m'
COLORS[LGREEN]='\033[01;32m'
COLORS[LYELLOW]='\033[01;33m'
COLORS[LBLUE]='\033[01;34m'
COLORS[LPURPLE]='\033[01;35m'
COLORS[LCYAN]='\033[01;36m'
COLORS[WHITE]='\033[01;37m'

colorize() {
    # $1 = a COLOR from the table above ^
    # $2 = a quoted string to print out in COLOR
    #
    # NOTE: 'colorize' doesn't print trailing new lines, ergo you may
    # use it inline:
    #
    #    $ echo "black stuff, `colorize GREEN 'green stuff'`, more black stuff
    echo -en "${COLORS[RESTORE]}${COLORS[${1}]}${2}${COLORS[RESTORE]}"
}

####################################################################

TESTID=`date +'%Y%m%d%S'`
export TESTCART="testcart-${TESTID}"
export TESTREPO="testrepo-${TESTID}"
export TESTUSER="testuser-${TESTID}"

####################################################################

export JPROFILE=yes

#!/usr/bin/env bash
while getopts "f" opt; do
    case $opt in
        "f" ) 
            echo "set force mode"
            FORCE="TRUE"
            ;;
    esac
done

set -e
archive=${1%/}

shift $(expr $OPTIND - 1) # remove option args
JARPATH="AbbrExpansion/out"
PARSECODE="Parse2-all.jar"
SEMANTICEXPAND="SemanticExpand-all.jar"
IDTABLE="idTable.csv"
EXTABLE="exTable.csv"
GZIP_IDTABLE=${IDTABLE}".gz"
GZIP_EXTABLE=${EXTABLE}".gz"
IDTABLE_PATH="${archive}/${IDTABLE}"
EXTABLE_PATH="${archive}/${EXTABLE}"
GZIP_IDTABLE_PATH="${archive}/${GZIP_IDTABLE}"
GZIP_EXTABLE_PATH="${archive}/${GZIP_EXTABLE}"
VERSION=$(bash --version | head -n 1 | sed -E 's/^.* ([0-9.]+)\.[0-9]+\([0-9]+\)-release.*$/\1/')

# bash requirement check
# if [[ $(echo "${VERSION} < 4.3" | bc) -eq 1 ]] ; then
#     echo "bash version must be 4.3 or later"
#     exit
# fi
# renas
echo "${archive}"
echo "start creating table."
FORCE="TRUE"

# remove jar signature
if [ -n "$(zipinfo -1 ${JARPATH}/${PARSECODE} | grep META-INF/.*SF)" ]; then
    echo "rm META-INF/*SF"
    zip -d "${JARPATH}/${PARSECODE}" 'META-INF/*SF'
fi
# create table
if [ "$FORCE" = "TRUE" ] || [ ! -f "${GZIP_EXTABLE_PATH}" ]; then
    echo "${archive} Run ParseCode"
    repo=${archive}"/repo"
    # parse code
    java -jar "${JARPATH}/${PARSECODE}" "${archive}"
    cd "AbbrExpansion/code/SemanticExpand"

    #./gradlew run --args "${archive}"

    # semantic expand
    java -jar "out/libs/${SEMANTICEXPAND}" "/work/${archive}"
    cd ../../..
    # normalize
    python3 -m renas.normalize "${archive}"
    # gzip
    echo "gzip tables"
    gzip -f "${archive}/${IDTABLE}"
    gzip -f "${archive}/${EXTABLE}"

    rm -rf "${repo}"

else
    echo "${IDTABLE_PATH} already exists. Skip."
fi
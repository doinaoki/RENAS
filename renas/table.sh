#!/usr/bin/env bash

set -e
archive=${1%/}

shift $(expr $OPTIND - 1) # remove option args
JARPATH="AbbrExpansion/out"
PARSECODE="Parse2-all.jar"
SEMANTICEXPAND="SemanticExpand-all.jar"
IDTABLE="idTable.csv"
EXTABLE="exTable.csv"
RECORD="record.json"
CLASS_RECORD="classRecord.json"
GZIP_IDTABLE=${IDTABLE}".gz"
GZIP_EXTABLE=${EXTABLE}".gz"
IDTABLE_PATH="${archive}/${IDTABLE}"
EXTABLE_PATH="${archive}/${EXTABLE}"
GZIP_IDTABLE_PATH="${archive}/${GZIP_IDTABLE}"
GZIP_EXTABLE_PATH="${archive}/${GZIP_EXTABLE}"

# renas
echo "${archive}"
echo "start creating table."

# remove jar signature
if [ -n "$(zipinfo -1 ${JARPATH}/${PARSECODE} | grep META-INF/.*SF)" ]; then
    echo "rm META-INF/*SF"
    zip -d "${JARPATH}/${PARSECODE}" 'META-INF/*SF'
fi

# create table
echo "${archive} Run ParseCode"
repo="${archive}/repo"
# parse code
java -jar "${JARPATH}/${PARSECODE}" "${archive}"
cd "AbbrExpansion/code/SemanticExpand"

# semantic expand
java -jar "out/libs/${SEMANTICEXPAND}" "/work/${archive}"
cd ../../..
# normalize
python3 -m renas.relationship.normalize "${archive}"
# gzip
echo "gzip tables"
#gzip -f "${archive}/${IDTABLE}"
gzip -f "${archive}/${EXTABLE}"
gzip -f "${archive}/${RECORD}"
gzip -f "${archive}/${CLASS_RECORD}"

echo "delete unnecessary file"
rm "${archive}/${GZIP_IDTABLE}"
rm -rf "${repo}"

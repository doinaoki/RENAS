PROJECT=$1
REPOPATH="$PROJECT/archives/"

COMMITS=`ls $REPOPATH`
#echo $COMMITS
set -e
for i in $COMMITS
do
    renas/table.sh $REPOPATH$i -f
done

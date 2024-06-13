REPO_NAME=$1

REPO_PATH="projects/${REPO_NAME}"
python -m renas.getRefactoring ${REPO_PATH}

python -m script.create_rename_json ${REPO_PATH}

python -m renas.downloadNLTK

python -m renas.gitOneArchive ${REPO_PATH} -f

python -m renas.renas ${REPO_PATH} -f

python -m oldRenas.renas ${REPO_PATH} -f

python -m renas.integrateRecommend ${REPO_PATH}

python -m renas.MergeRecommend ${REPO_PATH}

python -m renas.RandomRecommend ${REPO_PATH}

python -m renas.MergeRandomRecommend ${REPO_PATH}

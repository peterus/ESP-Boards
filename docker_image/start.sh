#!/bin/bash

USER=$USER
REPOSITORY=$REPOSITORY
ACCESS_TOKEN=$ACCESS_TOKEN
LABELS=$LABELS
RUNNER_NAME=$RUNNER_NAME

REG_TOKEN=$(curl -sX POST -H "Authorization: token ${ACCESS_TOKEN}" https://api.github.com/repos/${USER}/${REPOSITORY}/actions/runners/registration-token | jq .token --raw-output)

cd /home/docker/actions-runner

./config.sh --url https://github.com/${USER}/${REPOSITORY} --token ${REG_TOKEN} --name ${RUNNER_NAME} --labels ${LABELS}

cleanup() {
    echo "Removing runner..."
    ./config.sh remove --unattended --token ${REG_TOKEN}
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!

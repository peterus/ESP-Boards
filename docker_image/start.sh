#!/bin/bash

USER=$USER
REPOSITORY=$REPOSITORY
ACCESS_TOKEN=$ACCESS_TOKEN
LABELS=$LABELS
RUNNER_NAME=$RUNNER_NAME
USB_ID=$USB_ID

curl -sX POST -H "Authorization: token ${ACCESS_TOKEN}" https://api.github.com/repos/${USER}/${REPOSITORY}/actions/runners/registration-token

REG_TOKEN=$(curl -sX POST -H "Authorization: token ${ACCESS_TOKEN}" https://api.github.com/repos/${USER}/${REPOSITORY}/actions/runners/registration-token | jq .token --raw-output)

echo $REG_TOKEN

cd /home/docker/actions-runner

./config.sh --url https://github.com/${USER}/${REPOSITORY} --token ${REG_TOKEN} --name ${RUNNER_NAME} --labels ${LABELS}

echo "USB_ID=$USB_ID" >> .env
echo "RUNNER_NAME=$RUNNER_NAME" >> .env

cleanup() {
    echo "Removing runner..."
    ./config.sh remove --unattended --token ${REG_TOKEN}
}

trap 'cleanup; exit 130' INT
trap 'cleanup; exit 143' TERM

./run.sh & wait $!

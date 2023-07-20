#!/bin/python3

import os
import json
import docker
from pathlib import Path

SERIAL_BY_ID = Path("/dev/serial/by-id")

usb_ids = os.listdir(SERIAL_BY_ID)

f = open('boards.json')
boards = json.load(f)

# reverse search do detect if we have a usb device which is not in the list
found_boards = []
for board in boards:
    if board['usb id'] in usb_ids:
        found_boards.append(board)

for board in found_boards:
    print(f"found board: {board['name']}")

volumes=["locks:/locks", "/dev:/dev"]


client = docker.from_env()
for board in found_boards:
    container = client.containers.list(filters={'name': board['name']})
    if len(container) == 0:
        print(f"starting {board['name']}")
        environment=["USER=peterus", "REPOSITORY=ESP-Boards", f"LABELS={board['labels']}", f"RUNNER_NAME={board['name']}", f"ACCESS_TOKEN={os.getenv('ACCESS_TOKEN')}"]
        container = client.containers.run("ghcr.io/peterus/esp-boards:main", detach=True, auto_remove=True, volumes=volumes, environment=environment, name=board['name'])

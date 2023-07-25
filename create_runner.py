#!/bin/python3

import os
import json
import docker
import time
from typing import Optional
from pathlib import Path

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
environment = ["USER=peterus", "REPOSITORY=ESP-Boards", f"ACCESS_TOKEN={ACCESS_TOKEN}"]
volumes = ["locks:/locks", "/dev:/dev"]
docker_image = "ghcr.io/peterus/esp-boards:main"


class Board(object):
    __slots__ = ("name", "usb_id", "labels", "cpp_defines")

    def __init__(self, name, usb_id, labels, cpp_defines):
        self.name = name
        self.usb_id = usb_id
        self.labels = labels
        self.cpp_defines = cpp_defines


def get_current_serial_ports() -> list[str]:
    SERIAL_BY_ID = Path("/dev/serial/by-id")
    return os.listdir(SERIAL_BY_ID)


def get_defined_boards() -> list[Board]:
    f = open('boards.json')
    for board in json.load(f):
        yield Board(**board)


def match_serial_port_to_defined(port: str, boards: list[Board]) -> Optional[Board]:
    for board in boards:
        if board.usb_id in port:
            return board
    return None


def is_defined_board_in_serial_ports(board: Board, ports: list[str]) -> bool:
    for port in ports:
        if board.usb_id in port:
            return True
    return False


def create_new_docker_container(client: docker.DockerClient, board: Board) -> None:
    environment_cont = environment
    environment_cont.append(f"LABELS={board.labels}")
    environment_cont.append(f"RUNNER_NAME={board.name}")
    environment_cont.append(f"CPP_DEFINES={board.cpp_defines}")
    environment_cont.append(f"USB_ID={board.usb_id}")
    container = client.containers.run(docker_image, detach=True,
                                      auto_remove=True, volumes=volumes, environment=environment_cont, name=board.name)


def is_container_running(client: docker.DockerClient, board: Board) -> bool:
    return len(client.containers.list(filters={'name': board.name})) != 0


def stop_container(client: docker.DockerClient, board: Board):
    containers = client.containers.list(filters={'name': board.name})
    for container in containers:
        container.stop()


def main():
    if not ACCESS_TOKEN:
        print("ACCESS_TOKEN not defined!")
        exit(1)

    client = docker.from_env()
    print(f"pulling latest image: '{docker_image}'")
    client.images.pull(docker_image)
    defined_boards = get_defined_boards()
    print("Current Serial Ports:")
    for serial_port in get_current_serial_ports():
        matched = match_serial_port_to_defined(serial_port, defined_boards)
        if matched:
            if not is_container_running(client, matched):
                print(f"  * {serial_port}  -  {matched.name}  -- starting up")
                create_new_docker_container(client, matched)
            else:
                print(f"  * {serial_port}  -  {matched.name}  -- running")
        else:
            print(f"  * {serial_port}  -  no board defined!")

    print("")
    time.sleep(2)

    print("checking defined boards:")
    for board in get_defined_boards():
        if not is_defined_board_in_serial_ports(board, get_current_serial_ports()):
            if not is_container_running(client, board):
                print(f"  * {board.name}  --  not running and no port found")
            else:
                print(f"  * {board.name}  --  running, but no port found, will stop now!")
                stop_container(client, board)
        else:
            if not is_container_running(client, board):
                print(f"  * {board.name}  --  not running, but port found -> looks like something is not working!")
            else:
                print(f"  * {board.name}  --  running")


if __name__ == "__main__":
    main()

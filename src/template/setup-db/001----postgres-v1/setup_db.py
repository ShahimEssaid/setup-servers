import pathlib
import sys
import time

import docker.models.containers

import setupservers
from setupservers import docker_client
import docker.errors as errors


def can_provide_db(setup_db) -> bool:
    setup_info: setupservers.SetupInfo = setup_db.info
    try:
        docker_client.images.get_registry_data(f"{setup_info.dbs_name}:{setup_info.dbs_version}")
    except errors.NotFound:
        return False
    return True


def provide_db(setup_db):
    info: setupservers.SetupInfo = setup_db.info

    for action in setup_db.dbs_actions:
        if action == 'run':
            run_db(info)
        elif action == 'stop':
            stop_db(info)


def run_db(info):
    if info.dbs_status == 'running':
        setupservers.console_warn(f"Database server already {info.dbs_status}, ignoring run action.")
        return

    work_dir_name = pathlib.Path(info.setup_path).name
    docker_container_name = setupservers.docker_container_name(__name__, work_dir_name)

    info.dbs_container_name = docker_container_name
    volume_path = pathlib.Path(info.setup_path) / 'dbs-volume'
    volume_path.mkdir(parents=True, exist_ok=True);
    info.dbs_volume_base = str(volume_path)
    info.docker_volumes = {str(info.dbs_volume_base): {'bind': '/var/lib/postgresq/data', 'mode': 'rw'}}
    ports = {5432: int(info.dbs_port)}

    environment = {'PGDATA': '/var/lib/postgresq/data/pgdata',
                   'POSTGRES_USER': info.dbs_user,
                   'POSTGRES_PASSWORD': info.dbs_pass}
    docker_client.containers.run(info.dbs_name + ":" + info.dbs_version,
                                 user=info.dbs_uid,
                                 name=info.dbs_container_name,
                                 remove=True,
                                 detach=True,
                                 volumes=info.docker_volumes,
                                 environment=environment,
                                 ports=ports)

def stop_db(info):
    if info.dbs_status != 'running':
        setupservers.console_warn("Container not running, skipping stopping.")
    docker_client.containers.get(info.dbs_container_name).stop()

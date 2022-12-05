# from __future__ import annotations
import os
import platform
import time
import typing as t
from pathlib import Path

import click
import docker
from clickactions import Actions, Command, Action
from docker.errors import NotFound
from docker.models.containers import Container
from docker.types.containers import ContainerConfig

import setupservers
import setupservers.util
from setupservers import DBServerState


# pydevd.settrace(host='localhost', port=5678, stdoutToServer=True, stderrToServer=UnicodeTranslateError,
#                 suspend=False)


class PostgresDockerParams(object):
    def __init__(self):
        self.docker_tag: t.Optional[str] = None
        self.docker_uid: t.Optional[str] = None
        self.docker_auto_remove: t.Optional[bool] = False
        self.dbs_user: t.Optional[str] = None
        self.dbs_pass: t.Optional[str] = None
        self.dbs_host: t.Optional[str] = None
        self.dbs_port: t.Optional[str] = None
        self.actions: t.Optional[t.List] = []
        self.unsafe: t.Optional[bool] = False
        self.interactive: t.Optional[bool] = False


class PostgresDockerState(DBServerState):
    def __init__(self, path: Path):
        super(PostgresDockerState, self).__init__(path)
        self.params: PostgresDockerParams = PostgresDockerParams()

        if not hasattr(self, 'container_uuid'):
            self.container_uuid: t.Optional[str] = None
        if not hasattr(self, 'container_name'):
            self.container_name: t.Optional[str] = None
        if not hasattr(self, 'volume_path'):
            self.volume_path: t.Optional[Path] = None
        if not hasattr(self, 'docker_tag'):
            self.docker_tag: t.Optional[str] = None
        if not hasattr(self, 'docker_uid'):
            self.docker_uid: t.Optional[str] = None

    def _clear(self):
        self.container_uuid = None
        self.container_name = None
        self.docker_tag = None
        self.docker_uid = None
        super(PostgresDockerState, self)._clear()


@click.command(name='postgres-docker', cls=Command)
@click.option("--work-dir", help="The work directory for this command.")
@click.option("--docker-tag", default='latest')
@click.option("--docker-uid")
@click.option("--docker-auto-remove", is_flag=True)
@click.option("--dbs-user", default='postgres')
@click.option("--dbs-pass", default='postgres')
@click.option("--dbs-host", default='localhost')
@click.option("--dbs-port", type=int, default=5432)
@click.option("--action",
              multiple=True,
              help="Various actions in desired order. Few imply others. Current actions: "
                   "dbs-start, dbs-stop, docker-remove.")
@click.option("--unsafe", is_flag=True)
@click.option("--interactive", is_flag=True)
@click.pass_context
def command(
        click_context: click.Context, work_dir, docker_tag, docker_uid, docker_auto_remove,
        dbs_user, dbs_pass, dbs_host, dbs_port, action,
        unsafe, interactive,
):
    actions: Actions = click_context.obj
    if work_dir is None:
        work_dir = click_context.command.name

    state: PostgresDockerState = actions.get_action_state(Path(work_dir) or Path(click_context.command.name),
                                                          PostgresDockerState)
    params = state.params

    params.docker_tag = docker_tag
    params.docker_uid = docker_uid
    params.docker_auto_remove = docker_auto_remove
    params.dbs_user = dbs_user
    params.dbs_pass = dbs_pass
    params.dbs_host = dbs_host
    params.dbs_port = dbs_port
    params.actions = action
    params.unsafe = unsafe
    params.interactive = interactive

    postgres_docker = PostgresDockerAction(actions, state)
    postgres_docker.run_actions()


class PostgresDockerAction(Action[PostgresDockerState]):

    def __init__(self,
                 actions: Actions,
                 state: PostgresDockerState):
        super(PostgresDockerAction, self).__init__(actions, state)
        self.docker_client: docker.DockerClient = docker.from_env()

    def run_actions(self):
        # self.checks()
        for action in self.state.params.actions:
            if action == 'dbs-start':
                self.dbs_start()
            elif action == 'dbs-stop':
                self.dbs_stop()
            elif action == 'docker-remove':
                self.docker_remove()

    def dbs_start(self):
        container: Container = None
        if self.state.container_uuid:
            container = self.docker_client.containers.get(self.state.container_uuid)
            container.start()
            attrs = container.attrs
        else:
            self.state.docker_tag = self.state.docker_tag or self.state.params.docker_tag

            if platform.system() != 'Windows':
                uid = os.getuid()
                self.state.docker_uid = self.state.docker_uid or uid or self.state.params.docker_uid

            self.state.container_name = setupservers.util.docker_container_name(__name__, self.state.path)
            self.state.dbs_user = self.state.dbs_user or self.state.params.dbs_user
            self.state.dbs_pass = self.state.dbs_pass or self.state.params.dbs_pass

            self.state.dbs_host = self.state.dbs_host or self.state.params.dbs_host
            self.state.dbs_port_preferred = self.state.dbs_port_preferred or self.state.params.dbs_port
            self.state.dbs_port = setupservers.find_free_port(self.state.dbs_host, self.state.dbs_port_preferred)

            self.state.volume_path = self.state.path / 'docker-volume'
            self.state.volume_path.mkdir(parents=True, exist_ok=True)
            volumes = {str(self.state.volume_path): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}}
            environment = {'PGDATA': '/var/lib/postgresql/data/pgdata',
                           'POSTGRES_USER': self.state.dbs_user,
                           'POSTGRES_PASSWORD': self.state.dbs_pass}
            ports = {5432: int(self.state.dbs_port)}

            container = self.docker_client.containers.run(
                "postgres:" + self.state.docker_tag,
                user=self.state.docker_uid,
                name=self.state.container_name,
                remove=self.state.params.docker_auto_remove,
                detach=True,
                volumes=volumes,
                environment=environment,
                ports=ports
            )
            self.state.container_uuid = container.id

        for i in range(10):
            container.reload()
            if container.status == 'running':
                break
            time.sleep(i)

        self.state.dbs_status = container.status
        self.state.dbs_type = 'postgres'
        self.state.save()
        self.logger.info(f"Started PostgreSQL on {self.state.dbs_host}:{self.state.dbs_port} from directory: {self.state.path}.")
        self.logger.info(f"Docker UUID: {self.state.container_uuid}")

    def dbs_stop(self):
        if self.state.container_uuid:
            container: Container = self.docker_client.containers.get(self.state.container_uuid)
            auto_remove = container.attrs['HostConfig']['AutoRemove']
            container.stop()
            if auto_remove:
                self.state._clear()
            else:
                for i in range(10):
                    container.reload()
                    if container.status == 'exited':
                        break
                    time.sleep(i)
                self.state.dbs_status = container.status
            self.logger.info(f"Stopped PostgreSQL on {self.state.dbs_host}:{self.state.dbs_port} from directory: {self.state.path}")
        else:
            self.logger.info(f"PostgreSQL already stopped from directory: {self.state.path}")
        self.state.save()

    def docker_remove(self):
        if self.state.container_uuid:
            container: Container = self.docker_client.containers.get(self.state.container_uuid)
            container.stop()
            container.remove()
            self.logger.info(f"Removing PostgreSQL Docker container id: {self.state.container_uuid}")
            self.state._clear()
            self.state.save()

    # def checks(self):
    #     if self.empty_state and self.volume_path.exists():
    #         # something went wrong and the state wasn't updated
    #         if self.interactive:
    #             if click.confirm("Docker volume exists but that state is not recorded. Delete volume?:"):
    #                 shutil.rmtree(self.volume_path)
    #             else:
    #                 self.action_state.volume_path = self.volume_path.relative_to(self.action_state.path)
    #         else:
    #             if self.unsafe:
    #                 shutil.rmtree(self.volume_path)
    #             else:
    #                 self.action_state.volume_path = self.volume_path.relative_to(self.action_state.path)

    # def _find_container(self, create: bool = False, docker_remove: bool = True) \
    #         -> t.Optional[docker.models.containers.Container]:
    #
    #     container: t.Optional[Container] = None
    #
    #     if self.state.container_uuid is not None:
    #         try:
    #             container = self.docker_client.containers.get(self.state.container_uuid)
    #         except NotFound as e:
    #             pass
    #
    #     if container is None and self.state.container_name is not None:
    #         try:
    #             container = self.docker_client.containers.get(self.state.container_name)
    #         except NotFound as e:
    #             pass
    #
    #     container_name = setupservers.util.docker_container_name(__name__, self.state.path)
    #
    #     if container is None:
    #         try:
    #             container = self.docker_client.containers.get(container_name)
    #         except NotFound as e:
    #             pass
    #
    #     if container is None and create:
    #         self.state.container_name = container_name
    #         self.state.dbs_user = self.state.dbs_user or self.state.params.dbs_user
    #         self.state.dbs_pass = self.state.dbs_pass or self.state.params.dbs_pass
    #
    #         self.state.dbs_host = self.state.dbs_host or self.state.params.dbs_host
    #         self.state.dbs_port = self.state.dbs_port or self.state.params.dbs_port
    #         self.state.dbs_port = setupservers.find_free_port(self.state.dbs_host, self.state.dbs_port)
    #
    #         self.state.volume_path = self.state.volume_path or self.state.path / 'docker-volume'
    #
    #         port_bindings = {'5432/tcp': (self.state.dbs_host, str(self.state.dbs_port))}
    #         # environment = {'PGDATA': '/var/lib/postgresql/data/pgdata',
    #         #                'POSTGRES_USER': self.state.dbs_user,
    #         #                'POSTGRES_PASSWORD': self.state.dbs_pass}
    #         binds = {str(self.state.volume_path): {'bind': '/var/lib/postgresql/data', 'mode': 'rw'}}
    #
    #         environment = ['PGDATA=/var/lib/postgresql/data/pgdata',
    #                        f'POSTGRES_USER={self.state.dbs_user}',
    #                        f'POSTGRES_PASSWORD={self.state.dbs_pass}']
    #
    #         self.state.docker_tag = self.state.docker_tag or self.state.params.docker_tag
    #         self.state.docker_uid = self.state.docker_uid or self.state.params.docker_uid
    #
    #         host_config = None
    #         if docker_remove:
    #             host_config = self.docker_client.api.create_host_config(binds=binds, port_bindings=port_bindings,
    #                                                                     auto_remove=True)
    #         else:
    #             host_config = self.docker_client.api.create_host_config(binds=binds, port_bindings=port_bindings)
    #
    #         container_config: ContainerConfig = self.docker_client.api.create_container_config(
    #             image='postgres:' + self.state.docker_tag,
    #             command=None,
    #             user=self.state.docker_uid,
    #             detach=True,
    #             ports=[('5432', 'tcp')],
    #             environment=environment,
    #             volumes=['/var/lib/postgresql/data'],
    #             host_config=host_config
    #         )
    #
    #         result = self.docker_client.api.create_container_from_config(container_config, self.state.container_name)
    #         self.state.container_uuid = result['Id']
    #
    #     self.state.save()
    #     return self.docker_client.containers.get(self.state.container_uuid)

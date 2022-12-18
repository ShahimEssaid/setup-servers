import errno
import os
import pathlib
import platform
import shutil
import signal
import subprocess
import time
import typing as t
from pathlib import Path
from subprocess import CompletedProcess
from typing import Union, Any

import click
import git
import yaml
from clickactions import Command, Action, Actions
from git import Repo

import setupservers
from setupservers import FhirServerState


class HapiJpaStarterParams(object):
    def __init__(self):
        self.git_url: t.Optional[str] = None
        self.git_ref: t.Optional[str] = None
        self.hapi_port: t.Optional[int] = None
        self.mvn_local_repo: t.Optional[str] = None
        self.mvn_rebuild: t.Optional[bool] = False
        self.dbs_work_dir: t.Optional[str] = None
        self.actions: t.Optional[t.List[str]] = []

        self.java_debug: t.Optional[bool] = False
        self.java_debug_attach: t.Optional[bool] = False
        self.java_debug_suspend: t.Optional[bool] = False
        self.java_debug_ip: t.Optional[str] = None
        self.java_debug_port: t.Optional[int] = None

        self.spring_profiles: t.Optional[str] = None


class HapiJpaStarterState(FhirServerState):
    def __init__(self, path: Path):
        super(HapiJpaStarterState, self).__init__(path)
        self.params: HapiJpaStarterParams = HapiJpaStarterParams()

        if not hasattr(self, 'git_sha'):
            self.git_sha: t.Optional[str] = None


@click.command(name='hapi-jpa-starter', cls=Command)
@click.option('--work-dir', help='The work directory for this run of the command.')
@click.option('--git-url', default='https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git')
@click.option('--git-ref', default='master')
@click.option('--hapi-port', type=int, default=8888)
@click.option('--mvn-local-repo', default='.m2')
@click.option('--mvn-rebuild', is_flag=True)
@click.option('--dbs-work-dir')
@click.option('--spring-profiles', default='local')
@click.option('--action', multiple=True, help='hapi-start  hapi-stop')
@click.option('--java-debug', is_flag=True)
@click.option('--java-debug-attach', is_flag=True)
@click.option('--java-debug-suspend', is_flag=True)
@click.option('--java-debug-ip', default='127.0.0.1')
@click.option('--java-debug-port', type=int, default=8999)
@click.pass_context
def command(
        ctx: click.Context,
        work_dir,
        git_url,
        git_ref,
        hapi_port,
        mvn_local_repo,
        mvn_rebuild,
        dbs_work_dir,
        action,

        java_debug,
        java_debug_attach,
        java_debug_suspend,
        java_debug_ip,
        java_debug_port,

        spring_profiles
):
    actions: Actions = ctx.obj
    state: HapiJpaStarterState = actions.get_action_state(work_dir or ctx.command.name, HapiJpaStarterState)

    params = state.params
    params.git_url = git_url
    params.git_ref = git_ref
    params.hapi_port = hapi_port
    params.mvn_local_repo = mvn_local_repo
    params.mvn_rebuild = mvn_rebuild
    params.dbs_work_dir = dbs_work_dir
    params.actions = action

    params.java_debug = java_debug
    params.java_debug_attach = java_debug_attach
    params.java_debug_suspend = java_debug_suspend
    params.java_debug_ip = java_debug_ip
    params.java_debug_port = java_debug_port

    params.spring_profiles = spring_profiles

    hapi = HapiJpaStarterAction(actions, state)
    hapi.run()


MAVEN_DIR = pathlib.Path('apache-maven-3.8.6')
MAVEN_TAR_GZ = pathlib.Path(f'{MAVEN_DIR}-bin.tar.gz')
MAVEN_URL = f'https://archive.apache.org/dist/maven/maven-3/3.8.6/binaries/{MAVEN_TAR_GZ}'

# HAPI_GIT_URL = 'https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git'
HAPI_GIT_DIR = pathlib.Path('hapi-jpa-starter')
HAPI_RUN_DIR = 'hapi-run'


class HapiJpaStarterAction(Action[HapiJpaStarterState]):
    def __init__(self, actions: Actions, state: HapiJpaStarterState):
        super(HapiJpaStarterAction, self).__init__(actions, state)
        self.maven_home = self.state.path / MAVEN_DIR

        mvn_local_repo = Path(state.params.mvn_local_repo)
        if mvn_local_repo.is_absolute():
            self.maven_repo = mvn_local_repo
        else:
            self.maven_repo = self.state.path / mvn_local_repo

        if platform.system() == 'Windows':
            self.mvn_cmd = str(
                self.state.path / MAVEN_DIR / 'bin' / 'mvn.cmd')
        else:
            self.mvn_cmd = str(
                self.state.path / MAVEN_DIR / 'bin' / 'mvn')

        self.hapi_repo = self.state.path / HAPI_GIT_DIR
        self.hapi_run_path: Path = self.state.path / HAPI_RUN_DIR
        self.hapi_run_path.mkdir(parents=True, exist_ok=True)

        self.db_server: t.Optional[setupservers.DBServerState] = None
        if self.state.params.dbs_work_dir is not None:
            self.db_server = self.actions.get_action_state(self.state.params.dbs_work_dir, setupservers.DBServerState)

    def run(self):

        for action in self.state.params.actions:
            if action == 'hapi-start':
                self._hapi_start()
            elif action == 'hapi-stop':
                self._hapi_stop()

    def _hapi_start(self):
        self._hapi_build_prepare()

        if self.state.pid is not None and not setupservers.pid_exists(self.state.pid):
            self.state.pid = None
            self.state.status = 'stopped'

        if self.state.git_sha != self.requested_sha or self.state.params.mvn_rebuild:
            # we need to rebuild
            if self.state.status == 'running':
                raise Exception('Requested to start hapi with a different build but it is running. Stop hapi first.')
            self._hapi_build()
        else:
            if self.state.status == 'running':
                return

        with open(self.hapi_run_path / 'application-local.yaml') as f:
            hapi_local_config = yaml.safe_load(f)
        if hapi_local_config is None:
            hapi_local_config = {}

        if 'server' not in hapi_local_config:
            hapi_local_config['server'] = {}

        port = setupservers.find_free_port('localhost', self.state.params.hapi_port)

        hapi_local_config['server']['port'] = port

        if 'hapi' not in hapi_local_config:
            hapi_local_config['hapi'] = {}
        if 'fhir' not in hapi_local_config['hapi']:
            hapi_local_config['hapi']['fhir'] = {}

        if 'tester' not in hapi_local_config['hapi']['fhir']:
            hapi_local_config['hapi']['fhir']['tester'] = {}
        if 'home' not in hapi_local_config['hapi']['fhir']['tester']:
            hapi_local_config['hapi']['fhir']['tester']['home'] = {}

        self.state.fhir_url = f'http://localhost:{port}/fhir'
        hapi_local_config['hapi']['fhir']['tester']['home']['server_address'] = self.state.fhir_url

        with open(self.hapi_run_path / 'application-local.yaml', 'w') as f:
            yaml.safe_dump(hapi_local_config, f)

        args = ['java',
                f'-Dspring.profiles.active={self.state.params.spring_profiles}',
                f'-Dlogging.config={str(self.hapi_run_path / "logback.xml")}'
                ]

        if self.state.params.java_debug:
            server = 'n' if self.state.params.java_debug_attach else 'y'
            suspend = 'y' if self.state.params.java_debug_suspend else 'n'
            address = self.state.params.java_debug_ip
            port = setupservers.find_free_port(address, int(self.state.params.java_debug_port))
            agent = f"-agentlib:jdwp=transport=dt_socket,server={server},suspend={suspend},address={address}:{port}"
            args.append(agent)
            self.logger.info(f"HAPI {self.state.path.name} debugger configured as: {agent}")

        args.extend([
            '-jar',
            'ROOT.war'
        ])

        if self.db_server is not None and self.db_server.dbs_type == 'postgres':
            args.extend([
                f'--spring.datasource.url=jdbc:postgresql://localhost:{self.db_server.dbs_port}/postgres',
                '--spring.datasource.username=postgres',
                '--spring.datasource.password=postgres',
                '--spring.datasource.driverClassName=org.postgresql.Driver',
                '--spring.jpa.properties.hibernate.dialect=ca.uhn.fhir.jpa.model.dialect.HapiFhirPostgres94Dialect'
            ])
        p = subprocess.Popen(args, cwd=self.hapi_run_path)
        self.state.pid = p.pid
        self.state.status = 'running'
        self.state.save()
        self.logger.info(f"HAPI FHIR endpoint starting on: {self.state.fhir_url}")

    def _hapi_stop(self):
        if self.state.pid is None:
            self.logger.info("HAPI already stopped.")
            return
        try:
            os.kill(self.state.pid, signal.SIGTERM)
        except OSError as err:
            if err.errno == errno.ESRCH:
                self.logger.info("HAPI not running but state file is not up to date.")

        for i in range(10):
            try:
                os.kill(self.state.pid, 0)
                time.sleep(i)
            except OSError as err:
                if err.errno == errno.ESRCH:
                    # no such process
                    break
                else:
                    # some other error
                    raise err
        self.state.pid = None
        self.state.status = 'stopped'
        self.state.save()
        self.logger.info(f"HAPI stopped")

    def _hapi_build_prepare(self):
        # install maven if needed
        if not self.maven_home.exists():
            setupservers.download_file(MAVEN_URL, self.state.path / MAVEN_TAR_GZ)
            setupservers.unpack_targz(self.state.path / MAVEN_TAR_GZ, self.state.path)

        # clone and checkout hapi starter
        if not self.hapi_repo.exists():
            git.Repo = git.Repo.clone_from(self.state.params.git_url, self.hapi_repo)

        repo = Repo(self.hapi_repo)
        origin = repo.remotes.origin
        origin.fetch()

        if self.state.params.git_ref in origin.refs:
            repo.head.reference = origin.refs[self.state.params.git_ref].commit
        elif self.state.params.git_ref in repo.tags:
            repo.head.reference = repo.tags[self.state.params.git_ref].commit
        else:
            repo.head.reference = repo.commit(self.state.params.git_ref)

        repo.head.reset(index=True, working_tree=True)

        self.requested_sha = repo.head.object.hexsha
        repo.close()

    def _hapi_build(self):
        # build and install
        completed: Union[CompletedProcess[Any], CompletedProcess[bytes]] = subprocess.run(
            [
                self.mvn_cmd,
                f'-Dmaven.repo.local={str(self.maven_repo)}',
                '-U',
                '-f',
                str(self.hapi_repo / 'pom.xml'),
                '-Pboot',
                'clean',
                'package'
            ],
            capture_output=True)
        self._log_subprocess_output(completed)
        if completed.returncode != 0:
            raise Exception(f'Maven build failed with exit code {completed.returncode}. See log files.')

        shutil.copy(src=self.hapi_repo / 'target' / 'ROOT.war', dst=self.hapi_run_path / 'ROOT.war')
        shutil.copy(src=self.hapi_repo / 'src' / 'main' / 'resources' / 'application.yaml',
                    dst=self.hapi_run_path / 'application.yaml')
        if not (self.hapi_run_path / 'application-local.yaml').exists():
            with open(self.hapi_run_path / 'application-local.yaml', 'w'):
                pass
        if not (self.hapi_run_path / 'logback.xml').exists():
            shutil.copy(src=self.hapi_repo / 'src' / 'main' / 'resources' / 'logback.xml',
                        dst=self.hapi_run_path / 'logback.xml')

        self.state.git_sha = self.requested_sha
        self.state.status = 'built'
        self.state.save()

    def _log_subprocess_output(self, completed: CompletedProcess):
        for line in completed.stdout.splitlines():
            self.logger.debug(line.decode('utf-8'))
        for line in completed.stderr.splitlines():
            self.logger.error(line.decode('utf-8'))

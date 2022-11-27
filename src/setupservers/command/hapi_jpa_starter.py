import os
import pathlib
import sys
from pathlib import Path

import click
import clickactions
import git
from clickactions import ActionState, DictToAttr
from git import Repo

import setupservers

MAVEN_URL = 'https://archive.apache.org/dist/maven/maven-3/3.8.6/binaries/apache-maven-3.8.6-bin.tar.gz'
MAVEN_TARGZ = pathlib.Path('apache-maven-3.8.6.tar.gz')
MAVEN_DIR = pathlib.Path('apache-maven-3.8.6')

HAPI_GIT_URL = 'https://github.com/hapifhir/hapi-fhir-jpaserver-starter.git'
HAPI_GIT_DIR = pathlib.Path('hapi-jpa-starter')


class HapiJpaStarter:
    def __init__(self, action_state: clickactions.ActionState, actions: clickactions.Actions):
        self.action_state: clickactions.ActionState = action_state
        self.actions: clickactions.Actions = actions
        self.maven_home = self.action_state.path / MAVEN_DIR
        self.maven_repo = self.action_state.path / '.m2'
        self.hapi_repo = self.action_state.path / HAPI_GIT_DIR

        if sys.platform.startswith('win'):
            self.mvn = str(
                self.action_state.path / MAVEN_DIR / 'bin' / 'mvn.cmd') + f' -Dmaven.repo.local={str(self.maven_repo)}'
        else:
            self.mvn = str(
                self.action_state.path / MAVEN_DIR / 'bin' / 'mvn') + f' -Dmaven.repo.local={str(self.maven_repo)}'

    def run(self):
        self.unpack_maven()
        self.maven_test_run()
        self.hapi_checkout()
        self.hapi_build()

        pass

    def unpack_maven(self):
        if not self.maven_home.exists():
            self.action_state.path.mkdir(parents=True, exist_ok=True)
            setupservers.download_file(MAVEN_URL, self.action_state.path / MAVEN_TARGZ)
            setupservers.unpack_targz(self.action_state.path / MAVEN_TARGZ, self.action_state.path)

    def maven_test_run(self):
        os.system(self.mvn + ' --version')

    def hapi_checkout(self):
        if not self.hapi_repo.exists():
            git.Repo = git.Repo.clone_from(HAPI_GIT_URL, self.hapi_repo)

        repo = Repo(self.hapi_repo)
        repo.remotes.origin.fetch()
        repo.git.checkout(self.action_state.kwargs.git_ref)

    def hapi_build(self):
        os.system(self.mvn + f" -f {str(self.hapi_repo / 'pom.xml')} -Pboot clean package")


@click.command(name='hapi-jpa-starter', cls=clickactions.Command)
@click.option("--work-dir", help="The work directory for this run of the command.")
@click.option("--git-ref")
@click.pass_context
def action_cli(
        ctx: click.Context,
        work_dir: Path = None,
        **kwargs
):
    work_dir = work_dir or Path(action_cli.name)
    actions: clickactions.Actions = ctx.obj
    action_state: ActionState = actions.get_action_state(work_dir)
    action_state.kwargs = DictToAttr(kwargs)

    hapi = HapiJpaStarter(action_state, actions)
    hapi.run()

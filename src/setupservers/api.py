import os
import pathlib
import sys
import types
from importlib.machinery import SourceFileLoader


def load_module(module_name: str, module_path: pathlib.Path) -> types.ModuleType:
    module: types.ModuleType = SourceFileLoader("setupservers." + module_name, str(module_path)).load_module()
    loaded_modules[module.__name__] = module
    return module


class SetupBase:
    def __init__(self, setup_name: str, setup_path: pathlib.Path):
        self.setup_name = setup_name
        self.setup_path = setup_path


class SetupProviderBase:
    def __init__(self, setup: SetupBase, provider_directory: pathlib.Path):
        if not provider_directory.exists() or not provider_directory.is_dir():
            raise Exception("Provider path is not a directory or does not exist: " + str(provider_directory))
        self.setup = setup
        self.provider_directory: pathlib.Path = provider_directory
        self.provider_path: pathlib.Path = None
        self.provider_module: types.ModuleType = None

    def find_provider_module(self) -> types.ModuleType:
        dir_parts = str(self.provider_directory.name).split("--")
        if len(dir_parts) > 3:
            print("Setup provider directory has too many underscores: " + str(self.provider_directory))
            sys.exit(11)
        if len(dir_parts) == 3:
            provider_name = dir_parts[1]
        else:
            provider_name = dir_parts[0]
        provider_file_name = provider_name + ".py"
        self.provider_path = self.provider_directory / provider_file_name
        if not self.provider_path.exists():
            self.provider_path = self.provider_directory / (self.setup.setup_name + ".py")
        if not self.provider_path.exists():
            raise Exception("Failed to find provider path for provider directory {dir} and setup name {name}".format(
                dir=self.provider_directory, name=self.setup.setup_name))
        # we have the provider path. Build a module name to load it
        provider_module_name = self.setup.setup_name + "_"
        if len(dir_parts) == 3:
            provider_module_name += dir_parts[1] + "_" + dir_parts[2]
        else:
            provider_module_name += "_".join(dir_parts)

        self.provider_module = load_module(provider_module_name, self.provider_path)

        return self.provider_module


class ServersSetup:
    def __init__(self):
        self.home_directory = pathlib.Path(os.curdir).absolute()
        self.working_directory = pathlib.Path(os.curdir).absolute() / "working-directory"

    def run(self):
        print("Running from ServersSetup")
        print("Home directory: " + str(self.home_directory))
        print("Working directory: " + str(self.working_directory))
        print()


servers_setup = ServersSetup()

loaded_modules = {}

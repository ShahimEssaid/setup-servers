import click
import clickactions


class SetupServerCommands(clickactions.Commands):
    def __init__(self, **kwargs):
        super(SetupServerCommands, self).__init__(command_entry_points={'clickactions.command': '^(py-debug)$',
                                                                   'setupservers.command': None}, chain=True, **kwargs)


@click.command(cls=SetupServerCommands)
def commands():
    # print("SetupServersCli running")
    pass

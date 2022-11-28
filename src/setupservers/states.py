import pathlib
import typing as t

from clickactions import ActionState


class DBUser:
    pass


class DBDatabase:
    pass


class DBServerState(ActionState):
    def __init__(self, path: pathlib.Path):
        super(DBServerState, self).__init__(path)

        if not hasattr(self, 'dbs_type'):
            self.dbs_type: t.Optional[str] = None
        if not hasattr(self, 'dbs_user'):
            self.dbs_user: t.Optional[str] = None
        if not hasattr(self, 'dbs_pass'):
            self.dbs_pass: t.Optional[str] = None
        if not hasattr(self, 'dbs_host'):
            self.dbs_host: t.Optional[str] = None
        if not hasattr(self, 'dbs_port'):
            self.dbs_port: t.Optional[str] = None
        if not hasattr(self, 'dbs_port_preferred'):
            self.dbs_port_preferred: t.Optional[str] = None
        if not hasattr(self, 'dbs_status'):
            self.dbs_status: t.Optional[str] = None

        if not hasattr(self, 'users'):
            self.users: t.Dict[str, DBUser] = {}
        if not hasattr(self, 'databases'):
            self.databases: t.Dict[str, DBDatabase] = {}

    def _clear(self):
        self.dbs_status = None
        self.dbs_host = None
        self.dbs_port = None
        self.dbs_port_preferred = None


class FhirServerState(ActionState):
    def __init__(self, path: pathlib.Path):
        super(FhirServerState, self).__init__(path)

        if not hasattr(self, 'fhir_url'):
            self.fhir_url: t.Optional[str] = None
        if not hasattr(self, 'fhir_version'):
            self.fhir_version: t.Optional[str] = None
        if not hasattr(self, 'pid'):
            self.pid: t.Optional[int] = None
        if not hasattr(self, 'status'):
            self.status: t.Optional[str] = None


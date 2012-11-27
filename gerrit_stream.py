import json
import subprocess


class GerritStream:
    def __init__(self, host, user, port=22, key=None):
        self.host = host
        self.user = user
        self.port = port
        self.key = key
        self.command = self._build_command()
        self._create_connection()

    def _build_command(self):
        command = ['ssh',
                   '{0}@{1}'.format(self.user, self.host),
                   '-p', str(self.port),
                   '-o', 'StrictHostKeyChecking=no']
        if self.key is not None:
            command.extend(('-i', str(self.key)))
        command.extend(('gerrit', 'stream-events'))
        return command

    def _create_connection(self):
        self.subproc = subprocess.Popen(self.command,
                                        stdin=subprocess.DEVNULL,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.DEVNULL,
                                        universal_newlines=True)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.subproc.stdout.readline()
        return json.loads(line)


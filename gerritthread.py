
'''
    Copyright 2010, The Android Open Source Project

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
'''

# bridge script to irc channel from gerrit livestream
# written by jeff sharkey and kenny root
# with modifications by jeremy morse, peter law and richard barlow

import logging
import paramiko
import simplejson
import socket
import threading
import time

# config file section titles
GERRIT = "GerritServer"

class GerritThread(threading.Thread):
    def __init__(self, config, event_handler):
        super(GerritThread, self).__init__()
        self.setDaemon(True)
        self.config = config
        self.handler = event_handler
        self.logger = logging.getLogger('gerritbot.gerritthread')

    def run(self):
        while True:
            self.run_internal()
            self.logger.info(self, "Sleeping and wrapping around.")
            time.sleep(5)

    def run_internal(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        host = self.config.get(GERRIT, "host")
        port = self.config.getint(GERRIT, "port")
        user = self.config.get(GERRIT, "user")
        privkey = self.config.get(GERRIT, "privkey")

        try:
            self.logger.info("Connecting to '%s'.", host)
            client.connect(host, port, user, key_filename=privkey, timeout=60)
            client.get_transport().set_keepalive(60)

            stdin, stdout, stderr = client.exec_command("gerrit stream-events")
            for line in stdout:
                self.logger.debug(line)
                try:
                    event = simplejson.loads(line)
                    self.handler(event)
                except ValueError, KeyError:
                    self.logger.exception("Error handling event '%s'.", line)
            client.close()
        except:
            self.logger.exception("Unexpected error")


def printing_handler(event):
    """
    A trivial hadler which just dumps the event object to stdout,
    to show how it looks.
    """
    print(event)

if __name__ == '__main__':
    """
    A dummy main section to show how you might run your script.
    """
    import ConfigParser
    import sys

    config = ConfigParser.ConfigParser()
    config.read("gerritbot.conf")

    gerrit = GerritThread(config, printing_handler); gerrit.start()

    while True:
        try:
            line = sys.stdin.readline()
        except KeyboardInterrupt:
            break

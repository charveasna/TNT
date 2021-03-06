# Copyright (c) 2019, Substratum LLC (https://substratum.net) and/or its affiliates. All rights reserved.
import pytest
import pexpect
from node_docker_commands import NodeDockerCommands

class TestNodeDockerCommands:

    @pytest.fixture
    def mocks(self, mocker):
        self.mock_executor = mocker.patch('node_docker_commands.Executor').return_value
        self.mock_terminal_executor = mocker.patch('node_docker_commands.TerminalExecutor')
        mock_os = mocker.patch('node_docker_commands.os')
        mock_os.getcwd.return_value = 'cwd'
        self.mock_print = mocker.patch('__builtin__.print')

    def test_init(self, mocks):
        subject = NodeDockerCommands('bacon', 'ip function')

        assert subject.get_ip == 'ip function'
        assert subject.name == 'bacon'
        self.mock_terminal_executor.assert_called_with(self.mock_executor)

    def test_start_nonexistent(self, mocks):
        subject = NodeDockerCommands('bacon', lambda: '1.2.3.4')
        self.mock_executor.execute_async.return_value.expect.return_value = 1  # nonexistent
        node_args = {
            'dns-servers': '--dns-servers 1.1.1.1',
            'log-level': '--log-level trace',
            'data-directory': '--data-directory /tmp'
        }
        self.mock_executor.execute_sync.return_value = 'success'

        result = subject.start(node_args)

        self.mock_executor.execute_async.assert_called_with([
            'docker', 'ps', '--all', '-q', '-f name=bacon'
        ])
        self.mock_executor.execute_async.return_value.expect.assert_called_with(
            ['[0-9a-fA-F]+', pexpect.EOF],
            timeout=None
        )

        self.mock_executor.execute_sync.assert_called_with([
            'docker', 'run',
            '--detach',
            '--ip', '1.2.3.4',
            '--dns', '127.0.0.1',
            '--name', 'bacon',
            '--hostname', 'bacon',
            '--net', 'test_net',
            '--volume', 'cwd/binaries/:/node_root/node',
            'test_net_tools',
            '/node_root/node/SubstratumNode',
            '--dns-servers', '1.1.1.1',
            '--log-level', 'trace',
            '--data-directory', '/tmp',
            '--ip', '1.2.3.4',
            '--earning-wallet', '0x01020304010203040102030401020304EEEEEEEE',
            '--consuming-private-key', '89d59b93ef6a94c977e1812b727d5f123f7d825ab636e83aad3e2845a68eaedb'
        ])

        assert result == 'success'

    def test_start_existing(self, mocks, mocker):
        subject = NodeDockerCommands('bacon', lambda: '1.2.3.4')
        self.mock_executor.execute_async.return_value.expect.return_value = 0  # existing
        node_args = {
            'dns-servers': '--dns-servers 1.1.1.2',
            'log-level': '--log-level debug',
            'data-directory': '--data-directory /tmp',
            'additional-args': '--neighbors howdy'
        }
        self.mock_executor.execute_sync.return_value = 'success'

        result = subject.start(node_args)

        self.mock_executor.execute_async.assert_called_with([
            'docker', 'ps', '--all', '-q', '-f name=bacon'
        ])
        self.mock_executor.execute_async.return_value.expect.assert_called_with(
            ['[0-9a-fA-F]+', pexpect.EOF],
            timeout=None
        )

        assert self.mock_executor.execute_sync.mock_calls == [
            mocker.call([
                'docker', 'rm', '-f', 'bacon'
            ]),
            mocker.call([
                'docker', 'run',
                '--detach',
                '--ip', '1.2.3.4',
                '--dns', '127.0.0.1',
                '--name', 'bacon',
                '--hostname', 'bacon',
                '--net', 'test_net',
                '--volume', 'cwd/binaries/:/node_root/node',
                'test_net_tools',
                '/node_root/node/SubstratumNode',
                '--dns-servers', '1.1.1.2',
                '--log-level', 'debug',
                '--data-directory', '/tmp',
                '--ip', '1.2.3.4',
                '--earning-wallet', '0x01020304010203040102030401020304EEEEEEEE',
                '--consuming-private-key', '89d59b93ef6a94c977e1812b727d5f123f7d825ab636e83aad3e2845a68eaedb',
                '--neighbors', 'howdy'
            ])
        ]

        assert result == 'success'

    def test_stop(self, mocks):
        subject = NodeDockerCommands('bacon', None)
        self.mock_executor.execute_sync.return_value = 'stopped'

        result = subject.stop()

        self.mock_executor.execute_sync.assert_called_with([
            'docker', 'stop', '-t0', 'bacon'
        ])

        assert result == 'stopped'

    def test_cat_logs(self, mocks):
        subject = NodeDockerCommands('bacon', None)
        self.mock_executor.execute_async.return_value = 'meow'

        result = subject.cat_logs()

        self.mock_executor.execute_async.assert_called_with(
            ["docker", "exec", "-it", "bacon", "cat", "/tmp/SubstratumNode_rCURRENT.log"]
        )

        assert result == 'meow'

    def test_retrieve_logs(self, mocks):
        subject = NodeDockerCommands('bacon', None)
        self.mock_executor.execute_sync.return_value = 'logs!'

        result = subject.retrieve_logs('chicago')

        self.mock_executor.execute_sync.assert_called_with([
            'docker', 'cp', 'bacon:/tmp/SubstratumNode_rCURRENT.log', 'chicago'
        ])

        assert result == 'logs!'

    def test_update(self, mocks):
        subject = NodeDockerCommands('bacon', None)

        result = subject.update('000000100000011000000111001111')

        self.mock_print.assert_called_with('Binaries are volume-mapped for Docker-based Nodes; no update is required.')

        assert result == 0

    def test_tail(self, mocks):
        subject = NodeDockerCommands('bacon', lambda: '1.2.3.4')
        self.mock_terminal_executor.return_value.execute_in_new_terminal.return_value = 'tailing'

        result = subject.tail()

        self.mock_terminal_executor.return_value.execute_in_new_terminal.assert_called_with(
            '\"bacon(1.2.3.4)\" docker exec -it bacon tail -f -n 250 /tmp/SubstratumNode_rCURRENT.log'
        )

        assert result == 'tailing'

    def test_shell(self, mocks):
        subject = NodeDockerCommands('bacon', lambda: '1.2.3.4')
        self.mock_terminal_executor.return_value.execute_in_new_terminal.return_value = 'shelling'

        result = subject.shell()

        self.mock_terminal_executor.return_value.execute_in_new_terminal.assert_called_with('\"bacon(1.2.3.4)\" docker exec -it bacon bash')

        assert result == 'shelling'

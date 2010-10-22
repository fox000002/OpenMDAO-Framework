"""
Test object service sub-objects for better test coverage.
Most functionality is exercised by test_distsim.py or test_extcode.py,
but in an unobservable manner as far as test coverage is concerned.
"""

import logging
import os.path
import shutil
import sys
import time
import unittest
import nose

from openmdao.main.objserverfactory import ObjServerFactory, ObjServer, \
                                           start_server
from openmdao.main.rbac import Credentials, set_credentials
from openmdao.util.testutil import assert_raises


# Used to disable tests when running full suite on Windows.
_NAME = __name__


class TestCase(unittest.TestCase):
    """ Test object service sub-objects for better test coverage. """

    def test_factory(self):
        # FIXME: temporarily disable this test on Windows.
#        if _NAME != '__main__' and sys.platform == 'win32':
#            raise nose.SkipTest()

        logging.debug('')
        logging.debug('test_factory')

        testdir = 'test_factory'
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        os.mkdir(testdir)
        os.chdir(testdir)

        try:
            # Create a factory.
            set_credentials(Credentials())
            factory = ObjServerFactory()

            # List types.
            types = factory.get_available_types()
            names = [name for name, version in types]
            self.assertTrue('openmdao.test.ExecComp' in names)

            # Create a component.
            exec_comp = factory.create('openmdao.test.ExecComp')
            exec_comp.run()

            # Force failed factory server startup via invalid port.
            assert_raises(self, "start_server(port='xyzzy')",
                          globals(), locals(), RuntimeError,
                          'Server startup failed')
        finally:
            os.chdir('..')
            if sys.platform == 'win32':
                time.sleep(2)  # Wait for process shutdown.
            shutil.rmtree(testdir)

    def test_server(self):
        logging.debug('')
        logging.debug('test_server')
        
        testdir = 'test_server'
        if os.path.exists(testdir):
            shutil.rmtree(testdir)
        os.mkdir(testdir)
        os.chdir(testdir)

        try:
            # Create a server.
            server = ObjServer()

            # Create a component.
            exec_comp = server.create('openmdao.test.ExecComp')
            exec_comp.run()
            egg_info = exec_comp.save_to_egg('exec_comp', '0')

            # Echo some arguments.
            args = server.echo('Hello', 'world!')
            self.assertEqual(args[0], 'Hello')
            self.assertEqual(args[1], 'world!')

            # Execute a command.
            cmd = 'dir' if sys.platform == 'win32' else 'ls'
            return_code, error_msg = \
                server.execute_command(cmd, None, 'cmd.out', None, None, 0, 10)
            self.assertEqual(return_code, 0)

            return_code, error_msg = \
                server.execute_command('no-such-command', None, 'stdout', 'stderr',
                                       None, 0, 10)
            self.assertNotEqual(return_code, 0)

            # Load a model.
            obj = server.load_model(egg_info[0])
            obj.run()

            assert_raises(self, "server.load_model('no-such-egg')",
                          globals(), locals(), ValueError,
                          "'no-such-egg' not found.")

            # Bogus file accesses.
            assert_raises(self, "server.open('../xyzzy', 'r')", globals(), locals(),
                          RuntimeError, "Can't open '../xyzzy', not within root ")
            assert_raises(self, "server.open('xyzzy', 'r')", globals(), locals(),
                          IOError, "[Errno 2] No such file or directory: 'xyzzy'")

            # Create a file.
            with server.open('xyzzy', 'w') as out:
                 out.write('Hello world!\n')
                 out.flush()

            # Zip it.
            server.pack_zipfile(['xyzzy'], 'zipped')

            # Make it read-only.
            server.chmod('zipped', 0400)

            if sys.platform == 'win32':
                msg = '[Error 2] The system cannot find the file specified'
            else:
                msg = "[Errno 2] No such file or directory: 'no-such-file'"
            assert_raises(self, "server.chmod('no-such-file', 0400)",
                          globals(), locals(), OSError, msg) 

            # Get stats.
            info = server.stat('zipped')

            assert_raises(self, "server.stat('no-such-file')",
                          globals(), locals(), OSError, msg)

            # Remove zipped contents.
            server.remove('xyzzy')

            if sys.platform == 'win32':
                msg = '[Error 2] The system cannot find the file specified'
            else:
                msg = "[Errno 2] No such file or directory: 'xyzzy'"
            assert_raises(self, "server.remove('xyzzy')",
                          globals(), locals(), OSError, msg)

            # Unpack.
            server.unpack_zipfile('zipped')
            server.chmod('zipped', 0600)  # Ensure we can remove under Windows.

            # Verify contents.
            inp = server.open('xyzzy', 'r')
            try:
                data = inp.read()
                self.assertEqual(data, 'Hello world!\n')
            finally:
                inp.close()

        finally:
            os.chdir('..')
            if sys.platform == 'win32':
                time.sleep(2)  # Wait for process shutdown.
            shutil.rmtree(testdir)


if __name__ == '__main__':
    sys.argv.append('--cover-package=openmdao.main')
    sys.argv.append('--cover-erase')
    nose.runmodule()


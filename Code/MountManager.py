
from panda3d.core import Filename, VirtualFileSystem, getModelPath
from DebugObject import DebugObject

from direct.stdpy.file import join, isdir, isfile
import os


class MountManager(DebugObject):

    """ This classes mounts the required directories for the pipeline to run.
    This is important if the pipeline is in a subdirectory for example. The mount
    manager also handles the lock, storing the current PID into a file named
    instance.pid and ensuring that there is only 1 instance of the pipeline running
    at one time. """

    def __init__(self):
        """ Creates a new mount manager """
        DebugObject.__init__(self, "MountManager")
        self.writePath = "Temp/"
        self.basePath = "."
        self.lockFile = "instance.pid"

    def setWritePath(self, pth):
        """ Set a writable directory for generated files. This can be a string
        path name or a multifile with openReadWrite(). If no pathname is set
        then the root directory is used.

        Applications are usually installed system wide and wont have write
        access to the basePath. It will be wise to at least use tempfile
        like tempfile.mkdtemp(prefix='Shader-tmp'), or an application directory
        in the user's home/app dir."""

        self.writePath = Filename.fromOsSpecific(pth).getFullpath()

    def setBasePath(self, pth):
        """ Sets the path where the base shaders and models on are contained. This
        is usually the root of the rendering pipeline folder """
        self.debug("Set base path to '" + pth + "'")
        self.basePath = Filename.fromOsSpecific(pth).getFullpath()

    def getLock(self):
        """ Checks if we are the only instance running. If there is no instance running,
        write the current PID to the instance.pid file. If the instance file exists,
        checks if the specified process still runs. This way only 1 instance of
        the pipeline can be run at one time. """

        # Check if there is a lockfile at all
        if isfile(self.lockFile):
            # Read process id from lockfile
            try:
                with open(self.lockFile, "r") as handle:
                    pid = int(handle.readline())
            except Exception, msg:
                self.error("Failed to read lockfile")
                return False

            # Check if the process is still running
            if self._checkPIDRunning(pid):
                self.error("Found running instance")
                return False

            # Process is not running anymore, we can write lockfile and continue
            self._writeLock()
            return True

        else:
            # When there is no lockfile, just create it and continue
            self._writeLock()
            return True

    def _checkPIDRunning(self, pid):
        """ Checks if a pid is still running """

        # Code snippet from ntrrgc
        # http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid

        if os.name == 'posix':
            import errno
            if pid < 0:
                return False
            try:
                os.kill(pid, 0)
            except OSError as e:
                return e.errno == errno.EPERM
            else:
                return True
        else:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            SYNCHRONIZE = 0x100000

            process = kernel32.OpenProcess(SYNCHRONIZE, 0, pid)
            if process != 0:
                kernel32.CloseHandle(process)
                return True
            else:
                return False

    def _writeLock(self):
        """ Internal method to write the current pid to the instance.pid lockfile """
        with open(self.lockFile, "w") as handle:
            handle.write(str(os.getpid()))

    def mount(self):
        """ Inits the VFS Mounts """

        self.debug("Setting up virtual filesystem.")
        vfs = VirtualFileSystem.getGlobalPtr()

        # Mount data and models
        vfs.mountLoop(join(self.basePath, 'Data'), 'Data', 0)
        vfs.mountLoop(join(self.basePath, 'Models'), 'Models', 0)
        vfs.mountLoop(join(self.basePath, 'Config'), 'Config', 0)

        # Ensure the pipeline write path exists, and if not, create it
        if not isdir(self.writePath):
            self.debug("Creating temp path, as it does not exist yet")
            try:
                os.makedirs(self.writePath, 0777)
            except Exception, msg:
                self.error("Failed to create temp path:",msg)
                import sys
                sys.exit(0)

        # Mount the pipeline temp path
        self.debug("Mounting",self.writePath,"as PipelineTemp/")
        vfs.mountLoop(self.writePath, 'PipelineTemp/', 0)

        # #pragma include "something" searches in current directory first, 
        # and then on the model-path. Append the Shader directory to the modelpath
        # to ensure the shader includes can be found.
        base_path = Filename(self.basePath)
        getModelPath().appendDirectory(join(base_path.getFullpath(), 'Shader'))

        # Add the pipeline root directory to the model path aswell
        getModelPath().appendDirectory(base_path.getFullpath())

        # Append the write path to the model directory to make pragma include 
        # find the ShaderAutoConfig.include
        write_path = Filename(self.writePath)
        getModelPath().appendDirectory(write_path.getFullpath())

    def unmount(self):
        """ Unmounts the VFS """
        raise NotImplementedError()

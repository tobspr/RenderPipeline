
from panda3d.core import Filename, VirtualFileSystem, getModelPath
from DebugObject import DebugObject

from direct.stdpy.file import join, isdir, isfile
import os


class MountManager(DebugObject):

    """ This classes manages VirtualFileSystem mounts and also the
    shader cache, including AutoConfig """

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
        #self.writePath = Filename.fromOsSpecific(pth)
        #self.writePath.makeAbsolute()
        #self.writePath = self.writePath.getFullpath()

    def setBasePath(self, pth):
        """ Sets the path where the base shaders and models on are contained """
        self.debug("Set base path to '" + pth + "'")
        self.basePath = Filename.fromOsSpecific(pth).getFullpath()
        #self.basePath = Filename.fromOsSpecific(pth)
        #self.basePath.makeAbsolute()
        #self.basePath = self.basePath.getFullpath()


    def getLock(self):
        """ Checks if we are the only instance running """

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
        """ Checks if a pid is running """

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
        """ Internal method to write the current pid to a file """
        with open(self.lockFile, "w") as handle:
            handle.write(str(os.getpid()))

    def mount(self):
        """ Inits the VFS Mounts """

        self.debug("Setting up virtual filesystem.")
        vfs = VirtualFileSystem.getGlobalPtr()

        # Mount shaders
        # vfs.mountLoop(join(self.basePath, 'Shader'), 'Shader', 0)

        # Mount data and models
        vfs.mountLoop(join(self.basePath, 'Data'), 'Data', 0)
        vfs.mountLoop(join(self.basePath, 'Models'), 'Models', 0)
        vfs.mountLoop(join(self.basePath, 'Config'), 'Config', 0)
        #vfs.mountLoop(join(self.basePath, 'Demoscene.ignore'), 'Demoscene.ignore', 0)

        # Just mount everything
        # vfs.mountLoop(self.basePath, '.', 0)

        if not isdir(self.writePath):
            self.debug("Creating temp path, as it does not exist yet")
            try:
                os.makedirs(self.writePath, 0777)
            except Exception, msg:
                self.error("Failed to create temp path:",msg)
                import sys
                sys.exit(0)

        self.debug("Mounting",self.writePath,"as PipelineTemp/")
        vfs.mountLoop(self.writePath, 'PipelineTemp/', 0)

        # #pragma include "something" searches in current directory first, 
        #and then on the model-path.
        base_path = Filename(self.basePath)
        #bp.makeAbsolute()
        getModelPath().appendDirectory(join(base_path.getFullpath(), 'Shader'))
        getModelPath().appendDirectory(base_path.getFullpath())
        #this is necessary to make pragma include find ShaderAutoConfig.include
        write_path = Filename(self.writePath)
        #wp.makeAbsolute()
        getModelPath().appendDirectory(write_path.getFullpath())
        #print("Current model-path: {}").format(getModelPath())

    def unmount(self):
        """ Unmounts the VFS """
        self.warn("TODO: Unmount")

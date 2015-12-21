
import os
import sys
import atexit

from panda3d.core import Filename, VirtualFileSystem, get_model_path
from panda3d.core import VirtualFileMountRamdisk
from direct.stdpy.file import join, isdir, isfile

from ..Util.DebugObject import DebugObject


class MountManager(DebugObject):

    """ This classes mounts the required directories for the pipeline to run.
    This is important if the pipeline is in a subdirectory for example. The
    mount manager also handles the lock, storing the current PID into a file
    named instance.pid and ensuring that there is only 1 instance of the
    pipeline running at one time. """

    def __init__(self, pipeline):
        """ Creates a new mount manager """
        DebugObject.__init__(self)
        self._pipeline = pipeline
        self._write_path = None
        self._base_path = self._find_basepath()
        self._lock_file = "instance.pid"
        self._model_paths = []
        self._mounted = False
        self._do_cleanup = True

        self.debug("Auto-Detected base path to", self._base_path)

        atexit.register(self._on_exit_cleanup)

    def set_write_path(self, pth):
        """ Set a writable directory for generated files. This can be a string
        path name or a multifile with openReadWrite(). If no pathname is set
        then the root directory is used.

        This feature is usually only used for debugging, the pipeline will dump
        all generated shaders and other temporary files to that directory.
        If you don't need this, you can use set_virtual_write_path(), which
        will create the temporary path in the VirtualFileSystem, thus not
        writing any files to disk. """
        self._write_path = Filename.from_os_specific(pth).get_fullpath()
        self._lock_file = join(self._write_path, "instance.pid")

    def set_virtual_write_path(self):
        """ This method sets the write directory to a virtual directory,
        so that no files are actually written to disk. This is the default
        setting. Also see set_write_path. """
        self._write_path = None

    def set_base_path(self, pth):
        """ Sets the path where the base shaders and models on are contained. This
        is usually the root of the rendering pipeline folder """
        self.debug("Set base path to '" + pth + "'")
        self._base_path = Filename.from_os_specific(pth).get_fullpath()

    def disable_cleanup(self):
        """ Disables the cleanup of the tempfolder after the application stopped.
        This is mostly useful for debugging, to analyze the generated tempfiles
        even after the pipeline stopped running """
        self._do_cleanup = False

    def get_base_path(self):
        """ Returns the base path previously set with set_base_path """
        return self._base_path

    def get_lock(self):
        """ Checks if we are the only instance running. If there is no instance
        running, write the current PID to the instance.pid file. If the
        instance file exists, checks if the specified process still runs. This
        way only 1 instance of the pipeline can be run at one time. """

        # Check if there is a lockfile at all
        if isfile(self._lock_file):
            # Read process id from lockfile
            try:
                with open(self._lock_file, "r") as handle:
                    pid = int(handle.readline())
            except IOError as msg:
                self.error("Failed to read lockfile:", msg)
                return False

            # Check if the process is still running
            if self._is_pid_running(pid):
                self.error("Found running instance")
                return False

            # Process is not running anymore, we can write the lockfile
            self._write_lock()
            return True

        else:
            # When there is no lockfile, just create it and continue
            self._write_lock()
            return True

    def _find_basepath(self):
        """ Attempts to find the pipeline base path by looking at the location
        of this file """
        pth = os.path.abspath(join(os.path.dirname(os.path.realpath(__file__)), "../.."))
        return Filename.from_os_specific(pth).get_fullpath()

    def _is_pid_running(self, pid):
        """ Checks if a pid is still running """

        # Code snippet from:
        # http://stackoverflow.com/questions/568271/how-to-check-if-there-exists-a-process-with-a-given-pid

        if os.name == 'posix':
            import errno
            if pid < 0:
                return False
            try:
                os.kill(pid, 0)
            except OSError as err:
                return err.errno == errno.EPERM
            else:
                return True
        else:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(0x100000, 0, pid)
            if process != 0:
                kernel32.CloseHandle(process)
                return True
            else:
                return False

    def _write_lock(self):
        """ Internal method to write the current process id to the instance.pid
        lockfile. This is used to ensure no second instance of the pipeline is
        running. """

        with open(self._lock_file, "w") as handle:
            handle.write(str(os.getpid()))

    def _try_remove(self, fname):
        """ Tries to remove the specified filename, returns either True or False
        depending if we had success or not """
        try:
            os.remove(fname)
            return True
        except IOError:
            pass
        return False

    def _on_exit_cleanup(self):
        """ Gets called when the application exists """

        if self._do_cleanup:
            self.debug("Cleaning up ..")

            if self._write_path is not None:

                # Try removing the lockfile
                self._try_remove(self._lock_file)

                # Check for further tempfiles in the write path
                # We explicitely use os.listdir here instead of pandas listdir,
                # to work with actual paths
                for fname in os.listdir(self._write_path):
                    pth = join(self._write_path, fname)

                    # Tempfiles from the pipeline start with "$$" to distinguish
                    # them from user created files
                    if isfile(pth) and fname.startswith("$$"):
                        self._try_remove(pth)

                # Delete the write path if no files are left
                if len(os.listdir(self._write_path)) < 1:
                    try:
                        os.removedirs(self._write_path)
                    except IOError:
                        pass

    def is_mounted(self):
        """ Returns wheter the MountManager was already mounted by calling
        mount() """
        return self._mounted

    def mount(self):
        """ Inits the VFS Mounts """

        self.debug("Setting up virtual filesystem.")
        self._mounted = True
        vfs = VirtualFileSystem.get_global_ptr()

        # Mount data and models
        dirs_to_mount = ["Data", "Config", "Effects", "Plugins", "Config", "Shader"]
        for directory in dirs_to_mount:
            vfs.mount_loop(join(self._base_path, directory), directory, 0)

        if isdir(join(self._base_path, "Models")):
            vfs.mount_loop(join(self._base_path, 'Models'), 'Models', 0)

        # Convert the base path to something the os can work with
        sys_base_path = Filename(self._base_path).to_os_specific()

        # Add plugin folder to the include path
        sys.path.insert(0, join(sys_base_path, 'Plugins'))

        # Add current folder to the include path
        sys.path.insert(0, sys_base_path)

        # Mount the pipeline temp path:
        # If no write path is specified, use a virtual ramdisk
        if self._write_path is None:
            self.debug("Mounting ramdisk as $$PipelineTemp/")
            vfs.mount(VirtualFileMountRamdisk(), "$$PipelineTemp/", 0)
        else:
            # In case an actual write path is specified:
            # Ensure the pipeline write path exists, and if not, create it
            if not isdir(self._write_path):
                self.debug("Creating temp path, it does not exist yet")
                try:
                    os.makedirs(self._write_path)
                except IOError as msg:
                    self.fatal("Failed to create temp path:", msg)
            self.debug("Mounting", self._write_path, "as $$PipelineTemp/")
            vfs.mount_loop(self._write_path, '$$PipelineTemp/', 0)

        # #pragma include "something" searches in current directory first,
        # and then on the model-path. Append the Shader directory to the
        # modelpath to ensure the shader includes can be found.
        self._model_paths.append(join(self._base_path, "Shader"))

        # Add the pipeline root directory to the model path as well
        self._model_paths.append(self._base_path)
        self._model_paths.append(".")

        # Append the write path to the model directory to make pragma include
        # find the ShaderAutoConfig.include
        self._model_paths.append("$$PipelineTemp")

        # Add the plugins dir to the model path so plugins can include their
        # own resources more easily
        self._model_paths.append(join(self._base_path, "Plugins"))

        # Write the model paths to the global model path
        for pth in self._model_paths:
            get_model_path().append_directory(pth)


    def unmount(self):
        """ Unmounts the VFS """
        raise NotImplementedError()


from __future__ import print_function

import os
import sys
import urllib
import zipfile
import shutil

try: 
    # Include cStringIO in case its available, since its faster
    from cStringIO import StringIO
except: 
    try:
        # Python 2.7
        from StringIO import StringIO
    except:
        try:
            # Python 3.4
            import io

            # Use bytes IO, since we get a bytes object, too
            StringIO = io.BytesIO
        except:
            assert False, "Could not import StringIO module."


class SubmoduleDownloader:

    """ Util class to download and extract (sub-)modules from github """

    @staticmethod
    def download_submodule(author, module_name, dest_path, ignore_list):
        """ Downloads a submodule from the given author and module name, and extracts
        all files which are not on the ignore_list to the dest_path.

        Example: download_submodule("tobspr", "RenderPipeline", ".", ["README.md", "LICENSE"])
         """

        # Make directory, if it does not exist yet
        if not os.path.isdir(dest_path):
            os.makedirs(dest_path)

        # Construct download url
        source_url = "https://github.com/" + author + "/" + module_name + "/archive/master.zip"
        prefix = module_name + "-master"
        print("Fetching:", source_url)

        try:
            # Python 2.7
            urlopen = urllib.urlopen
        except:
            # Python 3.4
            import urllib.request
            urlopen = urllib.request.urlopen

        # Download the zip
        try:
            usock = urlopen(source_url)
            zip_data = usock.read()
            usock.close()
        except Exception as msg:
            print("ERROR: Could not fetch module", module_name, "! Reason:", msg, file=sys.stderr)
            sys.exit(2)

        # Extract the zip
        zip_ptr = StringIO(zip_data)

        try:
            zip_handle = zipfile.ZipFile(zip_ptr)
        except zipfile.BadZipfile:
            print("ERROR: Invalid zip file!", file=sys.stderr)
            sys.exit(3)

        if zip_handle.testzip() is not None:
            print("ERROR: Invalid zip file checksums!", file=sys.stderr)
            sys.exit(1)

        num_files, num_dirs = 0, 0

        for fname in zip_handle.namelist():
            rel_name = fname.replace(prefix, "").replace("\\", "/").lstrip("/")
            if not rel_name:
                continue

            is_file = not rel_name.endswith("/")
            rel_name = dest_path.rstrip("/\\") + "/" + rel_name

            # Files
            if is_file:
                for ignore in ignore_list:
                    if ignore in rel_name:
                        break
                else:
                    with zip_handle.open(fname, "r") as source, open(rel_name, "wb") as dest:
                        shutil.copyfileobj(source, dest)
                    num_files += 1
                            
            # Directories
            else:
                if not os.path.isdir(rel_name):
                    os.makedirs(rel_name)
                num_dirs += 1

        print("Extracted", num_files, "files and", num_dirs, "directories")

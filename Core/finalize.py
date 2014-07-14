import sys
import shutil


source = sys.argv[1]
ext = source.split(".")[-1]
shutil.copyfile(source, "RPCore."+ext)

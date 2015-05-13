
rootDir = "../../"



sourceDirectories = ["Code/", "Shader/", "Toolkit/"]
ignorePattern = [".pyc"]
extensions = "py compute fragment vertex ini include geometry glsl cxx h I".split()

print "Code Analyzer v0.2"

from os import listdir
from os.path import join, isfile


def convertPath(pth):
    return pth.replace("\\", "/").rstrip("/")


def countLines(filename):
    with open(filename, "r") as handle:
        content = handle.readlines()
    return len(content)

currentIndent = 0

def analyzeDirectory(src):
    global currentIndent

    currentIndent += 1
    # prefix = "  " * currentIndent
    # print prefix,"Analyzing", src

    lines = 0
    for f in listdir(src):
        abspath = join(src, f)
        ignoreFile = False
        for ignore in ignorePattern:
            if convertPath(ignore) in convertPath(abspath):
                ignoreFile = True
                break

        if ignoreFile:
            continue

        if isfile(abspath):
            ext = f.split(".")[-1].lower()
            if ext in extensions:
                lines += countLines(abspath)
        else:
            lines += analyzeDirectory(abspath)

    currentIndent -= 1

    return lines

totalLines = 0

for src in sourceDirectories:
    lines = analyzeDirectory(join(rootDir, src))
    totalLines += lines
    print "  -> Directory", src, "has", lines, "Code Lines"

print "Total Lines of Code: ", totalLines

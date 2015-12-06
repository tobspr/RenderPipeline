"""

Script to download the Render Pipeline samples

"""

import sys
sys.path.insert(0, "../")

from Code.Util.SubmoduleDownloader import SubmoduleDownloader


if __name__ == "__main__":
    SubmoduleDownloader.download_submodule("tobspr", "RenderPipeline-Samples", ".", ["README.md"])

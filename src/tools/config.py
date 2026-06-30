from sys import platform
import os


if "linux" in platform:
    LINUX = True
    os.environ["FPCALC"] = os.path.abspath("./src/assets/bin/fpcalc")
    from tools.mpris import MprisController

elif platform == "darwin":
    exit()
elif platform == "win32":
    WINDOWS = True
    os.environ["FPCALC"] = os.path.abspath("./src/assets/bin/fpcalc.exe")
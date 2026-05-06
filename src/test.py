import asyncio
from tools.library_manager import LibraryManager


LM = LibraryManager()
asyncio.run(LM.scan_folder("/home/ice424/Music", None))

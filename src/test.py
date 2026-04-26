import asyncio
from tools.fetch import GetCover


from tools.track import Track

async def main():
    track = Track.from_file("/home/ice424/Music/Prefer not to say/depressed hermit girl touches grass - Tanger, ISSBROKIE.flac")

    g =  GetCover(track, None)
    print("Fetching lyrics in background...")
    await asyncio.sleep(100)

asyncio.run(main())
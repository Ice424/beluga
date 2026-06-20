import os
import base64
import hashlib
import re

import acoustid as aid

from dataclasses import dataclass, field
from pathlib import Path
from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import APIC, ID3, ID3TimeStamp
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis

from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:
    from tools.library_manager import LibraryManager




@dataclass
class Track:
    COVER_CACHE = Path.home() / ".cache/beluga/covers"
    def __init__(
        self,
        file_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        artists: Optional[list[str]] = None,
        album: Optional[str] = None,
        tracknumber: Optional[int] = None,
        discnumber: Optional[int] = None,
        duration: Optional[float] = None,
        cover_path: Optional[Path] = None,
        cover_hash: Optional[str] = None,
        file_size: Optional[int] = None,
        modified_at: Optional[int] = None,
        file_hash: Optional[str] = None,
        chromaprint: Optional[bytes] = None,
        track_mbid: Optional[str] = None,
        recording_mbid: Optional[str] = None,
        acoustid: Optional[str] = None,
        artist_mbid: Optional[str] = None,
        release_year: Optional[str] = None,
        release_mbid: Optional[str] = None,
        release_group_mbid: Optional[str] = None
    ):
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.artists = artists or []
        self.raw_artist = None
        self.album = album
        self.tracknumber = tracknumber
        self.discnumber = discnumber
        self.duration = duration
        self.cover_path = cover_path
        self.cover_hash = cover_hash

        self.file_size = file_size
        self.modified_at = modified_at
        self.file_hash = file_hash
        
        self.chromaprint = chromaprint
        self.track_mbid = track_mbid 
        self.recording_mbid = recording_mbid
        self.acoustid = acoustid
        
        self.artist_mbid = artist_mbid
        
        self.release_year = release_year
        self.release_mbid = release_mbid
        self.release_group_mbid = release_group_mbid

    @classmethod
    def from_file(cls, file_path: str) -> "Track":
        track = cls(file_path=file_path)

        audio = File(file_path)
        if audio is None:
            raise ValueError(f"Invalid file: {file_path}")


        track.artists = []
        track.tracknumber = track.discnumber = None
         
         #METADATA
        if isinstance(audio, FLAC):
            track.title = audio.get("title", [None])[0]  # pyright: ignore[reportOptionalSubscript]
            track.raw_artist = ";".join(audio.get("artist", []))  # pyright: ignore[reportOptionalSubscript]
            track.artists = audio.get("artists", [])
            track.album = audio.get("album", [None])[0]  # pyright: ignore[reportOptionalSubscript]
            track.tracknumber = cls._parse_number(audio.get("tracknumber", [None])[0])  # pyright: ignore[reportOptionalSubscript]
            track.discnumber = cls._parse_number(audio.get("discnumber", [None])[0])  # pyright: ignore[reportOptionalSubscript]

            track.track_mbid = audio.get("MUSICBRAINZ_RELEASETRACKID", [None])[0] # pyright: ignore[reportOptionalSubscript]
            track.recording_mbid = audio.get("MUSICBRAINZ_TRACKID", [None])[0] # pyright: ignore[reportOptionalSubscript]
            track.acoustid = audio.get("acoustid_id", [None])[0] # pyright: ignore[reportOptionalSubscript]

            track.artist_mbid = audio.get("musicbrainz_artistid", [None])[0] # pyright: ignore[reportOptionalSubscript]

            track.release_year = audio.get("originalyear", [None])[0] # pyright: ignore[reportOptionalSubscript]
            track.release_mbid = audio.get("musicbrainz_albumid", [None])[0] # pyright: ignore[reportOptionalSubscript]
            track.release_group_mbid = audio.get("musicbrainz_releasegroupid", [None])[0] # pyright: ignore[reportOptionalSubscript]

        elif isinstance(audio.tags, ID3):
            track.title = cls._id3(audio, "TIT2")
            track.raw_artist = cls._id3(audio, "TPE1")
            track.album = cls._id3(audio, "TALB")
            track.tracknumber = cls._parse_number(cls._id3(audio, "TRCK"))
            track.discnumber = cls._parse_number(cls._id3(audio, "TPOS"))

            track.track_mbid = cls._id3(audio, "UFID:http://musicbrainz.org")
            track.recording_mbid = cls._id3(audio, "TXXX:MusicBrainz Recording Id")
            track.acoustid = cls._id3(audio, "TXXX:Acoustid Id")

            track.artist_mbid = cls._id3(audio, "TXXX:MusicBrainz Artist Id")

            track.release_year = cls._id3(audio, "TDOR") or cls._id3(audio, "TDRC")
            track.release_mbid = cls._id3(audio, "TXXX:MusicBrainz Album Id")
            track.release_group_mbid = cls._id3(audio, "TXXX:MusicBrainz Release Group Id")

        elif isinstance(audio, MP4):
            track.title = cls._mp4(audio, "\xa9nam")
            track.raw_artist = cls._mp4(audio, "\xa9ART")
            track.album = cls._mp4(audio, "\xa9alb")
            track.tracknumber = cls._parse_number(audio.tags.get("trkn", [(None, None)])[0])
            track.discnumber = cls._parse_number(audio.tags.get("disk", [(None, None)])[0])

            track.track_mbid = cls._mp4(audio, "----:com.apple.iTunes:MusicBrainz Track Id")
            track.recording_mbid = cls._mp4(audio, "----:com.apple.iTunes:MusicBrainz Recording Id")
            track.acoustid = cls._mp4(audio, "----:com.apple.iTunes:Acoustid Id")

            track.artist_mbid = cls._mp4(audio, "----:com.apple.iTunes:MusicBrainz Artist Id")

            track.release_year = cls._mp4(audio, "\xa9day")
            track.release_mbid = cls._mp4(audio, "----:com.apple.iTunes:MusicBrainz Album Id")
            track.release_group_mbid = cls._mp4(audio, "----:com.apple.iTunes:MusicBrainz Release Group Id")

        elif isinstance(audio, OggVorbis):
            track.title = audio.get("title", [None])[0]
            track.raw_artist = audio.get("artist", [None])[0]
            track.artists = audio.get("artist", [])
            track.album = audio.get("album", [None])[0]
            track.tracknumber = cls._parse_number(audio.get("tracknumber", [None])[0])
            track.discnumber = cls._parse_number(audio.get("discnumber", [None])[0])

            track.track_mbid = audio.get("musicbrainz_trackid", [None])[0]
            track.recording_mbid = audio.get("musicbrainz_recordingid", [None])[0]
            track.acoustid = audio.get("acoustid_id", [None])[0]

            track.artist_mbid = audio.get("musicbrainz_artistid", [None])[0]

            track.release_year = audio.get("originalyear", [None])[0] or audio.get("date", [None])[0]
            track.release_mbid = audio.get("musicbrainz_albumid", [None])[0]
            track.release_group_mbid = audio.get("musicbrainz_releasegroupid", [None])[0]

        else:
            raise ValueError(f"Unsupported file: {cls.file_path}")
        # ARTISTS
        if len(track.artists) <= 1:
            track.artists = cls._split_artists(track.raw_artist)
        track.artist = track.artists[0] if track.artists else None

        #DURATION
        track.duration = audio.info.length if audio else None

        #FILE INFO 
        stat = os.stat(file_path)
        track.file_size = stat.st_size
        track.modified_at = int(stat.st_mtime)
       
        if isinstance(track.release_year, ID3TimeStamp):
            track.release_year = track.release_year.text


        #COVER 
        track.cover_path, track.cover_hash = track._extract_cover(audio)
        if not track.title:
            track.title = Path(file_path).stem
        if not track.artist:
            track.artist = "Unknown"
        if not track.album:
            track.album = "Unknown"
        return track
    
    @classmethod
    def from_db(cls, row: dict[str, Any]) -> "Track":
        return cls(
            file_path=row["path"],
            title=row.get("title"),
            artist=row.get("artist"),
            artists=[row.get("artist")],
            album=row.get("album"),
            duration=row.get("duration"),
            tracknumber=row.get("track_number"),
            discnumber=row.get("disc_number"),
            cover_path= cls.COVER_CACHE / f"{row.get("cover_hash")}.jpg" if row.get("cover_hash") != "" else "",
            cover_hash=row.get("cover_hash"),
            file_hash=row.get("hash"),
            
            chromaprint=row.get("chromaprint"),
            recording_mbid = row.get("recording_mbid"),
            track_mbid=row.get("track_mbid"),
            acoustid =row.get("acoustid"),
            
            release_mbid= row.get("release_mbid")
            
            
        )
    
    
    
    def _extract_cover(self, audio) -> tuple[str,str]:
        """
        returns
            str: filepath
            str: hash
        """
        
        self.COVER_CACHE.mkdir(parents=True, exist_ok=True)

        data = None

        # FLAC
        if isinstance(audio, FLAC) and audio.pictures:
            data = audio.pictures[0].data

        # MP3
        elif isinstance(audio.tags, ID3):
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    data = tag.data
                    break

        # MP4
        elif isinstance(audio, MP4):
            cov = audio.tags.get("covr")
            if cov:
                data = cov[0]

        # OGG
        elif isinstance(audio, OggVorbis):
            # New standard
            pictures = audio.get("metadata_block_picture")
            if pictures:
                try:
                    import mutagen.flac

                    pic = mutagen.flac.Picture(base64.b64decode(pictures[0]))
                    data = pic.data
                    
                except Exception:
                    pass

            # Fallback
            cover = audio.get("coverart")
            if cover:
                try:
                    data = base64.b64decode(cover[0])
                except Exception:
                    pass
        if not data:
            return ("", "")
        cover_hash = hashlib.md5(data).hexdigest()
        cover_path = self.COVER_CACHE / f"{cover_hash}.jpg"
       

        if not cover_path.exists():
            with open(cover_path, "wb") as f:
                f.write(data)

        return (str(cover_path), cover_hash)

    @staticmethod
    def _file_info(path):
        stat = os.stat(path)
        return stat.st_size, int(stat.st_mtime)

    @staticmethod
    def hash(path, block_size=65536):
        h = hashlib.md5()
        size = os.path.getsize(path)

        with open(path, "rb") as f:
            h.update(f.read(block_size))
            if size > block_size:
                f.seek(-block_size, os.SEEK_END)
                h.update(f.read(block_size))

        return h.hexdigest()

    @staticmethod
    def _first(value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    @staticmethod
    def _parse_number(value):
        if not value:
            return None
        if isinstance(value, tuple):
            return value[0]
        if isinstance(value, str) and "/" in value:
            value = value.split("/")[0]
        try:
            return int(value)
        except:
            return None

    @staticmethod
    def _id3(audio, key):
        tag = audio.tags.get(key)
        if tag and hasattr(tag, 'text'):
            return tag.text[0]
        return None

    @staticmethod
    def _mp4(audio, key):
        values = audio.tags.get(key)
        return values[0] if values else None

    @staticmethod
    def _split_artists(artist: Optional[str]) -> list[str]:
        if not artist:
            return []

        separators = ["&", "feat.", "ft.", "with", ",", " and "]
        if ";" in artist:
            separators = [";"]
        artists = [artist]

        for sep in separators:
            new = []
            for a in artists:
                new.extend(a.split(sep))
            artists = new

        return [a.strip() for a in artists if a.strip()]

    def __repr__(self):
        return (
            f"<Track title={self.title!r} artist={self.artist!r} album={self.album!r} duration={self.duration:.1f}s>"
        )

    def generate_chromaprint(self):
        if self.chromaprint:
            return self.chromaprint
        else:
            try:
                self.chromaprint = aid.fingerprint_file(self.file_path)[1]
            except Exception as e:
                print(f"Failed to fingerprint file {self.file_path}, {e}")
                self.chromaprint = ""
            return self.chromaprint
    

        



# class AutoTrack(Track):
#         """
#     Track will automatically load info from file tags
#     Represents a single audio track with metadata and cover art.
#     """

#     COVER_CACHE = Path.home() / ".cache/beluga/covers"

#     def __init__(self, file_path: str):
#         super().__init__(file_path)

#         self.file_size: Optional[int] = None
#         self.modified_at: Optional[int] = None

#         self.audio = File(self.file_path)

#         self._load_metadata()
#         self._load_duration()
#         self._load_file_info()
        

#     def _load_file_info(self):
#         stat = os.stat(self.file_path)
#         self.file_size = stat.st_size
#         self.modified_at = int(stat.st_mtime)

#     def _load_metadata(self):
#         audio = self.audio

#         if audio is None:
#             raise ValueError(f"invalid file: {self.file_path}")

#         # FLAC
#         if isinstance(audio, FLAC):
#             self.title = audio.get("title", [None])[0]
#             self.artists = audio.get("artist", [])
#             self.raw_artist = audio.get("artist", [None])[0]
#             self.album = audio.get("album", [None])[0]
#             self.tracknumber = self._parse_number(audio.get("tracknumber", [None])[0])
#             self.discnumber = self._parse_number(audio.get("discnumber", [None])[0])

#         # MP3 (ID3)
#         elif isinstance(audio.tags, ID3):
#             self.title = self._get_id3_text(audio, "TIT2")
#             self.raw_artist = self._get_id3_text(audio, "TPE1")
#             self.artists = self._get_id3_text(audio, "TPE1")
#             self.album = self._get_id3_text(audio, "TALB")
#             self.tracknumber = self._parse_number(self._get_id3_text(audio, "TRCK"))
#             self.discnumber = self._parse_number(self._get_id3_text(audio, "TPOS"))

#         # MP4 / M4A
#         elif isinstance(audio, MP4):
#             self.title = self._get_mp4_text(audio, "\xa9nam")
#             self.raw_artist = self._get_mp4_text(audio, "\xa9ART")
#             self.artists = audio.get("artist", [])
#             self.album = self._get_mp4_text(audio, "\xa9alb")
#             self.tracknumber = self._parse_number(
#                 audio.tags.get("trkn", [(None, None)])[0]
#             )
#             self.discnumber = self._parse_number(
#                 audio.tags.get("disk", [(None, None)])[0]
#             )
#         elif isinstance(audio, OggVorbis):
#             self.title = audio.get("title", [None])[0]
#             self.raw_artist = audio.get("artist", [None])[0]
#             self.artists = audio.get("artist", [])
#             self.album = audio.get("album", [None])[0]
#             self.tracknumber = self._parse_number(audio.get("tracknumber", [None])[0])
#             self.discnumber = self._parse_number(audio.get("discnumber", [None])[0])
#         else:
#             raise ValueError(f"Unsupported file: {self.file_path}")
        
#         if self.artists:
#             self.artists = parse_artists(self.artists)
#             self.artist= self.artists[0]
            
#         else:
#             self.artist = "Unknown Artist"
            
#         if not self.title:
#             self.title = "Unknown Title"
#     def load_cover(self,):
#         """Extract cover art, save to cache, and generate base64 for UI."""
#         audio = self.audio

#         # FLAC
#         if isinstance(audio, FLAC) and audio.pictures:
#             data = audio.pictures[0].data
#             return self._save_cover(data)

#         # MP3
#         elif isinstance(audio.tags, ID3):
#             for tag in audio.tags.values():
#                 if isinstance(tag, APIC):
#                     return self._save_cover(tag.data)
#                     break

#         # MP4 / M4A
#         elif isinstance(audio, MP4):
#             cov = audio.tags.get("covr")
#             if cov:
#                 return self._save_cover(cov[0])
#         elif isinstance(audio, OggVorbis):
#             # New standard (preferred)
#             pictures = audio.get("metadata_block_picture")
#             if pictures:
#                 try:
#                     import mutagen.flac

#                     pic = mutagen.flac.Picture(base64.b64decode(pictures[0]))
#                     return self._save_cover(pic.data)
                    
#                 except Exception:
#                     pass

#             # Fallback (older tags)
#             cover = audio.get("coverart")
#             if cover:
#                 try:
#                     return self._save_cover(base64.b64decode(cover[0]))
#                 except Exception:
#                     pass
        

#     def _save_cover(self, data: bytes):
#         """Save cover to cache and store base64 for UI."""
#         self.COVER_CACHE.mkdir(parents=True, exist_ok=True)
        
#         cover_hash = hashlib.sha1(data).hexdigest()
#         cover_path = Path.home() / f".cache/beluga/covers/{cover_hash}.jpg"
        
#         if not cover_path.exists():
#             with open(cover_path, "wb") as f:
#                 f.write(data)
#         self.cover_path = str(cover_path)
#         return cover_hash

#     def _load_duration(self):
#         audio = self.audio
#         self.duration = audio.info.length if audio else None

#     @staticmethod
#     def _parse_number(value):
#         if not value:
#             return None
#         if isinstance(value, str) and "/" in value:
#             value = value.split("/")[0]
#         try:
#             return int(value)
#         except Exception:
#             return None

#     @staticmethod
#     def _get_id3_text(audio, key):
#         tag = audio.tags.get(key)
#         if tag:
#             return tag.text[0]
#         return None

#     @staticmethod
#     def _get_mp4_text(audio, key):
#         values = audio.tags.get(key)
#         if values:
#             return values[0]
#         return None

#     def __repr__(self):
#         return f"<Track title={self.title!r} artist={self.raw_artist!r} album={self.album!r} duration={self.duration:.1f}s>"

#     def to_db_tuple(self):
#         return (
#             self.title,
#             self.file_path,
#             self.compute_hash(),
#             self.file_size,
#             self.modified_at,
#             self.duration,
#         )


# def quick_hash(path):

#     h = hashlib.md5()
#     size = os.path.getsize(path)

#     with open(path, "rb") as f:
#         h.update(f.read(65536))

#         if size > 65536:
#             f.seek(-65536, os.SEEK_END)
#             h.update(f.read(65536))

#     return h.hexdigest()


# if __name__ == "__main__":
#     tr = AutoTrack("/home/ice424/Music/Prefer not to say/IMPULSE! - Tanger, Inferno.flac")
#     print(tr)


# def hash_file(self, file_path, block_size=65536):
#     md5 = hashlib.md5()
#     with open(file_path, "rb") as f:
#         while chunk := f.read(block_size):
#             md5.update(chunk)

#     file_hash = md5.hexdigest()
#     return file_hash




# def parse_artists(value: str | list[str]) -> list[str]:
#     if not value:
#         return []

#     if isinstance(value, list):
#         value = ";".join(value)

#     value = value.strip()

#     value = re.sub(r"\b(feat\.|ft\.|feat|ft|featuring)\b", ";", value, flags=re.IGNORECASE)


#     separators = ["&", " and ", ";", "/"]
#     for sep in separators:
#         value = value.replace(sep, ",")

#     artists = [a.strip() for a in value.split(",") if a.strip()]

#     return artists
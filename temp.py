import os
import hashlib
from pathlib import Path
from typing import Optional, List, Any

from mutagen import File
from mutagen.flac import FLAC
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis


class Track:
    """
    Pure data model for a track.
    No IO should happen in __init__.
    """

    COVER_CACHE = Path.home() / ".cache/beluga/covers"

    def __init__(
        self,
        file_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        artists: Optional[List[str]] = None,
        album: Optional[str] = None,
        tracknumber: Optional[int] = None,
        discnumber: Optional[int] = None,
        duration: Optional[float] = None,
        cover_path: Optional[str] = None,
        file_size: Optional[int] = None,
        modified_at: Optional[int] = None,
        file_hash: Optional[str] = None,
    ):
        self.file_path = file_path
        self.title = title
        self.artist = artist
        self.artists = artists or []
        self.album = album
        self.tracknumber = tracknumber
        self.discnumber = discnumber
        self.duration = duration
        self.cover_path = cover_path

        self.file_size = file_size
        self.modified_at = modified_at
        self.file_hash = file_hash

    # =========================
    # FACTORY METHODS
    # =========================

    @classmethod
    def from_file(cls, file_path: str) -> "Track":
        audio = File(file_path)
        if audio is None:
            raise ValueError(f"Invalid file: {file_path}")

        title = artist = album = None
        artists: List[str] = []
        tracknumber = discnumber = None

        # -------- FLAC --------
        if isinstance(audio, FLAC):
            title = cls._first(audio.get("title"))
            artists = audio.get("artist", [])
            artist = cls._first(artists)
            album = cls._first(audio.get("album"))
            tracknumber = cls._parse_number(cls._first(audio.get("tracknumber")))
            discnumber = cls._parse_number(cls._first(audio.get("discnumber")))

        # -------- MP3 --------
        elif isinstance(audio.tags, ID3):
            title = cls._id3(audio, "TIT2")
            artist = cls._id3(audio, "TPE1")
            album = cls._id3(audio, "TALB")

            artists = cls._split_artists(artist)

            tracknumber = cls._parse_number(cls._id3(audio, "TRCK"))
            discnumber = cls._parse_number(cls._id3(audio, "TPOS"))

        # -------- MP4 --------
        elif isinstance(audio, MP4):
            title = cls._mp4(audio, "\xa9nam")
            artist = cls._mp4(audio, "\xa9ART")
            album = cls._mp4(audio, "\xa9alb")

            artists = cls._split_artists(artist)

            tracknumber = cls._parse_number(audio.tags.get("trkn", [(None, None)])[0])
            discnumber = cls._parse_number(audio.tags.get("disk", [(None, None)])[0])

        # -------- OGG --------
        elif isinstance(audio, OggVorbis):
            title = cls._first(audio.get("title"))
            artists = audio.get("artist", [])
            artist = cls._first(artists)
            album = cls._first(audio.get("album"))

            tracknumber = cls._parse_number(cls._first(audio.get("tracknumber")))
            discnumber = cls._parse_number(cls._first(audio.get("discnumber")))

        else:
            raise ValueError(f"Unsupported file: {file_path}")

        duration = audio.info.length if audio.info else None

        file_size, modified_at = cls._file_info(file_path)
        file_hash = cls.quick_hash(file_path)

        track = cls(
            file_path=file_path,
            title=title,
            artist=artist,
            artists=artists,
            album=album,
            tracknumber=tracknumber,
            discnumber=discnumber,
            duration=duration,
            file_size=file_size,
            modified_at=modified_at,
            file_hash=file_hash,
        )

        track.cover_path = track._extract_cover(audio)

        return track

    @classmethod
    def from_db(cls, row: dict[str, Any]) -> "Track":
        return cls(
            file_path=row["path"],
            title=row.get("title"),
            artist=row.get("artist"),
            album=row.get("album"),
            duration=row.get("duration"),
            tracknumber=row.get("track_number"),
            discnumber=row.get("disc_number"),
            cover_path=row.get("cover_path"),
            file_hash=row.get("hash"),
        )

    # =========================
    # COVER HANDLING
    # =========================

    def _extract_cover(self, audio) -> Optional[str]:
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

        # OGG (rare)
        elif isinstance(audio, OggVorbis):
            # Some ogg files store base64 cover
            pic = audio.get("metadata_block_picture")
            if pic:
                import base64
                data = base64.b64decode(pic[0])

        if not data:
            return None

        cover_hash = hashlib.md5(data).hexdigest()
        cover_path = self.COVER_CACHE / f"{cover_hash}.jpg"

        if not cover_path.exists():
            with open(cover_path, "wb") as f:
                f.write(data)

        return str(cover_path)

    # =========================
    # HELPERS
    # =========================

    @staticmethod
    def _file_info(path):
        stat = os.stat(path)
        return stat.st_size, int(stat.st_mtime)

    @staticmethod
    def quick_hash(path, block_size=65536):
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
        return tag.text[0] if tag else None

    @staticmethod
    def _mp4(audio, key):
        values = audio.tags.get(key)
        return values[0] if values else None

    @staticmethod
    def _split_artists(artist: Optional[str]) -> List[str]:
        if not artist:
            return []

        separators = ["&", "feat.", "ft.", "with", ",", " and "]

        artists = [artist]

        for sep in separators:
            new = []
            for a in artists:
                new.extend(a.split(sep))
            artists = new

        return [a.strip() for a in artists if a.strip()]

    # =========================
    # DB HELPERS
    # =========================

    def to_db_tuple(self):
        return (
            self.title,
            self.file_path,
            self.file_hash,
            self.file_size,
            self.modified_at,
            self.duration,
        )

    def __repr__(self):
        return (
            f"<Track title={self.title!r} artist={self.artist!r} "
            f"album={self.album!r} duration={self.duration:.1f}s>"
        )
import sqlite3
import os
import hashlib
import asyncio

import traceback

from pathlib import Path
from tools.track import Track
from tools.fetch import GenIDs


class LibraryManager:
    def __init__(self) -> None:
        DB_PATH = Path.home() / ".cache/beluga"
        DB_PATH.mkdir(parents=True, exist_ok=True)
        setup = False
        if not os.path.isfile(DB_PATH / "music.sqlite"):
            setup = True
        self.conn = sqlite3.connect(DB_PATH / "music.sqlite", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.conn.execute("PRAGMA journal_mode = WAL;")
        self.conn.execute("PRAGMA synchronous = NORMAL;")
        self.cur = self.conn.cursor()
        self.conn.commit()

        self.new_cover_id = 1
        if setup:
            self.sql_setup()
            
    def close(self):
        self.conn.close()

    def sql_setup(self):

        self.cur.execute("""
        CREATE TABLE artists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        artist_mbid TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        self.cur.execute("""
        CREATE TABLE albums (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        year INTEGER,
        
        release_mbid TEXT UNIQUE,
        release_group_mbid TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        cover_id INTEGER,
        
        FOREIGN KEY(cover_id) REFERENCES covers(id)
        );
        """)
        self.cur.execute("""CREATE TABLE album_artists (
        album_id INTEGER,
        artist_id INTEGER,

    
        PRIMARY KEY (album_id, artist_id),
    
        FOREIGN KEY(album_id) REFERENCES albums(id) ON DELETE CASCADE,
        FOREIGN KEY(artist_id) REFERENCES artists(id) ON DELETE CASCADE
        );""")

        self.cur.execute("""
        CREATE TABLE tracks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        path TEXT NOT NULL UNIQUE,
        hash TEXT UNIQUE,
        album_id INTEGER,
        cover_id INTEGER,
        duration REAL,
        track_number INTEGER,
        disc_number INTEGER,
        
        modified_at TIMESTAMP,
        
        recording_mbid TEXT,
        track_mbid TEXT,
        acoustid TEXT,
        chromaprint BLOB,
        

        FOREIGN KEY(album_id) REFERENCES albums(id),
        FOREIGN KEY(cover_id) REFERENCES covers(id)
        );  
        """)

        self.cur.execute("""
            CREATE TABLE track_artists (
            track_id INTEGER,
            artist_id INTEGER,
            role TEXT DEFAULT 'primary',

            PRIMARY KEY (track_id, artist_id),

            FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            FOREIGN KEY(artist_id) REFERENCES artists(id) ON DELETE CASCADE
            );
            """)

        self.cur.execute("""
            CREATE TABLE covers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cover_hash TEXT UNIQUE,
                image_url TEXT
            )
            """)

        self.cur.execute("""
            CREATE TABLE playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

        self.cur.execute("""
            CREATE TABLE playlist_tracks (
            playlist_id INTEGER,
            track_id INTEGER,
            position INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            PRIMARY KEY (playlist_id, position),

            FOREIGN KEY(playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY(track_id) REFERENCES tracks(id) ON DELETE CASCADE
            );
            """)
        self.cur.execute("""
            CREATE VIRTUAL TABLE track_search USING fts5(
                track_id UNINDEXED,
                title,
                album,
                artists
            );
            """)
        
        self.conn.commit()

    async def scan_folder(self, folder: str, observers: list):
        loop = asyncio.get_running_loop()
        music_ext = {".flac", ".mp3", ".m4a", ".ogg", ".wav"}
        self.conn.execute("BEGIN")
        for path in Path(folder).rglob("*"):
            if path.suffix.lower() in music_ext:
                try:
                    await loop.run_in_executor(None, self.add_track, str(path))
                except Exception as e:
                    print(traceback.format_exc())

        self.conn.commit()

        for observer in observers:

            getattr(observer, "on_library_loaded")()

    async def update_fingerprints(self, folder: str, observers: list):
        tracks = tuple(self.get_tracks(limit=-1)[0])
        alert = False
        for track in tracks:
            if not Path(
                track.file_path
            ).exists(): 
                self.cur.execute(
                    """
                                 DELETE FROM tracks WHERE path = ?
                                 """,
                    (track.file_path,),
                )
            if not track.chromaprint and not track.acoustid and not track.release_mbid:
                alert = True
                chromaprint = await asyncio.to_thread(track.generate_chromaprint)
                self.add_chromaprint(chromaprint, track.file_hash)
                #GenIDs(track, self)

        self.conn.commit()
        print("Updated Chromaprints")
        for observer in observers:
            getattr(observer, "on_fingerprints_loaded")()

    
    def update_search_index(self, track_id: int):
        self.cur.execute(
            """
            DELETE FROM track_search
            WHERE track_id = ?
            """,
            (track_id,),
        )

        row = self.cur.execute(
            """
            SELECT
                t.id,
                t.title,
                COALESCE(al.title, '') AS album,
                COALESCE(GROUP_CONCAT(a.name, '||'), '') AS artists
            FROM tracks t
            LEFT JOIN albums al ON t.album_id = al.id
            LEFT JOIN track_artists ta ON ta.track_id = t.id
            LEFT JOIN artists a ON a.id = ta.artist_id
            WHERE t.id = ?
            GROUP BY t.id
            """,
            (track_id,),
        ).fetchone()

        if row:
            self.cur.execute(
                """
                INSERT INTO track_search(
                    track_id,
                    title,
                    album,
                    artists
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["title"],
                    row["album"],
                    row["artists"],
                ),
            )

    def add_track(self, file_path: str):
        exists, file_hash = self.track_hash_exists(file_path)
        
        track = Track.from_file(file_path)
        
        if exists:
            return

        cover_id = self.get_cover_id(track.cover_hash)

        artist_id = self.get_artist_id(track.artist, track.artist_mbid)
        artists = track.artists[1:]
        
        album_id = self.get_album_id(track.album, track.release_year, track.release_mbid, track.release_group_mbid)
        self.link_album_artist(album_id, artist_id)
        
        track_id = self.should_overwrite(track)


        if track_id is None:
            track_id = self.insert_track(
                track.title,
                file_path,
                album_id,
                track.duration,
                track.tracknumber,
                track.discnumber,
                file_hash,
                cover_id,
                track.modified_at,
                track.recording_mbid,
                track.track_mbid,
                track.acoustid
            )
        else:
            self.update_track(
                track.title,
                file_path,
                album_id,
                track.duration,
                track.tracknumber,
                track.discnumber,
                file_hash,
                cover_id,
                track.modified_at,
                track.recording_mbid,
                track.track_mbid,
                track.acoustid
            )

        self.link_track_artist(track_id, artist_id)
        artists = track.artists[1:]
        for artist in artists:
                artist_id = self.get_artist_id(artist, None)
                self.link_track_artist(track_id, artist_id)
        
        self.update_search_index(track_id)

    def should_overwrite(self, track: "Track") -> int | None:
        row = self.cur.execute(
            """
            SELECT id, modified_at
            FROM tracks
            WHERE path = ?
            """,
            (track.file_path,),
        ).fetchone()

        if row is None:
            return None

        db_modified = row["modified_at"]

        try:
            if int(track.modified_at) > int(db_modified):
                return row["id"]
        except (TypeError, ValueError):
            # If timestamps are missing or malformed, overwrite anyway
            return row["id"]

        return None
        

    def track_hash_exists(self, file_path) -> tuple[bool, str]:
        hash = hash_file(file_path)
        self.cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM tracks WHERE hash = ?
            )
        """,
            (hash,),
        )
        return (bool(self.cur.fetchone()[0]), hash)

    def get_artist_id(self, artist_name, artist_mbid):
        if not artist_name:
            artist_name = "Unknown Artist"

        row = self.cur.execute(
            "SELECT * FROM artists WHERE name=?", (artist_name,)
        ).fetchone()


        
        if row and artist_mbid and dict(row)["artist_mbid"] is None:
            self.cur.execute("""UPDATE artists SET name=?, artist_mbid=? WHERE id=?""", (artist_name, artist_mbid, dict(row)["id"]))
            return dict(row)["id"]
        elif row:
            return dict(row)["id"]
            
        self.cur.execute("""INSERT INTO artists(name, artist_mbid) VALUES (?, ?)""", (artist_name, artist_mbid,))

        return self.cur.lastrowid

    def get_album_id(self, album_name, year, release_mbid, release_group_mbid):
        if not album_name:
            album_name = "Unknown Album"

        row = self.cur.execute(
            "SELECT id FROM albums WHERE title=?", (album_name,)
        ).fetchone()

        if row:
            return row[0]

        self.cur.execute("INSERT INTO albums(title, year, release_mbid, release_group_mbid) VALUES (?,?,?,?)", (album_name, year, release_mbid, release_group_mbid,))

        return self.cur.lastrowid

    def link_track_artist(self, track_id, artist_id):
        self.cur.execute(
            """
        INSERT OR IGNORE INTO track_artists(track_id, artist_id)
        VALUES (?, ?)
        """,
            (track_id, artist_id),
        )

    def link_album_artist(self, album_id, artist_id):
        self.cur.execute(
            """
        INSERT OR IGNORE INTO album_artists(album_id, artist_id)
        VALUES (?, ?)
        """,
            (album_id, artist_id),
        )

    def insert_track(
        self,
        title,
        path,
        album_id,
        duration,
        track_no,
        disc_no,
        file_hash,
        cover_id,
        modified_at,
        recording_mbid,
        track_mbid,
        acoustid
    ):

        self.cur.execute(
            """
            INSERT INTO tracks
            (title, path, album_id, duration, track_number, disc_number, hash, cover_id,  modified_at, recording_mbid, track_mbid, acoustid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                path,
                album_id,
                duration,
                track_no,
                disc_no,
                file_hash,
                cover_id,
                modified_at,
                recording_mbid,
                track_mbid,
                acoustid
            ),
        )
        return self.cur.lastrowid

    def update_track(
        self,
        title,
        path,
        album_id,
        duration,
        track_no,
        disc_no,
        file_hash,
        cover_id,
        modified_at,
        recording_mbid,
        track_mbid,
        acoustid
    ):

        self.cur.execute(
            """
            UPDATE tracks
SET
    title = ?,
    album_id = ?,
    duration = ?,
    track_number = ?,
    disc_number = ?,
    hash = ?,
    cover_id = ?,
    modified_at = ?,
    recording_mbid = ?,
    track_mbid = ?,
    acoustid = ?
WHERE path = ?
            """,
            (
                title,
                album_id,
                duration,
                track_no,
                disc_no,
                file_hash,
                cover_id,
                modified_at,
                recording_mbid,
                track_mbid,
                acoustid,
                path,
            ),
        )

    def add_chromaprint(self, chromaprint, hash):
        self.cur.execute(
            """
            UPDATE tracks
            SET chromaprint = ?
            WHERE hash = ?
            """,
            (
                chromaprint,
                hash,
            ),
        )

    def get_cover_id(self, cover_hash):

        row = self.cur.execute(
            "SELECT id FROM covers WHERE cover_hash=?", (cover_hash,)
        ).fetchone()

        if row:
            return row[0]

        self.cur.execute("INSERT INTO covers(cover_hash) VALUES (?)", (cover_hash,))
        self.new_cover_id = int(self.cur.lastrowid) + 1  # type: ignore
        return self.cur.lastrowid

    def get_tracks(
    self,
    user_search="",
    ascending=True,
    limit=100,
    offset=0) -> tuple[list[Track], int]:
        

        direction = "ASC" if ascending else "DESC"
    
        search = user_search.strip()
    
        if search:
            fts_query = " ".join(
                f"{word}*"
                for word in search.split()
            )
    
            query = """
            SELECT
                t.*,
                al.title AS album,
                c.cover_hash,
                ts.artists,
                bm25(track_search) AS score,
                al.release_mbid
            FROM track_search ts
            JOIN tracks t ON t.id = ts.track_id
            LEFT JOIN albums al ON al.id = t.album_id
            LEFT JOIN covers c ON c.id = t.cover_id
            WHERE track_search MATCH ?
            ORDER BY score
            LIMIT ? OFFSET ?
            """
    
            rows = self.cur.execute(
                query,
                (fts_query, limit, offset)
            ).fetchall()
            
            self.cur.execute(
                """
                SELECT COUNT(*)
                FROM track_search
                WHERE track_search MATCH ?
                """,
                (fts_query,)
            )
            total = self.cur.fetchone()[0]
    
        else:
            query = f"""
            SELECT
                t.*,
                al.title AS album,
                c.cover_hash,
                COALESCE(
                    GROUP_CONCAT(a.name, '||'),
                    'Unknown Artist'
                ) AS artists,
                al.release_mbid
            FROM tracks t
            LEFT JOIN albums al ON al.id = t.album_id
            LEFT JOIN covers c ON c.id = t.cover_id
            LEFT JOIN track_artists ta ON ta.track_id = t.id
            LEFT JOIN artists a ON a.id = ta.artist_id
            GROUP BY t.id
            ORDER BY t.title COLLATE NOCASE {direction}
            LIMIT ? OFFSET ?
            """
    
            rows = self.cur.execute(query, (limit, offset)).fetchall()
            self.cur.execute(
                """
                SELECT COUNT(*)
                FROM track_search
                """,
            )
            total = self.cur.fetchone()[0]
    
        tracks = []
    
        for row in rows:
            data = dict(row)
            artists = data.get("artists", "")
    
            if artists:
                data["artists"] = artists.split("||")
                data["artist"] = data["artists"][0]
            else:
                data["artists"] = ["Unknown Artist"]
                data["artist"] = "Unknown Artist"
    
            tracks.append(Track.from_db(data))
    
        return (tracks, total)
    
    def get_cover_url(self, track:Track) -> str | None:
        query = """SELECT c.image_url
        FROM tracks t
        JOIN covers c ON t.cover_id = c.id
        WHERE t.path = ?"""
  
        
        row = self.cur.execute(query, (track.file_path,)).fetchone()
        return dict(row).get("image_url")
    
    def set_cover_url(self, track:Track, cover_url):
        query = """UPDATE covers
        SET image_url = ?
        WHERE id = (
            SELECT cover_id
            FROM tracks
            WHERE path = ?
        )"""
        self.cur.execute(query, (cover_url, track.file_path, ))
        self.conn.commit()
    
def hash_file(file_path, block_size=65536):
    h = hashlib.md5()
    size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        h.update(f.read(block_size))
        if size > block_size:
            f.seek(-block_size, os.SEEK_END)
            h.update(f.read(block_size))
        return h.hexdigest()

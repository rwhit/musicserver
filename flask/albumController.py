from mediaplayerController import get_mediaplayer
from baseController import BaseController
import psycopg2
import psycopg2.extensions
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

class AlbumController(BaseController):
    def __init__(self, config, connFactory):
        BaseController.__init__(self)
        self.config = config
        self.connFactory = connFactory

    def get_albums(self):
        albums = []
        conn = None
        try:
            conn = self.connFactory.getConnection()
            with conn.cursor() as cursor:
                cursor.execute('select title, artist, path, id from album order by title')
                albumData = cursor.fetchone()
                while albumData:
                    albums.append(albumData)
                    albumData = cursor.fetchone()
        finally:
            conn.close()
        return albums


import psycopg2
import psycopg2.extras

class ConnFactory:
    def __init__(self, config):
        self.config = config

    def getConnection(self):
        conn = psycopg2.connect('dbname={} user={}'.format(self.config.dbname, self.config.dbuser))
        psycopg2.extras.register_json(conn)
        return conn

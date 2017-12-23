from connFactory import ConnFactory

GLOBAL_CONFIG_DBNAMESPACE = 'global_config'

class MusicServerConfig():
    def __init__(self):
        # bootstrap
        self._config = {
            'dbname': 'pi',
            'dbuser': 'pi'
        }
        # TODO load rest from db
        conn = None
        try:
            conn = ConnFactory(self).getConnection()
            with conn.cursor() as cursor:
                cursor.execute('select key, value from app_state where namespace = %(namespace)s',
                               {'namespace': GLOBAL_CONFIG_DBNAMESPACE})
                for (key,value) in cursor.fetchall():
                  self._config[key] = value
        finally:
            if(conn):
                conn.close()

    def __getattr__(self, name):
        try:
            return self._config[name]
        except KeyError:
            raise AttributeError("'{}' object has no attribute '{}'".format('MusicServerConfig', name)) from None

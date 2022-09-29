from google.protobuf.json_format import MessageToJson, Parse
import time
from datetime import datetime, timedelta
import sqlite3


class SqlQueryCache:

    _cursor = None
    _connection = None

    def __init__(self):
        print("================== starting cache ================= ")

    @property
    def connection(self):
        if self._connection is None:
            # Set isolation level to None to autocommit all changes to the database.
            self._connection = sqlite3.connect("./test.db", check_same_thread=False, isolation_level=None)
            # self._connection = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    @property
    def cursor(self):
        """Start a cursor and create a database called 'session'"""
        if self._cursor is None:
            self._cursor = self.connection.cursor()
            self._cursor.execute(
                """CREATE TABLE IF NOT EXISTS cached_stat
                (storage_id, opaque_id, stored_value, btime)"""
            )

        return self._cursor

    def close(self):
        """Close the sqlite connection"""
        if self._cursor is not None:
            self._cursor.close()
            self._cursor = None

    def item_exists(self, storage_id, opaque_id):
        """Check to see if the session of a given name exists"""
        self.cursor.execute("SELECT * FROM cached_stat WHERE storage_id=? AND opaque_id=?", (storage_id, opaque_id))
        row = self.cursor.fetchone()
        exists = False
        print('-----------------')

        if row is not None:
            btime = row['btime']
            exists = datetime.fromtimestamp(btime) + timedelta(minutes=3) > datetime.fromtimestamp(time.time())
            if not exists:
                self.cursor.execute("DELETE FROM cached_stat WHERE storage_id=? AND opaque_id=?", (storage_id, opaque_id))

        print('item exists:', exists)
        return exists

    def save_item(self, storage_id=None, opaque_id=None, stored_value=None):
        btime = datetime.timestamp(datetime.now())
        stored_value = MessageToJson(stored_value)
        if not self.item_exists(storage_id, opaque_id):
            self.cursor.execute(
                "INSERT INTO cached_stat VALUES (?,?,?,?)", (storage_id, opaque_id, stored_value, btime)
            )

    def get_stored_value(self, storage_id, opaque_id, message):
        self.cursor.execute("SELECT * FROM cached_stat WHERE storage_id=? AND opaque_id=?", (storage_id, opaque_id))
        row = self.cursor.fetchone()
        if row is not None:
            return Parse(row['stored_value'], message)
        else:
            return None

    def __del__(self):
        self.close()

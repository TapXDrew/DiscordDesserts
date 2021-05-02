import json
import os
import sqlite3
import traceback

DATABASE = os.getcwd()+'/databases/Data.db'
TABLE = 'PlayerInfo'


class Player:
    def __init__(self, bot, ctx, user=None):
        self.config = json.load(open(os.getcwd() + '/config/config.json'))
        self.added_fields = []
        self.removed_fields = []

        self.bot = bot
        self.ctx = ctx
        self.ctx.author = user if user else ctx.author

        try:
            self.conn = sqlite3.connect(DATABASE)
        except sqlite3.Error:
            self.conn = None
            traceback.print_exc()
        self.cursor = self.conn.cursor()

        self._create_table()
        self._get_player_info()

    def _create_table(self):
        query = f"""CREATE TABLE IF NOT EXISTS {TABLE} (ID BIGINT PRIMARY KEY)"""
        self.cursor.execute(query)
        self.conn.commit()

    def _update_table(self):
        query = f"""SELECT * FROM {TABLE}"""
        cursor = self.cursor.execute(query)

        self.added_fields = []
        self.removed_fields = [name for name in self.config['Database Info']['Delete Fields'] if name in [field[0] for field in cursor.description]]

        info = self.cursor.fetchall()[0]
        if info:
            for column in self.config['Database Info']['All Fields']:
                try:
                    query = f"""ALTER TABLE {TABLE} ADD COLUMN {column} {self.config['Database Info'][column]['Type']} DEFAULT {self.config['Database Info'][column]['Value']}"""
                    self.cursor.execute(query)
                    self.conn.commit()
                    self.added_fields.append(column)
                except sqlite3.OperationalError:
                    pass
                except Exception:
                    traceback.print_exc()

            if self.config['Database Info']['Delete Fields']:
                fields = [(field, self.config['Database Info'][field]['Type'], self.config['Database Info'][field]['Value']) for field in self.config['Database Info']['All Fields'] if field not in self.config['Database Info']['Delete Fields']]

                query = f"""CREATE TABLE IF NOT EXISTS new_{TABLE} ({', '.join([f'{field[0]} {field[1]} DEFAULT {field[2]}' for field in fields])})"""
                self.cursor.execute(query)

                query = f"""INSERT INTO new_{TABLE} SELECT {', '.join([field[0] for field in fields])} FROM {TABLE}"""
                self.cursor.execute(query)

                query = f"""DROP TABLE IF EXISTS {TABLE}"""
                self.cursor.execute(query)

                query = f"""ALTER TABLE new_{TABLE} RENAME TO {TABLE}"""
                self.cursor.execute(query)

                self.conn.commit()

    def _get_player_info(self):
        try:
            self._update_table()
        except IndexError:
            self._create_player()
            return self._get_player_info()

        query = f"SELECT * FROM {TABLE} WHERE id = ?"
        self.cursor.execute(query, (self.ctx.author.id,))
        info = self.cursor.fetchall()[0]

        self.data = {}
        for key, value in zip(self.config['Database Info']['All Fields'], info):
            self.data[key] = value

    def _create_player(self):
        query = f"""INSERT INTO {TABLE} VALUES (?)"""
        self.cursor.execute(query, (self.ctx.author.id,))
        self.conn.commit()

    def update_value(self, column, value):
        query = f"UPDATE {TABLE} SET {column} = ? WHERE ID = ?"
        self.cursor.execute(query, (value, self.ctx.author.id))
        self.conn.commit()
        self._get_player_info()

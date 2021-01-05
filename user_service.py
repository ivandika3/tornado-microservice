import tornado.web
import tornado.log
import tornado.options
import sqlite3
import logging
import json
import time

class App(tornado.web.Application):

    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

        # Initialising db connection
        self.db = sqlite3.connect("users.db")
        self.db.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cursor = self.db.cursor()

        # Create table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS 'users' ("
            + "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
            + "name TEXT NOT NULL,"
            + "created_at INTEGER NOT NULL,"
            + "updated_at INTEGER NOT NULL"
            + ");"
        )
        self.db.commit()

# TODO: Refactor into separate file
class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))

# /users
class UsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self, name):
        # Parsing pagination params
        page_num = self.get_argument("page_num", 1)
        page_size = self.get_argument("page_size", 10)
        try:
            page_num = int(page_num)
        except:
            logging.exception("Error while parsing page_num: {}".format(page_num))
            self.write_json({"result": False, "errors": "invalid page_num"}, status_code=400)
            return

        try:
            page_size = int(page_size)
        except:
            logging.exception("Error while parsing page_size: {}".format(page_size))
            self.write_json({"result": False, "errors": "invalid page_size"}, status_code=400)
            return
        
        # # Parsing name param
        if name is not None:
            try:
                name = str(name)
            except:
                self.write_json({"result": False, "errors": "invalid name"}, status_code=400)
                return
        
        # Building select statement
        select_stmt = "SELECT * FROM users"
        
        # Order by and pagination
        limit = page_size
        offset = (page_num - 1) * page_size
        select_stmt += " ORDER BY created_at DESC LIMIT ? OFFSET ?"

        # Fetching listings from db
        if name is not None:
            args = (name, limit, offset)
        else: 
            args = (limit, offset)
        cursor = self.application.db.cursor()
        results = cursor.execute(select_stmt, args)

        users = []
        for row in results:
            fields = ["id", "name", "created_at", "updated_at"]
            user = {
                field: row[field] for field in fields
            }
            users.append(user)
        
        self.write_json({"result": True, "users": users})


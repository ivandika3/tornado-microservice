import tornado.web
import tornado.log
import tornado.options
import sqlite3
import logging
import json

class App(tornado.web.Application):

    def __init__(self, handlers, **kwargs):
        super().__init__(handlers, **kwargs)

        # Initialising db connection
        self.db = sqlite3.connect("listings.db")
        self.init_db()

    def init_db(self):
        cursor = self.db.cursor()

        # Create table
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS 'listings' ("
            + "id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,"
            + "user_id INTEGER NOT NULL,"
            + "listing_type TEXT NOT NULL,"
            + "price INTEGER NOT NULL,"
            + "created_at INTEGER NOT NULL,"
            + "updated_at INTEGER NOT NULL"
            + ");"
        )
        self.db.commit()

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj):
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(obj))

# /v1/listings
class GetListingsHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
        cursor = self.application.db.cursor()
        results = cursor.execute("SELECT * FROM 'listings' ORDER BY 'created_at' DESC")

        listings = []
        for row in results:
            listings.append(row)

        self.write_json({"listings": listings})

# /v1/listings/ping
class PingHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.write("pong!")

def make_app(options):
    return App([
        (r"/v1/listings/ping", PingHandler),
        (r"/v1/listings", GetListingsHandler),
    ], debug=options.debug)

if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6000)
    tornado.options.define("port", default=6000)
    # Specify whether the app should run in debug mode
    # Debug mode restarts the app automatically on file changes
    tornado.options.define("debug", default=True)

    # Read settings/options from command line
    tornado.options.parse_command_line()

    # Access the settings defined
    options = tornado.options.options

    # Create web app
    app = make_app(options)
    app.listen(options.port)
    logging.info("Starting listing service on port {}".format(options.port))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()

import tornado.web
import tornado.log
import tornado.options
import tornado.httpclient.AsyncHTTPClient
import tornado.httputil import url_concat
import logging
import json

# TODO: use env
# CONSTANTS
LISTINGS_URL = "http://127.0.0.1/6000/"
USERS_URL = "http://127.0.0.1/8000"

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))

class ListingsHandler(BaseHandler):
    @tornado.gen.coroutine
    def get(self):
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
        
        user_id = self.get_argument("user_id", None)
        if user_id is not None:
            try:
                user_id = int(user_id)

            except:
                self.write_json({"result": False, "errors": "invalid user_id"}, status_code=400)
                return

        # Call the listings service's API and (public-api service acts as a client)
        listingsURL = LISTINGS_URL
        usersURL = USERS_URL

        if user_id is not None:
            listingParams = {"user_id": user_id}
            listingsURL = url_concat(LISTINGS_URL, params)
            usersURL = USERS_URL + str(user_id)

        listingsResp, usersResp = parallel_fetch_id(listingsURL, usersURL)

        # If there is no user under that user_id - Foreign key constraints is violated

    @tornado.gen.coroutine
    def sync_fetch_gen(url):
        http_client = AsyncHTTPClient()
        response = yield http_client.fetch(url)
        raise gen.Return(response.body)

    # If the user_id param is supplied
    @tornado.gen.coroutine
    def parallel_fetch_id(listingsURL, usersURL):
        listingsResp, usersResp = yield [http_client.fetch(listingsURL),
                                         http_client.fetch(usersURL)]

    @tornado.gen.coroutine
    def post(self):

    

class UsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):


# Path to the request handler
def make_app(options):
    return App([
        (r"/public-api/listings", ListingsHandler),
        (r"/public-api/users", UsersHandler),
    ], debug=options.debug)


if __name__ == "__main__":
    # Define settings/options for the web app
    # Specify the port number to start the web app on (default value is port 6000)
    tornado.options.define("port", default=7000)
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
    logging.info("Starting public-api service. PORT: {}, DEBUG: {}".format(options.port, options.debug))

    # Start event loop
    tornado.ioloop.IOLoop.instance().start()
import tornado.web
import tornado.log
import tornado.options
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import url_concat
import logging
import json

# TODO: use env
LISTINGS_URL = "http://localhost:6000/listings"
USERS_URL = "http://localhost:8000/users"

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

        # TODO: Refactor
        # There are two ways that I can think to join Listings and Users based on the user_id
        # 1. For every listing, call an API to fetch the user with the specific user_id
        #       Limitation: need to call an API multiple times
        # 2. Use cache to store the user information so that we don't have to fetch the user for each listing
        #       Limitation: memory overhead (public-api service might be bloated) 
        # Decided to use approach 1

        http_client = AsyncHTTPClient()
        try :
            if user_id is not None:
                # Preparing URL parameters
                listingParams = {"user_id": user_id}
                listingsURL = url_concat(LISTING_URL, listingParams)
                userURL = USERS_URL + "/" + str(user_id)

                listingsResp, usersResp = yield [http_client.fetch(listingsURL), http_client.fetch(usersURL)]
                listings = json.loads(listingsResp.body.decode('utf-8'))['listings']
                user = json.loads(usersResp.body.decode('utf-8'))['user']
                # TODO: If there is no user under that user_id - Foreign key constraints is violated

                for listing in listings:
                    listing['user'] = user
            else:
                listingsResp = yield http_client.fetch(LISTINGS_URL)
                listings = json.loads(listingsResp.body.decode('utf-8'))['listings']

                for listing in listings:
                    usersURL = USERS_URL + "/" + str(listing['user_id'])
                    userResp = yield http_client.fetch(USERS_URL + "/" + str(listing['user_id']))

                    user = json.loads(userResp.body.decode('utf-8'))['user']
                    listing['user'] = user

        except Exception as e:
            http_client.close()
            self.write_json({"result": False, "errors": str(e)}, status_code=404)
            return

        http_client.close()
        self.write_json({"result": True, "listings": listings}, status_code=200)

    # TODO: DELETE IF NOT IN USE
    # @tornado.gen.coroutine
    # def sync_fetch_gen(url):
    #     http_client = AsyncHTTPClient()
    #     response = yield http_client.fetch(url)
    #     raise gen.Return(response.body)

    # @tornado.gen.coroutine
    # def parallel_fetch(listingsURL, usersURL):
    #     http_client = AsyncHTTPClient()
    #     listingsResp, usersResp = yield [http_client.fetch(listingsURL),
    #                                      http_client.fetch(usersURL)]
    #     return gen.Return(listingsResp.body, usersResp.body)
    
    @tornado.gen.coroutine
    def post(self):
        self.write_json({"result": False, "errors": "not implemented yet"}, status_code=400)

    

class UsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        self.write_json({"result": False, "errors": "not implemented yet"}, status_code=400)

# TODO: Remove if not in use
class InvalidUserIDError(Exception):
    # Exception raised when listings refer to user_id that does not exist
    # Acts as a foreign key constraint checker

    def __init__(self, message="One or more entries in listings are referring to user_id that does not exist."):
        self.message = message


# Path to the request handler
def make_app(options):
    return tornado.web.Application([
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
import os
import tornado.web
import tornado.log
import tornado.options
from tornado.httpclient import AsyncHTTPClient
from tornado.httputil import url_concat
from pymemcache.client import base
from pymemcache import serde
import logging
import json
import urllib

LISTINGS_URL = os.getenv('LISTINGS_URL')
USERS_URL = os.getenv('USERS_URL')
if LISTINGS_URL is None:
    LISTINGS_URL = "http://localhost:6000/listings"
if USERS_URL is None:
    USERS_URL = "http://localhost:8000/users"

class BaseHandler(tornado.web.RequestHandler):
    def write_json(self, obj, status_code=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.write(json.dumps(obj))

class ListingsHandler(BaseHandler):
    @tornado.gen.coroutine
    def get_user(self, user_id, http_client, memcache_client):
        user = memcache_client.get(str(user_id))
        if user is None:
            print("cache miss")
            userURL = USERS_URL + "/" + str(user_id)
            usersResp = yield http_client.fetch(userURL, raise_error=False)
            userJSON = json.loads(usersResp.body.decode('utf-8'))
            if not userJSON['result']:
                http_client.close()
                self.write_json(userJSON, status_code=400)
                return
            user = userJSON['user']
            memcache_client.set(str(user_id), user)
        else:
            print("cache hit")
        return user

    @tornado.gen.coroutine
    def get(self):
        # Parsing pagination params
        page_num = self.get_argument("page_num", 1)
        page_size = self.get_argument("page_size", 10)
        user_id = self.get_argument("user_id", None)

       
        http_client = AsyncHTTPClient()
        # Use memcached to cache repeated user 
        memcache_client = base.Client('localhost', serde=serde.pickle_serde)
        try :
            listingParams = {}
            if user_id is not None:
                listingParams = {"user_id": user_id, "page_num": page_num, "page_size": page_size}
                userURL = USERS_URL + "/" + str(user_id)
            else:
                listingsParams = {"page_num": page_num, "page_size": page_size}

            listingsURL = url_concat(LISTINGS_URL, listingParams)
            listingsResp = yield http_client.fetch(listingsURL, raise_error=False)
            listingsJSON = json.loads(listingsResp.body.decode('utf-8'))
            if not listingsJSON['result']:
                http_client.close()
                self.write_json(listingsJSON, status_code=400)
                return
            listings = listingsJSON['listings']

            if user_id is not None: 
                user = yield self.get_user(user_id, http_client, memcache_client)
            else :
                for listing in listings:
                    user = yield self.get_user(listing['user_id'], http_client, memcache_client)
                    listing['user'] = user
        except Exception as e:
            print(e)
            self.write_json({"result": False, "errors": str(e)}, status_code=400)
            http_client.close()
            return
        finally: 
            http_client.close()
        self.write_json({"result": True, "listings": listings}, status_code=200)

    @tornado.gen.coroutine
    def post(self):
        http_client = AsyncHTTPClient()
        try :
            # Collecting required params
            post_data = { "user_id" : self.get_argument("user_id"), 
                        "listing_type" : self.get_argument("listing_type"),
                        "price" : self.get_argument("price")}
            body = urllib.parse.urlencode(post_data)
            listingResp = yield http_client.fetch(LISTINGS_URL, method="POST", headers=None, body=body, raise_error=False)
            listing = json.loads(listingResp.body.decode('utf-8'))['listing']
        except Exception as e:
            http_client.close()
            self.write_json({"result": False, "errors": str(e)}, status_code=400)
            return
        finally: 
            http_client.close()
        self.write_json({"result": True, "listing": listing}, status_code=200)


class UsersHandler(BaseHandler):
    @tornado.gen.coroutine
    def post(self):
        http_client = AsyncHTTPClient()
        try:
            post_data = { "name" : self.get_argument("name")}
            body = urllib.parse.urlencode(post_data)
            userResp = yield http_client.fetch(USERS_URL, method="POST", headers=None, body=body, raise_error=False)
            user = json.loads(userResp.body.decode('utf-8'))['user']
        except Exception as e:
            http_client.close()
            self.write_json({"result": False, "errors": str(e)}, status_code=400)
            return
        finally: 
            http_client.close()
        self.write_json({"result" : True, "user" : user}, status_code=200)


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
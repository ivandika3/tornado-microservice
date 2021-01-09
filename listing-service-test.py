import services.listings.listing_service as listings
from tornado.testing import AsyncHTTPTestCase, gen_test

class TestListingService(AsyncHTTPTestCase):
    def get_app(self):
        return listings.make_app()

    @gen_test
    def test_listing_connectivity(self):
        response = yield self.http_client.fetch('/listings/ping')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, 'pong!')

if __name__ == '__main__':
    

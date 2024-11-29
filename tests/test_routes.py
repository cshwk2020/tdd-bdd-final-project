######################################################################
# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
import random
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus

from service import app
from service.common import status
from service.models import db, init_db, Product, Category
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        # """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        # """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)


        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)


        #
        # Uncomment this code once READ is implemented
        #

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)



    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)




    #
    # ADD YOUR TEST CASES HERE
    #

    # ----------------------------------------------------------
    # TEST LIST ALL
    # ----------------------------------------------------------
    def test_get_products(self):

        """It should list all Products"""
        N = 10
        self._create_products(N)
        response = self.client.get(BASE_URL) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json() 
        self.assertEqual(len(data), N)


    def test_get_products_by_name(self):
        
        N = 10
        products = self._create_products(N)
        rand_product = products[random.randint(0, N-1)]
        #
        rand_name_count = len([product for product in products if product.name == rand_product.name])
        #
        response = self.client.get(
            BASE_URL, query_string=f"name={quote_plus(rand_product.name)}" )
        #
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_products = response.get_json() 
        self.assertEqual(len(db_products), rand_name_count)


    def test_get_products_by_category(self):
        
        N = 10
        products = self._create_products(N)
        rand_product = products[random.randint(0, N-1)]
        #
        rand_category_count = len([product for product in products if product.category == rand_product.category])
        #
        response = self.client.get(
            BASE_URL, query_string=f"category={rand_product.category.name}" )
        #
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_products = response.get_json() 
        self.assertEqual(len(db_products), rand_category_count)


    def test_get_products_by_available(self):

        N = 10
        products = self._create_products(N)
        rand_bool = bool(random.randint(0, 1))
        #
        rand_bool_count = len([product for product in products if product.available is rand_bool])
        #
        response = self.client.get(
            BASE_URL, query_string=f"available={rand_bool}" )
        #
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_products = response.get_json() 
        self.assertEqual(len(db_products), rand_bool_count)




    def test_get_product(self):

        """It should list all Products"""
        N = 10
        self._create_products(N)
        #
        products = self._create_products(N)
        rand_product = products[random.randint(0, N-1)]
        #
        response = self.client.get(f"{BASE_URL}/{rand_product.id}") 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        db_product = response.get_json() 
        self.assertEqual(rand_product.id, db_product['id'])
        #
        response = self.client.get(f"{BASE_URL}/{N+100}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
 


    def test_update_product(self):
        #
        test_product = ProductFactory()
        create_response = self.client.post(BASE_URL, json=test_product.serialize()) 
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product_json = create_response.get_json()
        new_product_json["description"] = "unknown"
        update_response = self.client.put(f"{BASE_URL}/{new_product_json['id']}", json=new_product_json) 
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        updated_product = update_response.get_json() 
        self.assertEqual(updated_product["description"], "unknown")


    def test_update_nonexist_product(self):
        #
        test_product = ProductFactory()
        create_response = self.client.post(BASE_URL, json=test_product.serialize()) 
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        # update the product
        new_product_json = create_response.get_json()
        new_product_json["description"] = "unknown"
        update_response = self.client.put(f"{BASE_URL}/{1 + new_product_json['id']}", json=new_product_json) 
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)
        #app.logger.error('HTTP_404_NOT_FOUND', new_product_json['id'])
        

    def test_delete_product(self):
        #
        test_product = ProductFactory()
        create_response = self.client.post(BASE_URL, json=test_product.serialize()) 
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        # delete the product
        new_product_json = create_response.get_json()
        delete_response = self.client.delete(f"{BASE_URL}/{new_product_json['id']}", json=new_product_json) 
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        

    ################################

    def test_method_not_allowed(self):
        test_product = ProductFactory()
        #
        test_product.id = None
        update_response = self.client.put(f"{BASE_URL}", json=test_product.serialize())
        self.assertEqual(update_response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
       
         

    def test_method_exception(self):
        test_product = ProductFactory()
        #
        exception_response = self.client.post(f"{BASE_URL}/raise/exception", json=test_product.serialize())
        self.assertEqual(exception_response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR) 



    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)

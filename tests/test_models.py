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

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
 

from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory
from service.models import DataValidationError
import random

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #
 
    def test_read_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # 
        found_product = Product.find(product.id)
        self.assertEqual(found_product.id, product.id)
        self.assertEqual(found_product.name, product.name)
        self.assertEqual(found_product.description, product.description)
        self.assertEqual(found_product.price, product.price)
 

    def test_update_invalid_product(self):

        # create a product
        product = ProductFactory()
        product.id = None
        #
        with self.assertRaises(DataValidationError) as context:
            product.update()
       
 
    def test_update_a_product(self):

        # create a product
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)

        # modify desc
        product.description = "testing"
        original_id = product.id
        product.update()

        found_product = Product.find(original_id)
        self.assertEqual(found_product.id, original_id)
        self.assertEqual(found_product.description, "testing")

        #  
        products = Product.all()
        self.assertEqual(len(products), 1)
        first_product = products[0]
        self.assertEqual(first_product.id, original_id)
        self.assertEqual(first_product.description, "testing")
 

    def test_delete_a_product(self):
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertIsNotNone(product.id)
        #
        products = Product.all()
        self.assertEqual(len(products), 1)
        #
        product.delete()
        #  
        products = Product.all()
        self.assertEqual(len(products), 0)


    def test_list_all_products(self):

        N = 10
        for i in range(N):
            product = ProductFactory()
            product.create()
            #
            products = Product.all()
            self.assertEqual(len(products), i+1)
        #
        products = Product.all()
        for i in range(N):
            products[N-i-1].delete()
            #
            products = Product.all()
            self.assertEqual(len(products), N-i-1)


    def test_find_product_by_name(self):

        N = 10
        for i in range(N):
            product = ProductFactory()
            product.create()

        products = Product.all()
        mid_product = products[random.randint(0,N-1)]
        mid_product_count = len([product for product in products if product.name == mid_product.name])
        found_products = Product.find_by_name(mid_product.name)
        self.assertEqual(mid_product_count, found_products.count())
         
    
    def test_find_product_by_category(self):

        N = 10
        for i in range(N):
            product = ProductFactory()
            product.create()
        
        products = Product.all()
        rand_product = products[random.randint(0,N-1)]
        rand_product_category = rand_product.category
        #
        arr_count = len([product for product in products if product.category == rand_product_category])
        db_found = Product.find_by_category(rand_product_category)
        #
        self.assertEqual(db_found.count(), arr_count)
    

    def test_find_product_by_available(self):

        N = 10
        for i in range(N):
            product = ProductFactory()
            product.create()
        
        products = Product.all()
        rand_product = products[random.randint(0,N-1)]
        rand_product_available = rand_product.available
        #
        arr_count = len([product for product in products if product.available == rand_product_available])
        db_found = Product.find_by_availability(rand_product_available)
        #
        self.assertEqual(db_found.count(), arr_count)

 
    #
    def test_serialize_a_product(self):

        #
        product_1 = ProductFactory()
        product_1.create()
        #
        product_2 = ProductFactory()
        product_2.create()
        #
        dict_1 = product_1.serialize()
        #
        self.assertNotEqual(product_1.name, product_2.name)
        #
        deserialize_product = product_2.deserialize(dict_1)
        self.assertEqual(product_1.name, deserialize_product.name)

        #
        product_3 = ProductFactory()
        product_3.create()
        dict_3 = product_3.serialize()
        dict_3["available"] = "TRUE"
        with self.assertRaises(DataValidationError) as context:
            product_3.deserialize(dict_3)

        #
        product_4 = ProductFactory()
        product_4.create()
        dict_4 = product_4.serialize()
        dict_4["category"] = "NOT_EXISTS"
        
        with self.assertRaises(DataValidationError) as context:
            t4 = product_4.deserialize(dict_4)

        with self.assertRaises(DataValidationError) as context:
            t4 = product_4.deserialize(None)
            t4.name

 
    def test_find_product_by_price(self):

        N = 10
        for i in range(N):
            product = ProductFactory()
            product.create()
        
        products = Product.all()
        rand_product = products[random.randint(0,N-1)]
        rand_product_price = rand_product.price
        #
        arr_count = len([product for product in products if product.price == rand_product_price])
        db_found = Product.find_by_price(str(rand_product_price))
        #
        self.assertEqual(db_found.count(), arr_count)
         

        #

    
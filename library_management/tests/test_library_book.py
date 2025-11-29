from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import context

class TestLibraryBookCategory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Book = self.env['library.book']
        self.Category = self.env['library.category']
        self.category = self.Category.create({
            'name': 'Fiction'})

    def test_negative_price_constraint(self):
        with self.assertRaises(ValidationError):
            self.Book.create({
                'name': 'Bad Price Book',
                'price': -10.0
            })
        self.assertIn('The price of the book cannot be negative.', str(context.exception))

    def test_empty_category_constraint(self):
        book = self.Book.create({
            'name': 'No Category Book',
            'price': 15.0
        })
        with self.assertRaises(ValidationError):
            book.check_category_not_empty()
    
    def test_action_show_category_book_count(self):
        book1 = self.Book.create({
            'name': 'Book One',
            'price': 20.0,
            'category_id': self.category.id
        })
        book2 = self.Book.create({
            'name': 'Book Two',
            'price': 25.0,
            'category_id': self.category.id
        })
        book3 = self.Book.create({
            'name': 'Book Three',
            'price': 30.0,
            'category_id': self.category.id
        })
        (book1 + book2 + book3).action_show_category_book_count()
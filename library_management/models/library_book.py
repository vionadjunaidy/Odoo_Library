from odoo import models, fields, api
from functools import lru_cache
import requests
import logging

class LibraryBook(models.Model):
    _name = 'library.book'
    _description = 'Library Book'


    name = fields.Char(string='Title', required=True)
    author_id = fields.Many2one('library.author', string='Author')
    price = fields.Float(string='Price')
    category_id = fields.Many2one('library.category', string='Category')

    isbn = fields.Char(string='ISBN', readonly=True)
    publish_year = fields.Integer(string='Publication Year', readonly=True)

    @api.model
    @lru_cache(maxsize=128)
    def _fetch_OpenLibrary_data(self, title):
        if not title:
            return {}
        
        try:
            response = requests.get('https://openlibrary.org/search.json', params={'title': title}, timeout=5)
            response.raise_for_status()
        except requests.RequestException as e:
            _logger.error(f"Error fetching data from OpenLibrary: {e}")
            return {}
        data = response.json()
        if not data.get('docs'):
            return {}
        
        doc = data['docs'][0]

        isbn_list = doc.get('isbn')
        isbn = isbn_list[0] if isinstance(isbn_list, list) and isbn_list else False

        return {
            'isbn': isbn,
            'publish_year': doc.get('first_publish_year'),}
    
    def fetch_openlibrary_info(self):
        for book in self:
            data = self._fetch_OpenLibrary_data(book.name)
            if not data:
                book.message_post(body="No data found from OpenLibrary.")
                continue
            book.write(data)
            book.message_post(body="Fetched data from OpenLibrary.")

        return True

    @api.constrains('price')
    def _check_price(self):
        for book in self:
            if book.price < 0:
                raise models.ValidationError("The price of the book cannot be negative.")
    
    @api.constrains('category_id')
    def check_category_not_empty(self):
        for book in self:
            if not book.category_id:
                raise models.ValidationError("Each book must belong to a category.")
            
    def action_show_category_book_count(self):
        if not self:
            return True
        
        self = self.with_prefetch()

        books_with_category = self.filtered('category_id')
        if not books_with_category:
            return True
        
        category_ids = books_with_category.mapped('category_id').ids
        
        group_data = self.read_group(
            domain=[('category_id', 'in', category_ids)],
            fields=['category_id'],
            groupby=['category_id']
        )
        count_by_category = {group['category_id'][0]: group['category_id_count'] for group in group_data if group.get('category_id')}

        books_with_category.mapped('category_id')

        for book in books_with_category:
            category = book.category_id
            count = count_by_category.get(category.id, 0)
            message = f"Category '{category.name}' has {count} book(s)."
            book.message_post(body=message)

        return True
            
class LibraryCategory(models.Model):
    _name = 'library.category'
    _description = 'Library Category'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
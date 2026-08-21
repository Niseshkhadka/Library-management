from django.core.management.base import BaseCommand
from catalog.models import Author, Category, Book
from datetime import date

class Command(BaseCommand):
    help = 'Add sample books to the database for demo purposes'

    def handle(self, *args, **options):
        # Create Categories
        categories_data = [
            {'name': 'Fiction', 'description': 'Works of fiction and novels'},
            {'name': 'Classics', 'description': 'Classic literature'},
            {'name': 'Science Fiction', 'description': 'Science fiction and dystopian novels'},
            {'name': 'Fantasy', 'description': 'Fantasy and adventure'},
            {'name': 'Mystery', 'description': 'Mystery and thriller'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(name=cat_data['name'])
            if created:
                cat.description = cat_data['description']
                cat.save()
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created category: {cat_data['name']}"))
        
        # Create Authors
        authors_data = [
            'Harper Lee',
            'George Orwell',
            'Jane Austen',
            'F. Scott Fitzgerald',
            'Leo Tolstoy',
            'J.D. Salinger',
            'J.K. Rowling',
            'J.R.R. Tolkien',
            'Herman Melville',
            'Charlotte Brontë',
        ]
        
        authors = {}
        for author_name in authors_data:
            author, created = Author.objects.get_or_create(name=author_name)
            authors[author_name] = author
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created author: {author_name}"))
        
        # Create Books
        books_data = [
            {
                'title': 'To Kill a Mockingbird',
                'isbn': '9780061120084',
                'author': 'Harper Lee',
                'category': 'Classics',
                'description': 'A gripping tale of racial injustice and childhood innocence in the American South.',
                'published_date': date(1960, 7, 11),
                'total_copies': 5,
            },
            {
                'title': '1984',
                'isbn': '9780451524935',
                'author': 'George Orwell',
                'category': 'Science Fiction',
                'description': 'A dystopian masterpiece about totalitarianism and surveillance.',
                'published_date': date(1949, 6, 8),
                'total_copies': 4,
            },
            {
                'title': 'Pride and Prejudice',
                'isbn': '9780141199009',
                'author': 'Jane Austen',
                'category': 'Classics',
                'description': 'A timeless romance novel about love and social expectations.',
                'published_date': date(1813, 1, 28),
                'total_copies': 6,
            },
            {
                'title': 'The Great Gatsby',
                'isbn': '9780743273565',
                'author': 'F. Scott Fitzgerald',
                'category': 'Classics',
                'description': 'An American classic exploring wealth, love, and the American Dream.',
                'published_date': date(1925, 4, 10),
                'total_copies': 3,
            },
            {
                'title': 'War and Peace',
                'isbn': '9780199232765',
                'author': 'Leo Tolstoy',
                'category': 'Classics',
                'description': 'An epic novel set during the Napoleonic Wars with unforgettable characters.',
                'published_date': date(1869, 1, 1),
                'total_copies': 2,
            },
            {
                'title': 'The Catcher in the Rye',
                'isbn': '9780316769174',
                'author': 'J.D. Salinger',
                'category': 'Classics',
                'description': 'A controversial coming-of-age story following Holden Caulfield.',
                'published_date': date(1951, 7, 16),
                'total_copies': 4,
            },
            {
                'title': 'Harry Potter and the Philosopher\'s Stone',
                'isbn': '9780747532699',
                'author': 'J.K. Rowling',
                'category': 'Fantasy',
                'description': 'The magical beginning of a young wizard\'s journey at Hogwarts.',
                'published_date': date(1997, 6, 26),
                'total_copies': 8,
            },
            {
                'title': 'The Lord of the Rings: The Fellowship of the Ring',
                'isbn': '9780544003415',
                'author': 'J.R.R. Tolkien',
                'category': 'Fantasy',
                'description': 'An epic fantasy adventure in the magical world of Middle-earth.',
                'published_date': date(1954, 7, 29),
                'total_copies': 5,
            },
            {
                'title': 'Moby-Dick',
                'isbn': '9780142106594',
                'author': 'Herman Melville',
                'category': 'Classics',
                'description': 'A thrilling tale of obsession on the high seas with the legendary white whale.',
                'published_date': date(1851, 10, 18),
                'total_copies': 2,
            },
            {
                'title': 'Jane Eyre',
                'isbn': '9780141441146',
                'author': 'Charlotte Brontë',
                'category': 'Classics',
                'description': 'A passionate romance and tale of a strong-willed governess.',
                'published_date': date(1847, 10, 16),
                'total_copies': 3,
            },
        ]
        
        added_count = 0
        for book_data in books_data:
            author = authors[book_data['author']]
            category = categories[book_data['category']]
            
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    'title': book_data['title'],
                    'author': author,
                    'category': category,
                    'description': book_data['description'],
                    'published_date': book_data['published_date'],
                    'total_copies': book_data['total_copies'],
                    'available_copies': book_data['total_copies'],
                }
            )
            if created:
                added_count += 1
                self.stdout.write(self.style.SUCCESS(f"✓ Added book: {book_data['title']}"))
            else:
                self.stdout.write(f"⚠ Book already exists: {book_data['title']}")
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully added {added_count} books to the database!')
        )

from pathlib import Path
from django.core.files import File
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import Genre, Author, Book, BookInstance


GENRES = [
    'Художественная литература', 'Научная фантастика', 'Детектив',
    'Программирование', 'История', 'Философия', 'Психология',
    'Экономика', 'Математика', 'Физика',
]

AUTHORS = [
    ('Абай', 'Кунанбаев', 'Великий казахский поэт, мыслитель и композитор.'),
    ('Мухтар', 'Ауэзов', 'Казахский писатель, драматург, учёный.'),
    ('Фёдор', 'Достоевский', 'Русский писатель, мыслитель, один из самых значительных писателей.'),
    ('Лев', 'Толстой', 'Русский писатель, один из наиболее известных писателей мира.'),
    ('Джордж', 'Оруэлл', 'Английский писатель и публицист.'),
    ('Роберт', 'Мартин', 'Американский инженер ПО и автор книг по программированию.'),
    ('Эрих', 'Фромм', 'Немецкий социолог, философ, психоаналитик.'),
]

BOOKS = [
    {
        'title': 'Путь Абая',
        'authors': ['Ауэзов'],
        'genres': ['Художественная литература', 'История'],
        'isbn': '9785170901234',
        'summary': 'Эпический роман о жизни великого казахского поэта Абая Кунанбаева. Произведение охватывает широкую панораму жизни казахского общества XIX века.',
        'language': 'kk',
        'copies': 5,
        'cover': 'abayzholy.jpg',
    },
    {
        'title': 'Слова назидания',
        'authors': ['Кунанбаев'],
        'genres': ['Философия', 'Художественная литература'],
        'isbn': '9785170905678',
        'summary': 'Сборник философских трактатов и наставлений Абая Кунанбаева, обращённых к казахскому народу.',
        'language': 'kk',
        'copies': 3,
        'cover': 'qara_sozder.jpg',
    },
    {
        'title': 'Преступление и наказание',
        'authors': ['Достоевский'],
        'genres': ['Художественная литература', 'Детектив'],
        'isbn': '9785389012345',
        'summary': 'Роман о моральных и психологических терзаниях студента Раскольникова после совершения убийства.',
        'language': 'ru',
        'copies': 4,
        'cover': 'prestuplenie.jpg',
    },
    {
        'title': 'Война и мир',
        'authors': ['Толстой'],
        'genres': ['Художественная литература', 'История'],
        'isbn': '9785389098765',
        'summary': 'Роман-эпопея, описывающий русское общество в эпоху войн против Наполеона.',
        'language': 'ru',
        'copies': 3,
        'cover': 'voinaimir.jpg',
    },
    {
        'title': '1984',
        'authors': ['Оруэлл'],
        'genres': ['Научная фантастика', 'Художественная литература'],
        'isbn': '9780451524935',
        'summary': 'Антиутопический роман о тоталитарном обществе, где правительство контролирует каждый аспект жизни.',
        'language': 'en',
        'copies': 3,
        'cover': '1984.jpg',
    },
    {
        'title': 'Чистый код',
        'authors': ['Мартин'],
        'genres': ['Программирование'],
        'isbn': '9785446114948',
        'summary': 'Руководство по написанию качественного, читаемого и поддерживаемого кода.',
        'language': 'ru',
        'copies': 2,
        'cover': 'chistyicode.jpg',
    },
    {
        'title': 'Искусство любить',
        'authors': ['Фромм'],
        'genres': ['Психология', 'Философия'],
        'isbn': '9785170987654',
        'summary': 'Исследование природы любви как творческой силы, способной преобразить человека.',
        'language': 'ru',
        'copies': 2,
        'cover': 'isskustvo.jpg',
    },
    {
        'title': 'Братья Карамазовы',
        'authors': ['Достоевский'],
        'genres': ['Художественная литература', 'Философия'],
        'isbn': '9785389011111',
        'summary': 'Последний роман Достоевского — глубокое философское исследование веры, сомнения и свободы воли.',
        'language': 'ru',
        'copies': 2,
        'cover': 'karamazovy.jpg',
    },
]


class Command(BaseCommand):
    help = 'Заполнить базу данных тестовыми данными'

    def handle(self, *args, **options):
        static_img_dir = Path(__file__).resolve().parents[3] / 'static' / 'img'

        self.stdout.write('Создание жанров...')
        genres = {}
        for name in GENRES:
            genre, _ = Genre.objects.get_or_create(name=name)
            genres[name] = genre

        self.stdout.write('Создание авторов...')
        authors = {}
        for first, last, bio in AUTHORS:
            author, _ = Author.objects.get_or_create(
                first_name=first, last_name=last, defaults={'bio': bio}
            )
            authors[last] = author

        self.stdout.write('Создание книг и экземпляров...')
        for book_data in BOOKS:
            book, created = Book.objects.get_or_create(
                isbn=book_data['isbn'],
                defaults={
                    'title': book_data['title'],
                    'summary': book_data['summary'],
                    'language': book_data['language'],
                }
            )
            if created:
                for author_last in book_data['authors']:
                    book.authors.add(authors[author_last])
                for genre_name in book_data['genres']:
                    book.genres.add(genres[genre_name])

                for i in range(book_data['copies']):
                    BookInstance.objects.create(
                        book=book,
                        inventory_number=f'INV-{book.isbn[-4:]}-{i+1:03d}',
                    )
                self.stdout.write(f'  + {book.title} ({book_data["copies"]} экз.)')

            cover_filename = book_data.get('cover')
            if cover_filename and not book.cover:
                cover_path = static_img_dir / cover_filename
                if cover_path.exists():
                    with cover_path.open('rb') as image_file:
                        book.cover.save(cover_filename, File(image_file), save=True)
                    self.stdout.write(f'  • Обложка: {book.title} ← {cover_filename}')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'  ! Не найден файл обложки для "{book.title}": {cover_path}'
                    ))

        # Create librarian user
        if not User.objects.filter(username='librarian').exists():
            librarian = User.objects.create_user(
                username='librarian',
                password='librarian123',
                first_name='Айгуль',
                last_name='Библиотекарь',
                email='librarian@steppe.edu',
                is_staff=True,
            )
            librarian.profile.role = 'librarian'
            librarian.profile.save()
            self.stdout.write(self.style.WARNING(
                'Создан библиотекарь: librarian / librarian123'
            ))

        # Create student user
        if not User.objects.filter(username='student').exists():
            student = User.objects.create_user(
                username='student',
                password='student123',
                first_name='Алмас',
                last_name='Студентов',
                email='student@steppe.edu',
            )
            student.profile.student_id = 'STU-2024-001'
            student.profile.phone = '+7 777 123 4567'
            student.profile.save()
            self.stdout.write(self.style.WARNING(
                'Создан студент: student / student123'
            ))

        self.stdout.write(self.style.SUCCESS('Готово! База данных заполнена.'))

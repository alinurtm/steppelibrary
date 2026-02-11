import uuid
import qrcode
from io import BytesIO
from django.db import models
from django.core.files import File
from django.urls import reverse


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='Название')

    class Meta:
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'
        ordering = ['name']

    def __str__(self):
        return self.name


class Author(models.Model):
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    bio = models.TextField(blank=True, verbose_name='Биография')

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    def get_absolute_url(self):
        return reverse('catalog:author_detail', args=[self.pk])


class Book(models.Model):
    LANGUAGE_CHOICES = [
        ('kk', 'Казахский'),
        ('ru', 'Русский'),
        ('en', 'Английский'),
    ]

    title = models.CharField(max_length=300, verbose_name='Название')
    authors = models.ManyToManyField(Author, related_name='books', verbose_name='Авторы')
    genres = models.ManyToManyField(Genre, related_name='books', blank=True, verbose_name='Жанры')
    isbn = models.CharField('ISBN', max_length=13, unique=True, help_text='13-значный ISBN')
    summary = models.TextField(verbose_name='Описание', blank=True)
    cover = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name='Обложка')
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='ru', verbose_name='Язык')
    date_added = models.DateField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Книга'
        verbose_name_plural = 'Книги'
        ordering = ['-date_added', 'title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('catalog:book_detail', args=[self.pk])

    @property
    def available_copies(self):
        return self.instances.filter(status='available').count()

    @property
    def total_copies(self):
        return self.instances.count()

    def display_authors(self):
        return ', '.join(str(a) for a in self.authors.all())

    display_authors.short_description = 'Авторы'

    def display_genres(self):
        return ', '.join(str(g) for g in self.genres.all())

    display_genres.short_description = 'Жанры'


class BookInstance(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('reserved', 'Забронирован'),
        ('on_loan', 'Выдан'),
        ('lost', 'Утерян'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='instances', verbose_name='Книга')
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name='Инвентарный номер')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name='Статус')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, verbose_name='QR-код')
    condition_notes = models.TextField(blank=True, verbose_name='Примечания о состоянии')

    class Meta:
        verbose_name = 'Экземпляр книги'
        verbose_name_plural = 'Экземпляры книг'
        ordering = ['book', 'inventory_number']

    def __str__(self):
        return f'{self.book.title} [{self.inventory_number}]'

    def save(self, *args, **kwargs):
        if not self.inventory_number:
            self.inventory_number = f'INV-{str(self.id)[:8].upper()}'
        if not self.qr_code:
            self._generate_qr_code()
        super().save(*args, **kwargs)

    def _generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr_data = f'STEPPE-LIB:{self.inventory_number}'
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color='#1a365d', back_color='white')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        filename = f'qr_{self.inventory_number}.png'
        self.qr_code.save(filename, File(buffer), save=False)

    @property
    def status_badge_class(self):
        return {
            'available': 'bg-success',
            'reserved': 'bg-warning text-dark',
            'on_loan': 'bg-primary',
            'lost': 'bg-danger',
        }.get(self.status, 'bg-secondary')

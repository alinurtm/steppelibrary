from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator

from .models import Book, Author, Genre, BookInstance
from .forms import BookSearchForm


def book_list(request):
    form = BookSearchForm(request.GET)
    books = Book.objects.prefetch_related('authors', 'genres', 'instances').all()

    if form.is_valid():
        q = form.cleaned_data.get('q')
        genre = form.cleaned_data.get('genre')
        language = form.cleaned_data.get('language')
        available_only = form.cleaned_data.get('available_only')

        if q:
            books = books.filter(
                Q(title__icontains=q) |
                Q(authors__last_name__icontains=q) |
                Q(authors__first_name__icontains=q) |
                Q(isbn__icontains=q)
            ).distinct()

        if genre:
            books = books.filter(genres=genre)

        if language:
            books = books.filter(language=language)

        if available_only:
            books = books.filter(instances__status='available').distinct()

    paginator = Paginator(books, 12)
    page = request.GET.get('page')
    books_page = paginator.get_page(page)

    return render(request, 'catalog/book_list.html', {
        'books': books_page,
        'form': form,
        'genres': Genre.objects.annotate(book_count=Count('books')).filter(book_count__gt=0),
    })


def book_detail(request, pk):
    book = get_object_or_404(
        Book.objects.prefetch_related('authors', 'genres', 'instances'),
        pk=pk
    )
    instances = book.instances.all()
    available = instances.filter(status='available')

    has_reservation = False
    queue_position = None
    if request.user.is_authenticated:
        from loans.models import Reservation
        reservation = Reservation.objects.filter(
            user=request.user, book=book, is_active=True
        ).first()
        if reservation:
            has_reservation = True
            queue_position = reservation.queue_position

    return render(request, 'catalog/book_detail.html', {
        'book': book,
        'instances': instances,
        'available_count': available.count(),
        'has_reservation': has_reservation,
        'queue_position': queue_position,
    })


def author_list(request):
    authors = Author.objects.annotate(book_count=Count('books')).all()
    return render(request, 'catalog/author_list.html', {'authors': authors})


def author_detail(request, pk):
    author = get_object_or_404(Author, pk=pk)
    books = author.books.prefetch_related('instances').all()
    return render(request, 'catalog/author_detail.html', {
        'author': author,
        'books': books,
    })

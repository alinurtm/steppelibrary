from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import render
from django.db.models import Count

from catalog.models import Book, Genre


def home(request):
    books = Book.objects.prefetch_related('authors', 'instances').order_by('-date_added')[:8]
    genres = Genre.objects.annotate(book_count=Count('books')).filter(book_count__gt=0)
    total_books = Book.objects.count()
    return render(request, 'home.html', {
        'featured_books': books,
        'genres': genres,
        'total_books': total_books,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('catalog/', include('catalog.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('loans.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

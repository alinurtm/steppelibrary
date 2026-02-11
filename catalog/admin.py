from django.contrib import admin
from django.utils.html import format_html
from .models import Genre, Author, Book, BookInstance


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name']
    search_fields = ['last_name', 'first_name']


class BookInstanceInline(admin.TabularInline):
    model = BookInstance
    extra = 0
    readonly_fields = ['id', 'qr_code_preview']
    fields = ['id', 'inventory_number', 'status', 'condition_notes', 'qr_code_preview']

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="60" />', obj.qr_code.url)
        return '-'
    qr_code_preview.short_description = 'QR'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'display_authors', 'isbn', 'language', 'available_count', 'total_count']
    list_filter = ['genres', 'language', 'date_added']
    search_fields = ['title', 'isbn', 'authors__last_name']
    filter_horizontal = ['authors', 'genres']
    inlines = [BookInstanceInline]

    def available_count(self, obj):
        return obj.available_copies
    available_count.short_description = 'Доступно'

    def total_count(self, obj):
        return obj.total_copies
    total_count.short_description = 'Всего'


@admin.register(BookInstance)
class BookInstanceAdmin(admin.ModelAdmin):
    list_display = ['inventory_number', 'book', 'status', 'qr_code_preview']
    list_filter = ['status']
    search_fields = ['inventory_number', 'book__title']
    readonly_fields = ['id', 'qr_code_preview_large']

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="40" />', obj.qr_code.url)
        return '-'
    qr_code_preview.short_description = 'QR'

    def qr_code_preview_large(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" width="200" />', obj.qr_code.url)
        return '-'
    qr_code_preview_large.short_description = 'QR-код'

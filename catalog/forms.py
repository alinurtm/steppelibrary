from django import forms
from .models import Book, BookInstance, Author, Genre


class BookSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='',
        widget=forms.TextInput(attrs={
            'placeholder': 'Поиск по названию, автору, ISBN...',
            'class': 'form-control',
        })
    )
    genre = forms.ModelChoiceField(
        queryset=Genre.objects.all(),
        required=False,
        label='Жанр',
        empty_label='Все жанры'
    )
    language = forms.ChoiceField(
        choices=[('', 'Все языки')] + Book.LANGUAGE_CHOICES,
        required=False,
        label='Язык',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    available_only = forms.BooleanField(
        required=False,
        label='Только в наличии'
    )


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'authors', 'genres', 'isbn', 'summary', 'cover', 'language']
        widgets = {
            'authors': forms.CheckboxSelectMultiple,
            'genres': forms.CheckboxSelectMultiple,
            'summary': forms.Textarea(attrs={'rows': 4}),
        }


class BookInstanceForm(forms.ModelForm):
    class Meta:
        model = BookInstance
        fields = ['inventory_number', 'status', 'condition_notes']
        widgets = {
            'condition_notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['inventory_number'].required = False
        self.fields['inventory_number'].help_text = 'Оставьте пустым для автогенерации'


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name', 'bio']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }

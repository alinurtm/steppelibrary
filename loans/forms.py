from django import forms
from django.contrib.auth.models import User
from catalog.models import BookInstance


class IssueLoanForm(forms.Form):
    inventory_number = forms.CharField(
        max_length=50,
        label='Инвентарный номер / QR-код',
        widget=forms.TextInput(attrs={
            'placeholder': 'Отсканируйте QR или введите номер...',
            'class': 'form-control',
            'autofocus': True,
        })
    )
    borrower_username = forms.CharField(
        max_length=150,
        label='Логин читателя',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите логин студента...',
            'class': 'form-control',
        })
    )

    def clean_inventory_number(self):
        inv = self.cleaned_data['inventory_number']
        if inv.startswith('STEPPE-LIB:'):
            inv = inv.replace('STEPPE-LIB:', '')
        try:
            instance = BookInstance.objects.get(inventory_number=inv)
        except BookInstance.DoesNotExist:
            raise forms.ValidationError('Экземпляр с таким номером не найден.')
        if instance.status != 'available':
            raise forms.ValidationError(f'Экземпляр недоступен (статус: {instance.get_status_display()}).')
        return inv

    def clean_borrower_username(self):
        username = self.cleaned_data['borrower_username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise forms.ValidationError('Пользователь не найден.')
        if hasattr(user, 'profile') and user.profile.has_unpaid_fines:
            raise forms.ValidationError('У читателя есть неоплаченные штрафы. Выдача заблокирована.')
        return username


class ReturnLoanForm(forms.Form):
    inventory_number = forms.CharField(
        max_length=50,
        label='Инвентарный номер / QR-код',
        widget=forms.TextInput(attrs={
            'placeholder': 'Отсканируйте QR или введите номер...',
            'class': 'form-control form-control-lg',
            'autofocus': True,
        })
    )

    def clean_inventory_number(self):
        inv = self.cleaned_data['inventory_number']
        if inv.startswith('STEPPE-LIB:'):
            inv = inv.replace('STEPPE-LIB:', '')
        try:
            BookInstance.objects.get(inventory_number=inv)
        except BookInstance.DoesNotExist:
            raise forms.ValidationError('Экземпляр с таким номером не найден.')
        from .models import Loan
        active_loan = Loan.objects.filter(
            book_instance__inventory_number=inv,
            is_returned=False
        ).first()
        if not active_loan:
            raise forms.ValidationError('Нет активной выдачи для этого экземпляра.')
        return inv

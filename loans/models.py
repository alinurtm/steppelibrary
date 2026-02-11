from datetime import timedelta

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

from catalog.models import Book, BookInstance


class Loan(models.Model):
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans', verbose_name='Читатель')
    book_instance = models.ForeignKey(BookInstance, on_delete=models.CASCADE, related_name='loans', verbose_name='Экземпляр')
    issue_date = models.DateTimeField(default=timezone.now, verbose_name='Дата выдачи')
    due_date = models.DateTimeField(verbose_name='Срок возврата', blank=True)
    return_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата возврата')
    is_returned = models.BooleanField(default=False, verbose_name='Возвращена')

    class Meta:
        verbose_name = 'Выдача'
        verbose_name_plural = 'Выдачи'
        ordering = ['-issue_date']

    def __str__(self):
        return f'{self.borrower.get_full_name()} — {self.book_instance}'

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + timedelta(days=settings.LOAN_PERIOD_DAYS)
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.is_returned:
            return False
        return timezone.now() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        delta = timezone.now() - self.due_date
        return delta.days

    @property
    def days_remaining(self):
        if self.is_returned:
            return 0
        delta = self.due_date - timezone.now()
        return max(0, delta.days)


class Fine(models.Model):
    loan = models.OneToOneField(Loan, on_delete=models.CASCADE, related_name='fine', verbose_name='Выдача')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма (KZT)')
    is_paid = models.BooleanField(default=False, verbose_name='Оплачен')
    paid_date = models.DateTimeField(null=True, blank=True, verbose_name='Дата оплаты')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата начисления')

    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'
        ordering = ['-created_at']

    def __str__(self):
        status = 'оплачен' if self.is_paid else 'не оплачен'
        return f'Штраф {self.amount} KZT — {status}'


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservations', verbose_name='Читатель')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations', verbose_name='Книга')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата бронирования')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    notified = models.BooleanField(default=False, verbose_name='Уведомлён')
    notified_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата уведомления')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'book'],
                condition=models.Q(is_active=True),
                name='unique_active_reservation'
            )
        ]

    def __str__(self):
        return f'{self.user.get_full_name()} — {self.book.title}'

    @property
    def queue_position(self):
        return Reservation.objects.filter(
            book=self.book,
            is_active=True,
            created_at__lt=self.created_at
        ).count() + 1

    @property
    def is_expired(self):
        if not self.notified or not self.notified_at:
            return False
        expiry = self.notified_at + timedelta(hours=settings.RESERVATION_EXPIRY_HOURS)
        return timezone.now() > expiry

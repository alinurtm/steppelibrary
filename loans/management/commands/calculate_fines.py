from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from loans.models import Loan, Fine


class Command(BaseCommand):
    help = 'Рассчитать и начислить штрафы за просроченные книги'

    def handle(self, *args, **options):
        overdue_loans = Loan.objects.filter(
            is_returned=False,
            due_date__lt=timezone.now()
        ).exclude(fine__isnull=False)

        created_count = 0
        for loan in overdue_loans:
            days = (timezone.now() - loan.due_date).days
            if days > 0:
                amount = days * settings.FINE_PER_DAY_KZT
                Fine.objects.create(loan=loan, amount=amount)
                created_count += 1
                self.stdout.write(
                    f'  Штраф {amount} KZT для {loan.borrower.username} '
                    f'({loan.book_instance.book.title}, {days} дн.)'
                )

        # Update existing fines
        existing_fines = Fine.objects.filter(is_paid=False, loan__is_returned=False)
        updated_count = 0
        for fine in existing_fines:
            loan = fine.loan
            if loan.due_date < timezone.now():
                days = (timezone.now() - loan.due_date).days
                new_amount = days * settings.FINE_PER_DAY_KZT
                if new_amount != fine.amount:
                    fine.amount = new_amount
                    fine.save()
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово. Создано: {created_count}, обновлено: {updated_count}'
        ))

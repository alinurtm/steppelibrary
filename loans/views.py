from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.conf import settings

from catalog.models import Book, BookInstance
from .models import Loan, Fine, Reservation
from .forms import IssueLoanForm, ReturnLoanForm


def librarian_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'profile') or not request.user.profile.is_librarian:
            messages.error(request, 'Доступ только для библиотекарей.')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


@login_required
def dashboard(request):
    active_loans = Loan.objects.filter(
        borrower=request.user, is_returned=False
    ).select_related('book_instance__book')

    returned_loans = Loan.objects.filter(
        borrower=request.user, is_returned=True
    ).select_related('book_instance__book').order_by('-return_date')[:10]

    unpaid_fines = Fine.objects.filter(
        loan__borrower=request.user, is_paid=False
    ).select_related('loan__book_instance__book')

    active_reservations = Reservation.objects.filter(
        user=request.user, is_active=True
    ).select_related('book')

    total_fines = sum(f.amount for f in unpaid_fines)

    return render(request, 'loans/dashboard.html', {
        'active_loans': active_loans,
        'returned_loans': returned_loans,
        'unpaid_fines': unpaid_fines,
        'active_reservations': active_reservations,
        'total_fines': total_fines,
    })


@login_required
def reserve_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)

    if hasattr(request.user, 'profile') and request.user.profile.has_unpaid_fines:
        messages.error(request, 'У вас есть неоплаченные штрафы. Бронирование заблокировано.')
        return redirect('catalog:book_detail', pk=book_id)

    existing = Reservation.objects.filter(user=request.user, book=book, is_active=True).exists()
    if existing:
        messages.warning(request, 'Вы уже забронировали эту книгу.')
        return redirect('catalog:book_detail', pk=book_id)

    if book.available_copies > 0:
        messages.info(request, 'Книга есть в наличии, бронирование не требуется.')
        return redirect('catalog:book_detail', pk=book_id)

    reservation = Reservation.objects.create(user=request.user, book=book)
    messages.success(request, f'Вы встали в очередь. Ваша позиция: {reservation.queue_position}')
    return redirect('catalog:book_detail', pk=book_id)


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user, is_active=True)
    reservation.is_active = False
    reservation.save()
    messages.success(request, 'Бронирование отменено.')
    return redirect('loans:dashboard')


# ===== Staff views =====

@librarian_required
def staff_panel(request):
    recent_loans = Loan.objects.select_related(
        'borrower', 'book_instance__book'
    ).order_by('-issue_date')[:20]

    overdue_loans = Loan.objects.filter(
        is_returned=False, due_date__lt=timezone.now()
    ).select_related('borrower', 'book_instance__book')

    unpaid_fines = Fine.objects.filter(is_paid=False).select_related(
        'loan__borrower', 'loan__book_instance__book'
    )

    total_books = Book.objects.count()
    total_instances = BookInstance.objects.count()
    on_loan = BookInstance.objects.filter(status='on_loan').count()

    return render(request, 'loans/staff_panel.html', {
        'recent_loans': recent_loans,
        'overdue_loans': overdue_loans,
        'unpaid_fines': unpaid_fines,
        'total_books': total_books,
        'total_instances': total_instances,
        'on_loan': on_loan,
    })


@librarian_required
def issue_book(request):
    if request.method == 'POST':
        form = IssueLoanForm(request.POST)
        if form.is_valid():
            inv = form.cleaned_data['inventory_number']
            username = form.cleaned_data['borrower_username']
            instance = BookInstance.objects.get(inventory_number=inv)
            borrower = User.objects.get(username=username)

            loan = Loan.objects.create(
                borrower=borrower,
                book_instance=instance,
            )
            instance.status = 'on_loan'
            instance.save()

            # Cancel reservation if exists
            Reservation.objects.filter(
                user=borrower, book=instance.book, is_active=True
            ).update(is_active=False)

            messages.success(
                request,
                f'Книга "{instance.book.title}" выдана пользователю {borrower.get_full_name()}. '
                f'Срок возврата: {loan.due_date.strftime("%d.%m.%Y")}'
            )
            return redirect('loans:staff_panel')
    else:
        form = IssueLoanForm()
    return render(request, 'loans/issue_book.html', {'form': form})


@librarian_required
def return_book(request):
    if request.method == 'POST':
        form = ReturnLoanForm(request.POST)
        if form.is_valid():
            inv = form.cleaned_data['inventory_number']
            instance = BookInstance.objects.get(inventory_number=inv)
            loan = Loan.objects.filter(
                book_instance=instance, is_returned=False
            ).first()

            loan.is_returned = True
            loan.return_date = timezone.now()
            loan.save()

            # Check overdue and create fine
            if loan.due_date < timezone.now():
                days = (timezone.now() - loan.due_date).days
                amount = days * settings.FINE_PER_DAY_KZT
                Fine.objects.get_or_create(
                    loan=loan,
                    defaults={'amount': amount}
                )
                messages.warning(
                    request,
                    f'Книга возвращена с опозданием на {days} дней. '
                    f'Штраф: {amount} KZT.'
                )
            else:
                messages.success(request, f'Книга "{instance.book.title}" успешно возвращена.')

            # Check reservation queue
            next_reservation = Reservation.objects.filter(
                book=instance.book, is_active=True, notified=False
            ).order_by('created_at').first()

            if next_reservation:
                next_reservation.notified = True
                next_reservation.notified_at = timezone.now()
                next_reservation.save()
                instance.status = 'reserved'
                messages.info(
                    request,
                    f'Следующий в очереди: {next_reservation.user.get_full_name()}'
                )
            else:
                instance.status = 'available'

            instance.save()
            return redirect('loans:staff_panel')
    else:
        form = ReturnLoanForm()
    return render(request, 'loans/return_book.html', {'form': form})


@librarian_required
def manage_fines(request):
    if request.method == 'POST':
        fine_id = request.POST.get('fine_id')
        fine = get_object_or_404(Fine, pk=fine_id)
        fine.is_paid = True
        fine.paid_date = timezone.now()
        fine.save()
        messages.success(request, f'Штраф {fine.amount} KZT списан.')
        return redirect('loans:manage_fines')

    fines = Fine.objects.filter(is_paid=False).select_related(
        'loan__borrower', 'loan__book_instance__book'
    )
    return render(request, 'loans/manage_fines.html', {'fines': fines})


@librarian_required
def add_book(request):
    from catalog.forms import BookForm
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save()
            messages.success(request, f'Книга "{book.title}" добавлена.')
            return redirect('catalog:book_detail', pk=book.pk)
    else:
        form = BookForm()
    return render(request, 'loans/add_book.html', {
        'form': form,
        'title': 'Добавить книгу',
    })


@librarian_required
def add_instance(request, book_id):
    from catalog.forms import BookInstanceForm
    book = get_object_or_404(Book, pk=book_id)
    if request.method == 'POST':
        form = BookInstanceForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.book = book
            instance.save()
            messages.success(request, f'Экземпляр {instance.inventory_number} добавлен.')
            return redirect('catalog:book_detail', pk=book.pk)
    else:
        form = BookInstanceForm()
    return render(request, 'loans/add_instance.html', {
        'form': form,
        'book': book,
    })


@librarian_required
def view_qr(request, instance_id):
    instance = get_object_or_404(BookInstance, pk=instance_id)
    return render(request, 'loans/view_qr.html', {'instance': instance})


@librarian_required
def add_author(request):
    from catalog.forms import AuthorForm
    if request.method == 'POST':
        form = AuthorForm(request.POST)
        if form.is_valid():
            author = form.save()
            messages.success(request, f'Автор "{author}" добавлен.')
            return redirect('loans:staff_panel')
    else:
        form = AuthorForm()
    return render(request, 'loans/add_book.html', {
        'form': form,
        'title': 'Добавить автора',
    })

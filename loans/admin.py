from django.contrib import admin
from .models import Loan, Fine, Reservation


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ['borrower', 'book_instance', 'issue_date', 'due_date', 'is_returned', 'is_overdue']
    list_filter = ['is_returned', 'issue_date', 'due_date']
    search_fields = ['borrower__username', 'borrower__last_name', 'book_instance__inventory_number']
    readonly_fields = ['issue_date']


@admin.register(Fine)
class FineAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'is_paid', 'created_at']
    list_filter = ['is_paid', 'created_at']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['user', 'book', 'created_at', 'is_active', 'notified']
    list_filter = ['is_active', 'notified']

from django.urls import path
from . import views

app_name = 'loans'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reserve/<int:book_id>/', views.reserve_book, name='reserve_book'),
    path('cancel-reservation/<int:reservation_id>/', views.cancel_reservation, name='cancel_reservation'),

    # Staff
    path('staff/', views.staff_panel, name='staff_panel'),
    path('staff/issue/', views.issue_book, name='issue_book'),
    path('staff/return/', views.return_book, name='return_book'),
    path('staff/fines/', views.manage_fines, name='manage_fines'),
    path('staff/add-book/', views.add_book, name='add_book'),
    path('staff/add-author/', views.add_author, name='add_author'),
    path('staff/add-instance/<int:book_id>/', views.add_instance, name='add_instance'),
    path('staff/qr/<uuid:instance_id>/', views.view_qr, name='view_qr'),
]

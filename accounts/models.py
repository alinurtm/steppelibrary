from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('student', 'Студент'),
        ('librarian', 'Библиотекарь'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name='Роль')
    student_id = models.CharField(max_length=20, blank=True, verbose_name='Студенческий ID')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.get_role_display()})'

    @property
    def is_librarian(self):
        return self.role == 'librarian'

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def has_unpaid_fines(self):
        from loans.models import Fine
        return Fine.objects.filter(
            loan__borrower=self.user,
            is_paid=False
        ).exists()

    @property
    def total_unpaid_fines(self):
        from loans.models import Fine
        result = Fine.objects.filter(
            loan__borrower=self.user,
            is_paid=False
        ).aggregate(total=models.Sum('amount'))
        return result['total'] or 0


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

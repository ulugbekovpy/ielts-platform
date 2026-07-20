from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
from django.conf import settings

class IeltsUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email manzili kiritilishi shart")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class IeltsUser(AbstractBaseUser, PermissionsMixin):
    # Данные для аутентификации
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=255)
    password = models.CharField(max_length=500)
    
    # OTP-верификация
    is_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=4, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    # Платные функции
    is_premium = models.BooleanField(default=False)
    
    # Системные поля админки Django
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # --- ДАННЫЕ ОНБОРДИНГА (ПЛАНЫ ОБУЧЕНИЯ) ---
    
    # Экран 2: Опыт сдачи IELTS
    BACKGROUND_CHOICES = [
        ('passed', "Ha, topshirganman (Sertifikatga egaman)"),
        ('never', "Yo'q, topshirmaganman (Bu birinchisi bo'ladi)"),
        ('mock', "Faqat 'Mock Exam' (Pre-IELTS) topshirganman"),
    ]
    ielts_background = models.CharField(max_length=20, choices=BACKGROUND_CHOICES, blank=True, null=True)

    # Экран 3: Желаемый балл (Target Band Slider)[cite: 5]
    want_result = models.FloatField(default=7.5) # Изменили CharField на FloatField для удобства работы со слайдером

    # Экран 4: Проблемные секции (Challenges) — храним списком через запятую или JSON[cite: 5]
    # (Listening, Reading, Writing, Speaking, Timing, Vocabulary)[cite: 5]
    challenges = models.TextField(blank=True, null=True)

    # Экран 5: Сроки сдачи экзамена[cite: 5]
    EXAM_DATE_CHOICES = [
        ('under_month', 'Less than a month'),
        ('1_3_months', '1–3 months'),
        ('3_6_months', '3–6 months'),
        ('no_date', 'No date yet'),
    ]
    exam_timeline = models.CharField(max_length=20, choices=EXAM_DATE_CHOICES, blank=True, null=True)

    # Экран 6: Время на учебу в день[cite: 5]
    STUDY_TIME_CHOICES = [
        ('15m', '15 mins'),
        ('30m', '30 mins'),
        ('1h', '1 hour'),
        ('2h_plus', '2+ hours'),
    ]
    daily_study_time = models.CharField(max_length=15, choices=STUDY_TIME_CHOICES, blank=True, null=True)

    objects = IeltsUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def generate_otp(self):
        self.otp_code = str(random.randint(1000, 9999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp_code
    
    def __str__(self):
        return self.email


class UserStreak(models.Model):
    """
    Отдельная модель для трекинга ежедневной активности пользователя.
    Интегрируется с блоком: '🔥 1 kunlik uzluksiz' и 'Daily Streak Rewards'.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="streak"
    )
    current_streak = models.PositiveIntegerField(default=1, verbose_name="Current Daily Streak")
    longest_streak = models.PositiveIntegerField(default=1, verbose_name="Longest Daily Streak")
    last_activity_date = models.DateField(auto_now=True, verbose_name="Last Active Date")

    class Meta:
        verbose_name = "User Streak"
        verbose_name_plural = "User Streaks"

    def __str__(self):
        return f"{self.user.email} - {self.current_streak} days"


class DailyTask(models.Model):
    """
    Задачи и чек-листы на сегодня.
    Наполняет блок: '🎯 Bugungi Reja & Topshiriqlar'.
    """
    TASK_TYPES = [
        ('reading', 'Reading'),
        ('listening', 'Listening'),
        ('writing', 'Writing'),
        ('speaking', 'Speaking'),
        ('vocabulary', 'Vocabulary'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="daily_tasks"
    )
    title = models.CharField(max_length=255, verbose_name="Task Title")
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='reading')
    is_completed = models.BooleanField(default=False, verbose_name="Is Completed")
    date = models.DateField(auto_now_add=True, verbose_name="Task Date")

    class Meta:
        ordering = ['is_completed', '-id']
        verbose_name = "Daily Task"
        verbose_name_plural = "Daily Tasks"

    def __str__(self):
        return f"{self.user.email} - {self.title} ({'Done' if self.is_completed else 'Pending'})"


class MockResult(models.Model):
    """
    Результаты тестов.
    Наполняет блок 'Band History' (высчитывает Latest, Best и разницу до Target).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="mock_results"
    )
    listening_score = models.FloatField(default=0.0)
    reading_score = models.FloatField(default=0.0)
    writing_score = models.FloatField(default=0.0)
    speaking_score = models.FloatField(default=0.0)
    overall_band = models.FloatField(default=0.0, verbose_name="Overall Band")
    exam_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-exam_date']
        verbose_name = "Mock Result"
        verbose_name_plural = "Mock Results"

    def __str__(self):
        return f"{self.user.email} - Band {self.overall_band} ({self.exam_date.date()})"
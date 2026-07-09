from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from apps.core.models import BaseModel
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.apps import apps


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Role(models.TextChoices):
        DIRECTOR  = 'Director',  'Director'
        EXAMCELL  = 'Examcell',  'Exam Cell'
        HOD       = 'HOD',       'HOD'
        MENTOR    = 'Mentor',    'Mentor'
        FACULTY   = 'Faculty',   'Faculty'
        STUDENT   = 'Student',   'Student'
        PARENT    = 'Parent',    'Parent'

    full_name     = models.CharField(max_length=255, blank=True, default='')
    email         = models.EmailField(unique=True)
    phone         = models.CharField(max_length=15, blank=True, default='')
    role          = models.CharField(max_length=20, choices=Role.choices)
    departments   = models.ManyToManyField('academics.Department', blank=True, related_name='staff')
    is_active     = models.BooleanField(default=True)
    is_staff      = models.BooleanField(default=False)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['role']

    class Meta:
        verbose_name = 'User'
        ordering     = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.role})"

    def save(self, *args, **kwargs):
        # Enforce Director as full admin
        if self.role == self.Role.DIRECTOR:
            self.is_staff = True
            self.is_superuser = True
        super().save(*args, **kwargs)

    @property
    def is_mentor(self):
        from apps.faculty.models import StudentMentorAssignment
        from django.utils.timezone import now
        current_year = f"{now().year}-{now().year + 1}"
        return self.role == self.Role.MENTOR or StudentMentorAssignment.objects.filter(mentor=self, academic_year=current_year).exists()


class OTPRecord(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_records')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=50)  # e.g., 'login', 'reset_password'
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'OTP Record'
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {self.purpose}"


@receiver(m2m_changed, sender=User.departments.through)
def ensure_ai_aiml_for_common_faculty(sender, instance, action, **kwargs):
    if action not in ['post_add', 'post_set']:
        return
    Department = apps.get_model('academics', 'Department')
    if instance.role in [User.Role.FACULTY, User.Role.MENTOR]:
        ai = Department.objects.filter(code__iexact='AI').first() or Department.objects.filter(name__iexact='AI').first()
        aiml = Department.objects.filter(code__iexact='AIML').first() or Department.objects.filter(name__iexact='AIML').first()
        if not ai and not aiml:
            return
        current_ids = set(instance.departments.values_list('id', flat=True))
        if (ai and ai.id in current_ids) or (aiml and aiml.id in current_ids):
            to_add = []
            if ai and ai.id not in current_ids:
                to_add.append(ai)
            if aiml and aiml.id not in current_ids:
                to_add.append(aiml)
            if to_add:
                instance.departments.add(*to_add)
        return
    if instance.role == User.Role.HOD:
        dept_ids = list(instance.departments.values_list('id', flat=True))
        if len(dept_ids) > 1:
            instance.departments.set([dept_ids[0]])
        return

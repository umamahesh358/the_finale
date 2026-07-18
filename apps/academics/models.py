from apps.core.models import BaseModel
from django.db import models


class Department(BaseModel):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    hod = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    # college = models.ForeignKey('core.College', on_delete=models.CASCADE) # For Phase 1

    def __str__(self):
        return f"{self.code} — {self.name}"


class Section(BaseModel):
    name = models.CharField(max_length=10)  # A, B, C
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='sections')

    class Meta:
        unique_together = ('department', 'name')
        ordering = ['department__code', 'name']

    def __str__(self):
        return f"{self.department.code} - {self.name}"


class Subject(BaseModel):
    class SubjectType(models.TextChoices):
        THEORY = 'Theory', 'Theory'
        PRACTICAL = 'Practical', 'Practical'
        ELECTIVE = 'Elective', 'Elective'

    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    faculty = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='subjects_taught')
    semester = models.IntegerField()
    credits = models.IntegerField(default=3)
    type = models.CharField(max_length=20, choices=SubjectType.choices, default=SubjectType.THEORY)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Marks(BaseModel):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='marks')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    internal = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    external = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    grade = models.CharField(max_length=2, blank=True, default='')

    class Meta:
        verbose_name_plural = "Marks"
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject.code}: {self.total}"


class Attendance(BaseModel):
    student = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='attendance_records')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField(default=True)
    recorded_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)

    class Meta:
        verbose_name_plural = "Attendance"

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject.code} - {self.date}"


class AttendanceSummary(BaseModel):
    """Mentor-entered direct attendance percentage per student per subject."""
    student = models.ForeignKey(
        'students.StudentProfile', on_delete=models.CASCADE,
        related_name='attendance_summaries'
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)   # 0.00 – 100.00
    academic_year = models.CharField(max_length=15)
    recorded_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        verbose_name_plural = "Attendance Summaries"
        unique_together = ('student', 'subject', 'academic_year')

    def __str__(self):
        return f"{self.student.roll_no} - {self.subject.code}: {self.percentage}%"

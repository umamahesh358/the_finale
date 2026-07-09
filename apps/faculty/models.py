from apps.core.models import BaseModel
from django.db import models


class LessonPlan(BaseModel):
    subject      = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='lesson_plans')
    department   = models.ForeignKey('academics.Department', on_delete=models.CASCADE)
    uploaded_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    file         = models.FileField(upload_to='lesson_plans/')
    academic_year = models.CharField(max_length=15)
    target_year  = models.IntegerField(choices=[(1, 'I Year'), (2, 'II Year'), (3, 'III Year'), (4, 'IV Year')], null=True, blank=True)
    target_section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, null=True, blank=True)
    status       = models.CharField(max_length=20, default='Draft',
                    choices=[('Draft','Draft'),('Published','Published'),('Archived','Archived')])
    notes        = models.TextField(blank=True, default='')
    resource_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.subject.name} - {self.academic_year}"


class Timetable(BaseModel):
    department   = models.ForeignKey('academics.Department', on_delete=models.CASCADE)
    uploaded_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    semester     = models.IntegerField(null=True, blank=True)
    target_year  = models.IntegerField(choices=[(1, 'I Year'), (2, 'II Year'), (3, 'III Year'), (4, 'IV Year')], null=True, blank=True)
    target_section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, null=True, blank=True)
    file         = models.FileField(upload_to='timetables/')
    valid_from   = models.DateField()
    valid_to     = models.DateField(null=True, blank=True)
    academic_year = models.CharField(max_length=15, blank=True, default='')
    resource_link = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.department.name} - Sem {self.semester}"


class AcademicCalendar(BaseModel):
    """Semester-level academic calendar uploaded by HOD."""
    department   = models.ForeignKey('academics.Department', on_delete=models.CASCADE, related_name='calendars')
    uploaded_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    title        = models.CharField(max_length=200)
    academic_year = models.CharField(max_length=15)
    semester     = models.IntegerField(null=True, blank=True)
    target_year  = models.IntegerField(choices=[(1, 'I Year'), (2, 'II Year'), (3, 'III Year'), (4, 'IV Year')], null=True, blank=True)
    target_section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, null=True, blank=True)
    file         = models.FileField(upload_to='academic_calendars/')
    resource_link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.department.code} - {self.title}"


class TrainingProgram(BaseModel):
    """Department-level training programs managed by HOD."""
    department   = models.ForeignKey('academics.Department', on_delete=models.CASCADE, related_name='training_programs')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True, default='')
    start_date   = models.DateField()
    end_date     = models.DateField(null=True, blank=True)
    venue        = models.CharField(max_length=200, blank=True, default='')
    created_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    is_active    = models.BooleanField(default=True)
    registration_link = models.URLField(blank=True, null=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.title} ({self.department.code})"


class MentorAssignment(BaseModel):
    mentor        = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                        related_name='mentored_students', limit_choices_to=models.Q(role__in=['Faculty', 'Mentor']))
    student       = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE,
                        related_name='mentor_assignments')
    academic_year = models.CharField(max_length=15)
    assigned_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                        related_name='mentor_assignments_made')

    class Meta:
        unique_together = ('mentor', 'student', 'academic_year')

    def __str__(self):
        return f"Mentor: {self.mentor.email} -> Student: {self.student.roll_no}"


class StudentMentorAssignment(BaseModel):
    mentor        = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                        related_name='student_mentor_assignments', limit_choices_to=models.Q(role__in=['Faculty', 'Mentor']))
    students      = models.ManyToManyField('students.StudentProfile', related_name='direct_mentor_assignments', blank=True)
    academic_year = models.CharField(max_length=20)
    assigned_by   = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True,
                        related_name='student_mentor_assignments_made')

    def __str__(self):
        return f"Mentor: {self.mentor.email} ({self.academic_year})"


# ── SYLLABUS TRACKING ──────────────────────────────────────────────────────────
class SyllabusCoverage(BaseModel):
    """Tracks unit-wise syllabus completion per subject per faculty."""
    subject      = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='syllabus_coverage')
    faculty      = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='syllabus_entries')
    unit_number  = models.PositiveIntegerField()
    unit_title   = models.CharField(max_length=300)
    total_topics = models.PositiveIntegerField(default=1)
    covered_topics = models.PositiveIntegerField(default=0)
    document     = models.FileField(upload_to='syllabus_docs/', blank=True, null=True,
                    help_text='Upload unit-wise reference/notes')
    remarks      = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('subject', 'faculty', 'unit_number')
        ordering = ['unit_number']

    @property
    def completion_percent(self):
        if self.total_topics == 0:
            return 0
        return round((self.covered_topics / self.total_topics) * 100)

    def __str__(self):
        return f"{self.subject.code} Unit {self.unit_number} - {self.completion_percent}%"


# ── COHORT SYSTEM ──────────────────────────────────────────────────────────────
class Cohort(BaseModel):
    """Faculty-created group of students for internal courses."""
    class CohortType(models.TextChoices):
        ACADEMIC = 'academic', 'Academic / Subject'
        TRAINING = 'training', 'Training / Skill'

    name         = models.CharField(max_length=200)
    created_by   = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='cohorts')
    department   = models.ForeignKey('academics.Department', on_delete=models.SET_NULL,
                        null=True, blank=True, related_name='cohorts')
    cohort_type  = models.CharField(max_length=10, choices=CohortType.choices, default=CohortType.TRAINING)
    students     = models.ManyToManyField('students.StudentProfile', related_name='cohorts', blank=True)
    batch        = models.CharField(max_length=10, blank=True, default='')
    description  = models.TextField(blank=True, default='')
    is_active    = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.created_by.email})"


# ── INSTITUTION-LEVEL COURSES (Faculty-created) ────────────────────────────────
class InstitutionCourse(BaseModel):
    """Internal courses created by faculty — aptitude, verbal, coding, etc."""
    class CourseCategory(models.TextChoices):
        APTITUDE    = 'aptitude',    'Aptitude (All Students)'
        VERBAL      = 'verbal',      'Verbal'
        SOFT_SKILLS = 'soft_skills', 'Soft Skills'
        PROGRAMMING = 'programming', 'Programming'
        JAVA        = 'java',        'Java'
        DOTNET      = 'dotnet',      '.NET'
        PYTHON      = 'python',      'Python'
        ABAP        = 'abap',        'ABAP'
        OTHER       = 'other',       'Other'

    name         = models.CharField(max_length=300)
    category     = models.CharField(max_length=20, choices=CourseCategory.choices)
    created_by   = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='institution_courses')
    department   = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, related_name='institution_courses', null=True, blank=True)
    cohorts      = models.ManyToManyField(Cohort, related_name='institution_courses', blank=True)
    enrolled_students = models.ManyToManyField('students.StudentProfile', related_name='enrolled_institution_courses', blank=True)
    description  = models.TextField(blank=True, default='')
    is_published_to_profile = models.BooleanField(default=False,
        help_text='If True, students see this in their profile; else mentor-only')
    # Score template download
    score_template = models.FileField(upload_to='score_templates/', blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} [{self.get_category_display()}]"


class CourseMaterial(BaseModel):
    """Files/materials uploaded for an InstitutionCourse."""
    course   = models.ForeignKey(InstitutionCourse, on_delete=models.CASCADE, related_name='materials')
    title    = models.CharField(max_length=300)
    file     = models.FileField(upload_to='course_materials/')
    order    = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.name} - {self.title}"


class CourseLink(BaseModel):
    """Reference links uploaded for an InstitutionCourse."""
    course = models.ForeignKey(InstitutionCourse, on_delete=models.CASCADE, related_name='links')
    title  = models.CharField(max_length=300)
    url    = models.URLField()

    class Meta:
        ordering = ['title']

    def __str__(self):
        return f"{self.course.name} - {self.title}"


class CourseAssessment(BaseModel):
    """Assessments within an InstitutionCourse."""
    course   = models.ForeignKey(InstitutionCourse, on_delete=models.CASCADE, related_name='assessments')
    name     = models.CharField(max_length=300)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    is_published = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.course.name} - {self.name}"


class StudentCourseScore(BaseModel):
    """Individual student score in a CourseAssessment."""
    assessment = models.ForeignKey(CourseAssessment, on_delete=models.CASCADE, related_name='scores')
    student    = models.ForeignKey('students.StudentProfile', on_delete=models.CASCADE, related_name='course_scores')
    score      = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    remarks    = models.TextField(blank=True, default='')

    class Meta:
        unique_together = ('assessment', 'student')

    def save(self, *args, **kwargs):
        if self.assessment.max_score > 0:
            self.percentage = round((self.score / self.assessment.max_score) * 100, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.roll_no} - {self.assessment.name}: {self.percentage}%"

from apps.core.models import BaseModel
from django.db import models
from django.utils.text import slugify
import uuid


class StudentProfile(BaseModel):
    user       = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='student_profile')
    roll_no    = models.CharField(max_length=20, unique=True, db_index=True)
    batch      = models.CharField(max_length=10)           # e.g., "2022-2026"
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='students')
    section    = models.ForeignKey('academics.Section', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    cgpa       = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    resume     = models.FileField(upload_to='resumes/', blank=True)
    photo      = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    is_public  = models.BooleanField(default=False)
    slug       = models.SlugField(unique=True, blank=True)

    # Extended personal contact
    personal_email = models.EmailField(blank=True, default='')
    personal_phone = models.CharField(max_length=15, blank=True, default='')
    personal_email_verified = models.BooleanField(default=False)
    personal_phone_verified = models.BooleanField(default=False)

    # Social / Professional links (only shown if filled)
    linkedin_url   = models.URLField(blank=True, default='')
    github_url     = models.URLField(blank=True, default='')
    leetcode_url   = models.URLField(blank=True, default='')
    hackerrank_url = models.URLField(blank=True, default='')
    codechef_url   = models.URLField(blank=True, default='')
    codeforces_url = models.URLField(blank=True, default='')

    # Per-link visibility controls for public portfolio
    show_email_on_profile = models.BooleanField(default=True)
    show_resume_on_profile = models.BooleanField(default=True)
    show_linkedin_on_profile = models.BooleanField(default=True)
    show_github_on_profile = models.BooleanField(default=True)
    show_leetcode_on_profile = models.BooleanField(default=True)
    show_hackerrank_on_profile = models.BooleanField(default=True)
    show_codechef_on_profile = models.BooleanField(default=True)
    show_codeforces_on_profile = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Student Profile'
        ordering = ['roll_no']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.roll_no}-{self.user.email.split('@')[0]}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.roll_no} — {self.user.email}"


class EducationBackground(BaseModel):
    """SSC, Intermediate, Diploma, EAMCET, ECET details."""
    class EduType(models.TextChoices):
        SSC         = 'SSC',         '10th / SSC'
        INTERMEDIATE = 'Inter',      'Intermediate (12th)'
        DIPLOMA     = 'Diploma',     'Diploma'
        EAMCET      = 'EAMCET',      'AP/TS EAMCET Rank'
        ECET        = 'ECET',        'ECET Rank'

    student        = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='education')
    edu_type       = models.CharField(max_length=20, choices=EduType.choices)
    institution    = models.CharField(max_length=300, blank=True, default='')
    board_university = models.CharField(max_length=200, blank=True, default='')
    year_of_passing = models.PositiveIntegerField(null=True, blank=True)
    score          = models.CharField(max_length=20, blank=True, default='')  # % or GPA or Rank
    score_type     = models.CharField(max_length=10, default='%',
                        choices=[('%', 'Percentage'), ('GPA', 'GPA'), ('Rank', 'Rank')])
    is_verified    = models.BooleanField(default=False)
    verified_by    = models.ForeignKey('accounts.User', null=True, blank=True,
                        on_delete=models.SET_NULL, related_name='edu_verifications')

    class Meta:
        unique_together = ('student', 'edu_type')

    def __str__(self):
        return f"{self.student.roll_no} - {self.edu_type}"


class Certification(BaseModel):
    class CertType(models.TextChoices):
        LINK     = 'link',   'External Link (Credly/Exam Center)'
        UPLOAD   = 'upload', 'Manual Upload'
        COLLEGE  = 'college','College Issued'

    student    = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='certifications')
    cert_type  = models.CharField(max_length=10, choices=CertType.choices, default=CertType.UPLOAD)
    title      = models.CharField(max_length=300)
    issuer     = models.CharField(max_length=300)
    issued_date = models.DateField()
    cert_url   = models.URLField(blank=True, default='')   # For Credly / exam center link
    file       = models.FileField(upload_to='certifications/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey('accounts.User', null=True, blank=True,
                    on_delete=models.SET_NULL, related_name='cert_verifications')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.student.roll_no} - {self.title}"


class Project(BaseModel):
    class ProjectType(models.TextChoices):
        COLLEGE  = 'college',  'College Supervised'
        EXTERNAL = 'external', 'External'

    student      = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    project_type = models.CharField(max_length=10, choices=ProjectType.choices, default=ProjectType.EXTERNAL)
    title        = models.CharField(max_length=300)
    description  = models.TextField()
    tech_stack   = models.CharField(max_length=500)
    cover_image  = models.ImageField(upload_to='project_covers/', blank=True, null=True)
    is_group     = models.BooleanField(default=False)
    team_size    = models.PositiveIntegerField(default=1)
    repo_url     = models.URLField(blank=True, default='')
    is_verified  = models.BooleanField(default=False)   # college projects verified by faculty

    def __str__(self):
        return f"{self.student.roll_no} - {self.title}"


class Internship(BaseModel):
    student       = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='internships')
    organization  = models.CharField(max_length=300)
    role          = models.CharField(max_length=200)
    start_date    = models.DateField()
    end_date      = models.DateField(null=True, blank=True)
    technologies  = models.CharField(max_length=500, blank=True, default='')
    description   = models.TextField(blank=True, default='')
    supervisor_name  = models.CharField(max_length=200, blank=True, default='')
    supervisor_email = models.EmailField(blank=True, default='')
    certificate   = models.FileField(upload_to='internship_certs/', blank=True, null=True)

    def __str__(self):
        return f"{self.student.roll_no} - {self.organization}"


class Event(BaseModel):
    class EventScope(models.TextChoices):
        COLLEGE  = 'College',  'College'
        EXTERNAL = 'External', 'External'

    class EventRole(models.TextChoices):
        PARTICIPATION = 'Participation', 'Participation'
        AWARD         = 'Award',         'Award'
        POSITION      = 'Position',      'Position'

    student   = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='events')
    name      = models.CharField(max_length=300)
    scope     = models.CharField(max_length=10, choices=EventScope.choices)
    role      = models.CharField(max_length=15, choices=EventRole.choices)
    position  = models.CharField(max_length=100, blank=True, default='')
    organizer = models.CharField(max_length=200, blank=True, default='')
    location  = models.CharField(max_length=200, blank=True, default='')
    event_date = models.DateField()

    def __str__(self):
        return f"{self.student.roll_no} - {self.name}"


class Course(BaseModel):
    class CourseSource(models.TextChoices):
        FACULTY  = 'faculty', 'Faculty (College)'
        NPTEL    = 'nptel',   'NPTEL'
        EXTERNAL = 'external','External (Udemy/Coursera etc.)'

    student   = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='courses')
    title     = models.CharField(max_length=300)
    source    = models.CharField(max_length=10, choices=CourseSource.choices, default=CourseSource.EXTERNAL)
    platform  = models.CharField(max_length=100, blank=True, default='')
    completion_percentage = models.PositiveIntegerField(default=100)
    certificate_url = models.URLField(blank=True, default='')
    is_verified = models.BooleanField(default=False)  # For NPTEL, college can verify

    def __str__(self):
        return f"{self.student.roll_no} - {self.title}"


class Research(BaseModel):
    class ResearchType(models.TextChoices):
        COLLEGE  = 'college',  'College Collaborated'
        EXTERNAL = 'external', 'External'

    class Outcome(models.TextChoices):
        PAPER = 'paper', 'Research Paper'
        BOOK  = 'book',  'Book'
        OTHER = 'other', 'Other'

    student        = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='research')
    research_type  = models.CharField(max_length=10, choices=ResearchType.choices)
    title          = models.CharField(max_length=400)
    advisor_name   = models.CharField(max_length=200, blank=True, default='')
    advisor_email  = models.EmailField(blank=True, default='')
    outcome        = models.CharField(max_length=10, choices=Outcome.choices, default=Outcome.PAPER)
    publisher      = models.CharField(max_length=300, blank=True, default='')
    publication_url = models.URLField(blank=True, default='')
    published_date = models.DateField(null=True, blank=True)
    is_verified    = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.roll_no} - {self.title}"


class SemesterResult(BaseModel):
    """Student-submitted semester score entries verified by exam cell."""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='semester_results')
    semester = models.PositiveSmallIntegerField()
    exam_name = models.CharField(max_length=100, default='Semester Exam')
    subject_code = models.CharField(max_length=20, blank=True, default='')
    subject_name = models.CharField(max_length=200)
    score = models.DecimalField(max_digits=6, decimal_places=2)
    max_score = models.DecimalField(max_digits=6, decimal_places=2, default=100.0)
    grade = models.CharField(max_length=5, blank=True, default='')
    proof = models.FileField(upload_to='semester_results/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        'accounts.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='semester_result_verifications'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']
        unique_together = ('student', 'semester', 'exam_name', 'subject_code', 'subject_name')

    def __str__(self):
        return f"{self.student.roll_no} - Sem {self.semester} - {self.subject_name}"

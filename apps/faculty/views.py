import csv
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views import View
from django.views.generic import TemplateView
from django.utils.timezone import now
from django.db.models import Count, Avg, Q, Sum
from django.http import HttpResponse, JsonResponse
from django.contrib import messages

from apps.accounts.models import User
from apps.academics.models import Department, Section, Subject, Marks, Attendance
from apps.students.models import StudentProfile
from apps.faculty.models import (
    StudentMentorAssignment, LessonPlan, Timetable, AcademicCalendar,
    TrainingProgram, SyllabusCoverage, Cohort, InstitutionCourse,
    CourseMaterial, CourseAssessment, StudentCourseScore, CourseLink
)
from apps.core.models import Announcement
from apps.notifications.models import Notification, NotificationRecipient
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from apps.faculty import selectors


# ── ROLE GUARD MIXIN ───────────────────────────────────────────────────────────
class RoleRequiredMixin(LoginRequiredMixin):
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if self.allowed_roles and request.user.role not in self.allowed_roles:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)


class FacultyHubTemplateView(RoleRequiredMixin, TemplateView):
    allowed_roles = ['Faculty', 'Mentor', 'HOD']
    
    def get(self, request, *args, **kwargs):
        """Mark notifications as read when visiting any faculty portal page."""
        user = request.user
        
        # Get user's departments
        user_departments = list(user.departments.all())
        if user.role == 'HOD' and not user_departments:
            hod_dept = Department.objects.filter(hod=user).first()
            if hod_dept:
                user_departments = [hod_dept]
        
        # Build department filter (same logic as context processor)
        dept_filter = Q(target_department__isnull=True)
        if user_departments:
            dept_filter = dept_filter | Q(target_department__in=user_departments)
        
        # Get all relevant notifications for this user
        relevant_notifications = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).distinct()
        
        # Mark all relevant notifications as read for this user
        for notification in relevant_notifications:
            NotificationRecipient.objects.get_or_create(
                user=user,
                notification=notification,
                defaults={'is_read': True, 'read_at': now()}
            )
            # If it already exists and isn't marked as read, update it
            NotificationRecipient.objects.filter(
                user=user,
                notification=notification,
                is_read=False
            ).update(is_read=True, read_at=now())
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add unread notifications count to context for all faculty portal pages."""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's departments
        user_departments = list(user.departments.all())
        if user.role == 'HOD' and not user_departments:
            hod_dept = Department.objects.filter(hod=user).first()
            if hod_dept:
                user_departments = [hod_dept]
        
        # Build department filter
        dept_filter = Q(target_department__isnull=True)
        if user_departments:
            dept_filter = dept_filter | Q(target_department__in=user_departments)
        
        # Get updated unread count
        total_relevant = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).count()
        
        read_count = NotificationRecipient.objects.filter(user=user, is_read=True).count()
        unread_count = max(0, total_relevant - read_count)
        
        context['hod_unread_count'] = unread_count
        context['faculty_hub_data'] = build_faculty_hub_data(user)
        return context


ROMAN_YEARS = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}


def _student_year_from_batch(batch):
    try:
        start_year = int(str(batch).split('-')[0])
        return min(max(now().year - start_year + 1, 1), 4)
    except (TypeError, ValueError):
        return 1


def _batch_display_label(batch):
    """Convert raw batch string to human-readable year label, e.g. 'I Year (2025-2029)'."""
    yr = _student_year_from_batch(batch)
    roman = ROMAN_YEARS.get(yr, str(yr))
    return f"{roman} Year ({batch})"


def _semester_to_year(semester):
    """Map semester number (1-8) to B.Tech year (I-IV)."""
    try:
        sem = int(semester)
        yr = min(max((sem + 1) // 2, 1), 4)
        return ROMAN_YEARS.get(yr, str(yr))
    except (TypeError, ValueError):
        return None


def _user_departments(user):
    departments = list(user.departments.all())
    if user.role == 'HOD' and not departments:
        hod_dept = Department.objects.filter(hod=user).first()
        if hod_dept:
            departments = [hod_dept]
    return departments


def build_faculty_hub_data(user):
    """Backend replacement for the old faculty-hub/js/data.js demo arrays."""
    departments_qs = Department.objects.filter(id__in=[d.id for d in _user_departments(user)])
    if not departments_qs.exists() and user.role in ['HOD', 'Mentor', 'Faculty']:
        departments_qs = user.departments.all()

    sections_qs = Section.objects.filter(department__in=departments_qs).select_related('department')
    students_qs = StudentProfile.objects.filter(
        department__in=departments_qs,
        is_deleted=False
    ).select_related('user', 'department', 'section')

    # ── Role Isolation Logic (Exclude non-HOD from department-wide view/edit access) ──
    is_hod = user.role == 'HOD' or user.is_superuser
    if is_hod:
        cohorts_qs = Cohort.objects.filter(
            department__in=departments_qs,
            is_deleted=False
        )
        subjects_qs = Subject.objects.filter(department__in=departments_qs)
        institution_courses_qs = InstitutionCourse.objects.filter(
            Q(created_by=user) | Q(created_by__is_superuser=True) | Q(cohorts__department__in=departments_qs),
            is_deleted=False,
        ).distinct()
    else:
        cohorts_qs = Cohort.objects.filter(created_by=user, is_deleted=False)
        subjects_qs = Subject.objects.filter(faculty=user, is_deleted=False)
        institution_courses_qs = InstitutionCourse.objects.filter(created_by=user, is_deleted=False)

    departments = [
        {'id': str(dept.id), 'name': dept.name, 'code': dept.code}
        for dept in departments_qs
    ]
    sections = [
        {
            'id': str(section.id),
            'name': section.name,
            'departmentId': str(section.department_id),
            'year': 1,
        }
        for section in sections_qs
    ]
    cohorts = [
        {
            'id': str(cohort.id),
            'name': cohort.name,
            'departmentId': str(cohort.department_id) if cohort.department_id else '',
            'sectionIds': [],
            'year': _student_year_from_batch(cohort.batch),
            'status': 'active' if cohort.is_active else 'closed',
            'students_count': cohort.students.count(),
            'isOwner': cohort.created_by_id == user.id,
        }
        for cohort in cohorts_qs
    ]
    courses = [
        {
            'id': str(subject.id),
            'name': subject.name,
            'departmentId': str(subject.department_id),
            'sectionIds': [],
            'cohortIds': [],
            'year': max(min(int((subject.semester + 1) / 2), 4), 1),
            'published': True,
            'status': 'active',
            'isOwner': subject.faculty_id == user.id,
        }
        for subject in subjects_qs
    ]
    institution_courses = [
        {
            'id': str(course.id),
            'name': course.name,
            'category': course.category,
            'category_display': course.get_category_display(),
            'sectionIds': [],
            'cohortIds': [str(cohort.id) for cohort in course.cohorts.all()],
            'departmentId': str(course.department_id) if course.department_id else '',
            'studentIds': [str(s.id) for s in course.enrolled_students.all()],
            'students_count': course.enrolled_students.count(),
            'description': course.description,
            'year': 1,
            'published': course.is_published_to_profile,
            'status': 'active' if course.is_published_to_profile else 'closed',
            'isOwner': course.created_by_id == user.id,
            'studyMaterials': [
                {
                    'id': str(m.id),
                    'name': m.title,
                    'type': 'file',
                    'url': m.file.url if m.file else ''
                }
                for m in course.materials.all()
            ],
            'links': [
                {
                    'id': str(l.id),
                    'name': l.title,
                    'type': 'link',
                    'url': l.url
                }
                for l in course.links.all()
            ]
        }
        for course in institution_courses_qs
    ]
    students = []
    for student in students_qs:
        cohort = student.cohorts.first()
        avg_marks = Marks.objects.filter(student=student).aggregate(avg=Avg('total'))['avg'] or 0
        students.append({
            'id': str(student.id),
            'name': student.user.full_name or student.user.email,
            'regNo': student.roll_no,
            'rollNumber': student.roll_no,
            'sectionId': str(student.section_id) if student.section_id else '',
            'cohortId': str(cohort.id) if cohort else '',
            'departmentId': str(student.department_id),
            'year': _student_year_from_batch(student.batch),
            'batch': student.batch,
            'marks': round(float(avg_marks), 1),
            'courseCompletion': {},
        })

    dept_filter = Q(target_department__isnull=True)
    if departments_qs.exists():
        dept_filter |= Q(target_department__in=departments_qs)
    hod_updates = [
        {
            'id': str(notification.id),
            'title': notification.title,
            'content': notification.message,
            'date': notification.created_at.date().isoformat(),
            'departmentId': str(notification.target_department_id) if notification.target_department_id else '',
            'priority': 'high' if notification.is_global else 'medium',
        }
        for notification in Notification.objects.filter(dept_filter).order_by('-created_at')[:20]
    ]

    return {
        'departments': departments,
        'sections': sections,
        'cohorts': cohorts,
        'courses': courses,
        'institutionCourses': institution_courses,
        'students': students,
        'hodUpdates': hod_updates,
    }


class FacultyHubCohortsView(FacultyHubTemplateView):
    template_name = 'faculty/cohorts.html'


class FacultyHubExploreStudentsView(FacultyHubTemplateView):
    template_name = 'faculty/explore_students.html'


class FacultyHubHodUpdatesView(FacultyHubTemplateView):
    template_name = 'faculty/hod_updates.html'


class FacultyHubCoursesView(FacultyHubTemplateView):
    template_name = 'faculty/courses.html'


class FacultyHubInstitutionCoursesView(FacultyHubTemplateView):
    def get(self, request, *args, **kwargs):
        return redirect(f"{request.path.replace('institution-courses/', 'courses/')}?type=institutional")


class FacultyHubSettingsView(FacultyHubTemplateView):
    template_name = 'faculty/settings.html'


# ══════════════════════════════════════════════════════════════════════════════
# HOD DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class HODDashboardView(RoleRequiredMixin, View):
    allowed_roles = ['HOD']

    def get(self, request):
        dept = Department.objects.filter(hod=request.user).first()
        if not dept:
            dept = request.user.departments.first()
        if not dept:
            return render(request, 'faculty/hod_dashboard.html', {'no_dept': True})

        # ── Faculty in dept ──
        faculty_list = User.objects.filter(
            departments=dept, role__in=['Faculty', 'Mentor'], is_active=True
        ).annotate(subject_count=Count('subjects_taught'))

        # ── Mentor list for assignment ──
        mentors = User.objects.filter(departments=dept, role__in=['Faculty', 'Mentor'], is_active=True)

        current_year = f"{now().year}-{now().year + 1}"

        # ── Attach mentoring assignment display string if the user is a Mentor ──
        import re
        faculty_list = list(faculty_list)
        for member in faculty_list:
            member.mentoring_assignment_display = None
            if member.role in ['Faculty', 'Mentor']:
                assignment = StudentMentorAssignment.objects.filter(
                    mentor=member,
                    academic_year=current_year
                ).first()
                if assignment:
                    students_in_assignment = list(assignment.students.all().order_by('roll_no'))
                    if students_in_assignment:
                        first_s = students_in_assignment[0]
                        batch_val = first_s.batch
                        
                        yr_num = _student_year_from_batch(batch_val)
                        roman_years = {1: 'I', 2: 'II', 3: 'III', 4: 'IV'}
                        roman_yr = roman_years.get(yr_num, 'I')
                        
                        def get_roll_num(roll_no):
                            match = re.search(r'\d+$', roll_no)
                            return int(match.group()) if match else None
                        
                        roll_nums = [get_roll_num(s.roll_no) for s in students_in_assignment if get_roll_num(s.roll_no) is not None]
                        if roll_nums:
                            min_roll = min(roll_nums)
                            max_roll = max(roll_nums)
                            roll_range = f"({min_roll}-{max_roll})"
                        else:
                            roll_range = ""
                        
                        sec_str = f"-{first_s.section.name}" if first_s.section else ""
                        member.mentoring_assignment_display = f"{roman_yr} {dept.code}{sec_str} {roll_range}".strip()

        direct_assignments = StudentMentorAssignment.objects.filter(
            academic_year=current_year,
            students__department=dept
        ).distinct()

        dept_students_qs = StudentProfile.objects.filter(
            department=dept, is_deleted=False
        ).select_related('user', 'section')

        # Extract unique batches with human-readable year labels
        raw_batches = list(dept_students_qs.values_list('batch', flat=True).distinct().order_by('batch'))
        batches = raw_batches  # raw values for form submission
        batch_labels = {b: _batch_display_label(b) for b in raw_batches}

        # ── Year-wise student breakdown (I, II, III, IV Year) ──
        year_wise_stats = []
        for yr_num in [1, 2, 3, 4]:
            matching_batches = [b for b in raw_batches if _student_year_from_batch(b) == yr_num]
            count = dept_students_qs.filter(batch__in=matching_batches).count() if matching_batches else 0
            year_wise_stats.append({
                'year': yr_num,
                'roman': ROMAN_YEARS[yr_num],
                'count': count,
                'batches': matching_batches,
            })
        
        # Get sections in department
        sections = Section.objects.filter(department=dept)

        # Attach mentor name + year to each student
        dept_students = list(dept_students_qs)
        student_mentor_map = {}
        for assignment in direct_assignments:
            mentor_name = assignment.mentor.full_name or assignment.mentor.email
            for s in assignment.students.all():
                student_mentor_map[str(s.id)] = mentor_name
        for student in dept_students:
            student.assigned_mentor = student_mentor_map.get(str(student.id), "Unassigned")
            student.year_num = _student_year_from_batch(student.batch)
            student.year_roman = ROMAN_YEARS.get(student.year_num, 'I')

        # Build assigned mentors information
        assigned_mentors_info = {}
        for assignment in direct_assignments:
            students_in_assignment = list(assignment.students.all().order_by('roll_no'))
            if students_in_assignment:
                first_s = students_in_assignment[0]
                batch_val = first_s.batch
                sec_val = first_s.section
                all_class_students = list(StudentProfile.objects.filter(
                    department=dept, batch=batch_val, section=sec_val, is_deleted=False
                ).order_by('roll_no'))
                if all_class_students:
                    mid = (len(all_class_students) + 1) // 2
                    first_half_ids = {s.id for s in all_class_students[:mid]}
                    assigned_ids = {s.id for s in students_in_assignment}
                    is_first_half = len(assigned_ids.intersection(first_half_ids)) > len(assigned_ids) / 2
                    half_str = "1st Half" if is_first_half else "2nd Half"
                    assigned_mentors_info[str(assignment.mentor.id)] = {
                        'batch': batch_val,
                        'section': sec_val.name if sec_val else 'N/A',
                        'half': half_str
                    }

        # ── Dept performance (avg CGPA by year — I, II, III, IV) ──
        batch_performance = (
            StudentProfile.objects
            .filter(department=dept, is_deleted=False)
            .values('batch')
            .annotate(avg_cgpa=Avg('cgpa'), count=Count('id'))
            .order_by('batch')
        )
        # Aggregate by year number
        year_cgpa = {}  # {1: [values], 2: [values], ...}
        for b in batch_performance:
            yr = _student_year_from_batch(b['batch'])
            if yr not in year_cgpa:
                year_cgpa[yr] = {'total_cgpa': 0, 'total_count': 0}
            year_cgpa[yr]['total_cgpa'] += float(b['avg_cgpa'] or 0) * b['count']
            year_cgpa[yr]['total_count'] += b['count']
        perf_labels = []
        perf_values = []
        for yr_num in [1, 2, 3, 4]:
            perf_labels.append(f"{ROMAN_YEARS[yr_num]} Year")
            if yr_num in year_cgpa and year_cgpa[yr_num]['total_count'] > 0:
                avg = year_cgpa[yr_num]['total_cgpa'] / year_cgpa[yr_num]['total_count']
                perf_values.append(round(avg, 2))
            else:
                perf_values.append(0)

        # ── Lesson plans ──
        lesson_plans = LessonPlan.objects.filter(
            department=dept, is_deleted=False
        ).select_related('subject', 'uploaded_by').order_by('-created_at')[:10]

        # ── Timetables ──
        timetables = list(Timetable.objects.filter(
            department=dept, is_deleted=False
        ).order_by('-created_at')[:5])
        for tt in timetables:
            tt.year_roman = _semester_to_year(tt.semester)

        # ── Academic Calendars ──
        calendars = list(AcademicCalendar.objects.filter(
            department=dept, is_deleted=False
        ).order_by('-created_at')[:5])
        for cal in calendars:
            cal.year_roman = _semester_to_year(cal.semester)

        # ── Training programs ──
        training_programs = TrainingProgram.objects.filter(
            department=dept, is_deleted=False
        ).order_by('-start_date')[:10]

        # ── Branch notifications published by HOD to branch students ──
        announcements = Notification.objects.filter(
            sender=request.user,
            target_department=dept,
            target_role=Notification.TargetRole.STUDENT
        ).order_by('-created_at')[:20]


        # ── Syllabus completion (dept-wide) ──
        dept_subjects = Subject.objects.filter(department=dept)
        syllabus_summary = (
            SyllabusCoverage.objects
            .filter(subject__in=dept_subjects)
            .values('subject__name', 'subject__code')
            .annotate(
                total=Sum('total_topics'),
                covered=Sum('covered_topics')
            )
        )
        syllabus_totals = SyllabusCoverage.objects.filter(subject__in=dept_subjects).aggregate(
            total=Sum('total_topics'),
            covered=Sum('covered_topics'),
        )
        syllabus_total = float(syllabus_totals.get('total') or 0)
        syllabus_covered = float(syllabus_totals.get('covered') or 0)
        syllabus_pct = round((syllabus_covered / syllabus_total) * 100, 1) if syllabus_total else 0

        # ── Principal-forwarded summary (graph) ──
        total_students = StudentProfile.objects.filter(department=dept, is_deleted=False).count()
        assigned_count = StudentMentorAssignment.objects.filter(
            academic_year=current_year, students__department=dept
        ).values('students__id').distinct().count()
        unassigned_count = max(total_students - assigned_count, 0)
        avg_cgpa = (
            StudentProfile.objects
            .filter(department=dept, is_deleted=False)
            .aggregate(avg=Avg('cgpa'))['avg'] or 0
        )
        principal_labels = ['Avg CGPA', 'Mentor Assigned', 'Mentor Unassigned', 'Syllabus %']
        principal_values = [round(float(avg_cgpa), 2), assigned_count, unassigned_count, syllabus_pct]

        return render(request, 'faculty/hod_dashboard.html', {
            'dept':               dept,
            'faculty_list':       faculty_list,
            'mentors':            mentors,
            'direct_assignments': direct_assignments,
            'dept_students':      dept_students,
            'batches':            batches,
            'batch_labels':       batch_labels,
            'year_wise_stats':    year_wise_stats,
            'sections':           sections,
            'assigned_mentors_info': assigned_mentors_info,
            'current_year':       current_year,
            'lesson_plans':       lesson_plans,
            'timetables':         timetables,
            'calendars':          calendars,
            'training_programs':  training_programs,
            'announcements':      announcements,
            'announcement_categories': Announcement.Category.choices,
            'syllabus_summary':   list(syllabus_summary),
            'subjects':           dept_subjects,
            'perf_labels':        perf_labels,
            'perf_values':        perf_values,
            'principal_labels':   principal_labels,
            'principal_values':   principal_values,
        })

    def post(self, request):
        """Handle mentor assignments and file uploads."""
        action = request.POST.get('action')
        dept = Department.objects.filter(hod=request.user).first()
        if not dept:
            dept = request.user.departments.first()
        if not dept:
            return redirect('hod-dashboard')
        current_year = f"{now().year}-{now().year + 1}"



        if action == 'assign_mentor_halves':
            batch = request.POST.get('batch')
            section_id = request.POST.get('section_id')
            mentor_1_id = request.POST.get('mentor_1_id')
            mentor_2_id = request.POST.get('mentor_2_id')

            if batch and section_id and mentor_1_id and mentor_2_id:
                if mentor_1_id == mentor_2_id:
                    messages.error(request, "Please assign different mentors to each half of the class.")
                    return redirect('hod-dashboard')

                # Fetch all students in this batch & section
                students = list(StudentProfile.objects.filter(
                    department=dept, batch=batch, section_id=section_id, is_deleted=False
                ).order_by('roll_no'))

                if not students:
                    messages.error(request, "No students found in the selected batch and section.")
                    return redirect('hod-dashboard')

                # Split the students into two halves
                mid = (len(students) + 1) // 2
                half_1 = students[:mid]
                half_2 = students[mid:]

                def check_mentor_double_assigned(mentor_id):
                    existing = StudentMentorAssignment.objects.filter(
                        mentor_id=mentor_id, academic_year=current_year
                    ).first()
                    if existing:
                        other_students = existing.students.exclude(
                            id__in=[s.id for s in students]
                        )
                        if other_students.exists():
                            return True
                    return False

                if check_mentor_double_assigned(mentor_1_id):
                    mentor_user = User.objects.filter(id=mentor_1_id).first()
                    mentor_name = mentor_user.full_name if mentor_user else "selected 1st half mentor"
                    messages.error(request, f"{mentor_name} is already assigned to another class/batch.")
                    return redirect('hod-dashboard')

                if check_mentor_double_assigned(mentor_2_id):
                    mentor_user = User.objects.filter(id=mentor_2_id).first()
                    mentor_name = mentor_user.full_name if mentor_user else "selected 2nd half mentor"
                    messages.error(request, f"{mentor_name} is already assigned to another class/batch.")
                    return redirect('hod-dashboard')

                # 1st Half Assignment
                assign_1, _ = StudentMentorAssignment.objects.update_or_create(
                    mentor_id=mentor_1_id, academic_year=current_year,
                    defaults={'assigned_by': request.user}
                )
                for s in half_1:
                    other_assignments = StudentMentorAssignment.objects.filter(
                        academic_year=current_year
                    ).exclude(mentor_id=mentor_1_id)
                    for oa in other_assignments:
                        oa.students.remove(s)
                assign_1.students.set(half_1)

                # 2nd Half Assignment
                assign_2, _ = StudentMentorAssignment.objects.update_or_create(
                    mentor_id=mentor_2_id, academic_year=current_year,
                    defaults={'assigned_by': request.user}
                )
                for s in half_2:
                    other_assignments = StudentMentorAssignment.objects.filter(
                        academic_year=current_year
                    ).exclude(mentor_id=mentor_2_id)
                    for oa in other_assignments:
                        oa.students.remove(s)
                assign_2.students.set(half_2)

                # Clean up any empty assignments
                StudentMentorAssignment.objects.filter(
                    academic_year=current_year,
                    students__isnull=True
                ).delete()

                sec_name = students[0].section.name if students[0].section else 'N/A'
                messages.success(request, f"Mentor assignments updated successfully for {batch} - Section {sec_name}.")
                return redirect('hod-dashboard')

        elif action == 'assign_mentor_manual':
            mentor_id = request.POST.get('mentor_id')
            student_ids = request.POST.getlist('student_ids')

            if mentor_id and student_ids:
                mentor_user = User.objects.filter(id=mentor_id).first()
                if not mentor_user:
                    messages.error(request, "Selected mentor is invalid.")
                    return redirect('hod-dashboard')

                assign, _ = StudentMentorAssignment.objects.get_or_create(
                    mentor_id=mentor_id, academic_year=current_year,
                    defaults={'assigned_by': request.user}
                )

                students = list(StudentProfile.objects.filter(id__in=student_ids, department=dept, is_deleted=False))
                
                other_assignments = StudentMentorAssignment.objects.filter(
                    academic_year=current_year
                ).exclude(mentor_id=mentor_id)
                for oa in other_assignments:
                    oa.students.remove(*students)
                    
                assign.students.add(*students)
                
                messages.success(request, f"Manually assigned {len(students)} students to {mentor_user.full_name or mentor_user.email}.")
                return redirect('hod-dashboard')

        elif action == 'remove_mentor_assignment':
            assignment_id = request.POST.get('assignment_id')
            if assignment_id:
                StudentMentorAssignment.objects.filter(id=assignment_id).delete()
                messages.success(request, 'Mentor assignment removed.')

        elif action == 'upload_lesson_plan':
            subject_id = request.POST.get('subject_id')
            acad_year  = request.POST.get('academic_year', current_year)
            target_year = request.POST.get('target_year') or None
            target_section_id = request.POST.get('target_section') or None
            resource_link = request.POST.get('resource_link', '').strip()
            f = request.FILES.get('file')
            if subject_id and f:
                LessonPlan.objects.create(
                    subject_id=subject_id, department=dept,
                    uploaded_by=request.user, file=f, academic_year=acad_year,
                    target_year=target_year, target_section_id=target_section_id,
                    resource_link=resource_link
                )

        elif action == 'upload_timetable':
            semester   = request.POST.get('semester')
            target_year = request.POST.get('target_year') or None
            target_section_id = request.POST.get('target_section') or None
            valid_from = request.POST.get('valid_from')
            resource_link = request.POST.get('resource_link', '').strip()
            f = request.FILES.get('file')
            if valid_from and f:
                Timetable.objects.create(
                    department=dept, uploaded_by=request.user,
                    semester=semester or None, target_year=target_year, target_section_id=target_section_id,
                    valid_from=valid_from, file=f,
                    academic_year=current_year, resource_link=resource_link
                )

        elif action == 'upload_calendar':
            title    = request.POST.get('title')
            semester = request.POST.get('semester')
            target_year = request.POST.get('target_year') or None
            target_section_id = request.POST.get('target_section') or None
            resource_link = request.POST.get('resource_link', '').strip()
            f = request.FILES.get('file')
            if title and f:
                AcademicCalendar.objects.create(
                    department=dept, uploaded_by=request.user,
                    title=title, academic_year=current_year, 
                    semester=semester or None, target_year=target_year, target_section_id=target_section_id, 
                    file=f,
                    resource_link=resource_link
                )

        elif action == 'create_training':
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date') or None
            venue = request.POST.get('venue', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            registration_link = request.POST.get('registration_link', '').strip()
            if title and start_date:
                TrainingProgram.objects.create(
                    department=dept,
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    venue=venue,
                    created_by=request.user,
                    is_active=is_active,
                    registration_link=registration_link
                )

        elif action == 'update_training':
            training_id = request.POST.get('training_id')
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date') or None
            venue = request.POST.get('venue', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            if training_id and title and start_date:
                training = get_object_or_404(TrainingProgram, id=training_id, is_deleted=False)
                if training.department == dept:
                    training.title = title
                    training.description = description
                    training.start_date = start_date
                    training.end_date = end_date
                    training.venue = venue
                    training.is_active = is_active
                    training.save(update_fields=[
                        'title', 'description', 'start_date', 'end_date',
                        'venue', 'is_active', 'updated_at'
                    ])

        elif action == 'create_announcement':
            title = request.POST.get('title', '').strip()
            content = request.POST.get('content', '').strip()
            resource_link = request.POST.get('resource_link', '').strip()
            if title and content:
                Notification.objects.create(
                    sender=request.user,
                    title=title,
                    message=content,
                    resource_link=resource_link,
                    target_role=Notification.TargetRole.STUDENT,
                    target_department=dept,
                    is_global=False
                )

        return redirect('hod-dashboard')


# ══════════════════════════════════════════════════════════════════════════════
# MENTOR DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class FacultyHubMentoringView(RoleRequiredMixin, View):
    allowed_roles = ['Faculty', 'Mentor', 'HOD']

    def get(self, request, *args, **kwargs):
        user = request.user
        current_year = f"{now().year}-{now().year + 1}"
        
        # Verify if they are a mentor
        is_mentor = user.role in ['Mentor', 'HOD'] or StudentMentorAssignment.objects.filter(mentor=user, academic_year=current_year).exists()
        if not is_mentor:
            messages.error(request, "You are not assigned as a mentor to any class/students.")
            return redirect('faculty-dashboard')

        direct_students = StudentProfile.objects.filter(
            direct_mentor_assignments__mentor=user,
            direct_mentor_assignments__academic_year=current_year,
            is_deleted=False
        ).select_related('user', 'department', 'section').distinct()
        students = direct_students

        # ── Per-student academic overview ──
        student_stats = []
        for s in students:
            avg_marks = Marks.objects.filter(student=s).aggregate(avg=Avg('total'))['avg'] or 0
            total_att = Attendance.objects.filter(student=s).count()
            present   = Attendance.objects.filter(student=s, is_present=True).count()
            att_pct   = round((present / total_att * 100) if total_att else 0)
            student_stats.append({
                'student':    s,
                'avg_marks':  round(float(avg_marks), 1),
                'att_pct':    att_pct,
                'cgpa':       s.cgpa,
            })
            
        mentor_chart_data = [
            {
                'name': row['student'].user.full_name or row['student'].roll_no,
                'roll_no': row['student'].roll_no,
                'cgpa': float(row['cgpa'] or 0),
                'avg_marks': float(row['avg_marks'] or 0),
            }
            for row in student_stats
        ]

        # ── Subjects mentor can upload marks for ──
        subjects = Subject.objects.filter(
            department__in=user.departments.all()
        ).select_related('department') if user.departments.exists() else Subject.objects.all()

        # ── Institution courses published to this mentor's dashboard ──
        inst_courses = InstitutionCourse.objects.filter(
            cohorts__students__in=students
        ).distinct()

        # Build notification unread count for base_portal layout compatibility
        user_departments = list(user.departments.all())
        if user.role == 'HOD' and not user_departments:
            hod_dept = Department.objects.filter(hod=user).first()
            if hod_dept:
                user_departments = [hod_dept]
        
        dept_filter = Q(target_department__isnull=True)
        if user_departments:
            dept_filter = dept_filter | Q(target_department__in=user_departments)
            
        total_relevant = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).count()
        
        read_count = NotificationRecipient.objects.filter(user=user, is_read=True).count()
        unread_count = max(0, total_relevant - read_count)

        return render(request, 'faculty/mentor.html', {
            'student_stats':  student_stats,
            'subjects':       subjects,
            'assignments':    [],
            'inst_courses':   inst_courses,
            'current_year':   current_year,
            'mentor_chart_data': mentor_chart_data,
            'hod_unread_count': unread_count,
        })

    def post(self, request, *args, **kwargs):
        """Upload marks or attendance for mentored students."""
        action = request.POST.get('action')

        if action == 'upload_marks':
            student_id = request.POST.get('student_id')
            subject_id = request.POST.get('subject_id')
            internal   = request.POST.get('internal', 0)
            external   = request.POST.get('external', 0)
            total      = float(internal) + float(external)
            grade      = request.POST.get('grade', '')
            if student_id and subject_id:
                Marks.objects.update_or_create(
                    student_id=student_id, subject_id=subject_id,
                    defaults={'internal': internal, 'external': external,
                              'total': total, 'grade': grade}
                )
                messages.success(request, "Marks uploaded successfully.")

        elif action == 'upload_attendance':
            student_id  = request.POST.get('student_id')
            subject_id  = request.POST.get('subject_id')
            date_str    = request.POST.get('date')
            is_present  = request.POST.get('is_present') == 'on'
            if student_id and subject_id and date_str:
                Attendance.objects.get_or_create(
                    student_id=student_id, subject_id=subject_id, date=date_str,
                    defaults={'is_present': is_present, 'recorded_by': request.user}
                )
                messages.success(request, "Attendance uploaded successfully.")

        return redirect('faculty-mentor')


# ══════════════════════════════════════════════════════════════════════════════
# FACULTY DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
class FacultyDashboardView(RoleRequiredMixin, View):
    allowed_roles = ['Faculty', 'HOD', 'Mentor']

    def get(self, request):
        user = request.user
        departments = user.departments.all()
        
        # ── Mark notifications as read ──
        user_departments = list(user.departments.all())
        if user.role == 'HOD' and not user_departments:
            hod_dept = Department.objects.filter(hod=user).first()
            if hod_dept:
                user_departments = [hod_dept]
        
        # Build department filter
        dept_filter = Q(target_department__isnull=True)
        if user_departments:
            dept_filter = dept_filter | Q(target_department__in=user_departments)
        
        # Get all relevant notifications for this user
        relevant_notifications = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).distinct()
        
        # Mark all relevant notifications as read for this user
        for notification in relevant_notifications:
            NotificationRecipient.objects.get_or_create(
                user=user,
                notification=notification,
                defaults={'is_read': True, 'read_at': now()}
            )
            # If it already exists and isn't marked as read, update it
            NotificationRecipient.objects.filter(
                user=user,
                notification=notification,
                is_read=False
            ).update(is_read=True, read_at=now())
        
        # ── My subjects ──
        my_subjects = Subject.objects.filter(
            faculty=user, is_deleted=False
        ).select_related('department')

        # ── Syllabus coverage per subject ──
        syllabus_by_subject = {}
        for subj in my_subjects:
            units = SyllabusCoverage.objects.filter(subject=subj, faculty=user).order_by('unit_number')
            total = units.aggregate(t=Sum('total_topics'))['t'] or 0
            covered = units.aggregate(c=Sum('covered_topics'))['c'] or 0
            syllabus_by_subject[subj.id] = {
                'subject': subj,
                'units':   units,
                'total':   total,
                'covered': covered,
                'pct':     round((covered / total * 100) if total else 0),
            }

        # ── Cohorts (role-isolated) ──
        is_hod = user.role == 'HOD' or user.is_superuser
        if is_hod and departments.exists():
            my_cohorts = Cohort.objects.filter(
                department__in=departments,
                is_deleted=False,
                is_active=True
            ).annotate(student_count=Count('students'))
        else:
            my_cohorts = Cohort.objects.filter(
                created_by=user,
                is_deleted=False,
                is_active=True
            ).annotate(student_count=Count('students'))

        # ── Institution courses (role-isolated) ──
        if is_hod:
            my_courses = InstitutionCourse.objects.filter(
                Q(created_by=user) |
                Q(created_by__is_superuser=True) |
                Q(cohorts__department__in=departments)
            ).filter(is_deleted=False).distinct()
        else:
            my_courses = InstitutionCourse.objects.filter(
                created_by=user,
                is_deleted=False
            ).distinct()

        # ── Student performance in my subjects ──
        subject_performance = []
        for subj in my_subjects:
            avg = Marks.objects.filter(subject=subj).aggregate(avg=Avg('total'))['avg']
            count = Marks.objects.filter(subject=subj).count()
            coverage = syllabus_by_subject.get(subj.id, {})
            subject_performance.append({
                'subject': subj,
                'avg': round(float(avg), 1) if avg else 0,
                'count': count,
                'coverage_pct': coverage.get('pct', 0),
            })

        # ── Chart data ──
        perf_labels = [sp['subject'].code for sp in subject_performance]
        perf_values = [sp['avg'] for sp in subject_performance]

        # ── All students for cohort creation ──
        dept_students = StudentProfile.objects.filter(
            department__in=departments, is_deleted=False
        ).select_related('user', 'department') if departments.exists() else StudentProfile.objects.none()
        
        # ── Calculate unread notifications count ──
        total_relevant = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).count()
        
        read_count = NotificationRecipient.objects.filter(user=user, is_read=True).count()
        unread_count = max(0, total_relevant - read_count)

        return render(request, 'faculty/faculty_dashboard.html', {
            'my_subjects':        my_subjects,
            'syllabus_by_subject': syllabus_by_subject,
            'my_cohorts':         my_cohorts,
            'my_courses':         my_courses,
            'subject_performance': subject_performance,
            'dept_students':      dept_students,
            'departments':        departments,
            'perf_labels':        perf_labels,
            'perf_values':        perf_values,
            'hod_unread_count':   unread_count,
            'faculty_hub_data':   build_faculty_hub_data(user),
        })

    def post(self, request):
        action = request.POST.get('action')

        # ── Create Cohort ──
        if action == 'create_cohort':
            name     = request.POST.get('name', '').strip()
            ctype    = request.POST.get('cohort_type', 'training')
            batch    = request.POST.get('batch', '')
            desc     = request.POST.get('description', '')
            stud_ids = request.POST.getlist('student_ids')
            department_id = request.POST.get('department_id')
            if name:
                department = None
                if department_id:
                    department = Department.objects.filter(
                        id=department_id, id__in=request.user.departments.values_list('id', flat=True)
                    ).first()
                cohort = Cohort.objects.create(
                    name=name, created_by=request.user,
                    department=department,
                    cohort_type=ctype, batch=batch, description=desc
                )
                if stud_ids:
                    cohort.students.set(stud_ids)

        # ── Update Cohort ──
        elif action == 'update_cohort':
            cohort_id = request.POST.get('cohort_id')
            name      = request.POST.get('name', '').strip()
            ctype     = request.POST.get('cohort_type', 'training')
            batch     = request.POST.get('batch', '')
            desc      = request.POST.get('description', '')
            stud_ids  = request.POST.getlist('student_ids')
            department_id = request.POST.get('department_id')
            if cohort_id and name:
                cohort = get_object_or_404(Cohort, id=cohort_id, is_deleted=False)
                if (not cohort.department or cohort.department_id in request.user.departments.values_list('id', flat=True)) and (
                    cohort.created_by == request.user or cohort.created_by.is_superuser
                ):
                    if department_id:
                        new_dept = Department.objects.filter(
                            id=department_id, id__in=request.user.departments.values_list('id', flat=True)
                        ).first()
                        cohort.department = new_dept
                    cohort.name = name
                    cohort.cohort_type = ctype
                    cohort.batch = batch
                    cohort.description = desc
                    cohort.save(update_fields=['name', 'cohort_type', 'batch', 'description', 'department', 'updated_at'])
                    cohort.students.set(stud_ids)

        # ── Delete Cohort ──
        elif action == 'delete_cohort':
            cohort_id = request.POST.get('cohort_id')
            if cohort_id:
                cohort = get_object_or_404(Cohort, id=cohort_id, is_deleted=False)
                if cohort.created_by == request.user or request.user.is_superuser:
                    cohort.is_deleted = True
                    cohort.save(update_fields=['is_deleted', 'updated_at'])

        # ── Create Institution Course ──
        elif action == 'create_course':
            name          = request.POST.get('name', '').strip()
            category      = request.POST.get('category', 'other')
            description   = request.POST.get('description', '')
            publish       = request.POST.get('is_published_to_profile') == 'on'
            department_id = request.POST.get('department_id')
            student_ids   = request.POST.getlist('student_ids')
            if name:
                department = None
                if department_id:
                    department = Department.objects.filter(id=department_id).first()
                course = InstitutionCourse.objects.create(
                    name=name, category=category, created_by=request.user,
                    department=department,
                    description=description, is_published_to_profile=publish
                )
                if student_ids:
                    course.enrolled_students.set(student_ids)

        # ── Update Institution Course ──
        elif action == 'update_course':
            course_id     = request.POST.get('course_id')
            name          = request.POST.get('name', '').strip()
            category      = request.POST.get('category', 'other')
            description   = request.POST.get('description', '')
            publish       = request.POST.get('is_published_to_profile') == 'on'
            department_id = request.POST.get('department_id')
            student_ids   = request.POST.getlist('student_ids')
            if course_id and name:
                course = get_object_or_404(InstitutionCourse, id=course_id, is_deleted=False)
                if course.created_by == request.user or course.created_by.is_superuser:
                    department = None
                    if department_id:
                        department = Department.objects.filter(id=department_id).first()
                    course.name = name
                    course.category = category
                    course.department = department
                    course.description = description
                    course.is_published_to_profile = publish
                    course.save(update_fields=['name', 'category', 'department', 'description', 'is_published_to_profile', 'updated_at'])
                    course.enrolled_students.set(student_ids or [])

        # ── Delete Institution Course ──
        elif action == 'delete_course':
            course_id = request.POST.get('course_id')
            if course_id:
                course = get_object_or_404(InstitutionCourse, id=course_id, is_deleted=False)
                if course.created_by == request.user or course.created_by.is_superuser:
                    course.is_deleted = True
                    course.save(update_fields=['is_deleted', 'updated_at'])

        # ── Upload Course Material ──
        elif action == 'upload_material':
            course_id = request.POST.get('course_id')
            title     = request.POST.get('title', '').strip()
            f         = request.FILES.get('file')
            if course_id and title and f:
                course = get_object_or_404(InstitutionCourse, id=course_id)
                if course.created_by == request.user or course.created_by.is_superuser:
                    CourseMaterial.objects.create(course=course, title=title, file=f)

        # ── Delete Course Material ──
        elif action == 'delete_material':
            material_id = request.POST.get('material_id')
            if material_id:
                material = get_object_or_404(CourseMaterial, id=material_id)
                if material.course.created_by == request.user or material.course.created_by.is_superuser:
                    material.delete()

        # ── Add Course Link ──
        elif action == 'add_link':
            course_id = request.POST.get('course_id')
            title     = request.POST.get('title', '').strip()
            url       = request.POST.get('url', '').strip()
            if course_id and title and url:
                course = get_object_or_404(InstitutionCourse, id=course_id)
                if course.created_by == request.user or course.created_by.is_superuser:
                    CourseLink.objects.create(course=course, title=title, url=url)

        # ── Delete Course Link ──
        elif action == 'delete_link':
            link_id = request.POST.get('link_id')
            if link_id:
                link = get_object_or_404(CourseLink, id=link_id)
                if link.course.created_by == request.user or link.course.created_by.is_superuser:
                    link.delete()

        # ── Add Assessment ──
        elif action == 'add_assessment':
            course_id  = request.POST.get('course_id')
            aname      = request.POST.get('assessment_name', '').strip()
            max_score  = request.POST.get('max_score', 100)
            if course_id and aname:
                course = get_object_or_404(InstitutionCourse, id=course_id)
                if course.created_by == request.user or course.created_by.is_superuser:
                    CourseAssessment.objects.create(course=course, name=aname, max_score=max_score)

        # ── Update Syllabus Unit ──
        elif action == 'update_syllabus':
            subject_id     = request.POST.get('subject_id')
            unit_number    = request.POST.get('unit_number')
            unit_title     = request.POST.get('unit_title', '').strip()
            total_topics   = request.POST.get('total_topics', 1)
            covered_topics = request.POST.get('covered_topics', 0)
            doc            = request.FILES.get('document')
            remarks        = request.POST.get('remarks', '')
            if subject_id and unit_number:
                defaults = {
                    'unit_title': unit_title,
                    'total_topics': int(total_topics),
                    'covered_topics': int(covered_topics),
                    'remarks': remarks,
                }
                if doc:
                    defaults['document'] = doc
                SyllabusCoverage.objects.update_or_create(
                    subject_id=subject_id, faculty=request.user, unit_number=unit_number,
                    defaults=defaults
                )

        # ── Update Subject Marks ──
        elif action == 'update_marks':
            subject_id = request.POST.get('subject_id')
            student_id = request.POST.get('student_id')
            internal   = request.POST.get('internal', 0)
            external   = request.POST.get('external', 0)
            grade      = request.POST.get('grade', '')
            total      = float(internal) + float(external)
            if subject_id and student_id:
                Marks.objects.update_or_create(
                    student_id=student_id, subject_id=subject_id,
                    defaults={'internal': internal, 'external': external,
                              'total': total, 'grade': grade}
                )

        return redirect(request.META.get('HTTP_REFERER', 'faculty-dashboard'))


# ── SCORE TEMPLATE DOWNLOAD ────────────────────────────────────────────────────
@login_required
def download_score_template(request, course_id):
    course = get_object_or_404(InstitutionCourse, id=course_id)
    if course.created_by == request.user or course.created_by.is_superuser:
        assessments = course.assessments.all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    header = ['roll_no', 'student_name']
    for a in assessments:
        header.append(f'{a.name} (max:{a.max_score})')
    writer.writerow(header)

    # Student rows
    for cohort in course.cohorts.all():
        for student in cohort.students.all():
            row = [student.roll_no, student.user.full_name or student.user.email]
            for a in assessments:
                try:
                    score = StudentCourseScore.objects.get(assessment=a, student=student)
                    row.append(score.score)
                except StudentCourseScore.DoesNotExist:
                    row.append('')
            writer.writerow(row)

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{course.name}_scores.csv"'
    return response


# ── EXISTING API VIEWS (kept) ──────────────────────────────────────────────────
class FacultySubjectsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        subjects = selectors.get_subjects_by_faculty(request.user.id)
        data = [{"id": s.id, "name": s.name, "code": s.code,
                 "dept": s.department.name, "semester": s.semester} for s in subjects]
        return Response(data)


class PendingCertificationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        dept_ids = list(request.user.departments.values_list('id', flat=True))
        if request.user.role == 'HOD' and not dept_ids:
            hod_dept = Department.objects.filter(hod=request.user).first()
            if hod_dept:
                dept_ids = [hod_dept.id]
        if not dept_ids:
            return Response([])
        certs = selectors.get_pending_certifications_for_dept(dept_ids)
        data = [{"id": c.id, "title": c.title, "student": c.student.roll_no,
                 "student_id": c.student.id,
                 "issuer": c.issuer, "date": c.issued_date} for c in certs]
        return Response(data)

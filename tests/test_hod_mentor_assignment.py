import pytest
from django.urls import reverse
from django.utils import timezone
from django.test import Client
from apps.accounts.models import User
from apps.academics.models import Department, Section
from apps.students.models import StudentProfile
from apps.faculty.models import StudentMentorAssignment

@pytest.mark.django_db
def test_class_split_mentor_assignment():
    client = Client()
    
    # 1. Setup Department & HOD
    dept = Department.objects.create(name="Computer Science", code="CS")
    hod = User.objects.create(email="hod@cs.com", role="HOD")
    dept.hod = hod
    dept.save()
    
    # 2. Setup Section
    section = Section.objects.create(name="A", department=dept)
    
    # 3. Setup Mentors
    mentor_1 = User.objects.create(email="mentor1@cs.com", role="Mentor")
    mentor_2 = User.objects.create(email="mentor2@cs.com", role="Mentor")
    mentor_1.departments.add(dept)
    mentor_2.departments.add(dept)
    
    # 4. Setup 4 Students (R001 - R004)
    students = []
    for i in range(1, 5):
        user = User.objects.create(email=f"student{i}@cs.com", role="Student")
        profile = StudentProfile.objects.create(
            user=user,
            roll_no=f"R00{i}",
            batch="2022-2026",
            department=dept,
            section=section
        )
        students.append(profile)
        
    # Log in HOD
    client.force_login(hod)
    
    # 5. POST to HOD Dashboard for mentor split assignment
    url = reverse('hod-dashboard')
    response = client.post(url, {
        'action': 'assign_mentor_halves',
        'batch': '2022-2026',
        'section_id': section.id,
        'mentor_1_id': mentor_1.id,
        'mentor_2_id': mentor_2.id
    })
    
    assert response.status_code == 302 # redirect
    
    # 6. Verify assignments in DB
    # 1st half: students R001, R002
    assign_1 = StudentMentorAssignment.objects.get(mentor=mentor_1)
    assert set(assign_1.students.all()) == {students[0], students[1]}
    
    # 2nd half: students R003, R004
    assign_2 = StudentMentorAssignment.objects.get(mentor=mentor_2)
    assert set(assign_2.students.all()) == {students[2], students[3]}
    
    # 7. Verify double-assignment prevention constraint
    # Let's create a new batch/section
    section_b = Section.objects.create(name="B", department=dept)
    user_b = User.objects.create(email="student_b@cs.com", role="Student")
    profile_b = StudentProfile.objects.create(
        user=user_b,
        roll_no="R005",
        batch="2023-2027",
        department=dept,
        section=section_b
    )
    
    # Attempt to assign mentor_1 (who is already assigned to batch 2022-2026) to 2023-2027
    mentor_3 = User.objects.create(email="mentor3@cs.com", role="Mentor")
    mentor_3.departments.add(dept)
    
    response_double = client.post(url, {
        'action': 'assign_mentor_halves',
        'batch': '2023-2027',
        'section_id': section_b.id,
        'mentor_1_id': mentor_1.id, # Already assigned to 2022-2026!
        'mentor_2_id': mentor_3.id
    })
    
    # Should redirect, but session messages should show error
    assert response_double.status_code == 302
    # Verify assignment for mentor_1 did not change to include profile_b
    assert profile_b not in assign_1.students.all()

@pytest.mark.django_db
def test_manual_mentor_assignment_and_grouping():
    client = Client()
    
    # 1. Setup Department & HOD
    dept = Department.objects.create(name="Computer Science", code="CS")
    hod = User.objects.create(email="hod@cs.com", role="HOD")
    dept.hod = hod
    dept.save()
    
    # 2. Setup Students with None section to verify grouping handles it safely
    mentor = User.objects.create(email="mentor@cs.com", role="Mentor")
    mentor.departments.add(dept)
    
    user1 = User.objects.create(email="student1@cs.com", role="Student")
    profile1 = StudentProfile.objects.create(
        user=user1,
        roll_no="R101",
        batch="2022-2026",
        department=dept,
        section=None # null section
    )
    
    user2 = User.objects.create(email="student2@cs.com", role="Student")
    profile2 = StudentProfile.objects.create(
        user=user2,
        roll_no="R102",
        batch="2022-2026",
        department=dept,
        section=None # null section
    )
    
    # Log in HOD
    client.force_login(hod)
    
    # 3. GET HOD Dashboard to verify grouping renders safely
    url = reverse('hod-dashboard')
    response_get = client.get(url)
    assert response_get.status_code == 200
    assert "manual_students_grouped" in response_get.context
    
    # 4. Post manual assignment
    response_post = client.post(url, {
        'action': 'assign_mentor_manual',
        'mentor_id': mentor.id,
        'student_ids': [str(profile1.id), str(profile2.id)]
    })
    
    assert response_post.status_code == 302 # redirect
    
    # Verify both students assigned
    assignment = StudentMentorAssignment.objects.get(mentor=mentor)
    assert set(assignment.students.all()) == {profile1, profile2}


@pytest.mark.django_db
def test_hod_announcement_crud():
    from apps.notifications.models import Notification
    client = Client()
    dept = Department.objects.create(name="Computer Science", code="CS")
    hod = User.objects.create(email="hod@cs.com", role="HOD")
    dept.hod = hod
    dept.save()
    client.force_login(hod)
    
    # 1. Create
    url = reverse('hod-dashboard')
    response_create = client.post(url, {
        'action': 'create_announcement',
        'title': 'Test Title',
        'content': 'Test Content',
        'resource_link': 'https://example.com'
    })
    assert response_create.status_code == 302
    ann = Notification.objects.get(title='Test Title')
    assert ann.message == 'Test Content'
    assert ann.sender == hod
    
    # 2. Edit
    response_edit = client.post(url, {
        'action': 'edit_announcement',
        'announcement_id': ann.id,
        'title': 'Updated Title',
        'content': 'Updated Content',
        'resource_link': 'https://updated.com'
    })
    assert response_edit.status_code == 302
    ann.refresh_from_db()
    assert ann.title == 'Updated Title'
    assert ann.message == 'Updated Content'
    
    # 3. Delete
    response_delete = client.post(url, {
        'action': 'delete_announcement',
        'announcement_id': ann.id
    })
    assert response_delete.status_code == 302
    assert not Notification.objects.filter(id=ann.id).exists()


@pytest.mark.django_db
def test_edit_mentor_assignment():
    client = Client()
    dept = Department.objects.create(name="Computer Science", code="CS")
    hod = User.objects.create(email="hod@cs.com", role="HOD")
    dept.hod = hod
    dept.save()
    
    mentor_1 = User.objects.create(email="mentor1@cs.com", role="Mentor")
    mentor_2 = User.objects.create(email="mentor2@cs.com", role="Mentor")
    mentor_1.departments.add(dept)
    mentor_2.departments.add(dept)
    
    user1 = User.objects.create(email="student1@cs.com", role="Student")
    profile1 = StudentProfile.objects.create(
        user=user1, roll_no="R101", batch="2022-2026", department=dept
    )
    user2 = User.objects.create(email="student2@cs.com", role="Student")
    profile2 = StudentProfile.objects.create(
        user=user2, roll_no="R102", batch="2022-2026", department=dept
    )
    
    # Create initial assignment
    assignment = StudentMentorAssignment.objects.create(
        mentor=mentor_1,
        academic_year="2026-2027",
        assigned_by=hod
    )
    assignment.students.add(profile1)
    
    client.force_login(hod)
    url = reverse('hod-dashboard')
    
    # Edit: Change mentor to mentor_2, add profile2, remove profile1
    response = client.post(url, {
        'action': 'edit_mentor_assignment',
        'assignment_id': assignment.id,
        'mentor_id': mentor_2.id,
        'student_ids': [str(profile2.id)]
    })
    
    assert response.status_code == 302
    assignment.refresh_from_db()
    assert assignment.mentor == mentor_2
    assert set(assignment.students.all()) == {profile2}


@pytest.mark.django_db
def test_academic_documents_and_training_crud():
    client = Client()
    dept = Department.objects.create(name="Computer Science", code="CS")
    hod = User.objects.create(email="hod@cs.com", role="HOD")
    dept.hod = hod
    dept.save()
    
    from apps.academics.models import Subject
    subject = Subject.objects.create(name="Mathematics", code="M1", department=dept, semester=1)
    
    client.force_login(hod)
    url = reverse('hod-dashboard')
    
    # 1. LessonPlan CRUD
    from django.core.files.uploadedfile import SimpleUploadedFile
    test_file = SimpleUploadedFile("plan.pdf", b"file content", content_type="application/pdf")
    
    # Create Lesson Plan
    lp_create_res = client.post(url, {
        'action': 'upload_lesson_plan',
        'subject_id': subject.id,
        'academic_year': '2026-2027',
        'resource_link': 'https://example.com/original',
        'file': test_file
    })
    assert lp_create_res.status_code == 302
    from apps.faculty.models import LessonPlan
    lp = LessonPlan.objects.get(subject=subject)
    assert lp.resource_link == 'https://example.com/original'
    
    # Edit Lesson Plan
    lp_edit_res = client.post(url, {
        'action': 'edit_lesson_plan',
        'document_id': lp.id,
        'subject_id': subject.id,
        'academic_year': '2026-2027',
        'resource_link': 'https://example.com/edited'
    })
    assert lp_edit_res.status_code == 302
    lp.refresh_from_db()
    assert lp.resource_link == 'https://example.com/edited'
    
    # Delete Lesson Plan
    lp_delete_res = client.post(url, {
        'action': 'delete_lesson_plan',
        'document_id': lp.id
    })
    assert lp_delete_res.status_code == 302
    assert not LessonPlan.objects.filter(id=lp.id).exists()
    
    # 2. TrainingProgram CRUD
    from apps.faculty.models import TrainingProgram
    # Create training program via HOD view
    tp_create_res = client.post(url, {
        'action': 'create_training',
        'title': 'Original Training',
        'description': 'Original Desc',
        'start_date': '2026-07-20',
        'venue': 'Room 101',
        'is_active': 'on',
        'registration_link': 'https://reg.com'
    })
    assert tp_create_res.status_code == 302
    tp = TrainingProgram.objects.get(title='Original Training')
    assert tp.description == 'Original Desc'
    
    # Edit training program
    tp_edit_res = client.post(url, {
        'action': 'update_training',
        'training_id': tp.id,
        'title': 'Edited Training',
        'description': 'Edited Desc',
        'start_date': '2026-07-20',
        'venue': 'Room 102',
        'registration_link': 'https://reg-edited.com'
    })
    assert tp_edit_res.status_code == 302
    tp.refresh_from_db()
    assert tp.title == 'Edited Training'
    assert tp.venue == 'Room 102'
    assert tp.registration_link == 'https://reg-edited.com'
    
    # Delete training program
    tp_delete_res = client.post(url, {
        'action': 'delete_training',
        'training_id': tp.id
    })
    assert tp_delete_res.status_code == 302
    tp.refresh_from_db()
    assert tp.is_deleted is True


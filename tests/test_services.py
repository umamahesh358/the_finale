import pytest
from django.utils import timezone
from apps.accounts.models import User, OTPRecord
from apps.accounts.services import generate_and_send_otp, verify_otp
from apps.students.models import StudentProfile, Certification
from apps.students.services import verify_certification
from apps.academics.models import Department
from datetime import timedelta

@pytest.mark.django_db
class TestServices:
    
    def test_otp_flow(self):
        user = User.objects.create(email="test@test.com", role="Student")
        generate_and_send_otp(user, "login")
        
        record = OTPRecord.objects.get(user=user)
        assert record.is_used is False
        
        # Test valid verification
        result = verify_otp(user, record.otp_code, "login")
        assert result is True
        record.refresh_from_db()
        assert record.is_used is True

    def test_certification_verification(self):
        dept = Department.objects.create(name="CS", code="CS")
        user = User.objects.create(email="student@test.com", role="Student")
        profile = StudentProfile.objects.create(user=user, roll_no="R001", department=dept)
        cert = Certification.objects.create(
            student=profile, 
            title="Python Cert", 
            issuer="Google", 
            issued_date=timezone.now().date()
        )
        
        verifier = User.objects.create(email="faculty@test.com", role="Faculty")
        verify_certification(cert.id, verifier, True)
        
        cert.refresh_from_db()
        assert cert.is_verified is True

    def test_student_photo_upload(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.urls import reverse
        from django.test import Client

        dept = Department.objects.create(name="CS", code="CS")
        user = User.objects.create(email="student_profile@test.com", role="Student")
        profile = StudentProfile.objects.create(user=user, roll_no="R002", department=dept)

        client = Client()
        client.force_login(user)

        dummy_img = SimpleUploadedFile("avatar.jpg", b"file_content", content_type="image/jpeg")
        url = reverse('student-profile-edit')
        
        response = client.post(url, {
            'first_name': 'New',
            'last_name': 'Name',
            'photo': dummy_img
        })

        assert response.status_code == 302
        profile.refresh_from_db()
        assert profile.photo.name is not None
        assert profile.photo.name != ""
        assert profile.user.full_name == "New Name"

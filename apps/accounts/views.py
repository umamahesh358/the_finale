from django.contrib.auth import logout, login
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from apps.accounts.models import User
from apps.accounts.otp_services import create_and_send_otp, verify_otp
from apps.accounts.forms import VerifyOTPForm
from django.shortcuts import get_object_or_404
from django.conf import settings

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes
LOGIN_ROLES = ['Director', 'Examcell', 'HOD', 'Mentor', 'Faculty', 'Student', 'Parent']


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')




@method_decorator(ensure_csrf_cookie, name='get')
class LoginView(View):
    """
    Unified login: Phase 1 (Credentials)
    If successful, sends OTP and redirects to Phase 2 (Verification)
    """

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html', {})

    def post(self, request, *args, **kwargs):
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', '').strip()

        ip = get_client_ip(request)
        cache_key = f'login_attempts_{ip}'

        # ── Rate limit check ──
        attempts = cache.get(cache_key, 0)
        if attempts >= MAX_LOGIN_ATTEMPTS:
            return render(request, 'login.html', {
                'error': 'Too many login attempts. Please wait 5 minutes before trying again.',
                'identifier': identifier,
                'selected_role': role,
            })

        if not identifier or not password or not role:
            return render(request, 'login.html', {
                'error': 'Please fill in all fields and select your role.',
                'identifier': identifier,
                'selected_role': role,
            })

        if role not in LOGIN_ROLES:
            return render(request, 'login.html', {
                'error': 'Invalid role selected. Please choose a valid role.',
                'identifier': identifier,
                'selected_role': role,
            })

        # ── Look up user ──
        user = None
        student_profile = None
        if role == 'Examcell':
            if identifier.lower() != settings.EXAMCELL_LOGIN_EMAIL.lower():
                cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
                return render(request, 'login.html', {
                    'error': 'Invalid Exam Cell login ID.',
                    'identifier': identifier,
                    'selected_role': role,
                })
            user = User.objects.filter(email__iexact=settings.EXAMCELL_LOGIN_EMAIL).first()
        else:
            try:
                user = User.objects.get(email__iexact=identifier)
            except User.DoesNotExist:
                pass

        if user is None and role in ['Student', 'Parent']:
            from apps.students.models import StudentProfile
            try:
                profile = StudentProfile.objects.select_related('user').get(roll_no__iexact=identifier)
                user = profile.user
                student_profile = profile
            except StudentProfile.DoesNotExist:
                pass

        if user is None:
            cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
            return render(request, 'login.html', {
                'error': 'No account found with this ID. Contact your admin.',
                'identifier': identifier,
                'selected_role': role,
            })

        if not user.is_active:
            return render(request, 'login.html', {
                'error': 'Your account is inactive. Contact your admin.',
                'identifier': identifier,
                'selected_role': role,
            })

        is_faculty_mentor_compat = (role == 'Faculty' and user.role == 'Mentor')
        if user.role != role and not user.is_superuser and not is_faculty_mentor_compat:
            if role == 'Parent' and user.role == 'Student':
                request.session['is_parent_login'] = True
            else:
                cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
                return render(request, 'login.html', {
                    'error': f'This account is registered as {user.role}, not {role}.',
                    'identifier': identifier,
                    'selected_role': role,
                })

        # Check password policy (real credentials only)
        if role == 'Examcell':
            password_ok = password == settings.EXAMCELL_LOGIN_PASSWORD
        elif role in ['Student', 'Parent'] or user.role == 'Student':
            if student_profile is None:
                student_profile = getattr(user, 'student_profile', None)
            roll_password_ok = bool(
                student_profile and
                password.upper() == str(student_profile.roll_no).strip().upper()
            )
            password_ok = user.check_password(password) or roll_password_ok
        else:
            password_ok = user.check_password(password)

        if not password_ok:
            cache.set(cache_key, attempts + 1, LOCKOUT_SECONDS)
            remaining = MAX_LOGIN_ATTEMPTS - (attempts + 1)
            if user.is_superuser:
                error_msg = 'Incorrect password.'
            elif role == 'Examcell':
                error_msg = f'Incorrect password. Exam Cell password is {settings.EXAMCELL_LOGIN_PASSWORD}.'
            elif user.role == 'Student' or role == 'Parent':
                error_msg = 'Incorrect password. For students, password is your Register Number.'
            elif user.role in ['Faculty', 'HOD', 'Mentor']:
                error_msg = 'Incorrect password. Please use the password provided by admin.'
            else:
                error_msg = 'Incorrect password. Please use the password provided by admin.'
            if remaining <= 2 and remaining > 0:
                error_msg += f' ({remaining} attempts remaining)'
            return render(request, 'login.html', {
                'error': error_msg,
                'identifier': identifier,
                'selected_role': role,
            })

        # -- Credentials OK: start OTP phase --
        cache.delete(cache_key)

        # Superuser bypasses OTP
        if user.is_superuser:
            login(request, user)
            return redirect('/admin/')

        # Store pending user in session
        request.session['pending_user_id'] = str(user.id)
        request.session['pending_user_role'] = role

        # Send OTP (email)
        create_and_send_otp(user, 'login')

        return redirect('verify-otp')


@method_decorator(ensure_csrf_cookie, name='get')
class VerifyOTPView(View):
    def get(self, request):
        if 'pending_user_id' not in request.session:
            return redirect('login')
        
        user = get_object_or_404(User, id=request.session['pending_user_id'])
        form = VerifyOTPForm()
        return render(request, 'verify_otp.html', {'form': form, 'user_email': user.email})

    def post(self, request):
        if 'pending_user_id' not in request.session:
            return redirect('login')
        
        user = get_object_or_404(User, id=request.session['pending_user_id'])
        role = request.session.get('pending_user_role')
        form = VerifyOTPForm(request.POST)

        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            if verify_otp(user, otp_code, 'login'):
                # Success
                user.last_login_ip = get_client_ip(request)
                user.save(update_fields=['last_login_ip'])
                
                # Clean session
                del request.session['pending_user_id']
                if 'pending_user_role' in request.session:
                    del request.session['pending_user_role']
                
                login(request, user)
                # Route students directly to their portal
                if user.role == 'Student':
                    return redirect('student-portal')
                return redirect('dashboard')
            else:
                form.add_error('otp', 'Invalid or expired OTP code.')
        
        return render(request, 'verify_otp.html', {'form': form, 'user_email': user.email})


class LogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('login'))

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse_lazy('login'))

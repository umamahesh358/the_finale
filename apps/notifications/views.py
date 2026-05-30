from django.shortcuts import render, redirect, get_list_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.contrib import messages
from django.db.models import Q
from .models import Notification, NotificationRecipient
from apps.academics.models import Department


class NotificationListView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        user_departments = list(user.departments.all())
        if user.role == 'HOD' and not user_departments:
            hod_dept = Department.objects.filter(hod=user).first()
            if hod_dept:
                user_departments = [hod_dept]
        if user.role == 'Student' and hasattr(user, 'student_profile'):
            user_departments = [user.student_profile.department]
        if user.role == 'Parent' and hasattr(user, 'parent_profile'):
            user_departments = list(
                Department.objects.filter(students__parents=user.parent_profile).distinct()
            )

        dept_filter = Q(target_department__isnull=True)
        if user_departments:
            dept_filter = dept_filter | Q(target_department__in=user_departments)
        # Filters: Global OR (targeted role AND targeted/null department)
        notifications = Notification.objects.filter(
            Q(is_global=True) |
            (
                (Q(target_role='All') | Q(target_role=user.role)) &
                dept_filter
            )
        ).distinct().order_by('-created_at')

        context = {
            'notifications': notifications,
            'departments': Department.objects.all(),
            'user_departments': user_departments,
        }
        if user.role == 'Student' and hasattr(user, 'student_profile'):
            context['profile'] = user.student_profile
            
        return render(request, 'notifications/list.html', context)

class MarkAsReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk)
        NotificationRecipient.objects.get_or_create(
            user=request.user, 
            notification=notification,
            defaults={'is_read': True}
        )
        return redirect('notification-list')

class CreateNotificationView(LoginRequiredMixin, View):
    def post(self, request):
        # Strict permission check: Director can post anything, HOD can post to their department
        if not (request.user.is_superuser or request.user.role in ['Director', 'HOD']):
            messages.error(request, "Unauthorized to post notifications.")
            return redirect('dashboard')
            
        title = request.POST.get('title')
        message = request.POST.get('message')
        target_role = request.POST.get('target_role', 'All')
        is_global = request.POST.get('is_global') == 'on'
        
        # HOD restriction: can only post to their own department if not global
        dept_id = request.POST.get('department')
        if request.user.role == 'HOD' and not is_global:
            target_dept = Department.objects.filter(hod=request.user).first()
        elif dept_id:
            target_dept = Department.objects.filter(id=dept_id).first()
        else:
            target_dept = None

        Notification.objects.create(
            sender=request.user,
            title=title,
            message=message,
            target_role=target_role,
            target_department=target_dept,
            is_global=is_global if (request.user.is_superuser or request.user.role == 'Director') else False # Only Director can post global
        )
        
        messages.success(request, "Notification sent successfully.")
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from apps.core.models import Announcement, Event
from django.views import View

class DashboardView(View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            announcements = Announcement.objects.filter(is_active=True).order_by('category', '-created_at')
            news = announcements.filter(category='News')[:5]
            exams = announcements.filter(category='Exam')[:5]
            success_stories = announcements.filter(category='Event')[:5]
            
            return render(request, 'HOMEPAGE2.01/HOMEPAGE2.0/demo.html', {
                'news': news,
                'exams': exams,
                'success_stories': success_stories
            })

        role = request.user.role
        if role == 'Student':
            if request.session.get('is_parent_login'):
                return redirect('parent-portal')
            return redirect('student-portal')
        if role == 'Examcell':
            return redirect('student-verification-queue')
        if role == 'Director':
            return redirect('/admin/')
        if role in ['Faculty', 'Mentor', 'HOD']:
            role_redirect = {'HOD': 'hod-dashboard', 'Mentor': 'faculty-dashboard', 'Faculty': 'faculty-dashboard'}
            return redirect(role_redirect.get(role, 'faculty-dashboard'))
        if role == 'Parent':
            return redirect('parent-portal')
        return redirect('login')



class StudentListView(LoginRequiredMixin, TemplateView):
    template_name = 'students_list.html'


class FacultyListView(LoginRequiredMixin, TemplateView):
    template_name = 'faculty/faculty_dashboard.html'


class EventListView(LoginRequiredMixin, View):
    def get(self, request):
        events = Event.objects.filter(is_active=True)
        return render(request, 'events/event_list.html', {'events': events})


class EventCreateView(LoginRequiredMixin, UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.role in ['Director', 'HOD']

    def get(self, request):
        return render(request, 'events/event_form.html')

    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description')
        date = request.POST.get('date')
        location = request.POST.get('location')
        
        Event.objects.create(
            title=title,
            description=description,
            date=date,
            location=location,
            created_by=request.user
        )
        return redirect('event-list')

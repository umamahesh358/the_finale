from django.urls import path
from django.views.generic import RedirectView
from apps.faculty import views

# ── Faculty Portal UI URLs ──────────────────────────────────────────────────
ui_urlpatterns = [
    path('hod/',     views.HODDashboardView.as_view(),    name='hod-dashboard'),
    path('mentor/',  RedirectView.as_view(url='/faculty-portal/portal/mentoring/', permanent=False), name='mentor-dashboard'),
    path('portal/',  views.FacultyDashboardView.as_view(), name='faculty-dashboard'),
    path('portal/mentoring/', views.FacultyHubMentoringView.as_view(), name='faculty-mentor'),
    path('portal/cohorts/', views.FacultyHubCohortsView.as_view(), name='faculty-cohorts'),
    path('portal/explore-students/', views.FacultyHubExploreStudentsView.as_view(), name='faculty-explore-students'),
    path('portal/hod-updates/', views.FacultyHubHodUpdatesView.as_view(), name='faculty-hod-updates'),
    path('portal/courses/', views.FacultyHubCoursesView.as_view(), name='faculty-courses'),
    path('portal/institution-courses/', views.FacultyHubInstitutionCoursesView.as_view(), name='faculty-institution-courses'),
    path('portal/settings/', views.FacultyHubSettingsView.as_view(), name='faculty-settings'),
    path('courses/<str:course_id>/score-template/',
         views.download_score_template, name='score-template-download'),
]

# ── Legacy API URLs (kept for backward compat) ─────────────────────────────
urlpatterns = [
    path('subjects/',      views.FacultySubjectsView.as_view(),      name='faculty-subjects'),
    path('pending-certs/', views.PendingCertificationsView.as_view(), name='pending-certs'),
]

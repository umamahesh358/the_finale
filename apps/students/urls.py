from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.students import views

# ── API Router (under /api/v1/students/) ───────────────────
router = DefaultRouter()
router.register(r'profiles', views.StudentProfileViewSet, basename='student-profile')

# ── UI URLs (under /student/) ──────────────────────────────
ui_urlpatterns = [
    path('portal/',               views.StudentPortalView.as_view(),        name='student-portal'),
    path('portal/portfolio/',     views.StudentPortfolioView.as_view(),     name='student-portfolio'),
    path('portal/profile/',       views.StudentProfileEditView.as_view(),   name='student-profile-edit'),
    path('portal/academics/',     views.StudentAcademicsView.as_view(),     name='student-academics'),
    path('portal/certifications/', views.StudentCertificationsView.as_view(), name='student-certifications'),
    path('portal/projects/',      views.StudentProjectsView.as_view(),      name='student-projects'),
    path('portal/internships/',   views.StudentInternshipsView.as_view(),   name='student-internships'),
    path('portal/events/',        views.StudentEventsView.as_view(),        name='student-events'),
    path('portal/courses/',       views.StudentCoursesView.as_view(),       name='student-courses'),
    path('portal/research/',      views.StudentResearchView.as_view(),      name='student-research'),
    path('portal/education/',     views.StudentEducationView.as_view(),     name='student-education'),
    path('portal/contact-otp/',   views.StudentContactOtpView.as_view(),    name='student-contact-otp'),
    path('portal/toggle-public/', views.TogglePublicProfileView.as_view(),  name='student-toggle-public'),
    path('verification/queue/',   views.StudentVerificationQueueView.as_view(), name='student-verification-queue'),
    path('detail/<uuid:pk>/',     views.StudentManagementDetailView.as_view(), name='student-detail'),
    path('p/<slug:slug>/',        views.PublicStudentProfileView.as_view(), name='student-public-profile'),
]

# API-only patterns
urlpatterns = [path('', include(router.urls))]

from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    StaffViewSet,
    SpecializationViewSet,
    WorkingDayViewSet,
    DoctorDetailsViewSet,
    DoctorWorkingScheduleViewSet,
    AdminDashboard,
    LeaveRequestViewSet,  # New import for LeaveRequestViewSet
)

router = DefaultRouter()
router.register(r'staff', StaffViewSet)
router.register(r'specializations', SpecializationViewSet)
router.register(r'working-days', WorkingDayViewSet)
router.register(r'doctor-details', DoctorDetailsViewSet)         
router.register(r'doctor-schedules', DoctorWorkingScheduleViewSet)  
router.register(r'leave-requests', LeaveRequestViewSet)  # New endpoint for leave requests

urlpatterns = [
    path("dashboard/", AdminDashboard.as_view()),  # ✅ add function-based endpoint
]

urlpatterns += router.urls
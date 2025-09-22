from rest_framework.routers import DefaultRouter
from .views import (
    StaffViewSet,
    SpecializationViewSet,
    WorkingDayViewSet,
    DoctorDetailsViewSet,
    DoctorWorkingScheduleViewSet,
)

router = DefaultRouter()
router.register(r'staff', StaffViewSet)
router.register(r'specializations', SpecializationViewSet)
router.register(r'working-days', WorkingDayViewSet)
router.register(r'doctor-details', DoctorDetailsViewSet)         
router.register(r'doctor-schedules', DoctorWorkingScheduleViewSet)  

urlpatterns = router.urls

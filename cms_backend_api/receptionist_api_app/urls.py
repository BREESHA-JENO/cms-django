# receptionist_api_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, AppointmentViewSet, RecBillingViewSet, MyAppointmentsViewSet
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register('patients', PatientViewSet, basename='patients')
router.register('appointments', AppointmentViewSet, basename='appointments')
router.register('billing', RecBillingViewSet, basename='billing')
router.register('my-appointments', MyAppointmentsViewSet, basename='my-appointments')

urlpatterns = router.urls

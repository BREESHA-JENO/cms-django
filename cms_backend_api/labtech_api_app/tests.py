from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from .models import LabTestCategory, LabTest, LabResult, LabBilling
from .serializers import (
    LabTestCategorySerializer,
    LabTestSerializer,
    LabResultSerializer,
    LabBillingSerializer,
)
from django.utils import timezone


class LabTestCategoryViewSetTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.cat1 = LabTestCategory.objects.create(CategoryName="Blood Test")
        cls.cat2 = LabTestCategory.objects.create(CategoryName="Urine Test")

    def setUp(self):
        self.client = APIClient()

    def test_category_list(self):
        url = reverse("labtestcategory-list")
        response = self.client.get(url)
        serializer = LabTestCategorySerializer(LabTestCategory.objects.all(), many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_category_create(self):
        url = reverse("labtestcategory-list")
        data = {"CategoryName": "X-Ray"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LabTestCategory.objects.count(), 3)


class LabTestViewSetTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = LabTestCategory.objects.create(CategoryName="Blood Test")
        cls.test1 = LabTest.objects.create(LabTestName="Glucose", CategoryId=cls.category, Rate=200.00)
        cls.test2 = LabTest.objects.create(LabTestName="Cholesterol", CategoryId=cls.category, Rate=300.00)

    def setUp(self):
        self.client = APIClient()

    def test_labtest_list(self):
        url = reverse("labtest-list")
        response = self.client.get(url)
        serializer = LabTestSerializer(LabTest.objects.all(), many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

    def test_labtest_create(self):
        url = reverse("labtest-list")
        data = {"LabTestName": "Hemoglobin", "CategoryId": self.category.CategoryId, "Rate": 150.00}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LabTest.objects.count(), 3)


class LabResultViewSetTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.category = LabTestCategory.objects.create(CategoryName="Blood Test")
        cls.test = LabTest.objects.create(LabTestName="Glucose", CategoryId=cls.category, Rate=200.00)
        # For simplicity, use a dummy ID for PrescriptionLab foreign key
        from doctor_api_app.models import PrescriptionLab
        cls.prescription = PrescriptionLab.objects.create(PatientId=1, DoctorId=1)  
        cls.result = LabResult.objects.create(TestId=cls.test, Status="Pending", LabPrescriptionId=cls.prescription)

    def setUp(self):
        self.client = APIClient()

    def test_result_list(self):
        url = reverse("labresult-list")
        response = self.client.get(url)
        serializer = LabResultSerializer(LabResult.objects.all(), many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)


class LabBillingViewSetTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        from doctor_api_app.models import PrescriptionLab
        cls.prescription = PrescriptionLab.objects.create(PatientId=1, DoctorId=1)
        cls.bill = LabBilling.objects.create(LabPrescriptionId=cls.prescription, Amount=500.00)

    def setUp(self):
        self.client = APIClient()

    def test_billing_list(self):
        url = reverse("labbilling-list")
        response = self.client.get(url)
        serializer = LabBillingSerializer(LabBilling.objects.all(), many=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, serializer.data)

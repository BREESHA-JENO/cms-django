import re
from datetime import date
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.utils import timezone
from rest_framework import serializers

from .models import Staff, DoctorDetails, Specialization, WorkingDay, DoctorWorkingSchedule

User = get_user_model()


# ----------------------------
# User summary
# ----------------------------
class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "role"]


# ----------------------------
# Specialization
# ----------------------------
class SpecializationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialization
        fields = ['id', 'name']


# ----------------------------
# Working Day
# ----------------------------
class WorkingDaySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkingDay
        fields = ["id", "name"]


# ----------------------------
# Doctor Working Schedule
# ----------------------------
class DoctorWorkingScheduleSerializer(serializers.ModelSerializer):
    day = WorkingDaySerializer(read_only=True)
    day_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkingDay.objects.all(),
        source="day",
        write_only=True
    )

    class Meta:
        model = DoctorWorkingSchedule
        fields = ["id", "day", "day_id", "start_time", "end_time"]


# ----------------------------
# Doctor Details
# ----------------------------
class DoctorDetailsSerializer(serializers.ModelSerializer):
    specialization = SpecializationSerializer(read_only=True)
    specialization_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialization.objects.all(),
        source="specialization",
        write_only=True
    )
    specialization_name = serializers.CharField(source="specialization.name", read_only=True)
    schedules = DoctorWorkingScheduleSerializer(many=True, required=False)

    class Meta:
        model = DoctorDetails
        fields = [
            "specialization",
            "specialization_id",
            "specialization_name",
            "consultation_fee",
            "schedules",
        ]
        read_only_fields = ["staff"]

    def validate_consultation_fee(self, value):
        if value < 100:
            raise serializers.ValidationError("Consultation fee must be at least 100.")
        return value


# ----------------------------
# Staff Serializer
# ----------------------------
class StaffSerializer(serializers.ModelSerializer):
    doctor_details = DoctorDetailsSerializer(required=False)
    user_info = UserSummarySerializer(source="user", read_only=True)
    role = serializers.CharField(write_only=True)
    generated_password = serializers.CharField(read_only=True)

    class Meta:
        model = Staff
        fields = [
            'id',
            'staff_id',
            'user_info',
            'name',
            'blood_group',
            'email',
            'address',
            'phone_number',
            'dob',
            'gender',
            'date_of_joining',
            'role',
            'doctor_details',
            'generated_password'
        ]
        read_only_fields = ['staff_id', 'date_of_joining']

    # ---------- FIELD VALIDATIONS ----------
    def validate_name(self, value):
        if not re.match(r'^[A-Za-z\s]+$', value):
            raise serializers.ValidationError("Name should contain only alphabets and spaces.")
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long.")
        return value

    def validate_blood_group(self, value):
        valid_groups = {"A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"}
        if value.upper() not in valid_groups:
            raise serializers.ValidationError("Invalid blood group.")
        return value.upper()

    def validate_email(self, value):
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", value):
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_phone_number(self, value):
        if not re.match(r'^[6-9]\d{9}$', str(value)):
            raise serializers.ValidationError("Phone number must be 10 digits and start with 6,7,8, or 9.")
        return value

    def validate_gender(self, value):
        valid_genders = {"Male", "Female", "Other"}
        if value not in valid_genders:
            raise serializers.ValidationError("Gender must be 'Male', 'Female', or 'Other'.")
        return value

    # ---------- OBJECT LEVEL VALIDATION ----------
    def validate(self, attrs):
        dob = attrs.get("dob")
        role = attrs.get("role")

        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if role == "DOC" and (age < 25 or age > 80):
                raise serializers.ValidationError({"dob": "Doctor's age must be between 25 and 80."})
            elif role != "DOC" and (age < 18 or age > 80):
                raise serializers.ValidationError({"dob": "Staff age must be between 18 and 80."})

        doctor_data = self.initial_data.get("doctor_details")
        if role == "DOC" and not doctor_data:
            raise serializers.ValidationError({"doctor_details": "Doctor details are required for Doctor role."})
        if role != "DOC" and doctor_data:
            raise serializers.ValidationError({"doctor_details": "Doctor details allowed only for Doctor role."})

        return attrs

    # ---------- CREATE ----------
    def create(self, validated_data):
        doctor_data = validated_data.pop("doctor_details", None)
        role = validated_data.pop("role")

        email = validated_data["email"]

        # Check duplicate user
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})

        # Create User
        password = get_random_string(8)
        user = User.objects.create(
            username=email,
            email=email,
            role=role.upper(),
            password=make_password(password),
        )
        validated_data["user"] = user

        # Ensure date_of_joining
        if not validated_data.get("date_of_joining"):
            validated_data["date_of_joining"] = timezone.now().date()

        staff = Staff.objects.create(**validated_data)

        if role.upper() == "DOC" and doctor_data:
            schedules_data = doctor_data.pop("schedules", [])
            doctor = DoctorDetails.objects.create(staff=staff, **doctor_data)
            for schedule_data in schedules_data:
                DoctorWorkingSchedule.objects.create(doctor=doctor, **schedule_data)

        staff.generated_password = password
        return staff

    # ---------- UPDATE ----------
    def update(self, instance, validated_data):
        doctor_data = validated_data.pop("doctor_details", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instance.user.role == "DOC":
            if doctor_data:
                schedules_data = doctor_data.pop("schedules", None)
                doctor_details, _ = DoctorDetails.objects.get_or_create(staff=instance)
                for attr, value in doctor_data.items():
                    setattr(doctor_details, attr, value)
                doctor_details.save()

                if schedules_data is not None:
                    doctor_details.schedules.all().delete()
                    for schedule_data in schedules_data:
                        DoctorWorkingSchedule.objects.create(doctor=doctor_details, **schedule_data)
            else:
                raise serializers.ValidationError({"doctor_details": "Doctor details required for DOC."})
        else:
            DoctorDetails.objects.filter(staff=instance).delete()

        return instance

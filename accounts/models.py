from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """مدير المستخدم المخصص: يعتمد البريد الإلكتروني كمعرّف وحيد."""

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    مستخدم مخصص (Custom User):
    - تسجيل الدخول بالبريد الإلكتروني
    - يدعم صلاحيات الموظفين والسوبر أدمن
    """

    email = models.EmailField("البريد الإلكتروني", unique=True, db_index=True)
    first_name = models.CharField("الاسم الأول", max_length=60, blank=True)
    last_name = models.CharField("اسم العائلة", max_length=60, blank=True)

    phone_regex = RegexValidator(
        regex=r"^\+?\d{7,15}$",
        message="Phone must be numeric and can start with +, length 7-15.",
    )
    phone = models.CharField("رقم الجوال", max_length=20, blank=True, validators=[phone_regex])

    is_active = models.BooleanField("نشط", default=True)
    is_staff = models.BooleanField("موظف", default=False)

    date_joined = models.DateTimeField("تاريخ التسجيل", default=timezone.now)
    last_updated = models.DateTimeField("آخر تحديث", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

    def __str__(self) -> str:
        name = (self.first_name + " " + self.last_name).strip()
        return name or self.email


class CustomerProfile(models.Model):
    """بيانات إضافية للعميل (اختياري)."""

    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile", verbose_name="المستخدم")
    marketing_opt_in = models.BooleanField("الموافقة على رسائل التسويق", default=False)
    notes = models.TextField("ملاحظات", blank=True)

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "ملف عميل"
        verbose_name_plural = "ملفات العملاء"

    def __str__(self) -> str:
        return f"Profile({self.user_id})"


class Address(models.Model):
    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "عنوان شحن"
        BILLING = "billing", "عنوان فواتير"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="addresses", verbose_name="المستخدم")
    address_type = models.CharField("نوع العنوان", max_length=10, choices=AddressType.choices, default=AddressType.SHIPPING)

    full_name = models.CharField("الاسم الكامل", max_length=120)
    phone = models.CharField("رقم الجوال", max_length=20, blank=True)

    country = models.CharField("الدولة", max_length=60, default="Saudi Arabia")
    city = models.CharField("المدينة", max_length=60)
    district = models.CharField("الحي", max_length=80, blank=True)
    street = models.CharField("الشارع", max_length=120)
    building = models.CharField("رقم المبنى/الوحدة", max_length=40, blank=True)
    postal_code = models.CharField("الرمز البريدي", max_length=20, blank=True)

    is_default = models.BooleanField("افتراضي", default=False)

    created_at = models.DateTimeField("تاريخ الإنشاء", auto_now_add=True)
    updated_at = models.DateTimeField("آخر تحديث", auto_now=True)

    class Meta:
        verbose_name = "عنوان"
        verbose_name_plural = "العناوين"
        indexes = [
            models.Index(fields=["user", "address_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city}"

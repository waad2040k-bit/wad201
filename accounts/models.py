from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager using email as the unique identifier."""

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
    Minimal but production-ready custom user.
    - Uses email for login
    - Supports staff/superuser
    """

    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=60, blank=True)
    last_name = models.CharField(max_length=60, blank=True)

    phone_regex = RegexValidator(
        regex=r"^\+?\d{7,15}$",
        message="Phone must be numeric and can start with +, length 7-15.",
    )
    phone = models.CharField(max_length=20, blank=True, validators=[phone_regex])

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        name = (self.first_name + " " + self.last_name).strip()
        return name or self.email


class CustomerProfile(models.Model):
    """
    Optional extra info for customers.
    Keep it lightweight; you can extend later.
    """
    user = models.OneToOneField("accounts.User", on_delete=models.CASCADE, related_name="profile")
    marketing_opt_in = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile({self.user_id})"


class Address(models.Model):
    class AddressType(models.TextChoices):
        SHIPPING = "shipping", "Shipping"
        BILLING = "billing", "Billing"

    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=10, choices=AddressType.choices, default=AddressType.SHIPPING)

    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=20, blank=True)

    country = models.CharField(max_length=60, default="Saudi Arabia")
    city = models.CharField(max_length=60)
    district = models.CharField(max_length=80, blank=True)
    street = models.CharField(max_length=120)
    building = models.CharField(max_length=40, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "address_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.city}"

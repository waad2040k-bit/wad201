from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone


class Cart(models.Model):
    """
    Cart can be:
    - linked to a user (logged in)
    - or identified by session key (guest)
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name="carts")
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["session_key"]),
        ]

    def __str__(self) -> str:
        return f"Cart({self.id})"

    def subtotal(self) -> Decimal:
        total = Decimal("0.00")
        for item in self.items.all():
            total += item.line_total()
        return total


class CartItem(models.Model):
    cart = models.ForeignKey("sales.Cart", on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("cart", "variant")]
        indexes = [
            models.Index(fields=["cart", "variant"]),
        ]

    def __str__(self) -> str:
        return f"CartItem(cart={self.cart_id}, sku={self.variant.sku})"

    def line_total(self) -> Decimal:
        return (self.variant.price or Decimal("0.00")) * Decimal(self.quantity)


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders")

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    placed_at = models.DateTimeField(default=timezone.now)

    # Snapshot fields (أفضل من ربط Address مباشرة في الطلب)
    shipping_name = models.CharField(max_length=120)
    shipping_phone = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=60, default="Saudi Arabia")
    shipping_city = models.CharField(max_length=60)
    shipping_district = models.CharField(max_length=80, blank=True)
    shipping_street = models.CharField(max_length=120)
    shipping_building = models.CharField(max_length=40, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)

    notes = models.TextField(blank=True)

    currency = models.CharField(max_length=10, default="SAR")

    # Totals (stored for auditing)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "placed_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Order({self.id}) - {self.status}"

    def recalc_totals(self) -> None:
        subtotal = Decimal("0.00")
        for item in self.items.all():
            subtotal += item.line_total()

        self.subtotal_amount = subtotal
        # total = subtotal + shipping - discount
        self.total_amount = (self.subtotal_amount + self.shipping_amount) - self.discount_amount

    def mark_paid(self) -> None:
        self.status = self.Status.PAID
        self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey("sales.Order", on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items")

    # Snapshot of product data at purchase time
    sku = models.CharField(max_length=50)
    product_name = models.CharField(max_length=140)
    attributes = models.JSONField(default=dict, blank=True)

    unit_price = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        indexes = [
            models.Index(fields=["order", "sku"]),
        ]

    def __str__(self) -> str:
        return f"OrderItem(order={self.order_id}, sku={self.sku})"

    def line_total(self) -> Decimal:
        return self.unit_price * Decimal(self.quantity)


class Payment(models.Model):
    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        AUTHORIZED = "authorized", "Authorized"
        CAPTURED = "captured", "Captured"   # paid
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.ForeignKey("sales.Order", on_delete=models.CASCADE, related_name="payments")

    provider = models.CharField(max_length=40)  # e.g. "moyasar", "stripe", "tap"
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.INITIATED)

    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.00"))])
    currency = models.CharField(max_length=10, default="SAR")

    # Store provider IDs safely (no secrets)
    provider_payment_id = models.CharField(max_length=120, blank=True, db_index=True)
    failure_reason = models.CharField(max_length=250, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["provider", "provider_payment_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Payment({self.id}) {self.provider} {self.status}"


class Shipment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    order = models.OneToOneField("sales.Order", on_delete=models.CASCADE, related_name="shipment")
    carrier = models.CharField(max_length=60, blank=True)  # e.g. "Aramex", "SMSA"
    tracking_number = models.CharField(max_length=80, blank=True, db_index=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tracking_number"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"Shipment(order={self.order_id})"

from django.contrib import admin

from .models import Cart, CartItem, Order, OrderItem, Payment, Shipment


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    fields = ("variant", "quantity", "added_at")
    readonly_fields = ("added_at",)
    autocomplete_fields = ("variant",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "session_key", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("id", "user__email", "session_key")
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("cart", "variant", "quantity", "added_at")
    search_fields = ("cart__id", "variant__sku", "variant__product__name")


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("sku", "product_name", "unit_price", "quantity")
    readonly_fields = ("sku", "product_name", "unit_price")
    show_change_link = True


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ("provider", "status", "amount", "currency", "provider_payment_id", "updated_at")
    readonly_fields = ("updated_at",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "total_amount", "currency", "placed_at", "updated_at")
    list_filter = ("status", "currency", "placed_at")
    search_fields = ("id", "customer__email", "shipping_name", "shipping_phone", "shipping_city")
    date_hierarchy = "placed_at"
    inlines = [OrderItemInline, PaymentInline]
    readonly_fields = ("placed_at", "updated_at")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "sku", "product_name", "unit_price", "quantity")
    search_fields = ("order__id", "sku", "product_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "provider", "status", "amount", "currency", "provider_payment_id", "updated_at")
    list_filter = ("provider", "status", "currency")
    search_fields = ("order__id", "provider_payment_id")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ("order", "carrier", "tracking_number", "status", "shipped_at", "delivered_at", "updated_at")
    list_filter = ("status", "carrier")
    search_fields = ("order__id", "tracking_number", "carrier")
    readonly_fields = ("updated_at",)

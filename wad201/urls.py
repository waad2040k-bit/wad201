from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # Local apps
    path("accounts/", include("accounts.urls")),
    path("catalog/", include("catalog.urls")),
    path("sales/", include("sales.urls")),
]

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # اجعل الكتالوج هو الرئيسي (الجذر)
    path("", include("catalog.urls")),

    # باقي التطبيقات تبقى بمساراتها
    path("accounts/", include("accounts.urls")),
    path("sales/", include("sales.urls")),
]

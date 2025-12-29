from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# (اختياري) تعريب عناوين لوحة التحكم
admin.site.site_header = "لوحة إدارة المتجر"
admin.site.site_title = "إدارة المتجر"
admin.site.index_title = "التحكم والإعدادات"

urlpatterns = [
    path("admin/", admin.site.urls),

    # اجعل الكتالوج هو الرئيسي (الجذر)
    path("", include("catalog.urls")),

    # باقي التطبيقات تبقى بمساراتها
    path("accounts/", include("accounts.urls")),
    path("sales/", include("sales.urls")),
]

# عرض ملفات media أثناء التطوير فقط
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

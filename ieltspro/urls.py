from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from main.views import custom_page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main.urls")),
    path("edu/", include('materials.urls'))
] 

if not settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]

handler404 = 'main.views.custom_page_not_found'
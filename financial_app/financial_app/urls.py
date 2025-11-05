from django.contrib import admin
from django.urls import path, include
from accounts.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('accounts.urls')),
    path('', HomeView.as_view(), name='root'),  # Fix for 404 on /
]
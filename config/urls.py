
from django.contrib import admin
from django.urls import path, include
from games.views import home_page  # <--- ini yang penting!

urlpatterns = [
    path('', home_page, name='home'),  # <--- arahkan / ke home_page view Anda
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('games/', include(('games.urls', 'games'), namespace='games')),
]


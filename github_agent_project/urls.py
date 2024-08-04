# github_agent_project/urls.py

from django.contrib import admin
from django.urls import path
from github_agent.views import get_recommendations

urlpatterns = [
    path('admin/', admin.site.urls),
    path('get_recommendations/', get_recommendations, name='get_recommendations'),
    path('', get_recommendations, name='index'),  # Pointing to your index view
]
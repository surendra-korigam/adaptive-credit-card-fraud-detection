from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.urls import path
from monitor import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("accounts/logout/", LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("api/stats/", views.stats, name="stats"),
    path("api/transactions/", views.transactions, name="transactions"),
    path("api/stream/start/", views.start_stream, name="start_stream"),
    path("api/stream/stop/", views.stop_stream, name="stop_stream"),
    path("api/score/", views.score_transaction, name="score"),
    path("api/feedback/", views.feedback, name="feedback"),
]

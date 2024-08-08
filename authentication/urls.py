from django.urls import path
from . import views

urlpatterns = [
    path("register/",views.register_user,name="register_user"),
    path("login/",views.login_user,name="login_user"),
    path("verify-email/",views.verify_email,name="verify-email"),
    path("refresh_token/",views.refresh_token,name="refresh-token"),
    path("userInfo/",views.get_user_info,name="user_info")
]

from django.urls import path
from . import views

urlpatterns = [

    path(
        'signup/',
        views.signup_view,
        name='signup'
    ),

    path(
        'login/',
        views.login_view,
        name='login'
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout'
    ),

    path(
        'user-profile/',
        views.user_profile_api,
        name='user-profile'
    ),
    path(
        'user-profile/update/',
        views.update_profile_api,
        name='update-user-profile'
    ),

]
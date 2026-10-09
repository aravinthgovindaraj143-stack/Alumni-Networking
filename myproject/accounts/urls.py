from django.urls import path
from . import views


urlpatterns = [

    # HOME
    path(
        "",
        views.home_view,
        name="home"
    ),

    path(
        "home/",
        views.home_view,
        name="home"
    ),


    # MAIN PAGES
    path(
        "about/",
        views.about_view,
        name="about"
    ),

    path(
        "directory/",
        views.directory_view,
        name="directory"
    ),

    path(
        "scholarships/",
        views.scholarships_view,
        name="scholarships"
    ),

    path(
        "events/",
        views.events_view,
        name="events"
    ),

    path(
        "jobs/",
        views.jobs_view,
        name="jobs"
    ),

    path(
        "mentorship/",
        views.mentorship_view,
        name="mentorship"
    ),


    # REGISTRATION
    path(
        "register/",
        views.register_view,
        name="register"
    ),

    path(
        "send-otp/",
        views.send_otp,
        name="send_otp"
    ),

    path(
        "verify-otp/",
        views.verify_otp,
        name="verify_otp"
    ),


    # LOGIN
    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),
    path(
        "alumni/<str:register_number>/",
          views.alumni_profile_view,
        name="alumni_profile"
    ),
    path(
        "alumni/<str:register_number>/",
        views.similar_alumni_view,
        name="similar_alumni"
    ),
    path(
        "alumni/<str:register_number>/recommended/",
        views.recommended_alumni_view,
        name="recommended_alumni"
    )

]
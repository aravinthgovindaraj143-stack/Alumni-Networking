from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # HOME
    # =====================================================

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


    # =====================================================
    # MAIN PAGES
    # =====================================================

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
        "events/",
        views.events_view,
        name="events"
    ),

    path(
        "events/<int:event_id>/register/",
        views.event_register_view,
        name="event_register"
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


    # =====================================================
    # REGISTRATION
    # =====================================================

    path(
        "register/",
        views.register_view,
        name="register"
    ),

    # Existing OTP URL
    path(
        "send-otp/",
        views.send_otp,
        name="send_otp"
    ),

    # Existing OTP URL
    path(
        "verify-otp/",
        views.verify_otp,
        name="verify_otp"
    ),

    # -----------------------------------------------------
    # NEW REGISTRATION OTP URLS
    #
    # These are required by register.html:
    #
    # {% url 'send_registration_otp' %}
    # {% url 'verify_registration_otp' %}
    # -----------------------------------------------------

    path(
        "register/send-otp/",
        views.send_registration_otp,
        name="send_registration_otp"
    ),

    path(
        "register/verify-otp/",
        views.verify_registration_otp,
        name="verify_registration_otp"
    ),


    # =====================================================
    # LOGIN
    # =====================================================

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "login-count/",
        views.login_count_view,
        name="login_count"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),


    # =====================================================
    # ALUMNI PROFILE
    # =====================================================

    path(
        "alumni/<str:register_number>/",
        views.alumni_profile_view,
        name="alumni_profile"
    ),

    path(
        "alumni/<str:register_number>/similar/",
        views.similar_alumni_view,
        name="similar_alumni"
    ),

    path(
        "alumni/<str:register_number>/recommended/",
        views.recommended_alumni_view,
        name="recommended_alumni"
    ),

]
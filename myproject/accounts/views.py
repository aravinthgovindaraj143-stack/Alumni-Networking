from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

import random
import time

from datetime import datetime

from .models import Alumni


# =========================================================
# HOME
# =========================================================

def home_view(request):

    alumni = None
    display_name = "Guest"

    alumni_id = request.session.get("alumni_id")

    if alumni_id:

        try:
            alumni = Alumni.objects.get(
                id=alumni_id
            )

            display_name = alumni.full_name

        except Alumni.DoesNotExist:

            request.session.flush()

            alumni = None
            display_name = "Guest"

    total_alumni = Alumni.objects.count()

    active_alumni = total_alumni

    context = {

        "alumni": alumni,

        "display_name": display_name,

        "total_alumni": total_alumni,

        "active_alumni": active_alumni,

        "total_members": total_alumni,

        "active_members": active_alumni,

        "total_logins": request.session.get(
            "total_logins",
            0
        ),

    }

    return render(
        request,
        "accounts/home.html",
        context
    )


# =========================================================
# LOGIN
#
# Username = Register Number
# Password = shc
# =========================================================

def login_view(request):

    # =====================================================
    # ALREADY LOGGED IN
    # =====================================================

    if request.session.get("alumni_id"):

        return redirect("register")


    # =====================================================
    # LOGIN POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # REGISTER NUMBER
        # =================================================

        register_number = request.POST.get(
            "register_number",
            ""
        ).strip()


        # Support old HTML:
        # name="username"

        if not register_number:

            register_number = request.POST.get(
                "username",
                ""
            ).strip()


        register_number = register_number.upper()


        # =================================================
        # PASSWORD
        # =================================================

        password = request.POST.get(
            "password",
            ""
        ).strip()


        # =================================================
        # CHECK REGISTER NUMBER
        # =================================================

        if not register_number:

            messages.error(
                request,
                "Please enter your Register Number."
            )

            return redirect("login")


        # =================================================
        # CHECK PASSWORD
        # =================================================

        if not password:

            messages.error(
                request,
                "Please enter your password."
            )

            return redirect("login")


        # =================================================
        # COMMON PASSWORD
        # =================================================

        COMMON_PASSWORD = "shc"


        if password != COMMON_PASSWORD:

            messages.error(
                request,
                "Invalid Register Number or Password."
            )

            return redirect("login")


        # =================================================
        # FIND ALUMNI
        # =================================================

        try:

            alumni = Alumni.objects.get(
                register_number__iexact=register_number
            )

        except Alumni.DoesNotExist:

            messages.error(
                request,
                "Invalid Register Number or Password."
            )

            return redirect("login")


        # =================================================
        # LOGIN SUCCESS
        # =================================================

        request.session["alumni_id"] = alumni.id

        request.session["alumni_name"] = (
            alumni.full_name
        )

        request.session["alumni_register_number"] = (
            alumni.register_number
        )

        request.session["alumni_email"] = (
            alumni.email
        )


        # =================================================
        # LOGIN COUNT
        # =================================================

        total_logins = request.session.get(
            "total_logins",
            0
        )

        request.session["total_logins"] = (
            total_logins + 1
        )


        # =================================================
        # SUCCESS MESSAGE
        # =================================================

        messages.success(
            request,
            f"Welcome back, {alumni.full_name}!"
        )


        # =================================================
        # LOGIN → REGISTER / WELCOME PAGE
        # =================================================

        return redirect("register")


    # =====================================================
    # LOGIN PAGE
    # =====================================================

    total_alumni = Alumni.objects.count()

    context = {

        "total_members":
            total_alumni,

        "active_members":
            total_alumni,

        "total_logins":
            request.session.get(
                "total_logins",
                0
            ),

    }

    return render(
        request,
        "accounts/login.html",
        context
    )


# =========================================================
# LOGOUT
# =========================================================

def logout_view(request):

    request.session.flush()

    messages.success(
        request,
        "You have been logged out successfully."
    )

    return redirect("home")


# =========================================================
# SEND OTP
# =========================================================

def send_otp(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Invalid request method."

        })


    # =====================================================
    # GET EMAIL
    # =====================================================

    email = request.POST.get(
        "email",
        ""
    ).strip().lower()


    # =====================================================
    # CHECK EMAIL
    # =====================================================

    if not email:

        return JsonResponse({

            "success": False,

            "message":
                "Please enter your email address."

        })


    # =====================================================
    # CHECK EXISTING EMAIL
    # =====================================================

    if Alumni.objects.filter(
        email__iexact=email
    ).exists():

        return JsonResponse({

            "success": False,

            "message":
                "This email address is already registered."

        })


    # =====================================================
    # GENERATE OTP
    # =====================================================

    otp = str(
        random.randint(
            100000,
            999999
        )
    )


    # =====================================================
    # SAVE OTP IN SESSION
    # =====================================================

    request.session["registration_otp"] = otp

    request.session["registration_email"] = email

    request.session["otp_created_time"] = int(
        time.time()
    )

    request.session["otp_verified"] = False


    # =====================================================
    # SEND EMAIL
    # =====================================================

    try:

        send_mail(

            subject=
                "Alumni Portal - Email Verification OTP",

            message=f"""
Hello,

Your Alumni Portal verification OTP is:

{otp}

This OTP is required to complete your alumni registration.

Please do not share this OTP with anyone.

Regards,
Alumni Portal
""",

            from_email=
                settings.DEFAULT_FROM_EMAIL,

            recipient_list=[
                email
            ],

            fail_silently=False

        )


        return JsonResponse({

            "success": True,

            "message":
                "OTP sent successfully to your email."

        })


    except Exception as e:

        print(
            "OTP EMAIL ERROR:",
            e
        )

        return JsonResponse({

            "success": False,

            "message":
                "Unable to send OTP. Please check your email settings."

        })


# =========================================================
# VERIFY OTP
# =========================================================

def verify_otp(request):

    if request.method != "POST":

        return JsonResponse({

            "success": False,

            "message":
                "Invalid request method."

        })


    # =====================================================
    # ENTERED OTP
    # =====================================================

    entered_otp = request.POST.get(
        "otp",
        ""
    ).strip()


    # =====================================================
    # SAVED OTP
    # =====================================================

    saved_otp = request.session.get(
        "registration_otp"
    )


    if not saved_otp:

        return JsonResponse({

            "success": False,

            "message":
                "OTP not found. Please send a new OTP."

        })


    # =====================================================
    # OTP EXPIRY
    # =====================================================

    otp_created_time = request.session.get(
        "otp_created_time"
    )


    if otp_created_time:

        current_time = int(
            time.time()
        )


        # OTP valid for 10 minutes

        if current_time - otp_created_time > 600:

            request.session.pop(
                "registration_otp",
                None
            )

            request.session.pop(
                "registration_email",
                None
            )

            request.session.pop(
                "otp_created_time",
                None
            )

            request.session["otp_verified"] = False


            return JsonResponse({

                "success": False,

                "message":
                    "OTP has expired. Please send a new OTP."

            })


    # =====================================================
    # CHECK OTP
    # =====================================================

    if entered_otp != saved_otp:

        return JsonResponse({

            "success": False,

            "message":
                "Invalid OTP. Please try again."

        })


    # =====================================================
    # OTP VERIFIED
    # =====================================================

    request.session["otp_verified"] = True


    return JsonResponse({

        "success": True,

        "message":
            "Email verified successfully."

    })


# =========================================================
# REGISTER
# =========================================================

def register_view(request):

    # =====================================================
    # CHECK LOGIN SESSION
    # =====================================================

    alumni_id = request.session.get(
        "alumni_id"
    )


    # =====================================================
    # IF ALREADY LOGGED IN
    # =====================================================

    if alumni_id:

        try:

            logged_in_student = Alumni.objects.get(
                id=alumni_id
            )


            context = {

                "logged_in_student":
                    logged_in_student

            }


            return render(
                request,
                "accounts/register.html",
                context
            )


        except Alumni.DoesNotExist:

            request.session.flush()

            return render(
                request,
                "accounts/register.html"
            )


    # =====================================================
    # NORMAL REGISTRATION FORM
    # =====================================================

    if request.method == "GET":

        return render(
            request,
            "accounts/register.html"
        )


    # =====================================================
    # REGISTRATION POST
    # =====================================================

    if request.method == "POST":

        # =================================================
        # GET FORM VALUES
        # =================================================

        register_number = request.POST.get(
            "register_number",
            ""
        ).strip().upper()


        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()


        date_of_birth = request.POST.get(
            "date_of_birth",
            ""
        ).strip()


        email = request.POST.get(
            "email",
            ""
        ).strip().lower()


        phone = request.POST.get(
            "mobile",
            ""
        ).strip()


        # Support phone field

        if not phone:

            phone = request.POST.get(
                "phone",
                ""
            ).strip()


        batch = request.POST.get(
            "batch",
            ""
        ).strip()


        company = request.POST.get(
            "company",
            ""
        ).strip()


        position = request.POST.get(
            "position",
            ""
        ).strip()


        father_name = request.POST.get(
            "father_name",
            ""
        ).strip()


        # =================================================
        # STORE FORM DATA
        # =================================================

        form_data = {

            "register_number":
                register_number,

            "full_name":
                full_name,

            "date_of_birth":
                date_of_birth,

            "email":
                email,

            "mobile":
                phone,

            "phone":
                phone,

            "batch":
                batch,

            "company":
                company,

            "position":
                position,

            "father_name":
                father_name,

        }


        # =================================================
        # VALIDATE REGISTER NUMBER
        # =================================================

        if not register_number:

            messages.error(
                request,
                "Please enter your college register number."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE FULL NAME
        # =================================================

        if not full_name:

            messages.error(
                request,
                "Please enter your full name."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE DOB
        # =================================================

        if not date_of_birth:

            messages.error(
                request,
                "Please enter your date of birth."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE EMAIL
        # =================================================

        if not email:

            messages.error(
                request,
                "Please enter your email address."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE BATCH
        # =================================================

        if not batch:

            messages.error(
                request,
                "Please enter your batch / passing year."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE COMPANY
        # =================================================

        if not company:

            messages.error(
                request,
                "Please enter your company name or working place."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # VALIDATE POSITION
        # =================================================

        if not position:

            messages.error(
                request,
                "Please enter your position or job role."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # CONVERT DOB
        # =================================================

        try:

            dob_object = datetime.strptime(
                date_of_birth,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            messages.error(
                request,
                "Please enter a valid date of birth."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # CHECK OTP
        # =================================================

        otp_verified = request.session.get(
            "otp_verified",
            False
        )


        verified_email = request.session.get(
            "registration_email",
            ""
        ).lower()


        if not otp_verified:

            messages.error(
                request,
                "Please verify your email using OTP before registering."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # CHECK VERIFIED EMAIL
        # =================================================

        if verified_email != email:

            messages.error(
                request,
                "The verified email does not match your registration email."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # CHECK DUPLICATE REGISTER NUMBER
        # =================================================

        if Alumni.objects.filter(
            register_number__iexact=register_number
        ).exists():

            messages.error(
                request,
                "This register number is already registered."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # CHECK DUPLICATE EMAIL
        # =================================================

        if Alumni.objects.filter(
            email__iexact=email
        ).exists():

            messages.error(
                request,
                "This email address is already registered."
            )

            return render(
                request,
                "accounts/register.html",
                {
                    "form_data": form_data
                }
            )


        # =================================================
        # SAVE ALUMNI
        # =================================================

        alumni = Alumni(

            register_number=register_number,

            full_name=full_name,

            date_of_birth=dob_object,

            email=email,

            phone=phone,

            batch=batch,

            company=company,

            position=position,

        )


        alumni.save()


        # =================================================
        # CLEAR OTP DATA
        # =================================================

        request.session.pop(
            "registration_otp",
            None
        )

        request.session.pop(
            "registration_email",
            None
        )

        request.session.pop(
            "otp_created_time",
            None
        )

        request.session.pop(
            "otp_verified",
            None
        )


        # =================================================
        # SUCCESS
        # =================================================

        messages.success(
            request,
            "Registration successful! You can now login using your Register Number and the common password."
        )


        return redirect("login")


    # =====================================================
    # FALLBACK
    # =====================================================

    return render(
        request,
        "accounts/register.html"
    )


# =========================================================
# ALUMNI DIRECTORY
#
# Main directory contains ONLY basic alumni information.
# ML results are shown on separate pages.
# =========================================================

def directory_view(request):

    # =====================================================
    # GET ALL ALUMNI
    # =====================================================

    alumni_list = Alumni.objects.all().order_by(
        "full_name"
    )


    # =====================================================
    # SEARCH
    # =====================================================

    search = request.GET.get(
        "search",
        ""
    ).strip()


    if search:

        alumni_list = alumni_list.filter(

            Q(
                full_name__icontains=search
            )

            |

            Q(
                email__icontains=search
            )

            |

            Q(
                register_number__icontains=search
            )

            |

            Q(
                company__icontains=search
            )

            |

            Q(
                position__icontains=search
            )

            |

            Q(
                batch__icontains=search
            )

        )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "alumni_list":
            alumni_list,

        "alumni":
            alumni_list,

        "search":
            search,

        "total_alumni":
            Alumni.objects.count(),

    }


    return render(
        request,
        "accounts/directory.html",
        context
    )


# =========================================================
# ALUMNI PROFILE
#
# Opens when user clicks:
# "View Profile"
# =========================================================

def alumni_profile_view(request, register_number):

    alumnus = get_object_or_404(

        Alumni,

        register_number__iexact=register_number

    )


    context = {

        "alumnus":
            alumnus,

    }


    return render(

        request,

        "accounts/alumni_profile.html",

        context

    )


# =========================================================
# SIMILAR ALUMNI
#
# Uses the KNN results already calculated by the ML system.
#
# Example:
#
# ARAVINTH G
#       ↓
# Similar Alumni
#       ↓
# KNN results
#
# The KNN algorithm itself is NOT displayed here.
# =========================================================

def similar_alumni_view(request, register_number):

    alumnus = get_object_or_404(

        Alumni,

        register_number__iexact=register_number

    )


    # =====================================================
    # GET KNN RESULT
    # =====================================================

    similar_names = []


    if alumnus.knn_similar_alumni:

        similar_names = [

            name.strip()

            for name in alumnus.knn_similar_alumni.split(",")

            if name.strip()

        ]


    # =====================================================
    # FIND ALUMNI
    # =====================================================

    similar_alumni = Alumni.objects.filter(

        full_name__in=similar_names

    ).exclude(

        id=alumnus.id

    )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "alumnus":
            alumnus,

        "similar_alumni":
            similar_alumni,

    }


    return render(

        request,

        "accounts/similar_alumni.html",

        context

    )


# =========================================================
# RECOMMENDED ALUMNI
#
# Uses the Recommendation System results.
#
# The recommendation algorithm works in the background.
# User only sees useful recommended connections.
# =========================================================

def recommended_alumni_view(request, register_number):

    alumnus = get_object_or_404(

        Alumni,

        register_number__iexact=register_number

    )


    # =====================================================
    # GET RECOMMENDATION RESULT
    # =====================================================

    recommended_names = []


    if alumnus.recommended_alumni:

        recommended_names = [

            name.strip()

            for name in alumnus.recommended_alumni.split(",")

            if name.strip()

        ]


    # =====================================================
    # FIND ALUMNI
    # =====================================================

    recommended_alumni = Alumni.objects.filter(

        full_name__in=recommended_names

    ).exclude(

        id=alumnus.id

    )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "alumnus":
            alumnus,

        "recommended_alumni":
            recommended_alumni,

    }


    return render(

        request,

        "accounts/recommended_alumni.html",

        context

    )


# =========================================================
# EVENTS
# =========================================================

def events_view(request):

    return render(

        request,

        "accounts/events.html"

    )


# =========================================================
# JOBS
# =========================================================

def jobs_view(request):

    return render(

        request,

        "accounts/jobs.html"

    )


# =========================================================
# MENTORSHIP
# =========================================================

def mentorship_view(request):

    return render(

        request,

        "accounts/mentorship.html"

    )


# =========================================================
# SCHOLARSHIPS
# =========================================================

def scholarships_view(request):

    return render(

        request,

        "accounts/scholarships.html"

    )


# =========================================================
# ABOUT
# =========================================================

def about_view(request):

    alumni = None

    alumni_id = request.session.get(
        "alumni_id"
    )


    if alumni_id:

        try:

            alumni = Alumni.objects.get(
                id=alumni_id
            )

        except Alumni.DoesNotExist:

            alumni = None


    total_alumni = Alumni.objects.count()


    context = {

        "alumni":
            alumni,

        "total_alumni":
            total_alumni,

        "active_alumni":
            total_alumni,

    }


    return render(

        request,

        "accounts/about.html",

        context

    )
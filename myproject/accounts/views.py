from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

import json

from .models import Alumni, Event, EventRegistration, Job


# ============================================================
# CURRENT LOGGED-IN ALUMNI
# ============================================================

def _current_alumni(request):
    alumni_id = request.session.get("alumni_id")

    if not alumni_id:
        return None

    try:
        return Alumni.objects.get(id=alumni_id)
    except Alumni.DoesNotExist:
        request.session.flush()
        return None


# ============================================================
# TOTAL SUCCESSFUL LOGINS
# ============================================================

def _successful_login_total():
    return Alumni.objects.aggregate(
        total=Sum("successful_logins")
    )["total"] or 0


# ============================================================
# HOME
# ============================================================

def home_view(request):
    alumni = _current_alumni(request)
    total_alumni = Alumni.objects.count()

    return render(
        request,
        "accounts/home.html",
        {
            "alumni": alumni,
            "display_name": alumni.full_name if alumni else "Guest",
            "total_alumni": total_alumni,
            "active_alumni": total_alumni,
            "total_members": total_alumni,
            "active_members": total_alumni,
            "total_logins": _successful_login_total(),
        },
    )


# ============================================================
# ABOUT
# ============================================================

def about_view(request):
    alumni = _current_alumni(request)

    senior_alumni = Alumni.objects.order_by(
        "batch", "full_name"
    )[:7]

    roles = [
        "President",
        "Vice President",
        "Secretary",
        "Joint Secretary (Alumni Relations)",
        "Joint Secretary (Student Relations)",
        "Joint Secretary (Industry Relations)",
        "Treasurer",
    ]

    executive_members = [
        {"role": role, "alumni": person}
        for role, person in zip(roles, senior_alumni)
    ]

    total_alumni = Alumni.objects.count()

    return render(
        request,
        "accounts/about.html",
        {
            "alumni": alumni,
            "total_alumni": total_alumni,
            "active_alumni": total_alumni,
            "senior_alumni": senior_alumni,
            "executive_members": executive_members,
        },
    )


# ============================================================
# ALUMNI DIRECTORY
# ============================================================

def directory_view(request):
    search = request.GET.get("search", "").strip()
    current = _current_alumni(request)

    alumni_list = Alumni.objects.all().order_by("full_name")

    if search:
        alumni_list = alumni_list.filter(
            Q(full_name__icontains=search)
            | Q(company__icontains=search)
            | Q(position__icontains=search)
            | Q(location__icontains=search)
            | Q(register_number__icontains=search)
            | Q(email__icontains=search)
            | Q(batch__icontains=search)
        )

    total_alumni = Alumni.objects.count()

    total_batches = (
        Alumni.objects.values("batch").distinct().count()
    )

    total_companies = (
        Alumni.objects.exclude(company="")
        .values("company").distinct().count()
    )

    alumni_data = [
        {
            "id": a.id,
            "register_number": a.register_number,
            "full_name": a.full_name,
            "email": a.email,
            "phone": a.phone,
            "batch": a.batch,
            "company": a.company or "N/A",
            "position": a.position or "Alumni Member",
            "location": a.location or "",
            "kmeans_cluster": a.kmeans_cluster,
            "knn_similar_alumni": a.knn_similar_alumni or "",
            "recommended_alumni": a.recommended_alumni or "",
            "sentiment": a.sentiment or "",
        }
        for a in alumni_list
    ]

    demo_current = current or Alumni.objects.first()

    current_data = (
        {
            "id": demo_current.id,
            "full_name": demo_current.full_name,
            "register_number": demo_current.register_number,
        }
        if demo_current else {}
    )

    return render(
        request,
        "accounts/directory.html",
        {
            "alumni": current,
            "alumni_list": alumni_list,
            "alumni_members": alumni_list,
            "alumni_json": json.dumps(alumni_data),
            "current_json": json.dumps(current_data),
            "search": search,
            "total_alumni": total_alumni,
            "active_alumni": total_alumni,
            "total_batches": total_batches,
            "total_companies": total_companies,
        },
    )


# ============================================================
# JOBS
# ============================================================

def jobs_view(request):
    search = request.GET.get("search", "").strip()
    category = request.GET.get("category", "").strip()
    location = request.GET.get("location", "").strip()
    experience = request.GET.get("experience", "").strip()

    jobs = Job.objects.filter(is_active=True)

    if search:
        jobs = jobs.filter(
            Q(title__icontains=search)
            | Q(company__icontains=search)
            | Q(location__icontains=search)
            | Q(skills__icontains=search)
            | Q(description__icontains=search)
        )

    if category:
        jobs = jobs.filter(category=category)

    if location:
        jobs = jobs.filter(location__icontains=location)

    if experience:
        jobs = jobs.filter(experience=experience)

    today = timezone.localdate()

    jobs = jobs.filter(
        Q(last_date__isnull=True)
        | Q(last_date__gte=today)
    ).order_by("-created_at")

    return render(
        request,
        "accounts/jobs.html",
        {
            "alumni": _current_alumni(request),
            "jobs": jobs,
            "total_jobs": jobs.count(),
            "fresher_jobs": jobs.filter(
                experience="Fresher"
            ).count(),
            "internship_jobs": jobs.filter(
                category="INTERNSHIP"
            ).count(),
            "company_count": jobs.values(
                "company"
            ).distinct().count(),
            "search": search,
            "selected_category": category,
            "selected_location": location,
            "selected_experience": experience,
            "category_choices": Job.CATEGORY_CHOICES,
            "experience_choices": Job.EXPERIENCE_CHOICES,
        },
    )


# ============================================================
# MENTORSHIP
# ============================================================

def mentorship_view(request):
    search = request.GET.get("search", "").strip()

    mentors = Alumni.objects.all().order_by("full_name")

    if search:
        mentors = mentors.filter(
            Q(full_name__icontains=search)
            | Q(company__icontains=search)
            | Q(position__icontains=search)
            | Q(register_number__icontains=search)
        )

    return render(
        request,
        "accounts/mentorship.html",
        {
            "alumni": _current_alumni(request),
            "mentors": mentors,
            "mentor_count": mentors.count(),
            "search": search,
        },
    )


# ============================================================
# EVENTS
# ============================================================

def events_view(request):
    alumni = _current_alumni(request)

    events = list(
        Event.objects.all().order_by(
            "event_date", "start_time"
        )
    )

    upcoming_events = [
        event for event in events if not event.is_ended
    ]

    completed_events = [
        event for event in events if event.is_ended
    ]

    return render(
        request,
        "accounts/events.html",
        {
            "alumni": alumni,
            "events": events,
            "upcoming_events": upcoming_events,
            "completed_events": completed_events,
            "total_events": len(events),
            "upcoming_count": len(upcoming_events),
            "completed_count": len(completed_events),
        },
    )


# ============================================================
# EVENT REGISTRATION
# ============================================================

def event_register_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        try:
            guests = max(
                int(request.POST.get("guests", "0")), 0
            )
        except (ValueError, TypeError):
            guests = 0

        form_data = {
            "full_name": request.POST.get(
                "full_name", ""
            ).strip(),
            "register_number": request.POST.get(
                "register_number", ""
            ).strip(),
            "email": request.POST.get("email", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "attendance": request.POST.get(
                "attendance", ""
            ).strip(),
            "guests": guests,
            "food_preference": request.POST.get(
                "food_preference", ""
            ).strip(),
            "special_requirements": request.POST.get(
                "special_requirements", ""
            ).strip(),
            "lunch_required": request.POST.get(
                "lunch_required", "No"
            ).strip(),
        }

        errors = []

        required_fields = (
            "full_name", "register_number", "email", "phone"
        )

        if any(not form_data[field] for field in required_fields):
            errors.append("Please complete all required fields.")

        if guests > event.seats_available:
            errors.append(
                "This event does not have enough seats remaining."
            )

        if EventRegistration.objects.filter(
            event=event,
            register_number=form_data["register_number"],
        ).exists():
            errors.append(
                "This register number is already registered for the event."
            )

        if not errors:
            try:
                with transaction.atomic():
                    registration = EventRegistration.objects.create(
                        event=event,
                        **form_data
                    )

                request.session["event_registration_id"] = registration.id
                return redirect("event_registration_success")

            except IntegrityError:
                errors.append(
                    "Unable to complete registration. Please try again."
                )

        return render(
            request,
            "accounts/event_register.html",
            {
                "event": event,
                "errors": errors,
                "form_data": form_data,
            },
        )

    return render(
        request,
        "accounts/event_register.html",
        {"event": event},
    )


# ============================================================
# EVENT REGISTRATION SUCCESS
# ============================================================

def event_registration_success_view(request):
    registration_id = request.session.pop(
        "event_registration_id", None
    )

    if registration_id is None:
        return redirect("events")

    registration = get_object_or_404(
        EventRegistration.objects.select_related("event"),
        id=registration_id,
    )

    return render(
        request,
        "accounts/event_registration_sucess.html",
        {
            "event": registration.event,
            "registration": registration,
        },
    )


# ============================================================
# ALUMNI REGISTRATION
# ============================================================

def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        register_number = request.POST.get(
            "register_number", ""
        ).strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        batch = request.POST.get("batch", "").strip()

        if not full_name:
            messages.error(request, "Please enter your full name.")

        elif not register_number:
            messages.error(
                request, "Please enter your college register number."
            )

        elif not email:
            messages.error(
                request, "Please enter your email address."
            )

        elif Alumni.objects.filter(
            register_number__iexact=register_number
        ).exists():
            messages.error(
                request, "That register number is already registered."
            )

        elif Alumni.objects.filter(
            email__iexact=email
        ).exists():
            messages.error(
                request, "That email address is already registered."
            )

        else:
            try:
                Alumni.objects.create(
                    full_name=full_name,
                    register_number=register_number,
                    email=email,
                    phone=phone,
                    batch=int(batch) if batch else 2027,
                )

                messages.success(
                    request,
                    "Registration completed. Please log in."
                )
                return redirect("login")

            except ValueError:
                messages.error(
                    request, "Please enter a valid batch year."
                )

            except IntegrityError:
                messages.error(
                    request,
                    "Unable to complete registration. Please try again."
                )

    return render(request, "accounts/register.html")


# ============================================================
# OTP PLACEHOLDERS
# ============================================================

def send_registration_otp(request):
    return JsonResponse({
        "success": True,
        "message": "OTP request received.",
    })


def verify_registration_otp(request):
    return JsonResponse({
        "success": True,
        "verified": True,
    })


def send_otp(request):
    return send_registration_otp(request)


def verify_otp(request):
    return verify_registration_otp(request)


# ============================================================
# LOGIN
# ============================================================

def login_view(request):
    if request.method == "POST":
        register_number = (
            request.POST.get("username")
            or request.POST.get("register_number")
            or ""
        ).strip()

        alumnus = Alumni.objects.filter(
            register_number__iexact=register_number
        ).first()

        if alumnus:
            Alumni.objects.filter(
                pk=alumnus.pk
            ).update(
                successful_logins=F("successful_logins") + 1
            )

            request.session["alumni_id"] = alumnus.id
            request.session["alumni_name"] = alumnus.full_name
            request.session["alumni_register_number"] = (
                alumnus.register_number
            )
            request.session["alumni_email"] = alumnus.email

            return redirect("home")

        messages.error(request, "Invalid register number.")

    today = timezone.localdate()

    total_jobs = Job.objects.filter(
        is_active=True
    ).filter(
        Q(last_date__isnull=True)
        | Q(last_date__gte=today)
    ).count()

    return render(
        request,
        "accounts/login.html",
        {
            "total_members": Alumni.objects.count(),
            "total_events": Event.objects.count(),
            "total_jobs": total_jobs,
            "total_logins": _successful_login_total(),
        },
    )


# ============================================================
# LOGIN COUNT
# ============================================================

def login_count_view(request):
    return JsonResponse({
        "count": _successful_login_total(),
    })


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):
    request.session.flush()
    return redirect("home")


# ============================================================
# ALUMNI PROFILE
# ============================================================

def alumni_profile_view(request, register_number):
    alumnus = get_object_or_404(
        Alumni,
        register_number=register_number
    )

    return render(
        request,
        "accounts/alumni_profile.html",
        {
            "alumnus": alumnus,
            "alumni": _current_alumni(request),
        },
    )


# ============================================================
# SIMILAR ALUMNI
# ============================================================

def similar_alumni_view(request, register_number):
    alumnus = get_object_or_404(
        Alumni,
        register_number=register_number
    )

    similar_alumni = (
        Alumni.objects
        .exclude(id=alumnus.id)
        .filter(
            Q(company=alumnus.company)
            | Q(position=alumnus.position)
        )
        .order_by("full_name")[:10]
    )

    return render(
        request,
        "accounts/similar_alumni.html",
        {
            "alumnus": alumnus,
            "similar_alumni": similar_alumni,
            "alumni": _current_alumni(request),
        },
    )


# ============================================================
# RECOMMENDED ALUMNI
# ============================================================

def recommended_alumni_view(request, register_number):
    alumnus = get_object_or_404(
        Alumni,
        register_number=register_number
    )

    recommended_alumni = (
        Alumni.objects
        .exclude(id=alumnus.id)
        .order_by("full_name")[:10]
    )

    return render(
        request,
        "accounts/recommended_alumni.html",
        {
            "alumnus": alumnus,
            "recommended_alumni": recommended_alumni,
            "alumni": _current_alumni(request),
        },
    )
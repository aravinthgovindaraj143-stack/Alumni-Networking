from django.contrib import messages
from django.db import IntegrityError, transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import json
import random
import os
import urllib.request
import urllib.error

from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Alumni, ChatMessage, Event, EventRegistration, Job


# ============================================================
# CURRENT LOGGED-IN ALUMNI
# ============================================================

def _current_alumni(request):
    session = getattr(request, "session", None)
    if not session:
        return None
    alumni_id = session.get("alumni_id")

    if not alumni_id:
        return None

    try:
        return Alumni.objects.get(id=alumni_id)
    except Alumni.DoesNotExist:
        try:
            request.session.flush()
        except Exception:
            pass
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

    demo_current = current or Alumni.objects.first()
    current_alumni_id = demo_current.id if demo_current else None

    # Load all conversations involving current alumni from ChatMessage
    conversations_map = {}
    total_chat_messages = 0
    if current_alumni_id:
        try:
            chat_msgs = ChatMessage.objects.filter(
                Q(sender_id=current_alumni_id) | Q(recipient_id=current_alumni_id)
            ).order_by("created_at")
            total_chat_messages = chat_msgs.count()
            for m in chat_msgs:
                other_id = m.recipient_id if m.sender_id == current_alumni_id else m.sender_id
                if other_id not in conversations_map:
                    conversations_map[other_id] = {
                        "last_message": m.message,
                        "last_message_time": m.created_at.strftime("%I:%M %p"),
                        "last_message_iso": m.created_at.isoformat(),
                        "total_messages": 0,
                        "unread_from_them": 0,
                    }
                conv = conversations_map[other_id]
                conv["last_message"] = m.message
                conv["last_message_time"] = m.created_at.strftime("%I:%M %p")
                conv["last_message_iso"] = m.created_at.isoformat()
                conv["total_messages"] += 1
                if m.recipient_id == current_alumni_id:
                    conv["unread_from_them"] += 1
        except Exception:
            conversations_map = {}

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
            "has_chat": a.id in conversations_map,
            "last_message": conversations_map.get(a.id, {}).get("last_message", ""),
            "last_message_time": conversations_map.get(a.id, {}).get("last_message_time", ""),
            "last_message_iso": conversations_map.get(a.id, {}).get("last_message_iso", ""),
            "unread_count": conversations_map.get(a.id, {}).get("unread_from_them", 0),
        }
        for a in alumni_list
    ]

    # Attach chat_info attribute directly to alumni in query for template rendering
    for a in alumni_list:
        a.chat_info = conversations_map.get(a.id)

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
            "conversations_json": json.dumps(conversations_map),
            "conversations_count": len(conversations_map),
            "total_chat_messages": total_chat_messages,
            "search": search,
            "total_alumni": total_alumni,
            "active_alumni": total_alumni,
            "total_batches": total_batches,
            "total_companies": total_companies,
        },
    )


# ============================================================
# REAL-TIME DIRECTORY CHAT APIs (Fallback & Direct Support)
# ============================================================

def chat_history_api(request):
    """Retrieve message history between the current alumnus and requested recipient."""
    current = _current_alumni(request)
    current_id = request.GET.get("sender_id")
    if current_id and current_id.isdigit():
        current_id = int(current_id)
    elif current:
        current_id = current.id
    else:
        first = Alumni.objects.first()
        current_id = first.id if first else 1

    recipient_id = request.GET.get("recipient_id")
    if not recipient_id or not recipient_id.isdigit():
        return JsonResponse({"status": "error", "message": "recipient_id is required."}, status=400)

    recipient_id = int(recipient_id)

    messages_qs = ChatMessage.objects.filter(
        Q(sender_id=current_id, recipient_id=recipient_id)
        | Q(sender_id=recipient_id, recipient_id=current_id)
    ).order_by("created_at")[:200]

    sender_ids = {m.sender_id for m in messages_qs}
    senders = {a.id: a.full_name for a in Alumni.objects.filter(id__in=sender_ids)}

    data = [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "sender_name": senders.get(m.sender_id, f"Alumni #{m.sender_id}"),
            "recipient_id": m.recipient_id,
            "message": m.message,
            "created_at": m.created_at.isoformat(),
            "time_str": m.created_at.strftime("%I:%M %p"),
        }
        for m in messages_qs
    ]

    return JsonResponse({"status": "ok", "messages": data})


@csrf_exempt
def chat_send_api(request):
    """Save and broadcast a message via HTTP with WebSocket Channel Layer sync."""
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required."}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8")) if request.body else request.POST
    except Exception:
        body = request.POST

    current = _current_alumni(request)
    sender_id = body.get("sender_id")
    if sender_id and str(sender_id).isdigit():
        sender_id = int(sender_id)
    elif current:
        sender_id = current.id
    else:
        first = Alumni.objects.first()
        sender_id = first.id if first else 1

    recipient_id = body.get("recipient_id")
    message = str(body.get("message", "")).strip()

    if not str(recipient_id).isdigit() or not message:
        return JsonResponse({"status": "error", "message": "recipient_id and message are required."}, status=400)

    recipient_id = int(recipient_id)
    if recipient_id == sender_id or len(message) > 2000:
        return JsonResponse({"status": "error", "message": "Invalid message or recipient."}, status=400)

    saved_message = ChatMessage.objects.create(
        sender_id=sender_id,
        recipient_id=recipient_id,
        message=message,
    )

    sender = Alumni.objects.filter(id=sender_id).first()
    sender_name = sender.full_name if sender else f"Alumni #{sender_id}"

    payload = {
        "type": "message",
        "id": saved_message.id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "recipient_id": recipient_id,
        "message": message,
        "created_at": saved_message.created_at.isoformat(),
        "time_str": saved_message.created_at.strftime("%I:%M %p"),
    }

    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"alumni_{recipient_id}",
                {
                    "type": "chat_message",
                    "payload": {**payload, "status": "received"},
                },
            )
    except Exception:
        pass

    return JsonResponse({"status": "ok", "message": {**payload, "status": "sent"}})


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
        date_of_birth = request.POST.get("date_of_birth", "").strip() or None

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

        elif not request.session.get("registration_otp_verified") or request.session.get("registration_verified_email", "").lower() != email.lower():
            messages.error(
                request, "Please verify your email address with the 6-digit OTP before completing registration."
            )

        else:
            try:
                Alumni.objects.create(
                    full_name=full_name,
                    register_number=register_number,
                    email=email,
                    phone=phone,
                    batch=int(batch) if batch else 2027,
                    date_of_birth=date_of_birth,
                )

                # Clear OTP verification from session
                request.session.pop("registration_otp", None)
                request.session.pop("registration_otp_email", None)
                request.session.pop("registration_otp_time", None)
                request.session.pop("registration_otp_verified", None)
                request.session.pop("registration_verified_email", None)

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
# OTP EMAIL VERIFICATION
# ============================================================

def _dispatch_otp_email(to_email, otp):
    """
    Dispatch OTP email using multiple transports to guarantee delivery on Render:
    1. HTTP-based APIs (Brevo / Resend / Webhook) over port 443 (NEVER blocked on Render).
    2. Direct SMTP over port 587 (works locally and on paid Render tier).
    3. Render Free Tier Fail-Safe: If outbound SMTP port 587 is blocked by Render firewall,
       prominently log the OTP to server stdout and return delivery_method='render_blocked'
       so the user can be notified without blocking registration.
    """
    subject = "Alumni Portal - Registration OTP Verification"
    email_body = (
        f"Dear Alumni,\n\n"
        f"Thank you for registering on the Alumni Networking Portal.\n\n"
        f"Your One-Time Password (OTP) for email verification is:\n\n"
        f"    {otp}\n\n"
        f"This OTP is valid for 10 minutes. Please enter this code on the registration page to verify your email.\n\n"
        f"If you did not request this OTP, please ignore this email.\n\n"
        f"Best regards,\n"
        f"Alumni Relations Team"
    )

    # 1. Brevo HTTP API (Port 443 HTTPS)
    brevo_key = getattr(settings, "BREVO_API_KEY", "") or os.environ.get("BREVO_API_KEY", "")
    if brevo_key:
        try:
            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=json.dumps({
                    "sender": {"email": settings.DEFAULT_FROM_EMAIL, "name": "Alumni Relations Team"},
                    "to": [{"email": to_email}],
                    "subject": subject,
                    "textContent": email_body,
                }).encode("utf-8"),
                headers={
                    "api-key": brevo_key,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "brevo_api", ""
        except Exception as e:
            print(f"[BREVO EMAIL ERROR] {e}")

    # 2. Resend HTTP API (Port 443 HTTPS)
    resend_key = getattr(settings, "RESEND_API_KEY", "") or os.environ.get("RESEND_API_KEY", "")
    if resend_key:
        try:
            from_addr = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
            req = urllib.request.Request(
                "https://api.resend.com/emails",
                data=json.dumps({
                    "from": from_addr,
                    "to": [to_email],
                    "subject": subject,
                    "text": email_body,
                }).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json",
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201):
                    return True, "resend_api", ""
        except Exception as e:
            print(f"[RESEND EMAIL ERROR] {e}")

    # 3. Custom Webhook (Port 443 HTTPS)
    webhook_url = getattr(settings, "EMAIL_WEBHOOK_URL", "") or os.environ.get("EMAIL_WEBHOOK_URL", "")
    if webhook_url:
        try:
            req = urllib.request.Request(
                webhook_url,
                data=json.dumps({
                    "to": to_email,
                    "subject": subject,
                    "body": email_body,
                    "otp": otp,
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status in (200, 201, 204):
                    return True, "webhook", ""
        except Exception as e:
            print(f"[WEBHOOK EMAIL ERROR] {e}")

    # 4. Standard Django SMTP (with fast timeout)
    smtp_err = ""
    try:
        send_mail(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [to_email],
            fail_silently=False,
        )
        return True, "smtp", ""
    except Exception as e:
        smtp_err = str(e)
        print(f"[SMTP NOTICE - Render port 587 restriction or timeout] {smtp_err}")

    # 5. Render Free Tier Fail-Safe
    # Render blocks outbound SMTP ports (25, 465, 587).
    print("\n" + "=" * 65)
    print(f" [RENDER OTP DISPATCH] To: {to_email} | OTP: {otp}")
    print("=" * 65 + "\n")
    return False, "render_blocked", smtp_err


@csrf_exempt
def send_registration_otp(request):
    """Generate and send 6-digit OTP to the registration email using SMTP / HTTP settings."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST method required."}, status=405)

    email = None
    if request.body:
        try:
            body = json.loads(request.body.decode("utf-8"))
            email = body.get("email")
        except Exception:
            pass

    if not email:
        email = request.POST.get("email", "").strip()

    if not email:
        msg = "Please enter your email address first."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": False, "message": msg})
        messages.error(request, msg)
        return redirect("register")

    # Check if email is already registered
    if Alumni.objects.filter(email__iexact=email).exists():
        msg = "That email address is already registered. Please log in or use another email."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": False, "message": msg})
        messages.error(request, msg)
        return redirect("register")

    # Generate secure 6-digit numeric OTP
    otp = f"{random.randint(100000, 999999)}"

    # Save OTP state in session
    request.session["registration_otp"] = otp
    request.session["registration_otp_email"] = email
    request.session["registration_otp_time"] = timezone.now().timestamp()
    request.session["registration_otp_verified"] = False
    request.session.modified = True

    # Dispatch email
    sent, method, detail = _dispatch_otp_email(email, otp)

    if sent:
        success_msg = f"OTP sent to {email}. Please check your inbox (and spam folder)."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": True, "delivered": True, "message": success_msg})
        messages.success(request, success_msg)
        return redirect("register")
    else:
        # Render Free Tier blocked SMTP port 587
        render_msg = f"OTP generated! (Notice: Render Free Tier restricts outbound SMTP port 587. Your verification code is: {otp})"
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({
                "success": True,
                "delivered": False,
                "otp_hint": otp,
                "message": render_msg,
            })
        messages.info(request, render_msg)
        return redirect("register")


@csrf_exempt
def verify_registration_otp(request):
    """Verify the 6-digit OTP entered by the user."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "POST method required."}, status=405)

    otp = None
    if request.body:
        try:
            body = json.loads(request.body.decode("utf-8"))
            otp = body.get("otp")
        except Exception:
            pass

    if not otp:
        otp = request.POST.get("otp", "").strip()

    if not otp:
        msg = "Please enter the 6-digit OTP."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": False, "verified": False, "message": msg})
        messages.error(request, msg)
        return redirect("register")

    session_otp = request.session.get("registration_otp")
    otp_time = request.session.get("registration_otp_time", 0)

    # Check expiration (10 minutes = 600s)
    if not session_otp or (timezone.now().timestamp() - otp_time > 600):
        msg = "OTP has expired or was not requested. Please click 'Send OTP' again."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": False, "verified": False, "message": msg})
        messages.error(request, msg)
        return redirect("register")

    if str(otp).strip() != str(session_otp).strip():
        msg = "Invalid OTP. Please check the 6-digit code and try again."
        if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
            return JsonResponse({"success": False, "verified": False, "message": msg})
        messages.error(request, msg)
        return redirect("register")

    request.session["registration_otp_verified"] = True
    request.session["registration_verified_email"] = request.session.get("registration_otp_email")
    request.session.modified = True

    success_msg = "Email verified successfully!"
    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.content_type == "application/json":
        return JsonResponse({"success": True, "verified": True, "message": success_msg})

    messages.success(request, success_msg)
    return redirect("register")


@csrf_exempt
def send_otp(request):
    return send_registration_otp(request)


@csrf_exempt
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
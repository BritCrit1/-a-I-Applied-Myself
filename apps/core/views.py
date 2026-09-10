from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render

from apps.core.forms import SignUpForm
from apps.jobs.models import AgentTask, Application, Communication, FollowUp, Job, RunSetting
from apps.jobs.services import salary_label
from apps.profiles.models import CandidateProfile, Resume, SearchPreference


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "core/home.html")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def dashboard(request):
    latest_resume = Resume.objects.filter(user=request.user).first()
    profile = CandidateProfile.objects.filter(user=request.user).first()
    preferences = SearchPreference.objects.filter(user=request.user).first()
    applications = (
        Application.objects.filter(user=request.user)
        .select_related("job", "job__source")
        .order_by("-updated_at")[:8]
    )
    jobs = (
        Job.objects.filter(applications__user=request.user)
        .select_related("source")
        .distinct()
        .order_by("-match_score", "-updated_at")[:8]
    )
    agent_tasks = AgentTask.objects.filter(user=request.user).order_by("-updated_at")[:8]
    communications = Communication.objects.filter(application__user=request.user).order_by("-received_at", "-created_at")[:8]
    followups = FollowUp.objects.filter(application__user=request.user).select_related("application__job").order_by("due_at")[:8]
    counts = Application.objects.filter(user=request.user).aggregate(
        jobs_found=Count("job", distinct=True),
        strong_matches=Count("job", filter=Q(job__match_score__gte=80), distinct=True),
        applications_sent=Count("id", filter=Q(state__in=[Application.State.APPLIED, Application.State.AWAITING_RESPONSE])),
        interviews=Count("id", filter=Q(state=Application.State.INTERVIEW)),
        followups_due=Count("followups", filter=Q(followups__status=FollowUp.Status.PENDING)),
    )
    run_setting = RunSetting.objects.filter(user=request.user).first()
    return render(
        request,
        "core/dashboard.html",
        {
            "latest_resume": latest_resume,
            "profile": profile,
            "preferences": preferences,
            "applications": applications,
            "jobs": jobs,
            "agent_tasks": agent_tasks,
            "communications": communications,
            "followups": followups,
            "counts": counts,
            "run_setting": run_setting,
            "salary_label": salary_label,
        },
    )

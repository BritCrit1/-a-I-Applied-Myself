from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.forms import SignUpForm
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
    return render(
        request,
        "core/dashboard.html",
        {
            "latest_resume": latest_resume,
            "profile": profile,
            "preferences": preferences,
        },
    )

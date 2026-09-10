from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from apps.core.models import AuditLog
from apps.profiles.forms import CandidateProfileForm, ResumeUploadForm, SearchPreferenceForm
from apps.profiles.models import CandidateProfile, Resume, SearchPreference
from apps.profiles.services import confirm_profile, parse_resume_into_profile


@login_required
def upload_resume(request):
    if request.method == "POST":
        form = ResumeUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user
            resume.original_filename = request.FILES["file"].name
            resume.content_type = getattr(request.FILES["file"], "content_type", "")
            resume.save()
            parse_resume_into_profile(resume)
            AuditLog.objects.create(
                user=request.user,
                actor_type=AuditLog.ActorType.USER,
                action="resume.uploaded",
                target_type="resume",
                target_id=str(resume.id),
            )
            messages.success(request, "Resume uploaded. Confirm the extracted profile before running searches.")
            return redirect("profile_confirm")
    else:
        form = ResumeUploadForm()
    return render(request, "profiles/upload_resume.html", {"form": form})


@login_required
def confirm_candidate_profile(request):
    profile = CandidateProfile.objects.filter(user=request.user).first()
    if profile is None:
        messages.info(request, "Upload a resume before confirming your candidate profile.")
        return redirect("resume_upload")

    if request.method == "POST":
        form = CandidateProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save()
            confirm_profile(profile)
            AuditLog.objects.create(
                user=request.user,
                actor_type=AuditLog.ActorType.USER,
                action="candidate_profile.confirmed",
                target_type="candidate_profile",
                target_id=str(profile.id),
            )
            return redirect("search_preferences")
    else:
        form = CandidateProfileForm(instance=profile)
    return render(request, "profiles/confirm_profile.html", {"form": form, "profile": profile})


@login_required
def search_preferences(request):
    instance = SearchPreference.objects.filter(user=request.user).first()
    if request.method == "POST":
        form = SearchPreferenceForm(request.POST, instance=instance)
        if form.is_valid():
            preference = form.save(commit=False)
            preference.user = request.user
            preference.save()
            AuditLog.objects.create(
                user=request.user,
                actor_type=AuditLog.ActorType.USER,
                action="search_preferences.saved",
                target_type="search_preference",
                target_id=str(preference.id),
            )
            messages.success(request, "Job search profile saved.")
            return redirect("dashboard")
    else:
        form = SearchPreferenceForm(instance=instance)
    return render(request, "profiles/search_preferences.html", {"form": form})

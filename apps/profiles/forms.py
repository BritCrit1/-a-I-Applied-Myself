from django import forms

from apps.profiles.models import CandidateProfile, Resume, SearchPreference


class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ["file"]

    def clean_file(self):
        uploaded = self.cleaned_data["file"]
        if uploaded.size > 5 * 1024 * 1024:
            raise forms.ValidationError("Resume files must be 5 MB or smaller.")
        allowed = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        }
        content_type = getattr(uploaded, "content_type", "")
        if content_type and content_type not in allowed:
            raise forms.ValidationError("Upload a PDF, DOCX, or plain text resume.")
        return uploaded


class CandidateProfileForm(forms.ModelForm):
    class Meta:
        model = CandidateProfile
        fields = [
            "full_name",
            "phone",
            "email",
            "location",
            "work_authorization",
            "security_clearance",
        ]


class SearchPreferenceForm(forms.ModelForm):
    class Meta:
        model = SearchPreference
        fields = [
            "search_intent",
            "zip_code",
            "search_radius_miles",
            "work_mode",
            "priority",
            "minimum_salary",
        ]

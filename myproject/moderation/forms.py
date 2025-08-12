from django import forms
from .models import Report

class ReportForm(forms.ModelForm):
    class Meta: 
        model=Report
        fields=['reason','detail']
        widgets={
            "reason": forms.Select(attrs={"class":"form-select"}),
            "detail":forms.Textarea(attrs={'rows':4,'placeholder':"상세 사유(선택)"}),
        }
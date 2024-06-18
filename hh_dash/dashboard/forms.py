from django import forms
from django.core.exceptions import ValidationError
from django_jalali.forms import jDateField
from django_jalali.admin.widgets import AdminjDateWidget
from .models import DimProject


class DatePickerForm(forms.Form):
    start = jDateField(widget=AdminjDateWidget())
    end = jDateField(widget=AdminjDateWidget())


   # def clean(self):
    #     cleaned_data = super().clean()
    #     start_date = cleaned_data.get('start').split('-')
    #     end_date = self.cleaned_data['end'].split('-')
    #     start_year, start_month = int(start_date[0]), int(start_date[1])
    #     end_year, end_month = int(end_date[0]), int(end_date[1])
    #     if (start_year, start_month) == (end_year, end_month):
    #         raise ValidationError("same year")
    #     if (start_year, start_month) > (end_year, end_month):
    #         raise ValidationError("تاریخ شروع بزرگ‌تر از تاریخ پایان است!")



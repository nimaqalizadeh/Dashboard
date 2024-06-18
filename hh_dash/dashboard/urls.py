from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required


app_name = 'dashboard'

urlpatterns = [
    path('chart/bar', login_required(views.ProjectKindBarChartView.as_view()), name='bar_chart'),
    path('chart/sunburst', login_required(views.SunburstChartView.as_view()), name='sunburst_chart'),
    path('chart/treemap', login_required(views.ProjectKindTreemapChartView.as_view()), name='treemap_chart'),
    path('duplicate_signers', login_required(views.DuplicateSignerReport.as_view()), name='duplicate_signers'),
    path('duplicate_signers_range', login_required(views.DuplicateSignerReportRange.as_view()), name='duplicate_signers_range'),
    path('standard_timesheet', login_required(views.StandardTimesheet.as_view()), name='std_timesheet'),
    path('standard_timesheet_range', login_required(views.StandardTimesheetRange.as_view()), name='std_timesheet_range'),
    path('training_hours', login_required(views.TrainingHours.as_view()), name='training_hours'),
    path('training_hours_range', login_required(views.TrainingHoursRange.as_view()), name='training_hours_range'),
    path('home', views.home, name='home_page'),
    path('managerial_reports', views.managerial_reports, name='managerial_reports'),
    path('chart/project_kind', views.get_project_kind, name='project_kind'),
    path('chart/project_name', views.get_project_names, name='project_name'),
    path('chart/company_name', views.get_company_names, name='company_name'),
    path('chart/project_state_name', views.get_project_state_by_name, name='project_state_by_name'),
    path('chart/project_state_kind', views.get_project_state_by_kind, name='project_state_by_kind'),

]

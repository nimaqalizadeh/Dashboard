from django import views
from django.shortcuts import render, redirect
from .models import *
import plotly.express as px
from django.db.models import Count, Sum, F
from dashboard.forms import DatePickerForm
import jdatetime
from django.contrib import messages
import pandas as pd
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from datetime import datetime
import json
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

@login_required
def home(request):
    return render(request, 'dashboard/index.html')


@login_required
def managerial_reports(request):
    return render(request, 'dashboard/managerial_reports.html')

class ProjectKindBarChartView(views.View):
    def get(self, request):
        form = DatePickerForm()
        context = {"form": form}
        return render(request, "dashboard/bar_chart.html", context)

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')
        state = request.POST.get('project_state')

        if start:
            year, month, day = start.split('-')
            start_year, start_month, start_day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(start_year, start_month, start_day).togregorian()
        if end:
            year, month, day = end.split('-')
            end_year, end_month, end_day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(end_year, end_month, end_day).togregorian()

        if state == "خاتمه یافته":
            state_code = 3
        elif state == "در حال اجرا":
            state_code = 2
        elif state == "آماده اجرا":
            state_code = 1

        try:
            project_cost_table = (DimProject.objects.filter(status_key=state_code).select_related('activation_date_key')
                                  .filter(activation_date_key__created_ts__gte=start_date_greg,
                                          activation_date_key__created_ts__lte=end_date_greg)
                                  .values("project_kind")
                                  .annotate(Sum('project_cost'), Count('project_name'))
                                  .using('data')
                                  .order_by("project_cost__sum"))

            total_cost = project_cost_table.aggregate(Sum("project_cost__sum"))
            total_count = project_cost_table.aggregate(Sum("project_name__count"))

            project_cost_chart = (DimProject.objects.filter(status_key=state_code).select_related('activation_date_key')
                                  .filter(activation_date_key__created_ts__gte=start_date_greg,
                                          activation_date_key__created_ts__lte=end_date_greg)
                                  .values("project_kind", "project_name", "project_cost").using("data"))

            values = [project['project_cost'] for project in project_cost_chart]
            kinds = [project['project_kind'] for project in project_cost_chart]

            df = pd.DataFrame.from_records(project_cost_chart)
            fig = px.sunburst(df, path=['project_kind', 'project_name'], values=values,
                              color_discrete_sequence=px.colors.qualitative.Pastel2)

            fig.update_layout(
                # grid=dict(columns=2, rows=1),
                margin=dict(t=0, l=0, r=0, b=0)
            )
            chart = fig.to_html(full_html=False)

            fig_pie = px.pie(df, values='project_cost', names='project_kind',
                             color_discrete_sequence=px.colors.qualitative.Pastel2)
            pie_chart = fig_pie.to_html(full_html=False)

            project_status = {1: "آماده اجرا", 2: "در حال اجرا", 3: "خاتمه ‌یافته"}

            form = DatePickerForm()

            context = {"projects": project_cost_table, "chart": chart, "form": form, "total_count": total_count,
                       "total_cost": total_cost, "status": state, "pie_chart": pie_chart,
                       "start_year": start_year, "start_month": start_month, "start_day": start_day,
                       "end_year": end_year, "end_month": end_month, "end_day": end_day
                       }

        except ValueError:
            messages.error(request, "Error!")
            return redirect('/chart/bar')
        else:
            return render(request, "dashboard/bar_chart.html", context)

    # Receive the dates sent by ajax and filter project_kind


def date_validation(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    if start:
        year, month, day = start.split('-')
        year, month, day = int(year), int(month), int(day)
        start_date_greg = jdatetime.date(year, month, day).togregorian()
    if end:
        year, month, day = end.split('-')
        year, month, day = int(year), int(month), int(day)
        end_date_greg = jdatetime.date(year, month, day).togregorian()
        return start_date_greg, end_date_greg


# @login_required
def get_project_kind(request):
    start_date_greg, end_date_greg = date_validation(request)
    # Dropdown for project_kind
    project_kind = (DimProject.objects.filter(activation_date_key__created_ts__gte=start_date_greg,
                                              activation_date_key__created_ts__lte=end_date_greg)
                    .values("project_kind").distinct().using("data"))
    projects = [project['project_kind'] for project in project_kind]
    return JsonResponse(projects, safe=False)


def get_company_names(request):
    # Dropdown for company_name
    start_date_greg, end_date_greg = date_validation(request)
    project_kind = request.GET.get('project_kind')

    company_name = (DimProject.objects.filter(activation_date_key__created_ts__gte=start_date_greg,
                                              activation_date_key__created_ts__lte=end_date_greg)
                    .filter(project_kind__exact=project_kind)
                    .values("cost_center").distinct().using("data"))
    names = [project['cost_center'] for project in company_name]
    return JsonResponse(names, safe=False)


def get_project_names(request):
    # Dropdown for project_name
    start_date_greg, end_date_greg = date_validation(request)
    project_kind = request.GET.get('project_kind')
    company_name = request.GET.get('company_name')
    project_name = (DimProject.objects.filter(activation_date_key__created_ts__gte=start_date_greg,
                                              activation_date_key__created_ts__lte=end_date_greg)
                    .filter(project_kind__exact=project_kind)
                    .filter(cost_center__exact=company_name)
                    .values("project_name").distinct().using("data"))

    names = [project['project_name'] for project in project_name]
    return JsonResponse(names, safe=False)


def get_project_state_by_name(request):
    # Checkbox for project_state
    project_name = request.GET.get('project_name')
    project_state = (DimProject.objects.filter(project_name__exact=project_name)
                     .values("status_key__status").using("data"))

    states = [project['status_key__status'] for project in project_state]

    return JsonResponse(states, safe=False)


def get_project_state_by_kind(request):
    # Checkbox for project_state
    start_date_greg, end_date_greg = date_validation(request)
    project_state = (DimProject.objects.filter(activation_date_key__created_ts__gte=start_date_greg,
                                               activation_date_key__created_ts__lte=end_date_greg)
                     .values("status_key__status").distinct().using("data"))
    states = [state['status_key__status'] for state in project_state]
    return JsonResponse(states, safe=False)


class SunburstChartView(views.View):
    def get(self, request):
        form = DatePickerForm()
        context = {"form": form}
        return render(request, "dashboard/sunburst_chart.html", context)

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')
        state = request.POST.get('project_state')
        kind = request.POST.get('project_kind')
        company = request.POST.get('company_name')
        name = request.POST.get('project_name')

        if start:
            year, month, day = start.split('-')
            start_year, start_month, start_day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(start_year, start_month, start_day).togregorian()
        if end:
            year, month, day = end.split('-')
            end_year, end_month, end_day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(end_year, end_month, end_day).togregorian()

        if state == "خاتمه یافته":
            state_code = 3
        elif state == "در حال اجرا":
            state_code = 2
        elif state == "آماده اجرا":
            state_code = 1
        try:
            projects_detail = (FactProjectactivity.objects.select_related("project_key")
                               .filter(project_key__activation_date_key__created_ts__gte=start_date_greg,
                                       project_key__activation_date_key__created_ts__lte=end_date_greg)
                               .filter(project_key__project_kind__iexact=kind)
                               .filter(project_key__project_name__exact=name)
                               .filter(project_key__status_key=state_code)
                               .values("project_key__project_name", "user_key__user_lastname",
                                       "user_key__user_firstname", "project_key__project_kind",
                                       "project_key__cost_center",
                                       "user_key__job_key__job_title", "work_minutes").using("data"))

            values = [project['work_minutes'] / 60 for project in projects_detail]
            total_hours = sum(values)
            df = pd.DataFrame.from_records(projects_detail)
            fig = px.sunburst(df, path=['project_key__project_name', 'user_key__job_key__job_title',
                                        'user_key__user_lastname'], values=values,
                              color_discrete_sequence=px.colors.qualitative.Pastel2)

            fig.update_layout(
                # grid=dict(columns=2, rows=1),
                margin=dict(t=0, l=0, r=0, b=0)
            )
            chart = fig.to_html(full_html=False)

            form = DatePickerForm()

            project_table = (projects_detail.values("project_key__project_name", "user_key__user_lastname",
                                                    "user_key__user_firstname", "project_key__project_kind",
                                                    "project_key__cost_center",
                                                    "user_key__job_key__job_title")
                             .annotate(Sum("work_minutes")).order_by("work_minutes__sum").using("data"))
            project_table = project_table.annotate(work_hours=F('work_minutes__sum') / 60)

            # res = HttpResponse(content_type="application/ms-excel")
            # res["content-Disposition"] = 'attachment;filename=timesheet' + str(jdatetime.datetime.now()) + '.xlsx'
            #
            # workbook = xlwt.Workbook(encoding="utf-8")
            # worksheet = workbook.add_sheet("sheet1")
            # columns = ["نام خانوادگی", "نام", "سمت", "کارکرد (ساعت)"]
            # row_number = 0
            # for col in range(len(columns)):
            #     worksheet.write(row_number, col, columns[col])
            #
            # project_table_to_excel = project_table.values_list("")

            context = {"chart": chart, "form": form, "project_kind": kind, "company_name": company,
                       "project_name": name, "total_hours": total_hours, "project_state": state,
                       "project_table": project_table,
                       "start_year": start_year, "start_month": start_month, "start_day": start_day,
                       "end_year": end_year, "end_month": end_month, "end_day": end_day}

        except ValueError:
            messages.error(request, "Error!")
            return redirect('/chart/sunburst')
        else:
            return render(request, 'dashboard/sunburst_chart.html', context)


class ProjectKindTreemapChartView(views.View):
    def get(self, request):
        form = DatePickerForm()

        # Dropdown for project_kind
        project_kind = DimProject.objects.all().values("project_kind").distinct().using("data")
        context = {"form": form, "project_kind": project_kind}
        return render(request, "dashboard/treemap_chart.html", context)

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')
        status = request.POST.get('status')
        kind = request.POST.get('project_kind')

        if start:
            year, month, day = start.split('-')
            year, month, day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(year, month, day).togregorian()
        else:
            start_date_greg = jdatetime.date(1399, 1, 1).togregorian()

        if end:
            year, month, day = end.split('-')
            year, month, day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(year, month, day).togregorian()
        else:
            end_date_greg = jdatetime.datetime.now().togregorian()

        if status == '0':
            status = 3
        if kind == '0':
            kind = 'حسابرسي مالي'
        try:
            projects_detail = (FactProjectactivity.objects.select_related("project_key")
                               .filter(project_key__status_key=status)
                               .filter(project_key__activation_date_key__created_ts__gte=start_date_greg,
                                       project_key__activation_date_key__created_ts__lte=end_date_greg)
                               .filter(project_key__project_kind__iexact=kind)
                               .values("project_key__project_name", "project_key__project_kind",
                                       "user_key__user_lastname", "user_key__job_key__job_title",
                                       "work_hours").using("data"))

            project_status = {1: "آماده اجرا", 2: "در حال اجرا", 3: "خاتمه ‌یافته"}

            values = [project['work_hours'] / 60 for project in projects_detail]
            df = pd.DataFrame.from_records(projects_detail)

            fig = px.treemap(df, path=['project_key__project_kind', 'project_key__project_name',
                                       'user_key__job_key__job_title', 'user_key__user_lastname'],
                             values=values)

            fig.update_layout(
                # grid=dict(columns=2, rows=1),
                margin=dict(t=0, l=0, r=0, b=0)
            )
            chart = fig.to_html()

            form = DatePickerForm()
            # Dropdown for project_kind

            project_kind = DimProject.objects.all().values("project_kind").distinct().using("data")
            context = {"chart": chart, "form": form, "status": project_status[int(status)], "start_date": start,
                       "end_date": end, "project_kind": project_kind}

        except ValueError:
            messages.error(request, "Error!")
            return redirect('/chart/treemap')
        else:
            return render(request, "dashboard/treemap_chart.html", context)


# def has_consecutive_signers(lst):
#     consecutive_count = 0
#     for i in range(len(lst) - 1):
#         if relativedelta(lst[i + 1], lst[i]).years < 2:
#             consecutive_count += 1
#             if consecutive_count == 3:
#                 return True
#         else:
#             consecutive_count = 0
#     return False

def has_consecutive_signers(lst):
    consecutive_count = 0
    for i in range(len(lst) - 1):
        if (lst[i + 1] - lst[i]).days < 365:
            consecutive_count += 1
            if consecutive_count == 3:
                return True
        else:
            consecutive_count = 0
    return False


class DuplicateSignerReport(views.View):
    def get(self, request):
        duplicate_signer = (DimProject.objects.values("cost_center")
                            .annotate(Count("project_key"))
                            .filter(project_key__count__gt=2).exclude(signer_user=None).using("data"))

        duplicate_records = (
            DimProject.objects.filter(cost_center__in=[item['cost_center'] for item in duplicate_signer])
            .values("cost_center", "signer_user", "activation_date_key__created_ts", "project_key",
                    "project_kind", "project_name")
            .exclude(signer_user=None).order_by("activation_date_key__created_ts")
            .using("data"))

        df = pd.DataFrame.from_records(duplicate_records)
        result_df = df.groupby(by=['signer_user', 'project_kind', 'cost_center']).agg(
            count=('activation_date_key__created_ts', 'count'),
            years_list=('activation_date_key__created_ts', lambda x: list(x))).reset_index()

        sign_consecutively = result_df[result_df['years_list'].apply(has_consecutive_signers)]

        merge_df = pd.merge(df, sign_consecutively, on=['signer_user', 'project_kind', 'cost_center'], how='right')

        merge_df['timestamp'] = merge_df['activation_date_key__created_ts'].apply(
            lambda x: datetime.combine(x, datetime.min.time()).timestamp())
        merge_df['jalali'] = merge_df['timestamp'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x).strftime("%Y/%m/%d"))

        # column_to_drop = ["years_list"]
        # final_brief_df = sign_consecutively.drop(columns=column_to_drop)
        # column_rename = {"signer_user": "امضا کننده", "project_kind": "نوع پروژه", "cost_center": "نام شرکت",
        #                  "count": "دفعات تکرار"}
        # final_brief_df = final_brief_df.rename(columns=column_rename)

        column_to_drop = ["activation_date_key__created_ts", "project_key", "count", "years_list", "timestamp"]
        merge_df = merge_df.drop(columns=column_to_drop)
        # column_rename = {"signer_user": "امضا کننده", "project_kind": "نوع پروژه", "cost_center": "نام شرکت",
        #                  "project_name": "نام پروژه", "jalali": "تاریخ"}
        # final_df = merge_df.rename(columns=column_rename)

        # table_brief = final_brief_df.to_html(classes="table table-striped", index=False)
        # table_detail = final_df.to_html(classes="table table-striped", index=False)
        final_table = merge_df.groupby('signer_user').apply(
            lambda x: x.to_dict(orient='records')).to_dict()
        final_table = tuple((key, tuple(value)) for key, value in final_table.items())

        context = {'final_table': final_table}
        # context = {"table_brief": table_brief, "table_detail": table_detail}
        return render(request, 'dashboard/duplicate_signer.html', context)


class DuplicateSignerReportRange(views.View):
    def get(self, request):
        form = DatePickerForm()
        return render(request, 'dashboard/duplicate_signer_range.html', {"form": form})

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')

        if start:
            year, month, day = start.split('-')
            start_year, start_month, start_day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(start_year, start_month, start_day).togregorian()
        if end:
            year, month, day = end.split('-')
            end_year, end_month, end_day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(end_year, end_month, end_day).togregorian()

        duplicate_signer = (DimProject.objects
                            .filter(activation_date_key__created_ts__gte=start_date_greg,
                                    activation_date_key__created_ts__lte=end_date_greg)
                            .values("cost_center")
                            .annotate(Count("project_key"))
                            .filter(project_key__count__gt=2).exclude(signer_user=None).using("data"))

        duplicate_records = (
            DimProject.objects.filter(activation_date_key__created_ts__gte=start_date_greg,
                               activation_date_key__created_ts__lte=end_date_greg)
            .filter(cost_center__in=[item['cost_center'] for item in duplicate_signer])
            .values("cost_center", "signer_user", "activation_date_key__created_ts", "project_key",
                    "project_kind", "project_name")
            .exclude(signer_user=None).order_by("activation_date_key__created_ts")
            .using("data"))

        df = pd.DataFrame.from_records(duplicate_records)
        result_df = df.groupby(by=['signer_user', 'project_kind', 'cost_center']).agg(
            count=('activation_date_key__created_ts', 'count'),
            years_list=('activation_date_key__created_ts', lambda x: list(x))).reset_index()

        sign_consecutively = result_df[result_df['years_list'].apply(has_consecutive_signers)]

        merge_df = pd.merge(df, sign_consecutively, on=['signer_user', 'project_kind', 'cost_center'], how='right')

        merge_df['timestamp'] = merge_df['activation_date_key__created_ts'].apply(
            lambda x: datetime.combine(x, datetime.min.time()).timestamp())
        merge_df['jalali'] = merge_df['timestamp'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x).strftime("%Y/%m/%d"))

        column_to_drop = ["years_list"]
        final_brief_df = sign_consecutively.drop(columns=column_to_drop)
        column_rename = {"signer_user": "امضا کننده", "project_kind": "نوع پروژه", "cost_center": "نام شرکت",
                         "count": "دفعات تکرار"}
        final_brief_df = final_brief_df.rename(columns=column_rename)

        column_to_drop = ["activation_date_key__created_ts", "project_key", "count", "years_list", "timestamp"]
        merge_df = merge_df.drop(columns=column_to_drop)
        column_rename = {"signer_user": "امضا کننده", "project_kind": "نوع پروژه", "cost_center": "نام شرکت",
                         "project_name": "نام پروژه", "jalali": "تاریخ"}
        final_df = merge_df.rename(columns=column_rename)

        table_brief = final_brief_df.to_html(classes="table table-striped", index=False)
        table_detail = final_df.to_html(classes="table table-striped", index=False)

        form = DatePickerForm()
        context = {"table_brief": table_brief, "table_detail": table_detail, "form": form,
                   "start_year": start_year, "start_month": start_month, "start_day": start_day,
                   "end_year": end_year, "end_month": end_month, "end_day": end_day
                   }
        return render(request, 'dashboard/duplicate_signer_range.html', context)


def custom_group(value):
    modir = "مدير"
    sarparast = "سرپرست"
    hesabras_arshad = "حسابرس ارشد"
    komak_hesabras = 'حسابرس کمک'
    hesabras = "حسابرس"

    if modir in value:
        return modir
    elif sarparast in value:
        return sarparast
    elif hesabras_arshad in value:
        return hesabras_arshad
    elif hesabras in value:
        return hesabras
    elif komak_hesabras in value:
        return komak_hesabras
    else:
        return 'other_group'


class StandardTimesheet(views.View):

    def get(self, request):
        page = request.GET.get('page', 1)
        # start_date_greg, end_date_greg = date_validation()
        # status = request.GET.get('status')
        projects_detail = (FactProjectactivity.objects.select_related("project_key")
                           .values("project_key__project_name", "project_key__project_kind",
                                   "user_key__job_key__job_rasteh", "user_key__user_lastname",
                                   "user_key__user_firstname", "work_minutes").using("data"))
        projects_detail = projects_detail.annotate(work_hours=F('work_minutes') / 60)
        df = pd.DataFrame.from_records(projects_detail)
        # df.to_csv("standard.csv", encoding="utf-8-sig")
        # df.value_counts(subset=['user_key__job_key__job_rasteh'])

        group_by_on_project_name = df.groupby(by=['project_key__project_name']).agg(
            work_hours_project=('work_hours', 'sum')).reset_index()

        group_by_on_project_name_and_job_rasteh = df.groupby(
            by=['project_key__project_name', 'user_key__job_key__job_rasteh']).agg(
            work_hours_rasteh=('work_hours', 'sum')).reset_index()

        join_df_on_project_name = pd.merge(group_by_on_project_name_and_job_rasteh, group_by_on_project_name,
                                           how='left',
                                           on='project_key__project_name')

        join_df_on_project_name['user_key__job_key__job_rasteh'] = join_df_on_project_name[
            'user_key__job_key__job_rasteh'].apply(
            custom_group)

        group_by_on_each_group = join_df_on_project_name.groupby(
            ['project_key__project_name', 'user_key__job_key__job_rasteh']).agg(
            work_hours_group=('work_hours_rasteh', 'sum')).reset_index()

        group_by_on_each_group.sort_values('project_key__project_name', inplace=True)

        final_result = pd.merge(group_by_on_each_group, group_by_on_project_name,
                                on='project_key__project_name', how='left')

        final_result['percentage'] = (final_result['work_hours_group'] / final_result['work_hours_project']) * 100

        thresholds = {"مدير": 6, "سرپرست": 14, "حسابرس ارشد": 20, "حسابرس": 50, "حسابرس کمک": 10}

        for index, row in final_result.iterrows():
            job_rasteh = row['user_key__job_key__job_rasteh']
            threshold = thresholds.get(job_rasteh, None)
            if threshold is not None:
                final_result.at[index, "threshold"] = 1 if row['percentage'] > threshold else 0

        filtered_df = final_result.groupby('project_key__project_name').filter(lambda x: x['threshold'].sum() != 0)

        # column_rename = {"project_key__project_name": "نام پروژه", "user_key__job_key__job_rasteh": "سمت",
        #                  "work_hours_group": "زمان صرف شده فرد (ساعت)", "work_hours_project": "کل زمان صرف شده (ساعت)",
        #                  "percentage": "درصد انجام کار", "threshold": "عدم رعایت بودجه‌بندی"}
        # final_df = filtered_df.rename(columns=column_rename)

        # final_table = final_df.to_html(classes="table table-striped", index=False)
        # json_records = filtered_df.reset_index().to_json(orient='records')
        final_table = filtered_df.groupby('project_key__project_name').apply(
            lambda x: x.to_dict(orient='records')).to_dict()

        # arr = []
        # arr = json.loads(json_records)

        # pagination
        final_table = tuple((key, tuple(value)) for key, value in final_table.items())
        paginator = Paginator(final_table, 10)
        try:
            result = paginator.page(page)
        except PageNotAnInteger:
            result = paginator.page(1)
        except EmptyPage:
            result = paginator.page(paginator.num_pages)

        context = {"final_table": result}

        return render(request, 'dashboard/standard_timesheet.html', context)


class StandardTimesheetRange(views.View):
    def get(self, request):
        form = DatePickerForm()
        return render(request, 'dashboard/standard_timesheet_range.html', {"form": form})

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')
        page = request.GET.get('page', 1)

        if start:
            year, month, day = start.split('-')
            start_year, start_month, start_day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(start_year, start_month, start_day).togregorian()
        if end:
            year, month, day = end.split('-')
            end_year, end_month, end_day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(end_year, end_month, end_day).togregorian()

        projects_detail = (FactProjectactivity.objects.select_related("project_key")
                           .filter(project_key__activation_date_key__created_ts__gte=start_date_greg,
                                   project_key__activation_date_key__created_ts__lte=end_date_greg)
                           .values("project_key__project_name", "project_key__project_kind",
                                   "user_key__job_key__job_rasteh", "user_key__user_lastname",
                                   "user_key__user_firstname", "work_minutes").using("data"))
        projects_detail = projects_detail.annotate(work_hours=F('work_minutes') / 60)
        df = pd.DataFrame.from_records(projects_detail)
        # df.to_csv("standard.csv", encoding="utf-8-sig")
        # df.value_counts(subset=['user_key__job_key__job_rasteh'])

        group_by_on_project_name = df.groupby(by=['project_key__project_name']).agg(
            work_hours_project=('work_hours', 'sum')).reset_index()

        group_by_on_project_name_and_job_rasteh = df.groupby(
            by=['project_key__project_name', 'user_key__job_key__job_rasteh']).agg(
            work_hours_rasteh=('work_hours', 'sum')).reset_index()

        join_df_on_project_name = pd.merge(group_by_on_project_name_and_job_rasteh, group_by_on_project_name,
                                           how='left',
                                           on='project_key__project_name')

        join_df_on_project_name['user_key__job_key__job_rasteh'] = join_df_on_project_name[
            'user_key__job_key__job_rasteh'].apply(
            custom_group)

        group_by_on_each_group = join_df_on_project_name.groupby(
            ['project_key__project_name', 'user_key__job_key__job_rasteh']).agg(
            work_hours_group=('work_hours_rasteh', 'sum')).reset_index()

        group_by_on_each_group.sort_values('project_key__project_name', inplace=True)

        final_result = pd.merge(group_by_on_each_group, group_by_on_project_name,
                                on='project_key__project_name', how='left')

        final_result['percentage'] = (final_result['work_hours_group'] / final_result['work_hours_project']) * 100

        thresholds = {"مدير": 6, "سرپرست": 14, "حسابرس ارشد": 20, "حسابرس": 50, "حسابرس کمک": 10}

        for index, row in final_result.iterrows():
            job_rasteh = row['user_key__job_key__job_rasteh']
            threshold = thresholds.get(job_rasteh, None)
            if threshold is not None:
                final_result.at[index, "threshold"] = 1 if row['percentage'] > threshold else 0

        filtered_df = final_result.groupby('project_key__project_name').filter(lambda x: x['threshold'].sum() != 0)

        # column_rename = {"project_key__project_name": "نام پروژه", "user_key__job_key__job_rasteh": "سمت",
        #                  "work_hours_group": "زمان صرف شده فرد (ساعت)", "work_hours_project": "کل زمان صرف شده (ساعت)",
        #                  "percentage": "درصد انجام کار", "threshold": "عدم رعایت بودجه‌بندی"}
        # final_df = filtered_df.rename(columns=column_rename)

        # final_table = final_df.to_html(classes="table table-striped", index=False)
        final_table = filtered_df.groupby('project_key__project_name').apply(
            lambda x: x.to_dict(orient='records')).to_dict()

        final_table = tuple((key, tuple(value)) for key, value in final_table.items())
        # paginator = Paginator(final_table, 10)
        # try:
        #     result = paginator.page(page)
        # except PageNotAnInteger:
        #     result = paginator.page(1)
        # except EmptyPage:
        #     result = paginator.page(paginator.num_pages)

        form = DatePickerForm()
        context = {"final_table": final_table, "form": form,
                   "start_year": start_year, "start_month": start_month, "start_day": start_day,
                   "end_year": end_year, "end_month": end_month, "end_day": end_day
                   }

        return render(request, 'dashboard/standard_timesheet_range.html', context)

class TrainingHours(views.View):
    def get(self, request):
        page = request.GET.get("page", 1)
        project_kind = "آموزش"
        training = (FactProjectactivity.objects
                    .filter(project_key__project_kind__iexact=project_kind).select_related("user_key")
                    .values("project_key__project_name", "user_key__user_lastname", "user_key__user_firstname",
                            "work_minutes", "user_key__job_key__job_title",
                            "project_key__activation_date_key__created_ts")
                    .order_by("project_key__activation_date_key__created_ts").using("data"))
        training = training.annotate(work_hours=F('work_minutes') / 60)
        df = pd.DataFrame.from_records(training)
        df['timestamp'] = df['project_key__activation_date_key__created_ts'].apply(
            lambda x: datetime.combine(x, datetime.min.time()).timestamp())
        df['year'] = df['timestamp'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x).strftime("%Y"))

        result_df = df.groupby(by=["user_key__user_lastname", "user_key__user_firstname", "year"]).agg(
            training_hours=('work_hours', 'sum')).reset_index()

        less_than_40h_training = result_df[result_df['training_hours'] < 40]

        # column_rename = {"user_key__user_lastname": "نام خانوادگی", "user_key__user_firstname": "نام",
        #                  "year": "سال", "training_hours": "مجموع ساعات آموزش"}
        # final_df = less_than_40h_training.rename(columns=column_rename)

        final_table = less_than_40h_training.groupby(['user_key__user_lastname', 'user_key__user_firstname']).apply(
            lambda x: x.to_dict(orient='records')).to_dict()
        # final_table = final_df.to_html(classes="table table-striped", index=False)
        final_table = tuple((key, tuple(value)) for key, value in final_table.items())
        paginator = Paginator(final_table, 10)
        try:
            result = paginator.page(page)
        except PageNotAnInteger:
            result = paginator.page(1)
        except EmptyPage:
            result = paginator.page(paginator.num_pages)
        context = {"final_table": result}

        return render(request, 'dashboard/training_hours.html', context)


class TrainingHoursRange(views.View):
    def get(self, request):
        form = DatePickerForm()
        return render(request, 'dashboard/training_hours_range.html', {"form": form})

    def post(self, request):
        start = request.POST.get('start')
        end = request.POST.get('end')

        if start:
            year, month, day = start.split('-')
            start_year, start_month, start_day = int(year), int(month), int(day)
            start_date_greg = jdatetime.date(start_year, start_month, start_day).togregorian()
        if end:
            year, month, day = end.split('-')
            end_year, end_month, end_day = int(year), int(month), int(day)
            end_date_greg = jdatetime.date(end_year, end_month, end_day).togregorian()
        project_kind = "آموزش"
        training = (FactProjectactivity.objects
                    .filter(project_key__project_kind__iexact=project_kind)
                    .filter(project_key__activation_date_key__created_ts__gte=start_date_greg,
                            project_key__activation_date_key__created_ts__lte=end_date_greg)
                    .select_related("user_key")
                    .values("project_key__project_name", "user_key__user_lastname", "user_key__user_firstname",
                            "work_minutes", "user_key__job_key__job_title",
                            "project_key__activation_date_key__created_ts")
                    .order_by("project_key__activation_date_key__created_ts").using("data"))
        training = training.annotate(work_hours=F('work_minutes') / 60)
        df = pd.DataFrame.from_records(training)
        df['timestamp'] = df['project_key__activation_date_key__created_ts'].apply(
            lambda x: datetime.combine(x, datetime.min.time()).timestamp())
        df['year'] = df['timestamp'].apply(
            lambda x: jdatetime.datetime.fromtimestamp(x).strftime("%Y"))

        result_df = df.groupby(by=["user_key__user_lastname", "user_key__user_firstname", "year"]).agg(
            training_hours=('work_hours', 'sum')).reset_index()

        less_than_40h_training = result_df[result_df['training_hours'] < 40]

        # column_rename = {"user_key__user_lastname": "نام خانوادگی", "user_key__user_firstname": "نام",
        #                  "year": "سال", "training_hours": "مجموع ساعات آموزش"}
        # final_df = less_than_40h_training.rename(columns=column_rename)

        # final_table = less_than_40h_training.to_html(classes="table table-striped", index=False)
        final_table = less_than_40h_training.groupby(['user_key__user_lastname', 'user_key__user_firstname']).apply(
            lambda x: x.to_dict(orient='records')).to_dict()
        final_table = tuple((key, tuple(value)) for key, value in final_table.items())
        form = DatePickerForm()
        context = {"final_table": final_table, "form": form,
                   "start_year": start_year, "start_month": start_month, "start_day": start_day,
                   "end_year": end_year, "end_month": end_month, "end_day": end_day
                   }

        return render(request, 'dashboard/training_hours_range.html', context)

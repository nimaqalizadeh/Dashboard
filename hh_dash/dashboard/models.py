# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class DimDate(models.Model):
    date_key = models.IntegerField(primary_key=True)
    created_ts = models.DateField()
    year = models.SmallIntegerField()
    month = models.SmallIntegerField()
    day = models.SmallIntegerField()
    jalali_created_date = models.CharField(max_length=10)
    jalali_year = models.SmallIntegerField()
    jalali_month = models.SmallIntegerField()
    jalali_day = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'Dim.Date'


class DimDate1(models.Model):
    date_key = models.IntegerField(primary_key=True)
    created_ts = models.DateField(blank=True, null=True)
    year = models.SmallIntegerField(blank=True, null=True)
    month = models.SmallIntegerField(blank=True, null=True)
    day = models.SmallIntegerField(blank=True, null=True)
    jalali_created_date = models.CharField(max_length=10)
    jalali_year = models.SmallIntegerField(blank=True, null=True)
    jalali_month = models.SmallIntegerField(blank=True, null=True)
    jalali_day = models.SmallIntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Dim.Date1'


class DimEstimation(models.Model):
    estimation_key = models.AutoField(primary_key=True)
    estimated_time_d_id = models.CharField(max_length=20)
    project_key = models.ForeignKey('DimProject', models.DO_NOTHING, db_column='project_Key')  # Field name made lowercase.
    activity_part = models.CharField(max_length=50)
    job_rasteh = models.CharField(max_length=50)
    estimated_minutes = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Dim.Estimation'


class DimJob(models.Model):
    job_key = models.AutoField(primary_key=True)
    job_id = models.SmallIntegerField()
    rasteh_id = models.SmallIntegerField()
    job_rasteh = models.CharField(max_length=50, blank=True, null=True)
    job_title = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'Dim.Job'


class DimProject(models.Model):
    project_key = models.AutoField(primary_key=True)
    project_detail_id = models.IntegerField()
    project_kind = models.CharField(max_length=100)
    cost_center = models.CharField(max_length=555)
    activation_date_key = models.ForeignKey(DimDate, models.DO_NOTHING, to_field='date_key', db_column='activation_date_key', blank=True, null=True)
    end_date_key = models.ForeignKey(DimDate, models.DO_NOTHING, db_column='end_date_key', related_name='dimproject_end_date_key_set', blank=True, null=True)
    project_name = models.CharField(max_length=255)
    project_cost = models.BigIntegerField(blank=True, null=True)
    status_key = models.ForeignKey('DimStatus', models.DO_NOTHING, db_column='status_key')
    is_active = models.BooleanField()
    project_course = models.SmallIntegerField(blank=True, null=True)
    signer_user = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'Dim.Project'


class DimStatus(models.Model):
    status_key = models.AutoField(primary_key=True)
    status = models.CharField(max_length=11)

    class Meta:
        managed = False
        db_table = 'Dim.Status'


class DimUser(models.Model):
    user_key = models.AutoField(primary_key=True)
    user_job_id = models.SmallIntegerField()
    user_id = models.SmallIntegerField()
    job_key = models.ForeignKey(DimJob, models.DO_NOTHING, db_column='job_key')
    user_firstname = models.CharField(max_length=30)
    user_lastname = models.CharField(max_length=30)
    start_date_key = models.ForeignKey(DimDate, models.DO_NOTHING, db_column='start_date_key')
    is_active = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'Dim.User'


class FactProjectactivity(models.Model):
    key_fact_pact = models.AutoField(primary_key=True)
    project_key = models.ForeignKey(DimProject, models.DO_NOTHING, db_column='project_key')
    user_key = models.ForeignKey(DimUser, models.DO_NOTHING, db_column='user_key')
    date_key = models.ForeignKey(DimDate, models.DO_NOTHING, db_column='date_key')
    activity_part = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')
    job_rasteh = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')
    estimation_key = models.ForeignKey(DimEstimation, models.DO_NOTHING, db_column='estimation_key', blank=True, null=True)
    work_minutes = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Fact.ProjectActivity'


class FactUseractivity(models.Model):
    key_fact_uact = models.AutoField(primary_key=True)
    sheet_h_id = models.IntegerField()
    user_key = models.ForeignKey(DimUser, models.DO_NOTHING, db_column='user_key')
    date_key = models.ForeignKey(DimDate, models.DO_NOTHING, db_column='date_key')
    training_minutes = models.IntegerField()
    overwork_minutes = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'Fact.UserActivity'


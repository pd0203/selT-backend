from django.contrib import admin
from .models import EventUser, Graduate, SelTHighSchool, TestScore, College, User, SelTUserInfo, HighSchoolWeight
class GraduateAdmin(admin.ModelAdmin):
    list_display = ['id', 'gpa', 'admission_type', 'is_accepted', 'graduation_year', 'college', 'highschool']
    search_fields = ['id', 'gpa', 'admission_type', 'is_accepted', 'graduation_year', 'college__college', 'college__campus','college__major', 'highschool__name']
    ordering = ['id']

class HighSchoolAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location']
    search_fields = ['id', 'name', 'location']
    ordering = ['name']

class TestScoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'subject', 'score', 'unit', 'grade', 'semester', 'user_info', 'created_at', 'updated_at']
    search_fields = ['id', 'subject', 'score', 'unit', 'grade', 'semester', 'user_info', 'created_at', 'updated_at']
    ordering = ['id']

class CollegeAdmin(admin.ModelAdmin):
    list_display = ['id', 'college', 'campus', 'major', 'year', 'admission_type', 'min_gpa', 'max_gpa', 'avg_gpa', 'med_gpa', 'stdev_gpa']
    search_fields = ['id', 'college', 'campus', 'major', 'year', 'admission_type', 'min_gpa', 'max_gpa', 'avg_gpa', 'med_gpa', 'stdev_gpa']
    ordering = ['id']

class HighSchoolWeightAdmin(admin.ModelAdmin):
    list_display = ['id', 'highschool', 'year', 'weight', 'admission_type'] 
    search_fields = ['id', 'highschool__name', 'highschool__location', 'year', 'weight', 'admission_type']
    ordering = ['id']

class EventUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email', 'is_male', 'admission_type', 'avg_gpa', 'college', 'highschool']
    search_fields = ['id', 'name', 'email', 'is_male', 'admission_type', 'avg_gpa', 'college__college', 'college__campus','college__major', 'highschool__name']
    ordering = ['id']

admin.site.register(Graduate, GraduateAdmin)
admin.site.register(SelTHighSchool, HighSchoolAdmin)
admin.site.register(TestScore, TestScoreAdmin)
admin.site.register(User)
admin.site.register(SelTUserInfo)
admin.site.register(College, CollegeAdmin)
admin.site.register(HighSchoolWeight, HighSchoolWeightAdmin) 
admin.site.register(EventUser, EventUserAdmin)
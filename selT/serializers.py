from wsgiref import validate
from rest_framework import serializers
from drf_writable_nested.serializers import WritableNestedModelSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework.exceptions import ValidationError
from selT.models import *

class SelTHighSchoolRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelTHighSchool
        fields = ['name', 'location']
    def create(self, validated_data):
        instance = SelTHighSchool.objects.get(**validated_data)
        return instance 
    def validate(self, data): 
        if not SelTHighSchool.objects.filter(name=data['name'], location=data['location']):
            raise ValidationError('해당 고등학교명과 위치와 동일한 고등학교가 존재하지 않습니다.')
        return data 

class SelTHighSchoolReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelTHighSchool
        fields = ['id', 'name', 'location']

class EventSelTHighSchoolReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SelTHighSchool
        fields = ['name', 'location']

class HighSchoolWeightCreateSerializer(serializers.ModelSerializer): 
    class Meta:
        model = HighSchoolWeight
        fields = ['year']

class CollegeAcceptanceReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollegeAcceptance
        fields = ['id', 'college', 'year', 'admission_type', 'total_acceptance', 'total_student',  'highschool_id']

class GraduateAllReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Graduate
        fields = ['id', 'gpa', 'admission_type', 'graduation_year', 'is_accepted', 'college_id', 'highschool_id']

class TestScoreCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestScore
        fields = ['subject', 'score', 'unit', 'grade', 'semester', 'user_info', 'created_at', 'updated_at']
    def validate(self, data): 
        if data['grade'] < 1 or data['grade'] > 3: 
           raise ValidationError('학년은 1학년부터 3학년까지만 입력 가능합니다')
        if data['score'] < 1 or data['score'] > 9: 
           raise ValidationError('성적은 1등급에서 9등급만 입력 가능합니다')
        if data['semester'] < 1 or data['semester'] > 2: 
           raise ValidationError('1학기 또는 2학기 둘 중 하나로 입력해주시기 바랍니다')
        return data  
class TestScoreAllReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestScore
        fields = ['id', 'subject', 'score', 'unit', 'grade', 'semester']

class CollegeRetrieveSerializer(serializers.ModelSerializer): 
    class Meta: 
        model = College   
        fields = ('college', 'major', 'year', 'admission_type')
    def create(self, validated_data):
        instance = College.objects.get(**validated_data)
        return instance 
    def validate(self, data): 
        if not College.objects.filter(college=data['college'], major=data['major'], year=data['year'], admission_type=data['admission_type']):
            raise ValidationError('해당 대학교명, 캠퍼스, 전공, 년도, 입시전형과 일치하는 데이터가 존재하지 않습니다.')
        return data  

class CollegeReadSerializer(serializers.ModelSerializer): 
    class Meta:
        model = College  
        fields = ('id', 'college', 'campus', 'major', 'year', 'admission_type', 'min_gpa', 'max_gpa', 'avg_gpa', 'med_gpa', 'stdev_gpa')

class CollegeFilterReadSerializer(serializers.ModelSerializer): 
    class Meta:
        model = College  
        fields = ('college', 'major')
        
class EventCollegeReadSerializer(serializers.ModelSerializer): 
    class Meta:
        model = College  
        fields = ('college', 'major')

class EventUserCreateSerializer(WritableNestedModelSerializer):
    college = CollegeRetrieveSerializer(many=False, required=False)
    highschool = SelTHighSchoolRetrieveSerializer(many=False, required=True)
    class Meta:
        model = EventUser 
        fields = ('name', 'email', 'is_male', 'admission_type', 'avg_gpa', 'college', 'highschool') 

class UserInfoReadSerializer(serializers.ModelSerializer): 
    highschool = SelTHighSchoolReadSerializer(many=False, read_only=True) 
    testscore = TestScoreAllReadSerializer(many=True, read_only=True)
    class Meta:
        model = SelTUserInfo  
        fields = ('id', 'admission_type', 'is_male', 'highschool', 'testscore')

class UserInfoUpdateSerializer(WritableNestedModelSerializer): 
    college = CollegeRetrieveSerializer(many=False, required=False)
    class Meta:
        model = SelTUserInfo  
        fields = ('admission_type', 'college')

class UserInfoSignUpUpdateSerializer(WritableNestedModelSerializer): 
    highschool = SelTHighSchoolRetrieveSerializer(many=False, required=True)
    class Meta: 
        model = SelTUserInfo  
        fields = ('status', 'highschool', 'birthday', 'is_male')
    def validate(self, data): 
        if data['status'] != '학생' and data['status'] != '학부모' and data['status'] != '선생님':
           raise ValueError('회원유형은 학생 또는 학부모 또는 선생님 중 하나로 선택해 주시기 바랍니다')
        return data

class UserReadSerializer(serializers.ModelSerializer): 
    selT_user_info = UserInfoReadSerializer() 
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password', 'sns_type', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'created_at', 'updated_at', 'deleted_at', 'selT_user_info') 

class CustomRegisterSerializer(RegisterSerializer):
    username = None
    name = serializers.CharField()
    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['name'] = self.validated_data.get('name', '')
        return data

class GraduateUploadSerializer(serializers.ModelSerializer):
    file_uploaded = serializers.FileField()
    class Meta:
        model = Graduate
        fields = ['file_uploaded']
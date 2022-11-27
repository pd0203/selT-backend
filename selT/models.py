## DB다이어그램에서 DB설계를 시각화 한 뒤, Models.py에서 DB를 코드로 입력(모델링) ##

from django.db import models
from django.contrib.auth.models import ( AbstractUser, BaseUserManager )

## 하나의 클래스 = 하나의 DB 테이블을 코드화 ##
class SelTHighSchool(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    class Meta:
        db_table = "SelT_Highschools"
        constraints = [models.UniqueConstraint(fields = ['name', 'location'], name = 'unique_highschool')]
    def __str__(self):
        return f'{self.name} [{self.location}]'

class HighSchoolWeight(models.Model):
    weight = models.FloatField()
    year = models.PositiveSmallIntegerField()
    admission_type = models.CharField(max_length=100, null=True) 
    highschool = models.ForeignKey(SelTHighSchool, on_delete=models.CASCADE)
    class Meta:
        db_table = "Highschool_Weights"
    def __str__(self):
        return f'{self.highschool} - {self.year}: {self.weight}'

class CollegeAcceptance(models.Model):
    college = models.CharField(max_length=200)
    year = models.PositiveSmallIntegerField()
    admission_type = models.CharField(max_length=100)
    total_acceptance = models.PositiveIntegerField()
    total_student = models.PositiveIntegerField() 
    highschool = models.ForeignKey(SelTHighSchool, on_delete=models.CASCADE)
    class Meta:
        db_table = "College_Acceptances"
    def __str__(self):
        return f'{self.college} {self.total_acceptance} {self.year}'

class College(models.Model):
    college = models.CharField(max_length=100, null=True)
    campus = models.CharField(max_length=100, null=True)
    major = models.CharField(max_length=100, null=True) 
    year = models.PositiveSmallIntegerField(null=True)
    admission_type = models.CharField(max_length=100, null=True)
    min_gpa = models.FloatField(null=True)
    max_gpa = models.FloatField(null=True)
    avg_gpa = models.FloatField(null=True)
    med_gpa = models.FloatField(null=True)
    stdev_gpa = models.FloatField(null=True)
    class Meta:
        db_table = 'Colleges'
        constraints = [models.UniqueConstraint(fields = ['college', 'campus', 'major', 'year', 'admission_type'], name = 'unique_college')]
    def __str__(self): 
        return f'{self.college} - {self.major}, {self.id}'

class Graduate(models.Model):
    gpa = models.FloatField(null=True)
    admission_type = models.CharField(max_length=100, null=True)
    graduation_year = models.IntegerField(null=True)
    is_accepted = models.BooleanField(null=True)
    graduation_year = models.PositiveSmallIntegerField(null=True)
    college = models.ForeignKey(College, on_delete=models.CASCADE, null=True)
    highschool = models.ForeignKey(SelTHighSchool, on_delete=models.CASCADE, null=True, unique=False)
    file_uploaded = models.FileField(null=True)
    class Meta:
        db_table = "Graduates"
    def __str__(self):
        return f'{self.college}, {self.gpa}'

class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        # Create a User with the given email & password 
        if not email:
            raise ValueError(('Email address required'))

        user = self.model(
            email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        # Create a SuperUser with the given email & password 
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True) 
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser): 
    name = models.CharField(max_length=30, unique=False) 
    email = models.EmailField(max_length=128, unique=True)
    sns_type = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True) 
     
    username = None 
    first_name = None
    last_name = None
    date_joined = None
    
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()
    class Meta:
        db_table = 'Users'
    def __str__(self): 
        return self.email
    
class SelTUserInfo(models.Model):
    admission_type = models.CharField(max_length=30, null=True) 
    status = models.CharField(default='student', max_length=10, null=True)
    is_male = models.BooleanField(default=True) 
    birthday = models.DateField(null=True)  
    user = models.OneToOneField(User, related_name='selT_user_info', null=True, on_delete=models.CASCADE)
    highschool = models.ForeignKey(SelTHighSchool, related_name='selT_user_info', null=True, on_delete=models.CASCADE)
    college = models.ForeignKey(College, related_name='selT_user_info', null=True, on_delete=models.CASCADE)
    class Meta:
        db_table = 'SelT_User_Infos'
    def __str__(self): 
        return str(self.user)

class EventUser(models.Model):
    name = models.CharField(max_length=100) 
    email = models.CharField(max_length=100)
    is_male = models.BooleanField(default=True) 
    admission_type = models.CharField(max_length=100, null=True) 
    avg_gpa = models.FloatField()
    college = models.ForeignKey(College, related_name='Event_Users', null=True, on_delete=models.CASCADE) 
    highschool = models.ForeignKey(SelTHighSchool, related_name='Event_Users', null=True, on_delete=models.CASCADE)
    class Meta:
        db_table = 'Event_Users'
    def __str__(self): 
        return str(self.name)

class TestScore(models.Model):
    subject = models.CharField(max_length=100)
    score = models.FloatField()
    unit = models.PositiveSmallIntegerField()
    grade = models.PositiveSmallIntegerField()
    semester = models.PositiveSmallIntegerField()
    user_info = models.ForeignKey(SelTUserInfo, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = "Test_Scores"
    def __str__(self):
        return f'{self.subject}: ({self.score})'   

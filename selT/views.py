# 로직 구현 파일(views.py) - 모든 api 생성 #

from rest_framework import status
from selT.models import * 
from selT.serializers import * 

from django.db.models import Avg, Count
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from json.decoder import JSONDecodeError
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.kakao import views as kakao_views
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView, RegisterView, LoginView
from dj_rest_auth.jwt_auth import set_jwt_cookies
from rest_framework_simplejwt.settings import (api_settings as jwt_settings,)
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from datetime import datetime

import math 
import pandas as pd
import requests, json

service_base_url = getattr(settings, 'SERVICE_BASE_URL')
kakao_redirect_url = getattr(settings, 'KAKAO_CALLBACK_URL')
kakao_rest_api_key = getattr(settings, 'KAKAO_RESTAPI_KEY')

# 셀티 이벤트 및 확장버전용으로 유저가 고등학교 입력시 자동완성으로 보여줄 리스트를 반환하는 API  
class HighSchoolAPI(ModelViewSet):
    def get_queryset(self): 
        queryset = SelTHighSchool.objects.all()
        highschool = self.request.query_params.get('name', '') 
        location = self.request.query_params.get('location', '')
        if highschool or location: 
           queryset = SelTHighSchool.objects.order_by('name', 'location').values('name', 'location').distinct()
           queryset = queryset.filter(name__icontains=highschool).filter(location__icontains=location) 
        return queryset 
    def get_serializer_class(self):
        highschool = self.request.query_params.get('name', '')
        location = self.request.query_params.get('location', '')
        if highschool or location:  
           return EventSelTHighSchoolReadSerializer
        return SelTHighSchoolReadSerializer

class GraduateAPI(ModelViewSet):
    serializer_class = GraduateAllReadSerializer
    queryset = Graduate.objects.all()
    def get_queryset(self):
        return self.queryset.order_by('id')

# 정형화된 엑셀 파일을 DB에 넣어주는 API 
class UploadCSVAPI(ModelViewSet):
    serializer_class = GraduateUploadSerializer
    queryset = Graduate.objects.all()
    def get(self, request):
        return Response("GET API")
    def create(self, request):
        # 엑셀 파일을 변수에 담기
        file_uploaded = request.FILES.get('file_uploaded')
        # pandas 라이브러리를 활용하여 엑셀 파일 읽기 
        reader = pd.read_excel(file_uploaded)
        # 엑셀 파일을 row 단위로 읽으며, 각 DB 테이블에 데이터 담기 
        for _, row in reader.iterrows():
            College.objects.get_or_create(
                college = row['College'],
                campus = row['Campus'],
                major = row['Major'],
                year = row['Graduation Year'],
                admission_type = row['Admission Type']
            )
            if pd.isnull(row['Highschool']) and pd.isnull(row['Location']):
                hs = None
            else:
                SelTHighSchool.objects.get_or_create(
                name = row['Highschool'],
                location = row['Location']
                )
                hs = SelTHighSchool.objects.get(
                name = row['Highschool'],
                location = row['Location']
                )
            Graduate.objects.create(
                gpa = row['GPA'],
                admission_type = row['Admission Type'],
                is_accepted = row['Is Accepted'],
                graduation_year = row['Graduation Year'],
                college = College.objects.get(college = row['College'], 
                                              campus = row['Campus'],
                                              major = row['Major'],
                                              year = row['Graduation Year'], 
                                              admission_type = row['Admission Type']),
                highschool = hs
            )
        mingpa, maxgpa = 10.0, 0.0
        college_set = College.objects.all()
        # 위에서 각 DB 테이블에 담은 데이터 기반으로 College 테이블에 산출한 데이터 값 삽입 
        for coll in college_set.iterator():
            grad_set = Graduate.objects.filter(is_accepted = True, college = coll)
            maxgpa = grad_set.order_by('-gpa')[0].gpa
            mingpa = grad_set.order_by('gpa')[0].gpa
            gpa_sum = grad_set.aggregate(models.Sum('gpa'))['gpa__sum']
            avggpa = gpa_sum / grad_set.count()
            stdev = grad_set.aggregate(models.StdDev('gpa'))['gpa__stddev']
            midval = (grad_set.count() + 1) // 2
            if (grad_set.count()) % 2 == 1:
                medgpa = grad_set.order_by('gpa')[midval-1].gpa
            else:
                medgpa = ((grad_set.order_by('gpa')[midval-1].gpa + 
                          grad_set.order_by('gpa')[midval].gpa) / 2)
            coll.min_gpa = mingpa
            coll.max_gpa = maxgpa
            coll.avg_gpa = avggpa
            coll.med_gpa = medgpa
            coll.stdev_gpa = stdev
            coll.save()
        return Response('UPLOADING CSV FILES TO DATABASE SUCCEEDED')

class CollegeAcceptanceAPI(ModelViewSet):
    serializer_class = CollegeAcceptanceReadSerializer
    queryset = CollegeAcceptance.objects.all()
    def get_queryset(self):
        return self.queryset.order_by('id')

# 셀티 이벤트용으로 유저가 대학교 및 전공 입력시 자동완성으로 보여줄 리스트를 반환하는 API   
class CollegeEventAPI(ModelViewSet):
    serializer_class = EventCollegeReadSerializer
    def get_queryset(self): 
        queryset = College.objects.all()
        college = self.request.query_params.get('college', '') 
        major = self.request.query_params.get('major', '')
        admission_type = self.request.query_params.get('admission_type', '')
        if college or major: 
           queryset = College.objects.order_by('college', 'major', 'admission_type').values('college', 'major', 'admission_type').distinct()
           if admission_type: 
              queryset = queryset.filter(college__icontains=college).filter(major__icontains=major).filter(admission_type=admission_type)
           else:  
              queryset = queryset.filter(college__icontains=college).filter(major__icontains=major)
        return queryset 

# 셀티 확장 버전용으로 유저가 대학교 및 전공 입력시 자동완성으로 보여줄 리스트를 반환하는 API   
class CollegeFilterAPI(ModelViewSet):
    serializer_class = CollegeFilterReadSerializer 
    def get_queryset(self): 
        queryset = College.objects.all()
        college = self.request.query_params.get('college', '') 
        major = self.request.query_params.get('major', '')
        admission_type = self.request.query_params.get('admission_type', '')
        if college or major: 
           queryset = College.objects.order_by('college', 'major', 'admission_type').values('college', 'major', 'admission_type').distinct()
           if admission_type: 
              queryset = queryset.filter(college__icontains=college).filter(major__icontains=major).filter(admission_type=admission_type)
           else:  
              queryset = queryset.filter(college__icontains=college).filter(major__icontains=major)
        return queryset 

class CollegeAPI(ModelViewSet):
    queryset = College.objects.all()
    serializer_class = CollegeReadSerializer

# 셀티 이벤트용 입시 예측 API
class CollegePredictionEventAPI(ModelViewSet):
    queryset = EventUser.objects.all()
    serializer_class = EventUserCreateSerializer

    def create(self, request):
        try: 
          # EventUser 레코드 생성을 위한 작업
          # [1] DB Table 구조에 맞춰 데이터 변형
          latest_year = 2021 
          request.data['college']['year'] = latest_year 
          request.data['college']['admission_type'] = request.data['admission_type']
  
          # [2] EventUser 시리얼라이저 기반으로 DB에 레코드 Create
          serializer = self.get_serializer(data=request.data)
          serializer.is_valid(raise_exception=True)
          self.perform_create(serializer)
  
          # College Percentage 값 추출과 Feedback을 만들기 위한 작업
          # [1] 유저 데이터 파싱
          user_gpa = request.data['avg_gpa']
          if user_gpa < 1.0 or user_gpa > 9.0:
              raise ValueError("성적을 올바르게 입력해주시기 바랍니다") 
          is_male = request.data['is_male'] 
          admission_type = request.data['admission_type']
          highschool_name = request.data['highschool']['name']
          highschool_location = request.data['highschool']['location']
          college = request.data['college']['college']
          if is_male and '여대' in college:
                 raise ValueError("남성은 여대에 지원할 수 없습니다") 
          major = request.data['college']['major']
          year = request.data['college']['year']
  
          # [2] 유저 고등학교 조회 및 해당 가중치 조회
          highschool_weight = self.get_highschool_weight(highschool_name, highschool_location, year, admission_type)
  
          # [3] 희망 대학교 & 전공 조회
          college = College.objects.filter(college=college, major=major, year=year, admission_type=admission_type)[0]
          if not college:
             raise ValueError("현재 해당 대학교 및 학과는 아직 서비스되지 않습니다")
         
          # [4] 유저 성적과 해당 고등학교 가중치로 최종 성적 산출
          gpa = user_gpa * highschool_weight
          
          # [5] Z-Score 산출
          z_score = self.get_z_score(gpa, college)
  
          # [6] 백분율 산출
          college_percentage = self.get_percentage(z_score)
  
          # [7] Feedback 결정
          feedback = self.get_feedback(college_percentage)
          
          # [8] 프론트에 결과값 반환
          headers = self.get_success_headers(serializer.data)
          return Response({"college_percentage": college_percentage, "feedback": feedback}, status=status.HTTP_200_OK, headers=headers)
        except ValueError as v:
           return Response({'ERROR_MESSAGE': v.args}, status=status.HTTP_400_BAD_REQUEST)
    def get_highschool_weight(self, highschool_name, highschool_location, year, admission_type): 
        highschool = SelTHighSchool.objects.filter(name=highschool_name, location=highschool_location)[0]
        if not highschool:
           raise ValueError("현재 해당 고등학교는 아직 서비스되지 않습니다")
        highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type=admission_type, highschool=highschool)
        highschool_weight = 1 
        if highschool_weight_rough:
           highschool_weight = highschool_weight_rough[0].weight 
        elif not highschool_weight_rough and admission_type == '교과' : 
             highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type='종합', highschool=highschool)[0].weight
             highschool_weight = highschool_weight_rough * 0.85
        elif not highschool_weight_rough and admission_type == '종합':
             highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type='교과', highschool=highschool)[0].weight
             highschool_weight = highschool_weight_rough * 1.15
        return highschool_weight 
    def get_z_score(self, gpa, college): 
        z_score = 0 
        if college.stdev_gpa < 0.14 and college.admission_type == '교과': 
           z_score =  (gpa - college.avg_gpa) / 0.14  
        elif college.stdev_gpa >= 0.14 and college.admission_type == '교과': 
           z_score =  (gpa - college.avg_gpa) / college.stdev_gpa 
        elif college.stdev_gpa < 0.18 and college.admission_type == '종합': 
             z_score =  (gpa - college.avg_gpa) / 0.18
        elif college.stdev_gpa >= 0.18 and college.admission_type == '종합': 
             z_score =  (gpa - college.avg_gpa) / college.stdev_gpa 
        return z_score 
    def get_percentage(self, z_score): 
        result = 100 - (100 * 0.5 * (math.erf(z_score / 2 ** .5) + 1)) 
        if result > 80 : 
           result = result * 0.99
        return result
    def get_feedback(self, college_percentage):
        if college_percentage >= 0 and college_percentage < 20:
           return '꿈 깨'
        elif college_percentage >= 20 and college_percentage < 40: 
           return '많이 분발해'
        elif college_percentage >= 40 and college_percentage < 60: 
           return '한번 지원해봐'
        elif college_percentage >= 60 and college_percentage < 80: 
           return '이 정도면 콜?'
        elif college_percentage >= 80 and college_percentage <= 100:
           return '묻고 따블로 가'

# 셀티 확장 버전용 입시 예측 API 
class CollegePredictionAPI(ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = SelTUserInfo.objects.all()
    serializer_class = UserInfoUpdateSerializer
    def get_object(self): 
       queryset = self.get_queryset()
       if self.action == 'update':
          return get_object_or_404(queryset, user=self.request.user)
       return get_object_or_404(self.get_queryset())
    def update(self, request, *args, **kwargs): 
        try:
          partial = kwargs.pop('partial', False)
          # SelTUserInfo 레코드 생성을 위한 작업
          # [1] DB Table 구조에 맞춰 데이터 변형  
          latest_year = 2021
          if 'college' in request.data: 
              request.data['college']['admission_type'] = request.data['admission_type']
              request.data['college']['year'] = latest_year

          # [2] 해당 유저의 testscore를 DB에 레코드 Create 
          user_userinfo_id = SelTUserInfo.objects.filter(user_id=request.user.id)[0].id
          user_userinfo = SelTUserInfo.objects.filter(id=user_userinfo_id)[0]
          user_highschool = SelTHighSchool.objects.filter(id=user_userinfo.highschool_id)[0]
          self.create_testscore(user_userinfo_id, request.data['testscore'])

          # [3] SelTUserInfo 시리얼라이저 기반으로 DB에 레코드 Update  
          instance = self.get_object()
          serializer = self.get_serializer(instance, data=request.data, partial=partial)
          serializer.is_valid(raise_exception=True)
          self.perform_update(serializer)
          if getattr(instance, '_prefetched_objects_cache', None):
              # If 'prefetch_related' has been applied to a queryset, we need to
              # forcibly invalidate the prefetch cache on the instance.
              instance._prefetched_objects_cache = {}

          # College Percentage 값 추출과 Feedback을 만들기 위한 작업 
          # [1] 유저 데이터 파싱
          user_gpa = self.get_user_gpa(request.data['testscore']) 
          is_male = user_userinfo.is_male
          admission_type = request.data['admission_type']
          highschool_name = user_highschool.name
          highschool_location = user_highschool.location  
          year = latest_year
          college = request.data['college']['college'] if 'college' in request.data else None 
          major = request.data['college']['major'] if 'college' in request.data else None
          if is_male and 'college' in request.data and '여대' in college:
             raise ValueError("남성은 여대에 지원할 수 없습니다")
          is_prediction_available = True if college and major else False 

          # [2] 고교 가중치 구하기 
          highschool_weight = self.get_highschool_weight(user_highschool, year, admission_type)
  
          # [3] 유저 성적과 해당 고등학교 가중치로 최종 성적 산출 
          gpa = self.get_weighted_gpa(user_gpa, highschool_weight)
  
          # [4] 합격률 높은 순으로 인기 대학&전공 리스트 반환 
          colleges_by_difficulty = self.get_colleges_order_by_difficulty(admission_type) 
          
          # [5] 합격 가능성 높은 상위 대학&전공 리스트
          college_diagnosis = self.get_diagnosis(gpa, admission_type, is_male, colleges_by_difficulty, 21, 3)
          
          # [6] 헤더 설정 
          headers = self.get_success_headers(serializer.data)
          
          # [7] 프론트에 결과값 반환 
          ## 1. 희망 대학교&전공 미입력으로 입시 진단만 가능한 경우 
          if not is_prediction_available: 
             return Response({"진단결과" : college_diagnosis}, status=status.HTTP_200_OK, headers=headers)
          
          ## 2. 희망 대학교&전공 입력으로 입시 예측, 피드백, 입시 진단 모두 가능한 경우 
          college = College.objects.filter(college=college, major=major, year=year, admission_type=admission_type)[0]
          if not college: 
              raise ValueError("현재 입력하신 대학교 및 학과에 대한 해당 입시 젼형은 아직 서비스되지 않습니다")
          z_score = self.get_z_score(gpa, college)
          college_percentage = self.get_percentage(z_score)
          feedback = self.get_feedback(college_percentage) 
          return Response({"예측결과" : college_percentage, "피드백": feedback, "진단결과" : college_diagnosis}, status=status.HTTP_200_OK, headers=headers)
        except ValueError as v:
            return Response({'ERROR_MESSAGE': v.args}, status=status.HTTP_400_BAD_REQUEST)
    # 데이터 부족 문제로 특정 고등학교가 교과/종합 둘 중 하나의 전형으로만 가중치가 존재할 시 다른 입시 전형 가중치값을 산출해주는 함수 
    def get_highschool_weight(self, highschool, year, admission_type): 
        highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type=admission_type, highschool=highschool)
        highschool_weight = 1 
        if highschool_weight_rough:
           highschool_weight = highschool_weight_rough[0].weight 
        elif not highschool_weight_rough and admission_type == '교과' : 
             highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type='종합', highschool=highschool)[0].weight
             highschool_weight = highschool_weight_rough * 0.85
        elif not highschool_weight_rough and admission_type == '종합':
             highschool_weight_rough = HighSchoolWeight.objects.filter(year=year, admission_type='교과', highschool=highschool)[0].weight
             highschool_weight = highschool_weight_rough * 1.15
        return highschool_weight 
    # 유저의 대학교&학과별 표준점수를 산출하는 함수 
    def get_z_score(self, gpa, college): 
        z_score = 0 
        if college.stdev_gpa < 0.14 and college.admission_type == '교과': 
           z_score =  (gpa - college.avg_gpa) / 0.14  
        elif college.stdev_gpa >= 0.14 and college.admission_type == '교과': 
           z_score =  (gpa - college.avg_gpa) / college.stdev_gpa 
        elif college.stdev_gpa < 0.18 and college.admission_type == '종합': 
             z_score =  (gpa - college.avg_gpa) / 0.18
        elif college.stdev_gpa >= 0.18 and college.admission_type == '종합': 
             z_score =  (gpa - college.avg_gpa) / college.stdev_gpa 
        return z_score 
    # 유저의 표준점수 기반으로 합격률을 산출하는 함수 
    def get_percentage(self, z_score): 
        result = 100 - (100 * 0.5 * (math.erf(z_score / 2 ** .5) + 1)) 
        if result > 80 : 
           result = result * 0.99
        return result 
    # 유저에게 합격률별 맞춤형 피드백을 반환하는 함수 
    def get_feedback(self, college_percentage):
        if college_percentage >= 0 and college_percentage < 20:
           return '꿈 깨'
        elif college_percentage >= 20 and college_percentage < 40: 
           return '많이 분발해'
        elif college_percentage >= 40 and college_percentage < 60: 
           return '한번 지원해봐'
        elif college_percentage >= 60 and college_percentage < 80: 
           return '이 정도면 콜?'
        elif college_percentage >= 80 and college_percentage <= 100:
           return '묻고 따블로 가'
    # 유저의 최종 평균 성적, 입시 전형을 고려하여 합격률 높은 대학교&학과 리스트를 반환하는 입시 진단 함수 
    def get_diagnosis(self, gpa, admission_type, is_male, colleges_by_difficulty, list_limit, major_limit):
        result_list = [] 
        list_count = 0 
        list_on_limit = False 
        for college_name, difficulty in colleges_by_difficulty:
            temp_college_set = College.objects.filter(college=college_name, admission_type = admission_type)
            major_count = 0 
            for college in temp_college_set.iterator(): 
                z_score = self.get_z_score(gpa, college) 
                college_percentage = self.get_percentage(z_score)
                if is_male and '여대' in college.college: 
                   continue 
                if college_percentage >= 70: 
                   result = {'college': college.college, 'major': college.major, 'college_percentage': college_percentage}
                   result_list.append(result)
                   list_count += 1 
                   major_count += 1 
                if major_count >= major_limit:
                   break 
                if list_count >= list_limit :
                   list_on_limit = True
                   break 
            if list_on_limit: 
               break 
        result_list.sort(key=lambda x: (x['college_percentage'], x['college']), reverse=True)
        return result_list
    # 고등학교 가중치가 부여된 유저 성적을 산출하는 함수 
    def get_weighted_gpa(self, user_gpa, highschool_weight):
        return user_gpa * highschool_weight
    # 대학교를 입시전형별 합격 난이도대로 정렬하여 반환하는 함수 
    def get_colleges_order_by_difficulty(self, admission_type): 
        # 유저에게 보여줄 대학 리스트에서 제외할 대학교
        exceptions = ['우석대','원광대','경상대','인제대','가천대(메디컬)','경남대','계명대','동의대','강릉원주대','가톨릭대(성의)','을지대','조선대','공주대','신라대','대구대','인천가톨릭대(송도)','대구한의대']
        all_colleges = College.objects.filter(admission_type=admission_type)
        result_list = dict() 
        college_prev = ''
        gpa_sum = 0
        major_count = 1
        for college in all_colleges.iterator():
            # 유저에게 보여줄 대학 리스트에서 데이터부족으로 표준편차가 0.001 미만이거나 교대이거나 디자인학부는 제외  
            if college.stdev_gpa < 0.001 or exceptions.count(college.college) or '교대' in college.college or '디자인학부(공예전공)' in college.major: 
               continue 
            if college.college != college_prev: 
               gpa_sum = college.avg_gpa
               major_count = 1  
            else : 
               gpa_sum += college.avg_gpa 
               major_count += 1 
            college_prev = college.college
            # 각 대학교별로 평균낸 합격 성적에 차등티어값을 곱하여 합격 난이도값을 산출 
            result_list[college.college] = (gpa_sum/major_count)*self.get_college_value(college.college,college.major)
        # 합격 난이도대로 대학교를 정렬하여 리스트로 반환 
        sorted_college_by_difficulty = sorted(result_list.items(), key= lambda item:item[1], reverse=False) 
        return sorted_college_by_difficulty
    # 특정 대학교&학과의 티어값을 반환하는 함수 
    def get_college_value(self, college, major):
        tier_0 = ['의예과', '의과대학', '한의예과', '치의예과', '치의학과']
        tier_1 = ['서울대', '한국과학기술원(KAIST)', '포항공과대(POSTECH)']
        tier_2 = ['연세대', '고려대']
        tier_3 = ['서강대', '성균관대', '한양대', '이화여대', '서울교대']
        tier_4 = ['중앙대', '경희대', '한국외대', '서울시립대', '경인교대']
        tier_5 = ['건국대', '동국대', '홍익대', '숙명여대', '인하대', '아주대', '춘천교대', '울산과학기술원(UNIST)']
        tier_6 = ['부산대', '울산대', '경북대', '전북대', '전남대', '서울과학기술대', '국민대', '숭실대', '세종대', '단국대', '한국항공대', '성신여대'] 
        if major in tier_0: 
            return 0.5 
        if college in tier_1: 
             return 0.45
        elif college in tier_2: 
             return 0.52
        elif college in tier_3: 
             return 0.66
        elif college in tier_4: 
             return 0.74
        elif college in tier_5: 
             return 0.82
        elif college in tier_6: 
             return 0.9 
        else : 
             return 1 
    # 유저 성적 리스트를 한번에 DB TestScore 테이블에 삽입하는 함수 
    def create_testscore(self, userinfo_id, testscore_set):
        for testscore in testscore_set:    
            TestScore.objects.get_or_create( 
                subject = testscore['subject'], 
                score = testscore['score'],
                unit = testscore['unit'],
                grade = testscore['grade'],
                semester = testscore['semester'], 
                user_info_id = userinfo_id  
            ) 
        return Response({"Hello"},status=status.HTTP_200_OK) 
    # 유저가 입력한 각 학년 과목별 성적을 계산하여 최종 평균 성적을 산출하는 함수 
    def get_user_gpa(self, testscore_set):
        # 각 학년별 성적을 담을 배열 생성
        gpa_unit = [[0,0],[0,0],[0,0],[0,0]]
        gpa_by_grade = [0,0,0,0]
        gpa_sum = 0
        grade_count = 0  
        for testscore in testscore_set:
            # grade : 학년 
            grade = testscore['grade']
            # gpa_unit[grade][0] : 모든 과목 성적 * 단위수를 더한 값 저장
            if testscore['score'] < 1.0 or testscore['score'] > 9.0:
               raise ValueError('성적을 올바르게 입력해주시기 바랍니다')
            gpa_unit[grade][0] += testscore['score'] * testscore['unit']
            # gpa_unit[grade][1] : 모든 단위수를 더한 값 저장 
            gpa_unit[grade][1] += testscore['unit']
        # 각 학년별 단위수를 고려한 평균 성적 계산
        for i in range(1, len(gpa_unit)):
            if gpa_unit[i][1] == 0:
               break 
            gpa_by_grade[i] = gpa_unit[i][0]/gpa_unit[i][1]
            gpa_sum += gpa_by_grade[i]
            grade_count += 1
        # 유저의 최종 고교 성적 = 총 학년별 평균 성적 합계 / 재학 학년 수 
        user_gpa = gpa_sum / grade_count 
        return user_gpa 

# 고등학교 가중치 생성 API 
class HighSchoolWeightAPI(ModelViewSet):
    queryset = HighSchoolWeight.objects.all()
    serializer_class = HighSchoolWeightCreateSerializer
    def create(self, request):
        college_set = self.get_data_enough_colleges(120)
        year = request.data['year'] 
        total_highschool = SelTHighSchool.objects.count()
        highschool_first_pk = SelTHighSchool.objects.first().pk 
        weight_first_dict, weight_second_dict, count_weight_first_dict, count_weight_second_dict = {}, {}, {}, {}   
        test = 1  
        # college DB 테이블의 모든 대학교&학과 순회 
        for college in college_set.iterator(): 
            test += 1
            college_avg_gpa = college.avg_gpa
            college_admission_type = college.admission_type 
            # highschool 테이블의 모든 고등학교 순회 
            for idx in range(highschool_first_pk, highschool_first_pk+total_highschool):   
                highschool = SelTHighSchool.objects.get(pk = idx)
                # 해당 대학교&학과에 합격한 해당 고등학교 졸업생 조회 
                graduate_set = Graduate.objects.filter(is_accepted=True, college = college, highschool=highschool) 
                if graduate_set.count() == 0:   
                   continue 
                # 해당 대학교&학과에 합격한 고등학교 졸업생들의 평균 성적 산출
                graduate_avg_gpa = graduate_set.aggregate(Avg('gpa'))['gpa__avg'] 
                # 해당 대학교&학과 합격생들의 평균 성적과 해당 고등학교 졸업생들의 평균 성적 사이의 차를 이용한 가중치 계산 
                weight = college_avg_gpa/graduate_avg_gpa
                # 각 입시전형별로 합격생 수 카운트 
                if college_admission_type == '종합': 
                   self.update_weight_count_dict(weight_first_dict, count_weight_first_dict, weight, idx)
                if college_admission_type == '교과': 
                   self.update_weight_count_dict(weight_second_dict, count_weight_second_dict, weight, idx)
            # 가중치 계산 진행 상황 확인용 
            print(test/college_set.count() * 100, '%')
        # 각 입시 전형(종합/교과)별 최종 가중치 계산 
        self.create_highschool_weight(weight_first_dict, count_weight_first_dict, year, '종합')
        self.create_highschool_weight(weight_second_dict, count_weight_second_dict, year, '교과')
        return Response("CREATING HIGHSCHOOL WEIGHT SUCCEEDED", status=status.HTTP_200_OK)
    def get_data_enough_colleges(self, num): 
        all_college_names = College.objects.values('college').distinct().order_by('college')
        college_popularity = dict() 
        for name in all_college_names:
            college_name = name['college']
            colleges = College.objects.filter(college=college_name).annotate(num_graduates=Count('graduate')) 
            graduates_sum = 0
            for college in colleges.iterator():
                graduates_sum += college.num_graduates
            college_popularity[college_name] = graduates_sum 
        sorted_college_popularity = sorted(college_popularity.items(), key= lambda item:item[1], reverse=True)
        popular_colleges = [] 
        for college,count in sorted_college_popularity:
            if count < num:
               break
            popular_colleges.append(college)
        return College.objects.filter(college__in=popular_colleges)
    def update_weight_count_dict(self, weight_dict, count_dict, weight, i): 
            if weight_dict.get(i): 
                weight_dict[i] += weight 
                count_dict[i] += 1 
            else : 
                weight_dict[i] = weight 
                count_dict[i] = 1 
    # 각 입시전형별 전체 가중치 합을 카운트 수로 나눠 최종 가중치 산출 후 DB 테이블에 삽입 
    def create_highschool_weight(self, weight_dict, count_dict, highschool_year, admission_type):
        for idx in weight_dict:     
            weight_dict[idx] /= count_dict[idx]        
            HighSchoolWeight.objects.get_or_create( 
                weight = weight_dict[idx],  
                year = highschool_year, 
                admission_type = admission_type,
                highschool = SelTHighSchool.objects.get(pk=idx)
            ) 

# User 회원가입시 입력된 추가정보 처리 API 
class UserAPI(ModelViewSet):
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
       if self.action == 'update':
          return SelTUserInfo.objects.all()  
       return User.objects.all()   
    def get_object(self): 
       queryset = self.get_queryset()
       if self.action == 'update':
          return get_object_or_404(queryset, user=self.request.user)
       return get_object_or_404(self.get_queryset()) 
    def get_serializer_class(self):
        if self.action == 'update':
            return UserInfoSignUpUpdateSerializer
        return UserReadSerializer
    def update(self, request, *args, **kwargs):
        try: 
          partial = kwargs.pop('partial', False)
          instance = self.get_object()
          is_male = True 
          # highschool 에러처리
          highschool_name = request.data['highschool']['name']
          highschool_location = request.data['highschool']['location']
          highschool = SelTHighSchool.objects.filter(name=highschool_name, location=highschool_location)[0]
          if not highschool:
             raise ValueError("현재 해당 고등학교는 아직 서비스되지 않습니다")
          
          # birthday(주민번호 앞 7자리) 파싱 및 type 변환 
          # "97/02/17/1" -> date("1997-02-17") & 남성 
          # "01/03/25/4" date("2001-03-25") & 여성 
          # String -> Date 
          birthday = request.data['birthday'].split('/')
          if birthday[3] == '1' or birthday[3] == '3':
             is_male = True
          else :
             is_male = False
          
          if birthday[3] == '1' or birthday[3] == '2':
              birthday[0] = '19' + birthday[0] 
          else : 
             birthday[0] = '20' + birthday[0]
          birthday.pop() 
          formatted_birthday = '-'.join(birthday)
          request.data['birthday'] = datetime.strptime(formatted_birthday, "%Y-%m-%d").date()
          request.data['is_male'] = is_male
          serializer = self.get_serializer(instance, data=request.data, partial=partial)
          serializer.is_valid(raise_exception=True)
          self.perform_update(serializer)
          if getattr(instance, '_prefetched_objects_cache', None):
              instance._prefetched_objects_cache = {}
          user_name = request.user.name
          return Response(user_name + "님, 환영합니다", status=status.HTTP_200_OK)
        except ValueError as v:
            return Response({'ERROR_MESSAGE': v.args}, status=status.HTTP_400_BAD_REQUEST) 

# 자체 서비스 회원가입 API - 기존 dj-rest-auth 제공 회원가입 기능을 커스터마이징
class SignupAPI(RegisterView):
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        data = self.get_response_data(user)
        if data:
            # User 테이블에 정상적으로 데이터 주입 완료시 연결된 selT_user_info 생성
            SelTUserInfo.objects.create(user=User.objects.filter(email=user.email)[0])
            del(data['user'])
            # 기존 user 객체 대신 이름만 빼내기 
            data['name'] = user.name
            response = Response(
                data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        else:
            response = Response(status=status.HTTP_204_NO_CONTENT, headers=headers)
        return response

# 자체 서비스 로그인 API - 기존 dj-rest-auth 제공 로그인 기능을 커스터마이징 
class LoginAPI(LoginView): 
    def get_response(self):
        serializer_class = self.get_response_serializer()
        if getattr(settings, 'REST_USE_JWT', False):
            access_token_expiration = (timezone.now() + jwt_settings.ACCESS_TOKEN_LIFETIME)
            refresh_token_expiration = (timezone.now() + jwt_settings.REFRESH_TOKEN_LIFETIME)
            return_expiration_times = getattr(settings, 'JWT_AUTH_RETURN_EXPIRATION', False)
            data = {
                'user': self.user,
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
            }
            if return_expiration_times:
                data['access_token_expiration'] = access_token_expiration
                data['refresh_token_expiration'] = refresh_token_expiration
            serializer = serializer_class(
                instance=data,
                context=self.get_serializer_context(),
            )
        elif self.token:
            serializer = serializer_class(
                instance=self.token,
                context=self.get_serializer_context(),
            )
        else:
            return Response(status=status.HTTP_204_NO_CONTENT)        
        response_obj = {} 
        response_obj['access_token'] = serializer.data['access_token']
        response_obj['refresh_token'] = serializer.data['refresh_token'] 
        response_obj['name'] = self.user.name 
        response = Response(response_obj, status=status.HTTP_200_OK)
        if getattr(settings, 'REST_USE_JWT', False):
            set_jwt_cookies(response, self.access_token, self.refresh_token)
        return response

# 카카오 로그인/회원가입 API - Oauth 2.0 방식  
def kakao_login(request): 
    try :
      # [1] 프론트로부터 건네받은 인가코드로 카카오 서버에 access token 요청 
      data = json.loads(request.body)
      authentication_code = data["code"]
      access_token_json = requests.get(
          f"https://kauth.kakao.com/oauth/token?grant_type=authorization_code&client_id={kakao_rest_api_key}&redirect_uri={kakao_redirect_url}&code={authentication_code}").json()
      error = access_token_json.get("error") 
      if error: 
         raise JSONDecodeError(error)
      access_token = access_token_json.get("access_token")
      # [2] 해당 access token으로 카카오 서버로부터 유저 데이터 객체 응답 받기  
      user_data_json = requests.get("https://kapi.kakao.com/v2/user/me", headers={'Authorization': 'Bearer {}'.format(access_token)}).json()
      error = user_data_json.get("error")  
      if error:
         raise JSONDecodeError(error) 
      # [3] 건네받은 Kakao 유저 데이터 객체 파싱     
      kakao_account = user_data_json.get("kakao_account") 
      email = kakao_account.get("email")
      name = kakao_account.get("profile").get("nickname")
      # [4] Login and Signup 
      user = User.objects.get(email=email) 
      social_user = SocialAccount.objects.filter(user=user).first()
      # 유저가 입력한 이메일로 자체 서비스 회원가입 내역이 있다면 에러발생, 없다면 로그인 
      if social_user is None:
         raise ValueError('해당 이메일은 서비스에 존재하지만, SNS 유저가 아닙니다')
      # 유저가 입력한 이메일로 다른 SNS를 통한 회원가입 내역이 있다면 에러 발생, 없다면 로그인 
      if social_user.provider != 'kakao':
         raise ValueError('해당 이메일은 이미', social_user.provider, 'SNS 계정으로 회원가입 되어 있습니다') 
      data = {'access_token': access_token, 'code': authentication_code}
      accept = requests.post(
           f"{service_base_url}selT/kakao/login/finish/", data=data)
      accept_status = accept.status_code
      if accept_status != 200:
         raise ValueError('로그인에 실패했습니다. 다시 시도해주시기 바랍니다')
      accept_json = accept.json()
      accept_json.pop('user', None)
      # user의 access token, refresh token을 담은 객체를 프론트에 반환 
      return JsonResponse(accept_json)
    except User.DoesNotExist:
        # 기존에 가입된 유저가 없으면 새로 가입
        data = {'access_token': access_token, 'code': authentication_code}
        accept = requests.post(
            f"{service_base_url}selT/kakao/login/finish/", data=data)
        accept_status = accept.status_code
        if accept_status != 200:
           raise ValueError('로그인에 실패했습니다. 다시 시도해주시기 바랍니다') 
        # user의 access Token, refresh token을 json 형태로 프론트에 반환 
        accept_json = accept.json()
        accept_json.pop('user', None)
        User.objects.filter(email=email).update(name=name, password="", sns_type="카카오톡")
        #User DB 테이블과 연결된 SelTUserInfo 테이블에 user foreign key로 연결된 빈 레코드 생성 
        SelTUserInfo.objects.create(user=User.objects.filter(email=email)[0])
        return JsonResponse(accept_json)
    except ValueError as v:
        return JsonResponse({'ERROR_MESSAGE': v.args[0]}, status=status.HTTP_400_BAD_REQUEST) 

# 카카오 로그인/회원가입 API - Oauth 2.0 방식 
class KakaoLogin(SocialLoginView):
    adapter_class = kakao_views.KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = kakao_redirect_url

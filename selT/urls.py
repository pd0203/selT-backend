from django.urls import path, include
from .views import CollegePredictionEventAPI, CollegePredictionAPI, CollegeEventAPI, CollegeFilterAPI, CollegeAPI, HighSchoolWeightAPI, UserAPI, UploadCSVAPI, HighSchoolAPI, KakaoLogin, SignupAPI, LoginAPI, kakao_login 

urlpatterns = [
    path('userinfo', UserAPI.as_view({'get': 'list', 'put': 'update'}), name='users'),
    path('', include('dj_rest_auth.urls')),
    path('login', LoginAPI.as_view(), name='login'),
    path('signup', SignupAPI.as_view(), name='signup'),
    path('upload', UploadCSVAPI.as_view({'get': 'list', 'post': 'create'}), name='upload'),
    path('highschool', HighSchoolAPI.as_view({'get': 'list'}), name='highschool'),
    path('highschoolweight', HighSchoolWeightAPI.as_view({'post': 'create'}), name='highschoolweight'),
    path('college-prediction-event', CollegePredictionEventAPI.as_view({'post': 'create'}), name='collegepercentage-event'),
    path('college-prediction', CollegePredictionAPI.as_view({'put': 'update'}), name='collegepercentage'), 
    path('college-event', CollegeEventAPI.as_view({'get': 'list'}), name='college-event'),
    path('college-filter', CollegeFilterAPI.as_view({'get': 'list'}), name='college'),
    path('college', CollegeAPI.as_view({'get': 'list'}), name='college'),
    path('kakao/login/', kakao_login, name='kakao_login'),
    path('kakao/login/finish/', KakaoLogin.as_view(),
         name='kakao_login_todjango'),
]
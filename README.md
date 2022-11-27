# selT

입시 예측/진단 서비스

# 필수 File Directory 구성

├── manage.py
├── myselT
│ ├── settings.py
│ ├── urls.py
├── requirements.txt  
├── .env
└── selT
├── adapters.py
├── admin.py
├── models.py
├── serializers.py
├── urls.py
└── views.py

# 각 폴더/파일 설명

1. manage.py
   - django project 생성시 자동으로 설치되는 파일
   - 서버 실행에 root가 되는 파일
   - 따로 건드릴 코드 x
2. requirements.txt
   - 프로젝트에 필요한 모든 라이브러리 정보가 담긴 파일
   - 밑에 명시된 명령어로 이 파일에 명시된 라이브러리 한번에 설치 가능
3. .env
   - 외부에 공개되면 안되는 정보가 담긴 파일
   - 같은 서버에 대해 개발해도 개발자마다 로컬 환경이 달라 해당 파일 내용을 수정해야 한다
4. myselT 폴더
   - 프로젝트 selT에 대한 모든 환경 세팅 정보가 들어가 있는 프로젝트 root 폴더
   1. myselT/settings.py
      - selT 프로젝트에 관한 환경 설정 파일
   2. myselT/urls.py
      - 백엔드 API 호출을 위한 root 경로를 명시해둔 파일
5. selT 폴더
   - selT 서비스에 관한 모든 로직이 담겨있는 app folder
   1. selT/adapters.py
      - 자체 서비스 로그인 구현을 도와주는 dj-rest-auth 라이브러리에서 제공하는 기능들을 커스터마이징한 파일
   2. selT/admin.py
      - selT 관리자 페이지에서 DB에 담긴 데이터들을 정형화해서 쉽게 확인하기 위해 필요한 로직이 담긴 파일
   3. selT/models.py
      - selT에 필요한 DB Table 설계가 담긴 파일
      - makemigration과 migrate를 통해 DB에 반영할 설계 내용이 담겨있다
   4. selT/serializers.py
      - Django에는 없지만 Django-Rest-Framework에는 있는 기능이 바로 serializer
      - serializer.py는 각 DB Table에 담거나 조회하거나 할 때, 불러오거나 담을 데이터의 형식을 결정하고 데이터 유효성 검사도 도와주는 기능이 담긴 파일
   5. selT/urls.py
      - selT 백엔드 API의 url 경로를 설정해둔 파일
   6. selT/views.py
      - selT 백엔드 API의 모든 알고리즘이 담긴 파일

# 로컬에 백엔드 서버 운영 환경세팅 절차

1. github내 selT repository에서 초록색 Code 클릭 후 HTTPS clone용 url 복사
2. 로컬에서 코파카바나 폴더 생성 후 clone 받기
   - 명령어 : git clone "위 복사한 url"
3. conda 홈페이지에서 4.13 설치 (아나콘다)
4. 로컬 터미널 상에서 최신버전으로 update
   - conda update conda
5. 터미널을 킨다음, clone한 selT 폴더로 위치시키고 selT 프로젝트용 conda 가상환경 생성
   - conda create --name myconda python=3.8
6. (base) => (myconda) 변경 여부 확인
7. conda 가상 환경 실행
   - 명령어 : conda activate myconda
   - 종료 명령어 : conda deactivate
8. requirements.txt에 명시된 라이브러리 전부 설치
   - 명령어 : pip install -r requirements.txt
9. selT/models.py에서 DB 모델 설계한 내용을 로컬 MySQL DB에 반영
   - 전제 조건 : MySQL이 로컬에 설치되어 있고 .env에서 세팅이 되어있어야 한다
   - python manage.py makemigrations
   - python manage.py migrate
10. 서버 정상 작동 테스트
    - python manage.py runserver

# 로컬에서 EC2 서버 접근 방법

1. 터미널 상에서 다운 받은 copacabana.pem라는 key file이 위치한 폴더 디렉토리로 이동
   - ex) cd Desktop/Copacabana
2. 해당 key file 보안 완화
   - chmod 400 copacabana.pem
3. SSH로 프로젝트 코드가 담긴 EC2 서버로 접근
   - ssh -i copacabana.pem ubuntu@3.38.96.132
4. 코드 확인 가능

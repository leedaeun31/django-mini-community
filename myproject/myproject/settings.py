"""Django settings for myproject project."""
import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------
# 기본 경로 및 환경 변수 로드
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = Path(__file__).resolve().parent
load_dotenv(CONFIG_DIR / ".env")

# ---------------------------
# 환경 변수
# ---------------------------
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_CALLBACK_URL = os.getenv("NAVER_CALLBACK_URL")

# NCP Object Storage 관련 환경변수 (필수)
NCP_ACCESS_KEY = os.getenv("NCP_ACCESS_KEY")
NCP_SECRET_KEY = os.getenv("NCP_SECRET_KEY")
NCP_ENDPOINT   = os.getenv("NCP_ENDPOINT", "https://kr.object.ncloudstorage.com")
NCP_REGION     = os.getenv("NCP_REGION", "kr-standard")

# 정적/미디어 버킷명 (환경변수에서 관리 권장)
AWS_S3_STATIC_BUCKET_NAME = os.getenv("NCP_STATIC_BUCKET", "myproject-static")
AWS_S3_MEDIA_BUCKET_NAME  = os.getenv("NCP_MEDIA_BUCKET",  "myproject-media")

# CDN 사용 시 커스텀 도메인 (선택)
AWS_S3_CUSTOM_DOMAIN_STATIC = os.getenv("NCP_STATIC_DOMAIN")  # 예: static.cdn.example.com
AWS_S3_CUSTOM_DOMAIN_MEDIA  = os.getenv("NCP_MEDIA_DOMAIN")   # 예: media.cdn.example.com

# ---------------------------
# 사용자 인증 설정
# ---------------------------
AUTH_USER_MODEL = 'user.User'
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# ---------------------------
# Django 기본 앱 + 커스텀 앱
# ---------------------------
INSTALLED_APPS = [
    # Django 기본 앱
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # 내가 만든 앱
    'user',
    'main_page',
    'board',

    # 서드파티 앱
    'storages',
]

# ---------------------------
# 미들웨어
# ---------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------------------
# URL / WSGI
# ---------------------------
ROOT_URLCONF = 'myproject.urls'
WSGI_APPLICATION = 'myproject.wsgi.application'

# ---------------------------
# 템플릿 설정
# ---------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ---------------------------
# 데이터베이스
# ---------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------
# 비밀번호 검증
# ---------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------
# 국제화
# ---------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# ---------------------------
# 정적 파일 (수집 소스 경로)
# ---------------------------
# 로컬 소스 디렉터리들 (collectstatic가 이 경로들에서 파일을 모아 S3에 올림)
STATICFILES_DIRS = [
    BASE_DIR / 'myproject' / 'static',
]

# ---------------------------
# 기본 PK 타입
# ---------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------
# NCP Object Storage (S3 호환) - 핵심
# ---------------------------
AWS_ACCESS_KEY_ID = NCP_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = NCP_SECRET_KEY
AWS_S3_ENDPOINT_URL = NCP_ENDPOINT
AWS_S3_REGION_NAME = NCP_REGION
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_ADDRESSING_STYLE = "virtual"  # 권장

# STORAGES: Django 4.2+ 방식 (E005 해결)
STORAGES = {
    # 업로드 파일(미디어)
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": AWS_S3_MEDIA_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "addressing_style": AWS_S3_ADDRESSING_STYLE,
            "default_acl": "private",   # 운영 권장
            "location": "media",
            # 필요 시 'custom_domain': AWS_S3_CUSTOM_DOMAIN_MEDIA,
        },
    },
    # 정적 파일(collectstatic 대상)
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3StaticStorage",
        "OPTIONS": {
            "bucket_name": AWS_S3_STATIC_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "addressing_style": AWS_S3_ADDRESSING_STYLE,
            "default_acl": "public-read",  # 보통 공개
            "location": "static",
            # 필요 시 'custom_domain': AWS_S3_CUSTOM_DOMAIN_STATIC,
        },
    },
}

# S3 또는 CDN 도메인으로 URL 설정
STATIC_URL = (
    (f"https://{AWS_S3_CUSTOM_DOMAIN_STATIC}/" if AWS_S3_CUSTOM_DOMAIN_STATIC
     else f"https://{AWS_S3_STATIC_BUCKET_NAME}.kr.object.ncloudstorage.com/")
)
MEDIA_URL = (
    (f"https://{AWS_S3_CUSTOM_DOMAIN_MEDIA}/" if AWS_S3_CUSTOM_DOMAIN_MEDIA
     else f"https://{AWS_S3_MEDIA_BUCKET_NAME}.kr.object.ncloudstorage.com/")
)

# collectstatic가 로컬에 모을 위치는 사실 S3 사용 시 크게 의미 없음(없어도 됨)
# 남겨두고 싶으면 아래 유지
STATIC_ROOT = BASE_DIR / "staticfiles"

# ---------------------------
# 개발 모드 설정
# ---------------------------
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-env")
DEBUG = True
ALLOWED_HOSTS = ['*']

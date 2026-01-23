# 1. 파이썬 3.11 슬림 버전 사용
FROM python:3.11-slim
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*
# 2. 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 4. 소스 코드 복사
COPY . .

# 5. 포트 개방
EXPOSE 8501

# 6. 실행 명령어
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
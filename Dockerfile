# 1. 파이썬 3.11 슬림 버전 사용
FROM python:3.11-slim

# 2. 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3. 라이브러리 설치 (requirements.txt가 바뀌지 않으면 캐시 사용)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 4. Build ID (pip 레이어 이후에 위치해야 캐시가 유지됨)
ENV BUILD_ID=v5.8.1

# 5. 소스 코드 복사
COPY . .

# 6. 포트 개방
EXPOSE 8501

# 7. 실행 명령어
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
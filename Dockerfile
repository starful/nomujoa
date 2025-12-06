# 1. 파이썬 3.10 버전 사용
FROM python:3.10-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 전체 복사 (JSON 데이터 포함)
COPY . .

# 5. 포트 설정
ENV PORT=8080
EXPOSE 8080

# 6. 서버 실행 (Gunicorn 사용)
# app:app -> app 폴더 안의 __init__.py에 있는 app 객체를 실행한다는 뜻
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
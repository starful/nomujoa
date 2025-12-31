# 1. 파이썬 3.10 버전 사용
FROM python:3.10-slim

# 2. 작업 폴더 설정
WORKDIR /app

# 3. [최적화 핵심] 라이브러리 설치를 먼저 진행 (캐싱 활용)
# 소스코드가 바뀌어도 requirements.txt가 안 바뀌면 이 단계는 생략됨(즉시 완료)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 소스 코드 전체 복사 (이 부분이 바뀌어도 위 3번은 다시 안 함)
COPY . .

# 5. 포트 설정
ENV PORT=8080
EXPOSE 8080

# 6. 서버 실행
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
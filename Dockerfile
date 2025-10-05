FROM python:3.10

EXPOSE 8080
WORKDIR /app

COPY . ./

RUN pip install --no-cache-dir -r requirements.txt

# Works locally (defaults to 8080) AND on Cloud Run (uses $PORT)
ENTRYPOINT ["streamlit", "run", "app/app.py",\
            "--server.port=${PORT:-8080}",\
            "--server.address=0.0.0.0",\
            "--server.headless=true",\
            "--server.enableCORS=false",\
            "--server.enableXsrfProtection=false"]


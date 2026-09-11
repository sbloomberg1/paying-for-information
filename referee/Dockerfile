FROM python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
RUN useradd --create-home --uid 1000 app && mkdir -p /app /data && chown -R 1000:1000 /app /data
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY referee/gym_v1/ /app/gym_v1/
COPY referee/market.py referee/referee.py referee/transport.py /app/
USER 1000
CMD ["python", "/app/referee.py"]

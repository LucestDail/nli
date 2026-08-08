# NLI API — 경량 FastAPI 이미지 (daero 패턴)
FROM python:3.12-slim
WORKDIR /app

COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server/app ./server/app
COPY server/static ./server/static

# 스냅샷은 볼륨 마운트(/app/data). 이미지에 데이터 미포함(경량).
ENV NLI_GEOJSON=/app/data/nli_map.geojson \
    NLI_POINTS=/app/data/nli_points.json \
    NLI_DATASETS=/app/data/datasets.yml \
    NLI_STATIC=/app/server/static \
    PORT=8080

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8080"]

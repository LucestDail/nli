"""서버 설정 — 환경변수 오버라이드(daero 패턴). 비밀은 env로만."""
import os

# 경로(리포 루트 기준 or env). 온프렘: 볼륨 마운트 경로로 오버라이드.
GEOJSON = os.environ.get("NLI_GEOJSON", "data/processed/nli_map.geojson")
POINTS = os.environ.get("NLI_POINTS", "nli_points.json")
DATASETS_YML = os.environ.get("NLI_DATASETS", "data/datasets.yml")
STATIC_DIR = os.environ.get("NLI_STATIC", "server/static")

# 서버
PORT = int(os.environ.get("PORT", "8080"))
API_KEY = os.environ.get("API_KEY", "")          # 설정 시 ?key= 요구(무설정=공개)
RATELIMIT = os.environ.get("RATELIMIT", "1") != "0"
RL_CAPACITY = int(os.environ.get("RL_CAPACITY", "120"))
RL_REFILL = float(os.environ.get("RL_REFILL", "2"))

VERSION = "1.0"

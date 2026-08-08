"""스냅샷 데이터층 — geojson을 DuckDB(spatial)로 로드해 읽기전용 쿼리.
기동 시 1회 로드(daero의 timetable.bin 스냅샷 패턴에 상응). 3,559행이라 인메모리 충분.
"""
import duckdb, threading, os, json, yaml
from . import config

_con = None
_lock = threading.RLock()   # 재진입(q→con 재획득 데드락 방지)
_meta = None


def _init():
    global _con
    c = duckdb.connect()
    c.execute("INSTALL spatial; LOAD spatial")
    if not os.path.exists(config.GEOJSON):
        raise FileNotFoundError(f"스냅샷 geojson 없음: {config.GEOJSON}")
    # 속성 + geom 컬럼으로 로드. adm_cd는 문자열 보장.
    c.execute(f"CREATE TABLE dong AS SELECT * FROM ST_Read('{config.GEOJSON}')")
    c.execute("ALTER TABLE dong ALTER adm_cd TYPE VARCHAR")
    _con = c


def con():
    global _con
    if _con is None:
        with _lock:
            if _con is None:
                _init()
    return _con


def q(sql, params=None):
    """읽기전용 쿼리 → DataFrame. DuckDB 커넥션 보호(락)."""
    with _lock:
        return con().execute(sql, params or []).df()


def ready():
    try:
        return int(q("SELECT count(*) n FROM dong")["n"][0])
    except Exception:
        return 0


def datasets_meta():
    """datasets.yml → 출처·기준시점·라이선스 목록(캐시)."""
    global _meta
    if _meta is None:
        try:
            doc = yaml.safe_load(open(config.DATASETS_YML, encoding="utf-8"))
            _meta = doc.get("datasets", [])
        except Exception:
            _meta = []
    return _meta

"""스냅샷 데이터층 — geojson을 DuckDB(spatial)로 로드해 읽기전용 쿼리.
기동 시 1회 로드(daero의 timetable.bin 스냅샷 패턴에 상응). 3,559행이라 인메모리 충분.
"""
import duckdb, threading, os, json, yaml
from . import config

_con = None
_lock = threading.RLock()   # 재진입(q→con 재획득 데드락 방지)
_meta = None
_mtime = None               # 로드 당시 geojson mtime — 파일 교체 감지용


def _init():
    global _con, _mtime, _meta
    if not os.path.exists(config.GEOJSON):
        raise FileNotFoundError(f"스냅샷 geojson 없음: {config.GEOJSON}")
    c = duckdb.connect()
    c.execute("INSTALL spatial; LOAD spatial")
    # 속성 + geom 컬럼으로 로드. adm_cd는 문자열 보장.
    c.execute(f"CREATE TABLE dong AS SELECT * FROM ST_Read('{config.GEOJSON}')")
    c.execute("ALTER TABLE dong ALTER adm_cd TYPE VARCHAR")
    if _con is not None:
        try: _con.close()   # 리로드 시 이전 커넥션 정리
        except Exception: pass
    _con, _mtime, _meta = c, os.path.getmtime(config.GEOJSON), None


def con():
    """커넥션 반환. 스냅샷 파일이 교체되면(mtime 변화) 자동 리로드(무중단 근접 업데이트)."""
    global _con
    if _con is None:
        with _lock:
            if _con is None:
                _init()
        return _con
    try:
        if os.path.getmtime(config.GEOJSON) != _mtime:
            with _lock:
                if os.path.getmtime(config.GEOJSON) != _mtime:
                    _init()
    except OSError:
        pass
    return _con


def snap_mtime():
    """스냅샷 로드 시각(epoch) — health 신선도 노출용. 미로드면 None."""
    return _mtime


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

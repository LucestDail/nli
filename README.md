# 동네살기지수 (NLI) 프로젝트

공공데이터포털 표준데이터 300종을 융합한 읍면동 단위 살기좋은동네 지수

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Python 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 인증 정보 설정

```bash
# .env.example을 복사해서 .env 생성
cp .env.example .env

# .env 파일을 열어서 공공데이터포털 아이디/비밀번호 입력
# DATA_PORTAL_ID=실제아이디
# DATA_PORTAL_PW=실제비밀번호
```

### 3. 데이터 수집

```bash
# 자동 수집 실행
python collector.py
```

데이터는 `data/raw/` 폴더에 저장됩니다.

## 📁 프로젝트 구조

```
ThinkTank/
├── 기획서_동네살기지수.md          # 전체 기획 문서
├── 데이터수집목록.md               # 수집할 데이터셋 목록
├── collector.py                   # 데이터 자동 수집 스크립트
├── requirements.txt               # Python 패키지 의존성
├── .env.example                   # 환경 변수 템플릿
├── .env                           # 실제 인증 정보 (git 제외)
└── data/
    ├── raw/                       # 원본 데이터
    └── processed/                 # 처리된 데이터
```

## 🔧 문제 해결

### 로그인 실패 시
- `.env` 파일의 아이디/비밀번호가 정확한지 확인
- 공공데이터포털 웹사이트에서 직접 로그인 테스트

### 다운로드 실패 시
- 해당 데이터셋이 공공데이터포털에 존재하는지 확인
- 일부 데이터는 활용 신청 후 승인 대기 필요

### Chrome 드라이버 오류 시
- `webdriver-manager`가 자동으로 설치하지만, 실패 시 수동 설치
- Chrome 브라우저 최신 버전 확인

## 📊 로드맵

- [x] Phase 0: 기획서 작성
- [ ] Phase 0: 기준 데이터 수집 (읍면동 경계 + 인구)
- [ ] Phase 1: MVP 데이터 수집 및 스코어링 엔진
- [ ] Phase 2: 지도 및 대시보드
- [ ] Phase 3: 심화 분석 및 사각지대 리포트

#!/usr/bin/env bash
# NLI 배포 자동화 — index.html을 gh-pages + 홈랩에 배포하고 검증한다.
#
# 사전조건: 루트에서 파이프라인 재실행 → cp nli_map.html index.html → git commit(main)까지 완료된 상태.
#           이 스크립트는 "배포"만 한다(main 커밋은 사람이 메시지와 함께).
#
# 사용법:
#   SSHPASS=<홈랩비번> tools/deploy.sh            # gh-pages + 홈랩(집 내부망일 때)
#   tools/deploy.sh --gh-only                     # gh-pages만 (출근 등 홈랩 미도달 시)
#
# 비밀번호는 SSHPASS 환경변수로만 받는다(스크립트/리포에 저장하지 않음).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GH_ONLY="${1:-}"

HL_HOST="${HL_HOST:-192.168.11.25}"
HL_USER="${HL_USER:-seunghyun}"
HL_DIR="${HL_DIR:-/var/www/nli}"
HL_URL="${HL_URL:-http://$HL_HOST/nli}"
GH_URL="${GH_URL:-https://lucestdail.github.io/nli}"

[ -f index.html ] || { echo "❌ index.html 없음 — 먼저 빌드하세요"; exit 1; }
TARGET=$(wc -c < index.html | tr -d ' ')
echo "▶ 배포 대상 index.html: ${TARGET} bytes"

# ── 1) gh-pages (git worktree) ──
echo "▶ [1/3] gh-pages 배포"
WT=$(mktemp -d)
git worktree add -q "$WT" gh-pages
cp index.html "$WT/index.html"
( cd "$WT"
  if git diff --quiet; then echo "  변경 없음(이미 최신)"; else
    git add index.html
    git commit -q -m "배포: index.html 갱신

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
    git push -q origin gh-pages && echo "  ✅ push"
  fi )
git worktree remove --force "$WT"

# ── 2) 홈랩 (scp -O · 집 내부망일 때만) ──
if [ "$GH_ONLY" = "--gh-only" ]; then
  echo "▶ [2/3] 홈랩 건너뜀(--gh-only)"
elif ! curl -s -m 5 -o /dev/null "$HL_URL/"; then
  echo "▶ [2/3] 홈랩 미도달(출근/외부?) — 건너뜀"
else
  : "${SSHPASS:?SSHPASS 환경변수에 홈랩 비밀번호를 설정하세요}"
  echo "▶ [2/3] 홈랩 배포 (scp -O)"
  # scp는 반드시 -O (홈랩 sshd SFTP 서브시스템 비활성)
  sshpass -e scp -O -o StrictHostKeyChecking=no -o ConnectTimeout=10 index.html "$HL_USER@$HL_HOST:/tmp/index_new.html"
  BK="index.html.bak-$(date +%Y%m%d-%H%M%S)"
  # 로컬 $SSHPASS를 원격 sudo -S(stdin 비번)로 전개. 내부망 자기 서버 전제.
  sshpass -e ssh -o StrictHostKeyChecking=no "$HL_USER@$HL_HOST" \
    "echo '$SSHPASS' | sudo -S cp $HL_DIR/index.html $HL_DIR/$BK 2>/dev/null; \
     echo '$SSHPASS' | sudo -S mv /tmp/index_new.html $HL_DIR/index.html; \
     echo '$SSHPASS' | sudo -S chown www-data:www-data $HL_DIR/index.html"
  echo "  ✅ 배치(백업 $BK)"
fi

# ── 3) 검증 ──
echo "▶ [3/3] 라이브 검증"
if [ "$GH_ONLY" != "--gh-only" ] && curl -s -m 5 -o /dev/null "$HL_URL/"; then
  H=$(curl -sL -m 12 "$HL_URL/index.html?v=$(date +%s)" | wc -c | tr -d ' ')
  [ "$H" = "$TARGET" ] && echo "  홈랩 ✅ 일치" || echo "  홈랩 ⚠️ 불일치($H)"
fi
for i in 1 2 3 4 5 6; do
  G=$(curl -sL -m 12 "$GH_URL/index.html?v=$(date +%s)-$i" | wc -c | tr -d ' ')
  if [ "$G" = "$TARGET" ]; then echo "  gh-pages ✅ 반영"; break; fi
  echo "  gh-pages 전파 대기($i)…"; [ "$i" -lt 6 ] && sleep 22
done
echo "✔ 배포 완료"

# 🪙 BitAnalyzer

**Kivy와 Python을 활용한 실시간 암호화폐 시세 추적 및 호가 분석 도구.**

Binance, Upbit, Bybit 등 주요 거래소의 시세를 실시간으로 비교하고, 호가창(Order Book)의 매수/매도 잔량을 분석하여 시장의 압력(Buying/Selling Pressure)과 김치 프리미엄(K-Premium)을 시각화합니다.

---

## 📸 스크린샷

### 1. 코인 목록 선택

<img width="1512" height="949" src="https://github.com/user-attachments/assets/cb125b78-158e-412a-88f5-6292dc078899" />

### 2. 코인 시세/호가 확인

<img width="1512" height="949" src="https://github.com/user-attachments/assets/2eb77715-9800-4c92-bffe-fc599d892ecd" />

### 3. 코인 추세선 그래프 확인

<img width="1512" height="949" src="https://github.com/user-attachments/assets/28938e41-19ae-451c-a8f7-86b1896bbf56" />

<img width="1512" height="949" src="https://github.com/user-attachments/assets/5ae18f46-84ce-408c-9df1-9a70b4b37b03" />

---

## ✨ 주요 기능

### 1. 실시간 데이터 추적

- **멀티 거래소 지원**: Binance, Upbit, Bybit 등 주요 거래소의 데이터를 동시에 모니터링
- **실시간 시세(Last Price)**: 각 거래소의 최근 체결가 및 전일 대비 등락률 표시
- **자동 갱신**: 5초 주기로 데이터 자동 업데이트 및 갱신 시각(Timestamp) 표시

### 2. 시장 심리 분석

- **호가창(Order Book) 분석**: 매수/매도 호가 및 시세를 비교하여 현재 시장의 추세(Strong Buy/Sell Pressure)를 텍스트와 색상으로 시각화
- **김치 프리미엄(K-Premium)**: 실시간 환율을 적용하여 해외 거래소 대비 국내 거래소의 가격 차이를 %로 계산
- **크로스 마켓 분석**: 기준 코인(Base Coin)을 통일하되, 다양한 결제 화폐(Quote Currency, 예: KRW, USDT, BTC, ETH) 간의 비교를 지원하여 폭넓은 분석 가능

### 3. 사용자 친화적 UI

- **가독성 중심 디자인**: 직관적인 색상(Red/Green) 사용으로 상승/하락 및 매수/매도세 구분
- **확장된 비교 슬롯**: 최대 10개의 마켓을 동시에 비교할 수 있는 가로 스크롤 뷰 제공
- **반응형 레이아웃**: Kivy `.kv` 언어를 활용한 유연한 UI 구조
- **추세선 그래프 팝업**: 상세 분석을 위한 독립된 팝업 창과 인터랙티브 차트(Candle & Spread) 제공

---

## 🛠️ 트러블슈팅 (Trouble Shooting)

### 1. Kivy RecycleView '유령 체크(Ghost Check)' 현상 해결

- **문제 상황**: 마켓 검색 화면(RecycleView)에서 아이템을 선택한 후 다른 화면으로 이동했다가 돌아오면, 데이터(`selected_symbols`)는 초기화되었으나 UI 상의 체크박스는 여전히 체크된 상태로 남아있는 현상이 발생함.
- **원인 분석**:
  - **뷰 재사용(View Recycling)**: RecycleView는 성능 최적화를 위해 위젯을 파괴하지 않고 재사용함. 이때 이전 상태(체크됨)를 가진 위젯이 초기화되지 않고 새 데이터에 할당됨.
  - **바인딩 타이밍 이슈**: 데이터 갱신 시점과 KV 바인딩 시점이 엇갈려 상태 변화를 감지하지 못함.
- **해결 방법**:
  - **단일 진실 공급원(SSOT)**: `refresh_view_attrs` 메서드에서 파이썬 코드로만 체크박스 상태를 강제 주입.
  - **뷰 강제 재생성**: 화면 진입 시 데이터 리스트를 비운 후 미세한 지연 시간 뒤에 다시 채워 넣어 위젯 재생성을 유도.

### 2. 그래프 시계열 불일치 및 렌더링 오류 해결

- **문제 상황**: 상세 분석 팝업의 스프레드(Spread) 회색 막대 그래프가 차트의 맨 오른쪽(현재 시점)이 아닌 중간이나 엉뚱한 위치에 그려지거나, 아예 나타나지 않는 현상 발생.
- **원인 분석**:
  - **데이터 영속성 부재**: 실시간 API 호출은 성공했으나, 이를 MongoDB에 저장하는 Write 로직이 누락되어 Read 시 빈 껍데기만 조회됨.
  - **타임존(Timezone) 충돌**: MongoDB는 UTC 기준으로 저장되는 반면, 그래프 렌더러는 로컬 시간(KST)이나 혼합된 타임스탬프를 사용하여 X축 좌표 계산 시 9시간의 오차가 발생.
- **해결 방법**:
  - **데이터 파이프라인 구축**: `tracker_layout.py`의 메인 업데이트 루프에 `db_service.save_spread()`를 주입하여 실시간 데이터 적재 구현.
  - **타임존 정규화**: DB 저장 시에는 엄격한 UTC를 사용하고, 그래프 렌더링(`TrendGraphWidget`) 시에는 모든 타임스탬프를 KST로 변환하여 좌표를 계산하도록 통일.

---

## 📅 로드맵 (Roadmap)

이 프로젝트는 단순한 시세 확인을 넘어, 전문적인 분석 도구로 발전하는 것이 목표입니다.

- [x] **기본 기능 구현**: 3개 거래소 시세/호가 비교 및 K-Premium 계산
- [x] **UI 개선**: 현재가(Ticker) 추가 및 업데이트 타임스탬프 적용
- [x] **마켓 확장 및 필터링**:
  - 메이저/마이너 거래소 전체 리스트 검색 기능
  - 기축 통화별(USD, KRW, ETH, USDT) 그룹화 및 비교 기능
- [x] **심층 차트 분석**:
  - 과거 데이터(OHLCV) 연동을 통한 기간별(1H, 1D, 1M, 3M, 1Y) 추세선 그래프 구현
  - MongoDB 연동을 통한 실시간 스프레드(Spread) 기록 및 시각화
- [ ] **이상 감지 알림**: 급격한 가격 변동 및 대량 거래 포착 시 알림 기능 (진행 예정)

### 📈 향후 분석 기능 강화 (Analytics Roadmap)

**1. 크로스 마켓(Cross-Market) 비교**

- 동일 코인(예: BTC/USDT)을 여러 거래소(Binance, Bybit, Upbit 등)에서 동시에 띄워 거래소 간 가격 괴리율을 즉각적으로 포착.
- 최대 10개 마켓 동시 비교를 통해 차익 거래 기회 탐색.

**2. 스프레드(Spread) 및 추세 시각화**

- `최저 매도가(Lowest Ask)` vs `최고 매수가(Highest Bid)` 의 흐름을 실시간 추세선 차트로 시각화.
- 호가 공백(Gap)이나 비정상적인 스프레드 발생 시점을 시각적으로 식별하여 진입/청산 타이밍 보조.

**3. 유동성 및 수익성 분석 (Risk Management)**

- 거래 불가능한 영역(Liquidity Void)이나 슬리피지(Slippage)가 심한 마켓 감지.
- 예상 수익률이 수수료보다 낮을 경우 경고 메시지 제공 등 실질적 이익 분석 기능 추가 예정.

---

## 💻 기술 스택

#### Language & Framework

<p>
  <img src="https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/kivy-2.3.0-191A1B?style=for-the-badge&logo=kivy&logoColor=white">
</p>

#### DB & APIs

<p>
  <img src="https://img.shields.io/badge/ccxt-Data_Fetching-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white">
  <img src="https://img.shields.io/badge/asyncio-Concurrency-blue?style=for-the-badge">
  <img src="https://img.shields.io/badge/-MongoDB-13aa52?style=for-the-badge&logo=mongodb&logoColor=white">
</p>

#### Tools

<p>
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
  <img src="https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white">
</p>

---

## 🏗️ 프로젝트 구조

```text
.
├── LICENSE
├── README.md
└── src
    ├── __init__.py
    ├── main.py                     # 앱 엔트리 포인트
    ├── services
    │   ├── __init__.py
    │   ├── analysis_service.py     # 데이터 분석 로직 (K-Premium 등)
    │   ├── database_service.py     # MongoDB CRUD 및 연결 관리
    │   └── price_service.py        # CCXT API 비동기 연동
    └── ui
        ├── __init__.py
        ├── market_explorer.kv
        ├── market_explorer.py
        ├── order_book_widget.kv
        ├── order_book_widget.py
        ├── tracker_layout.kv
        ├── tracker_layout.py       # 메인 트래커 화면 및 데이터 갱신 루프
        └── trend_graph             # 상세 분석 그래프 (Candle + Spread)
            ├── __init__.py
            ├── constants.py        # 색상, KST 시간 설정, 상수 모음
            ├── graph_canvas.py     # 실제 선/면을 그리는 로직
            ├── graph_popup.py      # 로딩 텍스트, 레이아웃 관리, 토글 필터링
            └── graph_widget.py     # 데이터 비동기 호출, 팝업창 관리, 타이머 루프
```

## 🚀 프로젝트 실행

### 사전 요구 사항

- Python **3.8 이상**
- (선택) **MongoDB Community Server** (호가 데이터 저장 사용 시 필수)
- (선택) **Binance API Key** (Public 데이터 조회 시 일부 제한이 있을 수 있음)

### 설치

```bash
# 1. 리포지토리 클론
git clone https://github.com/bin778/BitAnalyzer.git
cd BitAnalyzer

# (권장) 가상 환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\activate  # Windows

# 필수 라이브러리 설치
pip install kivy ccxt python-dotenv pymongo
```

### 환경 설정

- `.env` 파일을 생성하고 본인의 Binance API 키 및 MongoDB 설정을 입력합니다:

```ini
BINANCE_API_KEY="YOUR_API_KEY_HERE"
BINANCE_API_SECRET="YOUR_API_SECRET_HERE"

MONGO_URI="mongodb://localhost:27017/"
MONGO_DB_NAME="YOUR_DB_NAME"
MONGO_USER="YOUR_DB_USER"
MONGO_PASSWORD="YOUR_DB_PASSWORD"
```

### 실행 방법

```bash
python src/main.py
```

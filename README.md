# 🪙 BitAnalyzer

> Kivy와 Python을 활용한 **실시간 암호화폐 시세 추적 및 호가 분석 도구**.
> Binance, Upbit, Bybit 등 주요 거래소의 시세를 실시간으로 비교하고, 호가창(Order Book)의 매수/매도 잔량을 분석하여 시장의 압력(Buying/Selling Pressure)과 김치 프리미엄(K-Premium)을 시각화한다.

---

## 📸 스크린샷

<img width="900" height="600" alt="BitAnalyzer Screenshot" src="https://github.com/user-attachments/assets/5a504ab5-9319-4ee3-b52b-0bfc739fca05" />

---

## ✨ 주요 기능

### 1. 실시간 데이터 추적

- **멀티 거래소 지원:** Binance, Upbit, Bybit 등 주요 거래소의 데이터를 동시에 모니터링
- **실시간 시세(Last Price):** 각 거래소의 최근 체결가 및 전일 대비 등락률 표시
- **자동 갱신:** 5초 주기로 데이터 자동 업데이트 및 갱신 시각(Timestamp) 표시

### 2. 시장 심리 분석

- **호가창(Order Book) 분석:** 매수/매도 잔량을 비교하여 현재 시장의 추세(Strong Buy/Sell Pressure)를 텍스트와 색상으로 시각화
- **김치 프리미엄(K-Premium):** 실시간 환율을 적용하여 해외 거래소 대비 국내 거래소의 가격 차이를 %로 계산

### 3. 사용자 친화적 UI

- **가독성 중심 디자인:** 직관적인 색상(Red/Green) 사용으로 상승/하락 및 매수/매도세 구분
- **반응형 레이아웃:** Kivy `.kv` 언어를 활용한 유연한 UI 구조

---

## 🛠️ 트러블슈팅 (Trouble Shooting)

### 1. Kivy RecycleView '유령 체크(Ghost Check)' 현상 해결

- **문제 상황**: 마켓 검색 화면(`RecycleView`)에서 아이템을 선택한 후 다른 화면으로 이동했다가 돌아오면, 데이터(`selected_symbols`)는 초기화되었으나 UI 상의 체크박스는 여전히 체크된 상태로 남아있는 현상이 발생함. 심지어 선택하지 않은 엉뚱한 아이템이 체크되어 있기도 함.

- **원인 분석**:

  - **뷰 재사용(View Recycling)**: RecycleView는 성능 최적화를 위해 스크롤 시 화면 밖으로 나간 위젯을 파괴하지 않고 재사용함. 이때 이전 데이터의 상태(체크됨)를 가진 위젯이 초기화되지 않은 채로 새 데이터에 할당됨.
  - **바인딩 타이밍 이슈**: KV 파일의 active: root.is_checked 바인딩이 데이터 갱신 시점과 엇갈리며, False -> False 로의 상태 변화(변화 없음)를 감지하지 못해 UI 갱신이 누락됨.

- **해결 방법**:
  - **단일 진실 공급원(SSOT) 원칙 적용**: KV 파일의 자동 바인딩을 제거하고, refresh_view_attrs 메서드에서 파이썬 코드로만 체크박스 상태(active)를 강제 주입하도록 변경.
  - **뷰 강제 재생성**: 화면 진입 시 rv.data 리스트를 완전히 비운([]) 후, 미세한 지연 시간(0.1초) 뒤에 다시 채워 넣는 방식을 적용. 이를 통해 Kivy가 모든 위젯을 폐기하고 깨끗한 상태의 위젯을 새로 생성하도록 유도하여 잔상 문제를 해결함.

---

## 📅 로드맵 (Roadmap)

이 프로젝트는 단순한 시세 확인을 넘어, 전문적인 분석 도구로 발전하는 것이 목표이다.

- [x] **기본 기능 구현:** 3개 거래소 시세/호가 비교 및 K-Premium 계산
- [x] **UI 개선:** 현재가(Ticker) 추가 및 업데이트 타임스탬프 적용
- [ ] **마켓 확장 및 필터링:** - 메이저/마이너 거래소 전체 리스트 검색 기능
  - 기축 통화별(USD, KRW, ETH, USDT) 그룹화 및 비교 기능
- [ ] **심층 차트 분석:**
  - 네이버 주식 스타일의 기간별(1일, 1주, 3개월 등) 추세선 그래프 시각화
  - 특정 마켓 클릭 시 상세 분석 팝업(Modal) 제공
- [ ] **이상 감지 알림:** 급격한 가격 변동 및 대량 거래 포착 시 알림 기능

---

## 💻 기술 스택

#### Language & Framework

<p>
  <img src="https://img.shields.io/badge/python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/kivy-2.3.0-191A1B?style=for-the-badge&logo=kivy&logoColor=white">
</p>

#### Libraries & APIs

<p>
  <img src="https://img.shields.io/badge/ccxt-Data_Fetching-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white">
  <img src="https://img.shields.io/badge/asyncio-Concurrency-blue?style=for-the-badge">
</p>

#### Tools

<p>
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
  <img src="https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white">
</p>

---

## 🏗️ 프로젝트 구조

```bash
├── LICENSE
├── README.md
└── src
    ├── __init__.py
    ├── main.py
    ├── services
    │   ├── __init__.py
    │   ├── analysis_service.py
    │   └── price_service.py
    └── ui
        ├── __init__.py
        ├── order_book_widget.kv
        ├── order_book_widget.py
        ├── tracker_layout.kv
        └── tracker_layout.py
```

## 🚀 프로젝트 실행

### 사전 요구 사항

- Python **3.8 이상**
- Binance 계정 및 **API Key (Public 데이터 조회 시 일부 제한이 있을 수 있음)**

### 설치

```bash
# 1. 리포지토리 클론
git clone https://github.com/[Your-Username]/BitAnalyzer.git
cd BitAnalyzer

# (권장) 가상 환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\activate  # Windows

# 필수 라이브러리 설치
pip install kivy ccxt python-dotenv
```

### 환경 설정

- `.env` 파일을 생성하고 본인의 Binance API 키를 입력:

```ini
BINANCE_API_KEY="YOUR_API_KEY_HERE"
BINANCE_API_SECRET="YOUR_API_SECRET_HERE"
```

### 실행 방법

```bash
python src/main.py
```

_(추후 업데이트 예정)_

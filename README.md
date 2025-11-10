# 🪙 BitAnalyzer

> Kivy와 Python을 사용한 실시간 암호화폐 시세 비교 프로그램. 현재는 Binance, UPBIT, ByBit 시세세 비교하는 프로그램 구현.

---

## 📸 스크린샷

<img width="900" height="550" alt="image" src="https://github.com/user-attachments/assets/f57c6057-1a0e-42c0-9a70-a2f8988c4931" />

---

## ✨ 주요 기능

- 여러 비트코인 거래소의 **BTC/USDT, BTC/KRW 현재 시세 표시**
- **'Refresh' 버튼**을 통한 수동 새로고침
- **`.kv` 파일**을 사용한 선언적 UI 디자인 적용

---

## 💻 기술 스택

#### Language

<p>
  <img src="https://img.shields.io/badge/python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/kivy-191A1B?style=for-the-badge&logo=kivy&logoColor=white">
</p>

#### API

<p>
  <img src="https://img.shields.io/badge/bitcoin-F7931A?style=for-the-badge&logo=bitcoin&logoColor=white">
</p>

#### Tools

<p>
  <img src="https://img.shields.io/badge/git-F05032?style=for-the-badge&logo=git&logoColor=white">
  <img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github&logoColor=white">
  <img src="https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white">
</p>

---

## 🏗️ 프로젝트 구조

```Bash
BitAnalyzer/
├── LICENSE
├── README.md
└── src/
├── init.py
├── main.py # Kivy 앱 실행 (Entry Point)
├── services/
│ ├── init.py
│ └── price_service.py # API 연동 및 데이터 처리 (비즈니스 로직)
└── ui/
├── init.py
├── tracker_layout.kv # UI 레이아웃 및 디자인 (Presentation)
└── tracker_layout.py # UI 이벤트 및 상태 관리 (Behavior)
```

## 🚀 프로젝트 실행

### 사전 요구 사항

- Python **3.8 이상**
- Binance 계정 및 **API Key (읽기 전용 권한)**

### 설치

```bash
# 리포지토리 클론
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

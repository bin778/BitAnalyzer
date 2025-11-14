# 🪙 BitAnalyzer

> Kivy와 Python을 사용한 실시간 암호화폐 시세 비교 프로그램. 현재는 Binance, UPBIT, ByBit 시세를 비교하고 앞으로의 추세를 확인하는 프로그램 구현.

---

## 📸 스크린샷

<img width="900" height="600" src="https://github.com/user-attachments/assets/5a504ab5-9319-4ee3-b52b-0bfc739fca05" />

---

## ✨ 주요 기능

- 여러 비트코인 거래소의 **BTC/USDT, BTC/KRW 현재 시세 및 호가의 경향성 표시**
- 5초마다 자동으로 **새로고침(Refresh)** 기능
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
├── LICENSE
├── README.md
└── src
    ├── __init__.py
    ├── main.py
    ├── services
    │   ├── __init__.py
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

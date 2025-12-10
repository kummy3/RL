# 로컬 vs 서버: Git 환경 설정 가이드

## 목차
1. [개요](#개요)
2. [로컬 컴퓨터 환경](#로컬-컴퓨터-환경)
3. [연구실 서버 환경](#연구실-서버-환경)
4. [차이점 정리](#차이점-정리)
5. [단계별 설정](#단계별-설정)

---

## 개요

### 상황 분석

#### 로컬 컴퓨터
```
당신이 직접 사용하는 개인 PC/Mac
- 자신의 이름으로 커밋
- 언제든 테스트 가능
- IDE(VS Code 등) 설치 가능
```

#### 연구실 서버
```
여러 명이 공유하는 Linux 서버
- CLI(Command Line Interface)만 사용
- 다른 팀원도 접근 가능
- 24/7 실행되는 환경
```

### 핵심 차이점

| 항목 | 로컬 컴퓨터 | 연구실 서버 |
|------|-----------|---------|
| **OS** | Windows/Mac | Linux (Ubuntu/CentOS 등) |
| **UI** | GUI (VS Code 등) | CLI (Terminal만) |
| **Git** | 있을 수도, 없을 수도 | 미리 설치되어 있는 경우가 많음 |
| **SSH 키** | 개인 키 1개 | 개인 키 1개 (로컬과 같아도 됨) |
| **사용자** | 본인만 | 팀원들도 접근 가능 |
| **권한** | 전체 권한 | 제한된 권한 (sudo 불가능할 수도) |

---

## 로컬 컴퓨터 환경

### ✅ 기본 설정

#### 1️⃣ Git 설치 확인
```bash
git --version

# 없으면 설치
# Mac: brew install git
# Windows: git-scm.com 에서 다운로드
# Linux: sudo apt install git
```

#### 2️⃣ Git 전역 설정
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# 설정 확인
git config --global --list
```

#### 3️⃣ SSH 키 생성
```bash
# 로컬 컴퓨터용 SSH 키
ssh-keygen -t ed25519 -C "local@company.com" -f ~/.ssh/github_local -N ""

# 공개 키 확인
cat ~/.ssh/github_local.pub
```

#### 4️⃣ SSH Config 설정
```bash
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_local
    AddKeysToAgent yes
EOF
```

#### 5️⃣ GitHub에 공개 키 등록
```
GitHub 웹사이트
→ Settings → SSH and GPG keys
→ New SSH key
→ ~/.ssh/github_local.pub 내용 붙여넣기
```

### ✅ 개발 워크플로우
```bash
# 1. 클론
git clone git@github-company:company/project.git
cd project

# 2. 브랜치 생성 (개인 작업용)
git checkout -b feature/my-feature

# 3. 코드 수정 및 커밋
git add .
git commit -m "Add new feature"

# 4. 푸시
git push origin feature/my-feature

# 5. Pull Request 생성 (GitHub 웹에서)
```

---

## 연구실 서버 환경

### ✅ 사전 확인

#### 1️⃣ 서버에 Git 설치되어 있는지 확인
```bash
# 서버에 SSH로 접속 후
ssh user@server.lab.com

# Git 설치 확인
git --version

# 없으면 요청
# (sudo 권한이 없을 수도 있으므로 관리자에게 요청)
```

#### 2️⃣ 서버에 SSH 키 존재 확인
```bash
# 서버에서 실행
ls ~/.ssh/

# id_rsa 또는 id_ed25519가 있으면 기존 키 사용 가능
cat ~/.ssh/id_rsa.pub
```

### ✅ 기본 설정 (처음 1회)

#### 1️⃣ 서버에서 Git 사용자 설정
```bash
# 서버에 SSH 접속
ssh user@server.lab.com

# Git 설정 (서버용)
git config --global user.name "Your Name"
git config --global user.email "your.email@company.com"

# 확인
git config --global --list
```

#### 2️⃣ SSH 키 설정 (2가지 방법)

**방법 A: 로컬의 키를 서버로 복사 (권장 X - 보안 위험)**
```bash
# 로컬 컴퓨터에서 (서버에 전송)
# 보안상 이 방법은 피하기
```

**방법 B: 서버에서 새 키 생성 (권장 ✅)**
```bash
# 서버에서 실행
ssh-keygen -t ed25519 -C "server@lab.com" -f ~/.ssh/github_server -N ""

# 공개 키 확인
cat ~/.ssh/github_server.pub
```

#### 3️⃣ GitHub에 서버의 공개 키 등록
```
로컬 컴퓨터의 GitHub 웹에서:
→ Settings → SSH and GPG keys
→ New SSH key
→ 서버의 ~/.ssh/github_server.pub 내용 붙여넣기
→ Title: "Lab Server"
```

#### 4️⃣ 서버에서 SSH Config 설정 (선택사항)
```bash
# 서버에서 실행
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_server
    AddKeysToAgent yes
EOF
```

### ✅ 서버에서의 워크플로우

#### 기본 사용법 (CLI만 사용)
```bash
# 1. 서버에 SSH 접속
ssh user@server.lab.com

# 2. 프로젝트 디렉토리로 이동
cd ~/projects

# 3. 클론 (처음 1회)
git clone git@github-company:company/project.git
cd project

# 4. 코드 수정 (nano, vim 등 에디터 사용)
nano my_code.py
# 또는
vim my_code.py

# 5. 커밋
git add my_code.py
git commit -m "Update ML model"

# 6. 푸시
git push origin main
```

#### 로컬에서 수정 → 서버에서 최신 코드 가져오기
```bash
# 로컬에서 수정 후 푸시
git push origin main

# 서버에서 최신 코드 받기
git pull origin main
```

### ✅ 서버에서의 고급 사용법

#### 장시간 실행되는 작업 (nohup 사용)
```bash
# 백그라운드에서 실행 (SSH 연결 끊겨도 계속 실행)
nohup python train.py > output.log 2>&1 &

# 프로세스 확인
ps aux | grep python

# 로그 확인
tail -f output.log
```

#### 코드 버전 관리
```bash
# 커밋 로그 보기
git log --oneline

# 이전 버전으로 돌아가기
git checkout COMMIT_HASH

# 현재 브랜치 상태 확인
git status
```

#### 충돌 해결 (여러 명이 작업할 때)
```bash
# Pull 시 충돌 발생
git pull origin main

# 충돌 파일 확인
git status

# 수동으로 파일 수정 (vim, nano)
vim conflicted_file.py

# 수정 후 다시 커밋
git add conflicted_file.py
git commit -m "Resolve merge conflict"
git push origin main
```

---

## 차이점 정리

### 📊 환경별 비교표

```
┌──────────────────┬─────────────────────┬─────────────────────┐
│      항목        │    로컬 컴퓨터       │   연구실 서버        │
├──────────────────┼─────────────────────┼─────────────────────┤
│ OS               │ Windows/Mac         │ Linux               │
│ 편집기           │ VS Code, IDE        │ nano, vim           │
│ Git 설치         │ 직접 설치 필요      │ 보통 사전 설치      │
│ SSH 키           │ 개인 키 1-2개       │ 서버 전용 키 1개    │
│ 권한             │ 전체 권한           │ 제한된 권한         │
│ 사용 방식        │ GUI + Terminal      │ Terminal only       │
│ 작업 흐름        │ IDE 기반            │ nano/vim 기반       │
│ 테스트           │ 언제든 가능         │ 서버 리소스 고려    │
│ 보안             │ 개인용              │ 팀 공유용           │
└──────────────────┴─────────────────────┴─────────────────────┘
```

### 🔑 SSH 키 관리

```
개인 GitHub 계정
    ├─ 로컬 컴퓨터: ~/.ssh/github_local.pub (GitHub에 등록)
    └─ 서버: ~/.ssh/github_server.pub (GitHub에 등록)
    
    → 2개 키 등록 (각각 다른 기기에서 사용)
```

---

## 단계별 설정

### 📋 로컬 컴퓨터 설정 (처음 1회)

```bash
# 1. Git 설치
git --version  # 없으면 설치

# 2. 전역 설정
git config --global user.name "이름"
git config --global user.email "이메일@company.com"

# 3. SSH 키 생성
ssh-keygen -t ed25519 -C "local@company.com" -f ~/.ssh/github_local -N ""

# 4. SSH Config 설정
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_local
    AddKeysToAgent yes
EOF

# 5. GitHub에 공개 키 등록 (웹사이트)
cat ~/.ssh/github_local.pub
```

### 📋 연구실 서버 설정 (처음 1회)

```bash
# 1. 서버 접속
ssh user@server.lab.com

# 2. Git 설치 확인
git --version

# 3. 전역 설정
git config --global user.name "이름"
git config --global user.email "이메일@company.com"

# 4. SSH 키 생성 (서버용)
ssh-keygen -t ed25519 -C "server@lab.com" -f ~/.ssh/github_server -N ""

# 5. SSH Config 설정
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_server
    AddKeysToAgent yes
EOF

# 6. 공개 키 확인 및 복사
cat ~/.ssh/github_server.pub
```

```
로컬 컴퓨터에서 GitHub 웹사이트에 접속:
Settings → SSH and GPG keys → New SSH key
"Lab Server" 라는 이름으로 위 공개 키 등록
```

### 📋 실제 워크플로우

#### 로컬에서 개발
```bash
# 로컬 컴퓨터
git clone git@github-company:company/project.git
cd project

# 코드 수정
# (VS Code 또는 텍스트 에디터)

git add .
git commit -m "Add feature"
git push origin main
```

#### 서버에서 실행
```bash
# 서버
ssh user@server.lab.com
cd ~/projects/project

# 최신 코드 받기
git pull origin main

# 모델 학습 등 실행
nohup python train.py > train.log 2>&1 &

# 진행상황 확인
tail -f train.log
```

---

## 📝 체크리스트

### 로컬 컴퓨터 (✓ 확인)
- [ ] Git 설치됨
- [ ] `git config --global` 설정됨
- [ ] SSH 키 생성됨 (`~/.ssh/github_local`)
- [ ] SSH Config 설정됨
- [ ] GitHub에 공개 키 등록됨
- [ ] `git clone` 테스트 성공

### 연구실 서버 (✓ 확인)
- [ ] Git 설치되어 있음
- [ ] `git config --global` 설정 (서버에서)
- [ ] SSH 키 생성됨 (`~/.ssh/github_server`)
- [ ] SSH Config 설정됨
- [ ] GitHub에 공개 키 등록됨 (로컬에서)
- [ ] 서버에서 `git clone` 테스트 성공

---

## 자주 하는 실수

### ❌ 실수 1: 로컬의 개인 키를 서버로 복사
```bash
# 절대 하지 마세요!
scp ~/.ssh/github_local user@server.lab.com:~/.ssh/

# 이유: 보안 위험 (중간에 탈취될 수 있음)
# 대신: 서버에서 새 키 생성하고 공개 키만 GitHub에 등록
```

### ❌ 실수 2: 같은 SSH 키를 여러 기기에서 공유
```bash
# 로컬과 서버에서 같은 키 사용 가능하지만, 권장하지 않음
# 이유: 한 기기가 손상되면 모든 기기가 위험

# 권장: 각 기기마다 다른 키 생성
로컬: github_local
서버: github_server
```

### ❌ 실수 3: 서버에서 sudo 권한 없이 패키지 설치 시도
```bash
# 권한 없는 상황
sudo apt install git-lfs  # ❌ 권한 거부

# 해결: 관리자에게 요청
# 또는 소스에서 컴파일 (복잡함)
```

### ❌ 실수 4: 서버에서 SSH 연결 끊김
```bash
# 터미널 끊김 → 모든 프로세스 종료
python train.py  # ❌ 연결 끊기면 중단

# 해결: nohup 사용
nohup python train.py > output.log 2>&1 &  # ✅ 백그라운드 실행
```

---

## 팁 & 트릭

### 🎯 서버에서 빠르게 작업하기
```bash
# SSH 연결 유지
# Terminal에서 KeepAlive 설정
cat >> ~/.ssh/config << 'EOF'
ServerAliveInterval 60
ServerAliveCountMax 10
EOF

# 이렇게 하면 장시간 유휴 상태에도 연결 유지
```

### 🎯 로컬에서 서버 파일 직접 수정
```bash
# VS Code에서 원격 개발 (SSH 확장)
# 1. VS Code 확장 → "Remote - SSH" 설치
# 2. Ctrl + Shift + P → "Remote-SSH: Connect to Host"
# 3. user@server.lab.com 입력
# 4. 서버의 파일을 마치 로컬처럼 편집

# 이 경우 서버의 파일도 자동으로 저장 가능!
```

### 🎯 Git 명령어 단축
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
alias gst="git status"
alias gp="git push"
alias gl="git pull"
alias gc="git commit -m"
alias ga="git add"

# 이후
ga .
gc "Fixed bug"
gp  # 대신 git push
```

---

## 요약

### 핵심 3가지

1. **로컬과 서버는 별도의 환경**
   - 각각 다른 SSH 키 사용
   - 각각 Git 설정 필요

2. **SSH 키는 기기마다 1개씩**
   - 로컬용 키 1개 (로컬 컴퓨터)
   - 서버용 키 1개 (연구실 서버)
   - 모두 GitHub에 등록

3. **작업 방식이 다름**
   - 로컬: GUI + Terminal
   - 서버: Terminal only (nano/vim)

### 최종 설정 구조

```
GitHub 계정 (회사)
├─ SSH Key 1: ~/github_local.pub (로컬에 등록)
└─ SSH Key 2: ~/github_server.pub (서버에 등록)

로컬 컴퓨터
├─ ~/.ssh/github_local (개인 키)
└─ ~/.ssh/config (github-company 설정)

연구실 서버
├─ ~/.ssh/github_server (개인 키)
└─ ~/.ssh/config (github-company 설정)
```

---

**작성일**: 2025-12-10  
**대상**: 로컬과 서버 환경에서 Git 사용하는 개발자  
**상황**: 로컬 개발 + 서버에서 모델 학습


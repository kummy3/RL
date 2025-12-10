# 회사용 vs 개인용 GitHub 계정 관리 전략

## 목차
1. [상황 분석](#상황-분석)
2. [계정 구조](#계정-구조)
3. [SSH 키 관리](#ssh-키-관리)
4. [Git Config 설정](#git-config-설정)
5. [실제 사용 시나리오](#실제-사용-시나리오)
6. [단계별 설정](#단계별-설정)

---

## 상황 분석

### 당신의 상황
```
연구실 서버
    ├─ 서버에서 돌리는 코드
    │  ├─ 회사 프로젝트 코드 → 회사 GitHub에 올림
    │  └─ 개인 연구 코드 → 개인 GitHub에 올림
    │
로컬 컴퓨터
    ├─ 개인 컴퓨터에서 개발한 코드 → 개인 GitHub에 올림
    └─ 회사 프로젝트 코드 → 회사 GitHub에 올림
```

### 해결 방법
**YES! 2개의 GitHub 계정이 필요합니다**

```
회사 GitHub 계정 (회사-kumhee-official)
    ├─ SSH 공개 키들 (모든 직원의 공개 키 등록)
    │  ├─ 직원 A의 공개 키
    │  ├─ 직원 B의 공개 키
    │  └─ 서버의 공개 키 (회사용)
    │
    └─ 레포지토리
       ├─ main-project/
       │  └─ kumhee/ (폴더)
       ├─ data-analysis/
       └─ ...

개인 GitHub 계정 (kummy3)
    ├─ SSH 공개 키
    │  ├─ 로컬 컴퓨터의 공개 키
    │  └─ 서버의 공개 키 (개인용)
    │
    └─ 레포지토리
       ├─ personal-research/
       ├─ RL/ (기존)
       └─ portfolio/
```

---

## 계정 구조

### 📊 전체 계정 매핑

```
┌────────────────────────────────────────────────────────────┐
│           회사 GitHub 계정                                   │
│         (회사-kumhee-official)                              │
│                                                              │
│  관리자가 볼 수 있는 정보:                                   │
│  ├─ 등록된 모든 직원의 공개 키                              │
│  ├─ 각 커밋의 주체 (Kim, Lee, Park 등)                    │
│  └─ 누가, 언제, 무엇을 했는지 완전히 추적 가능            │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│           개인 GitHub 계정                                   │
│              (kummy3)                                        │
│                                                              │
│  당신만 볼 수 있는 정보:                                     │
│  ├─ 개인 프로젝트들                                          │
│  ├─ 개인 연구 기록                                           │
│  └─ 포트폴리오                                               │
└────────────────────────────────────────────────────────────┘
```

### SSH 키 위치

```
홈 디렉토리 (~/.ssh/)
│
├─ github_company          (비공개 키 - 회사용)
├─ github_company.pub      (공개 키 - 회사 GitHub에 등록)
│
├─ github_personal         (비공개 키 - 개인용)
├─ github_personal.pub     (공개 키 - 개인 GitHub에 등록)
│
└─ config                  (SSH 설정)
   ├─ Host github-company  (회사용)
   └─ Host github-personal (개인용)
```

---

## SSH 키 관리

### 🔑 키 생성 계획

```
서버에서 필요한 키 (2개)
├─ ~/.ssh/github_company_server   (회사 프로젝트용)
└─ ~/.ssh/github_personal_server  (개인 프로젝트용)

로컬에서 필요한 키 (2개 옵션)
├─ 옵션 A: 서버의 키를 로컬에도 사용 (간단)
├─ 옵션 B: 로컬에서 별도의 키 생성 (안전)
└─ 추천: 옵션 B (각 기기마다 다른 키)
```

### 📋 키 생성 체크리스트

#### 서버에서 생성
```bash
# 서버 접속
ssh user@server.lab.com

# 회사용 키
ssh-keygen -t ed25519 -C "server-company@lab.com" \
  -f ~/.ssh/github_company_server -N ""

# 개인용 키
ssh-keygen -t ed25519 -C "server-personal@lab.com" \
  -f ~/.ssh/github_personal_server -N ""
```

#### 로컬에서 생성 (권장)
```bash
# 로컬 컴퓨터

# 회사용 키
ssh-keygen -t ed25519 -C "kim@company.com" \
  -f ~/.ssh/github_company_local -N ""

# 개인용 키
ssh-keygen -t ed25519 -C "kummy3@personal.com" \
  -f ~/.ssh/github_personal_local -N ""
```

### 🔐 SSH Config 설정

```bash
# ~/.ssh/config 내용

Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company_server
    # 또는 로컬일 경우
    # IdentityFile ~/.ssh/github_company_local
    AddKeysToAgent yes

Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_personal_server
    # 또는 로컬일 경우
    # IdentityFile ~/.ssh/github_personal_local
    AddKeysToAgent yes
```

---

## Git Config 설정

### 🎯 옵션 1: 전역 설정 (권장하지 않음)
```bash
# 문제: 모든 저장소에서 같은 설정 사용
# 결과: 회사 프로젝트에 개인 이름이 기록될 수 있음
git config --global user.name "kummy3"
git config --global user.email "kummy3@personal.com"
```

### ✅ 옵션 2: 저장소별 설정 (권장 ⭐)

#### 회사 프로젝트 설정
```bash
cd ~/projects/company-project
git config user.name "Kim Kumhee"
git config user.email "kim.kumhee@company.com"

# 확인
git config user.name
git config user.email
```

#### 개인 프로젝트 설정
```bash
cd ~/projects/personal-research
git config user.name "kummy3"
git config user.email "kummy3@personal.com"

# 확인
git config user.name
git config user.email
```

### 🔧 옵션 3: 조건부 설정 (고급)

```bash
# ~/.gitconfig 파일

[user]
    name = kummy3
    email = kummy3@personal.com

# 회사 디렉토리에서는 다른 설정
[includeIf "gitdir:~/projects/company/"]
    path = ~/projects/company/.gitconfig
```

```bash
# ~/projects/company/.gitconfig 파일

[user]
    name = Kim Kumhee
    email = kim.kumhee@company.com
```

이렇게 하면:
- `~/projects/company/` 하위 모든 저장소: 회사 이름/이메일 사용
- 다른 곳: 개인 이름/이메일 사용

---

## 실제 사용 시나리오

### 시나리오 1: 회사 프로젝트 (서버에서)

```bash
# 서버 접속
ssh user@server.lab.com

# 회사 레포 클론 (서버용 회사 키로 접근)
git clone git@github-company:company-name/main-project.git
cd main-project

# 회사용 git 설정 (로컬 설정)
git config user.name "Kim Kumhee"
git config user.email "kim.kumhee@company.com"

# 모델 학습 코드 수정
nano kumhee/train_model.py

# 커밋
git add kumhee/train_model.py
git commit -m "Improve model training speed"

# 푸시 (github-company SSH 설정 사용)
git push origin main

# 결과: 회사 GitHub에 "Kim Kumhee"로 기록됨
```

### 시나리오 2: 개인 프로젝트 (서버에서)

```bash
# 서버에서 개인 프로젝트 작업
git clone git@github-personal:kummy3/rl-research.git
cd rl-research

# 개인용 git 설정
git config user.name "kummy3"
git config user.email "kummy3@personal.com"

# 개인 연구 코드 수정
nano experiments/new_algorithm.py

# 커밋
git add experiments/new_algorithm.py
git commit -m "Test new RL algorithm"

# 푸시 (github-personal SSH 설정 사용)
git push origin main

# 결과: 개인 GitHub에 "kummy3"로 기록됨
```

### 시나리오 3: 로컬 컴퓨터에서

```bash
# 로컬 컴퓨터에서 회사 프로젝트 수정
git clone git@github-company:company-name/main-project.git
cd main-project
git config user.name "Kim Kumhee"
git config user.email "kim.kumhee@company.com"

# 코드 수정 및 푸시
git push origin main

# --------

# 로컬에서 개인 프로젝트 수정
git clone git@github-personal:kummy3/portfolio.git
cd portfolio
git config user.name "kummy3"
git config user.email "kummy3@personal.com"

# 코드 수정 및 푸시
git push origin main
```

---

## 단계별 설정

### 📋 Step 1: 회사 GitHub 계정 설정

#### 1-1: 계정 생성 또는 초대받기
```
회사에서 제공하는 GitHub 계정 사용
또는 회사 조직(Organization)에 초대받기
```

#### 1-2: 서버 공개 키 등록
```bash
# 서버에서
cat ~/.ssh/github_company_server.pub
# 복사 후

# 회사 GitHub 웹사이트
# Settings → SSH and GPG keys → New SSH key
# Title: "Lab Server - Company"
# 공개 키 등록
```

#### 1-3: 로컬 공개 키 등록
```bash
# 로컬에서
cat ~/.ssh/github_company_local.pub
# 복사 후

# 회사 GitHub 웹사이트
# Settings → SSH and GPG keys → New SSH key
# Title: "My Laptop - Company"
# 공개 키 등록
```

### 📋 Step 2: 개인 GitHub 계정 설정

#### 2-1: 계정 생성 (이미 있으면 스킵)
```
https://github.com/join
```

#### 2-2: 서버 공개 키 등록
```bash
# 서버에서
cat ~/.ssh/github_personal_server.pub
# 복사 후

# 개인 GitHub 웹사이트
# Settings → SSH and GPG keys → New SSH key
# Title: "Lab Server - Personal"
# 공개 키 등록
```

#### 2-3: 로컬 공개 키 등록
```bash
# 로컬에서
cat ~/.ssh/github_personal_local.pub
# 복사 후

# 개인 GitHub 웹사이트
# Settings → SSH and GPG keys → New SSH key
# Title: "My Laptop - Personal"
# 공개 키 등록
```

### 📋 Step 3: 로컬 설정

#### 3-1: SSH 키 생성
```bash
# 회사용
ssh-keygen -t ed25519 -C "kim@company.com" \
  -f ~/.ssh/github_company_local -N ""

# 개인용
ssh-keygen -t ed25519 -C "kummy3@personal.com" \
  -f ~/.ssh/github_personal_local -N ""
```

#### 3-2: SSH Config 설정
```bash
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company_local
    AddKeysToAgent yes

Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_personal_local
    AddKeysToAgent yes
EOF
```

### 📋 Step 4: 서버 설정

#### 4-1: SSH 키 생성
```bash
# 회사용
ssh-keygen -t ed25519 -C "server-company@lab.com" \
  -f ~/.ssh/github_company_server -N ""

# 개인용
ssh-keygen -t ed25519 -C "server-personal@lab.com" \
  -f ~/.ssh/github_personal_server -N ""
```

#### 4-2: SSH Config 설정
```bash
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company_server
    AddKeysToAgent yes

Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_personal_server
    AddKeysToAgent yes
EOF
```

### 📋 Step 5: 각 저장소에서 Git 설정

#### 로컬 회사 프로젝트
```bash
cd ~/projects/company-project
git config user.name "Kim Kumhee"
git config user.email "kim.kumhee@company.com"
```

#### 로컬 개인 프로젝트
```bash
cd ~/projects/personal-research
git config user.name "kummy3"
git config user.email "kummy3@personal.com"
```

#### 서버 회사 프로젝트
```bash
cd ~/projects/company-project
git config user.name "Kim Kumhee"
git config user.email "kim.kumhee@company.com"
```

#### 서버 개인 프로젝트
```bash
cd ~/projects/personal-research
git config user.name "kummy3"
git config user.email "kummy3@personal.com"
```

---

## 💡 핵심 정리

### ✅ 최종 구조

```
GitHub 계정 2개
│
├─ 회사 GitHub (회사-kumhee-official)
│  ├─ SSH 공개 키
│  │  ├─ 서버 공개 키 (github_company_server.pub)
│  │  └─ 로컬 공개 키 (github_company_local.pub)
│  └─ 저장소
│     └─ main-project/
│        └─ kumhee/ (폴더)
│
└─ 개인 GitHub (kummy3)
   ├─ SSH 공개 키
   │  ├─ 서버 공개 키 (github_personal_server.pub)
   │  └─ 로컬 공개 키 (github_personal_local.pub)
   └─ 저장소
      ├─ RL/
      └─ personal-research/
```

### 🔄 커밋 기록

#### 회사 프로젝트
```
Author: Kim Kumhee <kim.kumhee@company.com>
Date: 2025-12-10

    Improve model training
```

#### 개인 프로젝트
```
Author: kummy3 <kummy3@personal.com>
Date: 2025-12-10

    Add new algorithm
```

---

## 📊 비교표

| 항목 | 회사 GitHub | 개인 GitHub |
|------|-----------|-----------|
| **계정 이름** | company-kumhee | kummy3 |
| **사용자** | 회사 직원들 | 본인만 |
| **코드 성격** | 회사 프로젝트 | 개인 연구, 포트폴리오 |
| **관리자** | 회사 관리자 | 본인 |
| **커밋 주체** | Kim Kumhee | kummy3 |
| **SSH 키** | 직원 공개 키들 | 본인 공개 키 |
| **공개 여부** | Private (보통) | Public/Private |
| **목적** | 팀 협업, 추적 | 개인 기록, 포트폴리오 |

---

## 🚀 실제 사용 흐름

### 매일 아침 (서버에서)

```bash
# 1. 서버 접속
ssh user@server.lab.com

# 2. 회사 프로젝트 폴더로 이동
cd ~/company/main-project

# 3. 최신 코드 받기
git pull origin main

# 4. 모델 학습 실행
nohup python kumhee/train.py > kumhee/train.log 2>&1 &
```

### 오후 (개인 연구)

```bash
# 1. 개인 프로젝트 폴더로 이동
cd ~/research/rl-experiments

# 2. 최신 코드 받기
git pull origin main

# 3. 새 알고리즘 테스트
python experiments/test_new_algo.py

# 4. 코드 커밋
git add .
git commit -m "Test new Q-learning variant"
git push origin main
```

### 저녁 (회사 결과 정리)

```bash
# 1. 회사 프로젝트로 돌아감
cd ~/company/main-project

# 2. 학습 결과 확인 및 정리
cat kumhee/train.log

# 3. 결과 파일 커밋
git add kumhee/results/
git commit -m "Add training results"
git push origin main
```

---

## ⚠️ 주의사항

### ❌ 하면 안 되는 것
1. 비공개 키를 이메일이나 채팅으로 공유
2. 회사 키와 개인 키를 혼동
3. 회사 프로젝트에 개인 이메일로 커밋
4. 개인 프로젝트에 회사 이메일로 커밋

### ✅ 하면 좋은 것
1. 각 저장소마다 `git config` 설정 확인
2. 커밋 전에 이메일/이름 다시 확인
3. SSH 키 정기적으로 백업
4. 키 분실 시 즉시 GitHub에서 제거

---

**작성일**: 2025-12-10  
**상황**: 회사 프로젝트 + 개인 연구를 동시에 관리  
**목표**: 명확한 계정 분리 및 추적


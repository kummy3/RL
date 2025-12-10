# 회사 공동 GitHub 계정에 코드 올리기 (초보자용)

## 목차
1. [개요](#개요)
2. [사전 준비](#사전-준비)
3. [GitHub 웹사이트에서 할 일](#github-웹사이트에서-할-일)
4. [로컬 컴퓨터에서 할 일](#로컬-컴퓨터에서-할-일)
5. [VS Code에서 할 일](#vs-code에서-할-일)
6. [처음부터 끝까지 전체 흐름](#처음부터-끝까지-전체-흐름)

---

## 개요

### 상황
- 회사에서 공동으로 사용하는 GitHub 계정이 있음
- 당신은 이 계정에 개인 로컬 컴퓨터에서 코드를 올려야 함
- GitHub 경험이 없음

### 필요한 단계
1. 회사 GitHub 계정의 정보 받기
2. SSH 키 생성 및 설정
3. 로컬 Git 설정
4. 코드 커밋 및 푸시

---

## 사전 준비

### ✅ 필수 설치
```bash
# Mac
brew install git

# Ubuntu/Debian
sudo apt install git

# Windows
# https://git-scm.com/download/win 에서 다운로드 후 설치
```

### ✅ 확인 사항
```bash
# Git 설치 확인
git --version

# 회사 GitHub 계정 정보 확보
# - GitHub 계정 이름
# - GitHub 계정 이메일
# - 레포지토리 이름
# - 레포지토리 URL
```

---

## GitHub 웹사이트에서 할 일

### 1️⃣ 회사 GitHub 계정에 로그인
```
https://github.com 접속
→ Sign in 클릭
→ 회사 계정 이메일/비밀번호 입력
```

### 2️⃣ 본인 컴퓨터의 공개 SSH 키 등록

#### Step A: 공개 키 확인 또는 생성
로컬 컴퓨터 터미널에서:
```bash
# 기존 키 확인
ls ~/.ssh/

# 없으면 생성
ssh-keygen -t ed25519 -C "회사이메일@company.com" -f ~/.ssh/github_company -N ""
```

#### Step B: 공개 키 내용 복사
```bash
# 터미널에서 실행
cat ~/.ssh/github_company.pub
```

출력 결과를 **전체 복사**:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICDoPzi/kUv8XbruelLutulKtcIwRFk8tdM5xOE1QQCH company@example.com
```

#### Step C: GitHub에 공개 키 등록
```
GitHub 웹사이트 접속
→ 우측 상단 프로필 아이콘 클릭
→ Settings 클릭
→ 좌측 메뉴에서 "SSH and GPG keys" 클릭
→ "New SSH key" 버튼 클릭
→ Title: "My Company Work PC" (구분하기 쉬운 이름)
→ Key type: "Authentication Key" 선택
→ Key: 위에서 복사한 ssh-ed25519... 전체 붙여넣기
→ "Add SSH key" 클릭
```

✅ **GitHub에서 완료!**

---

## 로컬 컴퓨터에서 할 일

### 1️⃣ Git 전역 설정 (처음 1회만)

**터미널 또는 VS Code 터미널에서 실행:**

```bash
# 회사 계정 정보로 설정
git config --global user.name "회사이름 또는 팀이름"
git config --global user.email "회사이메일@company.com"

# 설정 확인
git config --global --list
```

**예시:**
```bash
git config --global user.name "Kim_Company_Dev"
git config --global user.email "dev@company.com"
```

### 2️⃣ SSH Config 설정 (처음 1회만)

**터미널에서 실행:**

```bash
# 편집기로 파일 생성
nano ~/.ssh/config
```

**다음 내용 입력:**
```
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company
    AddKeysToAgent yes
```

**저장하기:**
- `Ctrl + X` → `Y` → `Enter` (nano 편집기)

**또는 명령어로 한번에:**
```bash
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company
    AddKeysToAgent yes
EOF
```

### 3️⃣ SSH 연결 테스트

```bash
ssh -T git@github-company
```

**예상 출력:**
```
Hi company-account! You've successfully authenticated, 
but GitHub does not provide shell access.
```

✅ **성공! 이제 푸시할 준비 완료**

---

## VS Code에서 할 일

### 1️⃣ 프로젝트 폴더 열기

```
VS Code 실행
→ File → Open Folder
→ 코드를 저장할 폴더 선택
→ 폴더 선택
```

### 2️⃣ 터미널 열기

```
VS Code 상단 메뉴
→ Terminal → New Terminal
또는
Ctrl + ` (백틱)
```

### 3️⃣ 원격 레포지토리 클론

**회사 GitHub에서 클론 URL 확인:**
```
회사 GitHub 레포지토리 페이지
→ 초록색 "Code" 버튼 클릭
→ "SSH" 탭 선택
→ "git@github.com:..." 복사
```

**VS Code 터미널에서 실행:**
```bash
# 예: git clone git@github-company:company-name/project-repo.git
git clone git@github-company:회사깃허브이름/프로젝트이름.git
```

### 4️⃣ 클론한 폴더 열기

```
File → Open Folder
→ 방금 클론한 폴더 선택
```

### 5️⃣ 코드 수정 및 커밋

**파일 수정 후:**

```
VS Code 좌측 사이드바 → Source Control 아이콘 (갈래 모양)
또는 Ctrl + Shift + G
```

**변경된 파일 확인 후:**
```
1. "+" 버튼으로 파일 스테이징 (또는 모두 선택)
2. 상단 "Message" 입력창에 커밋 메시지 입력
3. "Commit" 버튼 클릭 또는 Ctrl + Enter
```

### 6️⃣ GitHub에 푸시

```
Source Control 창의 "..." 메뉴
→ "Push" 클릭
또는
터미널에서: git push origin main
```

---

## 처음부터 끝까지 전체 흐름

### 📋 체크리스트 (단계 순서)

#### 📍 Step 1: GitHub 웹사이트 (5분)
- [ ] 회사 GitHub 계정으로 로그인
- [ ] SSH 키 생성 (터미널에서)
- [ ] 공개 키 복사
- [ ] Settings → SSH and GPG keys → New SSH key 등록

#### 📍 Step 2: 로컬 컴퓨터 - 터미널 (10분)
```bash
# 1. 공개 키 확인/생성
cat ~/.ssh/github_company.pub

# 2. Git 전역 설정
git config --global user.name "회사팀이름"
git config --global user.email "회사이메일@company.com"

# 3. SSH Config 설정
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company
    AddKeysToAgent yes
EOF

# 4. SSH 연결 테스트
ssh -T git@github-company
```

#### 📍 Step 3: VS Code (15분)
```bash
# 1. VS Code 열기
code .

# 2. 터미널 열기 (Ctrl + `)

# 3. 레포지토리 클론
git clone git@github-company:회사이름/프로젝트이름.git

# 4. 폴더 열기
# File → Open Folder → 클론한 폴더

# 5. 코드 수정

# 6. Ctrl + Shift + G → 변경사항 커밋 → Push
```

---

## 실제 예시

### 상황: 회사 계정 "CompanyAI", 프로젝트 "MLproject"

#### 1️⃣ GitHub 웹 (회사 계정 로그인 후)
```
Settings → SSH and GPG keys → New SSH key
Title: "My Laptop"
Key: ssh-ed25519 AAAAC3... (전체 복사)
```

#### 2️⃣ 로컬 컴퓨터 - 터미널
```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "dev@company.com" -f ~/.ssh/github_company -N ""

# Git 설정
git config --global user.name "CompanyAI_Dev"
git config --global user.email "dev@company.com"

# SSH Config
cat > ~/.ssh/config << 'EOF'
Host github-company
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_company
    AddKeysToAgent yes
EOF

# 테스트
ssh -T git@github-company
```

#### 3️⃣ VS Code
```bash
# VS Code 열기
code .

# 터미널 (Ctrl + `)
git clone git@github-company:CompanyAI/MLproject.git

# 폴더 열기 후 코드 수정

# Ctrl + Shift + G → 커밋 & 푸시
```

---

## 문제 해결

### ❌ "Permission denied (publickey)" 오류
```
해결:
1. 공개 키가 GitHub에 등록됐는지 확인
2. SSH Config 파일 경로 확인 (~/.ssh/config)
3. ssh -T git@github-company 재테스트
```

### ❌ "fatal: Could not read from remote repository"
```
해결:
1. 클론 URL 확인 (git@github-company: 로 시작하는지)
2. SSH Config의 github-company 호스트명 확인
3. 인터넷 연결 확인
```

### ❌ VS Code에서 푸시가 안 됨
```
해결:
1. 터미널에서 직접 git push 실행
2. SSH 에이전트 추가: ssh-add ~/.ssh/github_company
3. VS Code 재시작
```

---

## 핵심 개념 정리

### GitHub 계정 구조
```
1개 GitHub 계정 = 1개 SSH 키
```

### 파일 위치
```
~/.ssh/github_company      (비공개 키 - 절대 공유X)
~/.ssh/github_company.pub  (공개 키 - GitHub에만 등록)
~/.ssh/config              (SSH 설정)
```

### 권한 설정
```bash
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/github_company
chmod 644 ~/.ssh/github_company.pub
```

### 이후 매번 사용 흐름
```
1. 코드 수정 (VS Code 또는 텍스트 에디터)
2. Ctrl + Shift + G (Source Control)
3. 커밋 메시지 입력
4. Commit 클릭
5. Push 클릭
```

---

## 추가 팁

### 🔐 보안
- 개인 키(`~/.ssh/github_company`)는 절대 공유하지 않기
- 공개 키(`github_company.pub`)만 GitHub에 등록
- 회사 컴퓨터를 바꿀 때마다 새 키 생성 권장

### 📝 좋은 커밋 메시지
```
좋음:
- "Add user authentication feature"
- "Fix bug in data processing"
- "Update documentation"

나쁨:
- "update"
- "fix"
- "asdfa"
```

### 🔄 팀 협업
```bash
# 최신 코드 받기 (매번 시작 전)
git pull origin main

# 푸시 전 충돌 확인
git status
```

---

**마지막 조언**: 
처음에는 이 과정이 복잡해 보이지만, 한 번 설정하면 이후로는 다음 3단계만 반복됩니다:
1. 코드 수정
2. 커밋 (Ctrl + Shift + G)
3. 푸시 (Push 버튼)

화이팅! 🚀

---

**작성일**: 2025-12-10  
**대상**: Git/GitHub 초보자  
**상황**: 회사 공동 GitHub 계정에 처음 코드 올리기


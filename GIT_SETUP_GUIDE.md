# Git 레포지토리 생성 및 GitHub 연결 가이드

## 목차
1. [개요](#개요)
2. [발생한 오류들](#발생한-오류들)
3. [단계별 설정 가이드](#단계별-설정-가이드)
4. [체크리스트](#체크리스트)

---

## 개요

이 문서는 로컬 git 레포지토리를 생성하고 GitHub 원격 저장소와 연결하는 전체 과정을 설명합니다.

---

## 발생한 오류들

### 1. Git User 정보 미설정
**오류 메시지:**
```
git에서 "user.name" 및 "user.email"을 구성해야 합니다.
```

**원인:**
- Git이 설치되어 있지만 전역 사용자 정보가 설정되지 않음
- 커밋을 할 때 누가 이 변경을 했는지 기록할 수 없음

**해결 방법:**
```bash
git config --global user.name "your-username"
git config --global user.email "your-email@example.com"
```

---

### 2. 원격 저장소 연결 없음
**오류 메시지:**
```
로컬 커밋은 되지만 GitHub 웹페이지에 나타나지 않음
```

**원인:**
- 로컬 git 레포지토리만 생성되고 GitHub 원격 저장소와 연결되지 않음
- `git push`가 어디로 보낼지 알 수 없음

**해결 방법:**
```bash
# 원격 저장소 추가
git remote add origin https://github.com/USERNAME/REPOSITORY.git

# 또는 SSH 사용 (추천)
git remote add origin git@github.com:USERNAME/REPOSITORY.git
```

---

### 3. HTTPS 인증 실패
**오류 메시지:**
```
Missing or invalid credentials.
Error: connect ECONNREFUSED
fatal: https://github.com/.../에 대한 인증이 실패하였습니다
```

**원인:**
- HTTPS URL 사용 시 GitHub 토큰 또는 비밀번호 인증이 필요
- 서버 환경에서 자동 인증이 작동하지 않음

**해결 방법:**
SSH 키를 이용한 인증으로 변경 (권장)

---

### 4. SSH Host Key 검증 실패
**오류 메시지:**
```
Host key verification failed.
fatal: 리모트 저장소에서 읽을 수 없습니다
```

**원인:**
- GitHub 호스트의 공개 키가 `~/.ssh/known_hosts`에 등록되지 않음
- 처음 SSH로 GitHub에 접속할 때 발생

**해결 방법:**
```bash
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
```

---

### 5. SSH 권한 거부 (Permission denied)
**오류 메시지:**
```
git@github.com: Permission denied (publickey).
fatal: 리모트 저장소에서 읽을 수 없습니다
```

**원인:**
- SSH 공개 키를 GitHub 계정에 등록하지 않음
- GitHub가 이 키를 인식하지 못함

**해결 방법:**
GitHub 웹사이트에서 공개 키 등록:
1. Settings → SSH and GPG keys
2. New SSH key 클릭
3. 생성된 공개 키 붙여넣기 및 저장

---

### 6. Push 거부 (Non-fast-forward)
**오류 메시지:**
```
! [rejected]        main -> main (non-fast-forward)
error: 레퍼런스를 'github.com:...'에 푸시하는데 실패했습니다
힌트: 현재 브랜치의 끝이 리모트 브랜치보다 뒤에 있으므로 업데이트가 거부되었습니다.
```

**원인:**
- GitHub 저장소에 이미 존재하는 커밋이 있음 (예: README.md)
- 로컬 브랜치가 원격 브랜치와 다르게 진행됨

**해결 방법:**
```bash
git pull --rebase origin main
git push origin main
```

---

### 7. 파일 충돌 (Checkout conflict)
**오류 메시지:**
```
error: 체크아웃 때문에 추적하지 않는 다음 작업 폴더의 파일을 덮어씁니다:
	README.md
```

**원인:**
- 로컬 파일과 원격 저장소의 파일명이 같음
- Rebase 시 원격 파일로 덮어쓰려고 시도

**해결 방법:**
```bash
# 방법 1: 파일 이름 변경 후 유지
mv README.md README.local.md
git add README.local.md
git commit -m "Rename local README"

# 방법 2: 파일 제거 (원격 버전만 유지)
rm README.md
git pull --rebase origin main
```

---

## 단계별 설정 가이드

### Step 1: Git 전역 설정
```bash
# 사용자 정보 설정
git config --global user.name "your-username"
git config --global user.email "your-email@example.com"

# 설정 확인
git config --global --list
```

### Step 2: 로컬 Git 레포지토리 생성
```bash
cd /your/project/directory
git init
```

### Step 3: SSH 키 생성
```bash
# ED25519 키 생성 (추천)
ssh-keygen -t ed25519 -C "your-email@example.com" -f ~/.ssh/github -N ""

# 또는 RSA 키 (호환성 높음)
ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts 2>/dev/null

# 공개 키 확인
cat ~/.ssh/github.pub
```

### Step 4: SSH Config 설정
```bash
cat > ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github
    AddKeysToAgent yes
EOF

chmod 600 ~/.ssh/config
```

### Step 5: GitHub에 공개 키 등록
1. https://github.com/settings/keys 접속
2. "New SSH key" 클릭
3. 다음 명령어로 출력된 공개 키 복사:
   ```bash
   cat ~/.ssh/github.pub
   ```
4. GitHub에 붙여넣기 및 저장

### Step 6: GitHub 호스트 키 등록
```bash
ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts 2>/dev/null
```

### Step 7: GitHub 저장소 생성
1. https://github.com/new 접속
2. 저장소 이름 입력
3. "Create repository" 클릭

### Step 8: 원격 저장소 연결
```bash
cd /your/project/directory

# 원격 저장소 추가 (SSH)
git remote add origin git@github.com:USERNAME/REPOSITORY.git

# 연결 확인
git remote -v
```

### Step 9: 로컬 파일 커밋
```bash
# 모든 파일 추가
git add .

# 또는 특정 파일만 추가
git add filename

# 커밋 생성
git commit -m "Initial commit"
```

### Step 10: GitHub에 푸시
```bash
# 브랜치 이름을 main으로 설정 (필요 시)
git branch -M main

# 원격에 푸시
git push -u origin main

# 이후 푸시는 다음과 같이 단순화
git push
```

---

## 체크리스트

### 초기 설정 (처음 1회만)
- [ ] Git 전역 사용자 정보 설정 (`git config --global`)
- [ ] SSH 키 생성 (`ssh-keygen`)
- [ ] SSH Config 파일 생성 (`~/.ssh/config`)
- [ ] GitHub 공개 키 등록 (웹사이트)
- [ ] GitHub 호스트 키 등록 (`ssh-keyscan`)

### 새로운 레포지토리마다
- [ ] GitHub에서 새 저장소 생성
- [ ] 로컬 디렉토리 생성
- [ ] Git 초기화 (`git init`)
- [ ] 원격 저장소 연결 (`git remote add origin`)
- [ ] 파일 추가 및 커밋 (`git add`, `git commit`)
- [ ] GitHub에 푸시 (`git push -u origin main`)

### 파일 충돌 발생 시
- [ ] 로컬 파일이 필요하면 이름 변경 (예: `.local` 접미사)
- [ ] 불필요하면 제거
- [ ] `git pull --rebase origin main` 실행
- [ ] 다시 푸시 (`git push origin main`)

---

## 유용한 Git 명령어

```bash
# 원격 저장소 상태 확인
git remote -v

# 로컬 커밋 상태 확인
git status

# 커밋 로그 보기
git log --oneline

# 원격과 로컬의 차이 확인
git diff origin/main main

# 브랜치 목록 확인
git branch -a

# 원격 저장소 URL 변경
git remote set-url origin git@github.com:USERNAME/REPOSITORY.git

# 마지막 커밋 메시지 수정
git commit --amend -m "New message"
```

---

## 참고사항

### HTTPS vs SSH
- **HTTPS**: 간단하지만 매번 인증 필요
- **SSH**: 초기 설정이 복잡하지만 자동 인증 가능 (권장)

### 브랜치 이름
- GitHub는 기본 브랜치를 `main`으로 설정 (이전: `master`)
- 로컬 브랜치도 `main`으로 맞춰주면 좋음

### 보안
- 개인 SSH 키는 절대 공유하지 않기
- `~/.ssh/` 디렉토리 권한: 700
- `~/.ssh/config` 파일 권한: 600

---

**작성일**: 2025-12-09  
**작성자**: imrl  
**상태**: 완성


!/bin/bash

# 사용법: bash run_all.sh 또는 ./run_all.sh (실행 권한 부여 후)

INVENTORY_FILE="inventory.ini"
ANSIBLE_BASH_ONLY_PLAYBOOK="discover_and_fetch_users_keys_bash_only.yml" # 플레이북 이름
PYTHON_PROCESS_SCRIPT="process_keys.py"
HTML_REPORT_FILE="authorized_keys_report_raw_mode.html" # HTML 보고서 파일 이름

# 함수: 사용자에게 메시지를 표시하고 수동 파일 열기를 안내합니다.
show_manual_open_message() {
    echo -e "\n-------------------#-------------------------------------------"
    echo "경고: 웹 브라우저에서 HTML 보고서를 자동으로 열 수 없습니다."
    echo "보고서 파일은 여기에 생성되었습니다: $(pwd)/$HTML_REPORT_FILE"
    echo "웹 브라우저를 열고 이 파일을 수동으로 드래그 앤 드롭하거나, 파일 탐색기에서 파일을 클릭하여 여세요."
    echo "--------------------------------------------------------------"
}

# fetched_data 디렉토리 초기화 (이전 실행 결과 제거)
echo "--- 기존 fetched_data 디렉토리 삭제 (선택 사항) ---"
rm -rf fetched_data
mkdir -p fetched_data # 새로운 fetched_data 디렉토리 생성

echo "--- SSH Authorized Keys 보고서 생성 프로세스 시작 (Bash 전용 모드) ---"
echo "경고: SSH 호스트 키 검증이 비활성화됩니다. (StrictHostKeyChecking=no)"

# 1. 원격 서버에서 Bash로 authorized_keys 파일 내용 수집
echo -e "\n[단계 1/2] 원격 서버에서 Bash로 authorized_keys 파일 내용 수집 중..."

# SSH StrictHostKeyChecking을 비활성화하여 연결 시 질문을 제거합니다.
ansible-playbook -i "$INVENTORY_FILE" "$ANSIBLE_BASH_ONLY_PLAYBOOK" --ssh-common-args='-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
if [ $? -ne 0 ]; then
    echo "오류: Ansible 플레이북 ($ANSIBLE_BASH_ONLY_PLAYBOOK) 실행에 실패했습니다."
    echo "원격 서버 연결, SSH 키, sudo 권한, 또는 Bash 스크립트 실행 문제를 확인하세요."
    exit 1
fi

# 2. 가져온 키 데이터를 기반으로 HTML 보고서 생성
echo -e "\n[단계 2/2] 가져온 키 데이터를 기반으로 HTML 보고서 생성 중..."
# process_keys.py는 Python 스크립트이므로, 클라이언트에 Python 환경이 필요합니다.
python3 "$PYTHON_PROCESS_SCRIPT"
if [ $? -ne 0 ]; then
    echo "오류: Python 스크립트 ($PYTHON_PROCESS_SCRIPT) 실행에 실패했습니다. 클라이언트에 Python이 설치되어 있는지 확인하세요."
    exit 1
fi

# 3. HTML 보고서 웹 브라우저로 열기
echo -e "\n--- HTML 보고서 열기: $HTML_REPORT_FILE ---"
# 운영체제에 따라 다른 명령어를 사용합니다.
# 브라우저 열기 시도 결과를 저장하여 실패 시 메시지를 표시합니다.
OPEN_SUCCESS=0

if [[ "$OSTYPE" == "darwin"* ]]; then # macOS
    open "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then # Linux
    xdg-open "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
elif [[ "$OSTYPE" == "cygwin" || "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then # Windows (Git Bash, WSL 등)
    cmd.exe /C start "$HTML_REPORT_FILE" && OPEN_SUCCESS=1
fi

# 만약 자동으로 열리지 않았다면, 수동으로 열도록 안내 메시지를 표시합니다.
if [ "$OPEN_SUCCESS" -eq 0 ]; then
    show_manual_open_message
else
    echo "웹 브라우저에서 보고서를 열었습니다."
fi

echo -e "\n--- SSH Authorized Keys 보고서 생성 프로세스 완료 ---"


import os
import re

# Raw 데이터 파일들이 저장될 기본 디렉토리를 정의합니다.
FETCHED_DATA_BASE_DIR = "./fetched_data/"
# 생성될 HTML 보고서 파일의 경로를 정의합니다.
HTML_REPORT_FILE = "authorized_keys_report_raw_mode.html"

def parse_raw_authorized_keys_data(file_path):
    """
    Bash 스크립트에서 수집된 raw authorized_keys 데이터를 파싱합니다.
    """
    keys_by_user = {}
    current_user = None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # ---HOST:hostname--- 라인은 무시합니다. (파일 이름에서 호스트명 추출)
                if line.startswith('---HOST:'):
                    continue
                # ---USER:username--- 라인에서 사용자 이름 추출
                elif line.startswith('---USER:'):
                    current_user = line.split(':', 1)[1].rstrip('---')
                    keys_by_user[current_user] = [] # 새 사용자 엔트리 초기화
                # 키 데이터 라인 파싱
                elif current_user and not line.startswith('---') and line: # 유효한 키 라인인지 확인
                    # "Error reading" 메시지는 건너뜁니다.
                    if "Error reading" in line:
                        continue

                    parts = line.split(None, 2) # 공백을 기준으로 최대 2번 분리
                    
                    key_type = parts[0] if len(parts) > 0 else 'Unknown'
                    key_data = parts[1] if len(parts) > 1 else 'N/A'
                    comment = parts[2] if len(parts) > 2 else 'N/A'
                    
                    keys_by_user[current_user].append({
                        'type': key_type,
                        'data': key_data,
                        'comment': comment
                    })
    except FileNotFoundError:
        print(f"Error: {file_path} 파일을 찾을 수 없습니다. Bash 플레이북을 먼저 실행했는지 확인하세요.")
    except Exception as e:
        print(f"파일을 읽거나 파싱하는 중 오류가 발생했습니다: {file_path}: {e}")
    return keys_by_user

def parse_all_raw_data_files(base_dir):
    """
    모든 호스트의 raw 데이터를 읽고 파싱합니다.
    """
    all_hosts_users_keys = {}
    if not os.path.exists(base_dir):
        print(f"Error: 디렉토리 '{base_dir}'를 찾을 수 없습니다. Bash 플레이북이 성공적으로 실행되었는지 확인하세요.")
        return all_hosts_users_keys

    # fetched_data 디렉토리 내의 모든 *_raw_auth_keys.txt 파일을 찾습니다.
    for filename in os.listdir(base_dir):
        if filename.endswith("_raw_auth_keys.txt"):
            # 파일 이름에서 호스트 이름 추출 (예: server1_raw_auth_keys.txt -> server1)
            host_name = filename.replace("_raw_auth_keys.txt", "")
            file_path = os.path.join(base_dir, filename)
            
            # 해당 호스트의 데이터를 파싱합니다.
            users_data_for_host = parse_raw_authorized_keys_data(file_path)
            
            if users_data_for_host:
                all_hosts_users_keys[host_name] = users_data_for_host
    return all_hosts_users_keys


def generate_html_report(all_hosts_users_keys_data, output_file):
    """
    모든 호스트 및 사용자의 키 데이터를 기반으로 HTML 보고서를 생성합니다.
    각 호스트/사용자별로 별도의 섹션과 테이블을 생성합니다.
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Authorized Keys 종합 보고서 (Bash 전용)</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            font-family: "Inter", sans-serif;
            background-color: #f3f4f6;
            color: #374151;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 0.5rem; /* rounded-lg */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); /* shadow-lg */
            padding: 2rem; /* p-8 */
            width: 100%;
            max-width: 1200px; /* max-w-4xl */
        }}
        .host-section {{
            margin-bottom: 2.5rem; /* mb-10 */
            border: 1px solid #e5e7eb; /* border-gray-200 */
            border-radius: 0.375rem; /* rounded-md */
            padding: 1.5rem; /* p-6 */
            background-color: #ffffff;
        }}
        .user-subsection {{
            margin-top: 1.5rem; /* mt-6 */
            margin-bottom: 1.5rem; /* mb-6 */
            padding: 1rem; /* p-4 */
            border: 1px solid #e5e7eb;
            border-radius: 0.375rem;
            background-color: #fcfcfc;
        }}
        .host-section:not(:last-child) {{
            margin-bottom: 2rem; /* 마지막 섹션 아래 여백 제거 */
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1.5rem; /* mt-6 */
        }}
        th, td {{
            padding: 0.75rem 1rem; /* px-4 py-3 */
            text-align: left;
            border-bottom: 1px solid #e5e7eb; /* border-gray-200 */
        }}
        th {{
            background-color: #f9fafb; /* bg-gray-50 */
            font-weight: 600; /* font-semibold */
            color: #1f2937; /* text-gray-900 */
        }}
        tr:hover {{
            background-color: #f3f4f6; /* hover:bg-gray-100 */
        }}
        .key-data {{
            word-break: break-all; /* 긴 키 데이터가 줄 바꿈되도록 합니다. */
        }}
    </style>
</head>
<body class="bg-gray-100 p-4 sm:p-6 lg:p-8">
    <div class="container mx-auto rounded-lg shadow-lg p-6 sm:p-8 lg:p-10">
        <h1 class="text-3xl sm:text-4xl font-bold text-gray-900 mb-6 text-center">Authorized Keys 종합 보고서 (Bash 전용)</h1>
        
        <p class="text-gray-700 mb-8 text-center">
            이 보고서는 원격 서버에 Python 인터프리터가 필요 없이 Bash 명령어를 통해서 수집된 SSH 키 정보를 표시합니다.
            각 섹션은 호스트의 키 목록을 나타내며, 호스트 내에서 사용자로 다시 나뉩니다.
        </p>
    """

    if not all_hosts_users_keys_data:
        html_content += """
        <div class="text-center text-gray-600 text-lg py-10 rounded-md bg-white border border-gray-200 p-6">
            <p>데이터를 찾을 수 없습니다. Ansible 플레이북이 성공적으로 파일을 가져왔는지 확인하세요.</p>
            <p class="mt-2 text-sm text-gray-500">
                파일은 <code>./fetched_data/&lt;hostname&gt;_raw_auth_keys.txt</code> 경로에 있어야 합니다.
            </p>
        </div>
        """
    else:
        # 호스트 이름을 알파벳 순으로 정렬하여 출력합니다.
        for hostname in sorted(all_hosts_users_keys_data.keys()):
            users_on_host = all_hosts_users_keys_data[hostname]
            html_content += f"""
        <div class="host-section rounded-md shadow-sm">
            <h2 class="text-2xl font-semibold text-gray-800 mb-4">호스트: <span class="text-indigo-600">{hostname}</span></h2>
            """
            if not users_on_host:
                html_content += """
                <p class="text-gray-500 italic">이 호스트에는 authorized_keys 파일이 있는 사용자를 찾을 수 없습니다.</p>
                """
            else:
                # 사용자 이름을 알파벳 순으로 정렬하여 출력합니다.
                for username in sorted(users_on_host.keys()):
                    keys = users_on_host[username]
                    html_content += f"""
            <div class="user-subsection rounded-md shadow-sm">
                <h3 class="text-xl font-medium text-gray-700 mb-3">사용자: <span class="text-green-600">{username}</span></h3>
                <div class="overflow-x-auto rounded-md border border-gray-200">
                    <table class="min-w-full divide-y divide-gray-200">
                        <thead class="bg-gray-50">
                            <tr>
                                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider rounded-tl-md">
                                    키 유형
                                </th>
                                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                                    키 데이터 / 지문
                                </th>
                                <th scope="col" class="px-4 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider rounded-tr-md">
                                    코멘트
                                </th>
                            </tr>
                        </thead>
                        <tbody class="bg-white divide-y divide-gray-200">
                """
                    if not keys:
                        html_content += """
                            <tr>
                                <td colspan="3" class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 text-center">
                                    이 사용자 계정의 authorized_keys 파일에서 유효한 키를 찾거나 파싱할 수 없습니다.
                                </td>
                            </tr>
                    """
                    else:
                        for key in keys:
                            html_content += f"""
                            <tr>
                                <td class="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                                    {key['type']}
                                </td>
                                <td class="px-4 py-3 text-sm text-gray-700 key-data">
                                    <code>{key['data']}</code>
                                </td>
                                <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                                    {key['comment']}
                                </td>
                            </tr>
                        """
                    html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
                    """
            html_content += """
        </div>
            """

    html_content += """
    </div>
</body>
</html>
    """

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML 보고서가 성공적으로 생성되었습니다: {output_file}")
    except Exception as e:
        print(f"HTML 보고서 생성 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    print("Python 스크립트 실행 중...")
    
    # raw 출력 파일에서 데이터를 파싱합니다.
    all_hosts_users_keys = parse_all_raw_data_files(FETCHED_DATA_BASE_DIR)

    # HTML 보고서를 생성합니다.
    generate_html_report(all_hosts_users_keys, HTML_REPORT_FILE)
    print("\n--- 다음 단계를 진행하세요 ---")
    print(f"HTML 보고서가 생성되었습니다: {HTML_REPORT_FILE}")
    print("이 파일을 웹 브라우저에서 열어 내용을 확인할 수 있습니다.")

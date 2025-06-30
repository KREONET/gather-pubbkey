# gather-pubbkey
This program for gathering Linux server pubbkey

```bash
bash run_all.sh
```

# 유의사항

## pubkey를 이용한  접속
`inventory.ini`의 `(ip changeme)'에 적절한 ip를 입력한다.
`inventory.ini`의 `ansible_ssh_private_key_file`에 프로그램을 실행하는 PC의 pubkey 경로를 입력한다.

## 보고서 확인
보고서는 Html 파일 형식으로 만들어진다.
HTML 파일은 웹 브라우저에서 자동으로도 열리고, 수동으로 열 수도 있습니다.

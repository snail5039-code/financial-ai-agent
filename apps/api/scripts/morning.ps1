# 평일 아침 자동 시작: 서버(autostart.ps1) → 에뮬레이터 → 모의투자 앱.
# 등록: 작업 스케줄러 "InvestAgentMorning" (평일 08:10, 절전이면 깨움). 지우기: Unregister-ScheduledTask -TaskName InvestAgentMorning -Confirm:$false
# 오늘 계획 승인은 이 스크립트가 아니라 Claude 예약 작업(08:35)이 앱 화면에서 한다.
# 잠금 PIN은 넣지 않는다 (사람 몫). 잠겨 있으면 로그에 남기고 풀릴 때까지 최대 1시간 기다린다.
# 로그: %LOCALAPPDATA%\invest-agent\server.log (autostart.ps1과 같은 파일)

$ErrorActionPreference = 'Continue'
$log = Join-Path $env:LOCALAPPDATA 'invest-agent\server.log'
function Note($text) { Add-Content -Path $log -Value "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [아침] $text" -Encoding utf8 }
$sdk = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { 'C:\Users\snail\dev\android' }
$adb = Join-Path $sdk 'platform-tools\adb.exe'
$app = 'com.investagent.invest_client'

& (Join-Path $PSScriptRoot 'autostart.ps1')

if (-not ((& $adb devices) -match 'emulator-5554\s+device')) {
    Note '에뮬레이터 켜기'
    # -gpu host가 아니면 창이 검게만 보였다 (10/26). 창을 최소화하지 않는다 (11/10 화면이 안 보였다)
    # -no-snapshot-load: 빠른 부팅 스냅샷을 불러오면 화면이 멈춰 터치가 안 먹었다 (11/12). 항상 새로 부팅한다
    Start-Process (Join-Path $sdk 'emulator\emulator.exe') -ArgumentList '-avd', 'invest_phone', '-timezone', 'Asia/Seoul', '-gpu', 'host', '-no-snapshot-load'
    & $adb wait-for-device
    for ($i = 0; $i -lt 60; $i++) { if ((& $adb shell getprop sys.boot_completed) -match '1') { break }; Start-Sleep 3 }
}
& $adb shell svc power stayon true
& $adb shell input keyevent KEYCODE_WAKEUP

for ($i = 0; $i -lt 120; $i++) {
    if ((& $adb shell dumpsys window) -match 'isKeyguardShowing=false') { break }
    if ($i -eq 0) { Note '잠금 화면: 사람이 PIN을 풀어야 앱을 켤 수 있음 (최대 1시간 기다림)' }
    Start-Sleep 30
}
if ((& $adb shell dumpsys window) -match 'isKeyguardShowing=true') { Note '잠금이 안 풀려 앱을 못 켬'; exit 1 }

& $adb shell monkey -p $app -c android.intent.category.LAUNCHER 1 *> $null
Note '앱 켬'
# 장중 점검(watch.py)이 읽는 앱 로그. 이 스크립트가 끝나도 따로 돈다 (전에 띄운 것은 끄고 하나만)
Get-CimInstance Win32_Process -Filter "Name='adb.exe'" | Where-Object { $_.CommandLine -like '*logcat*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Process -FilePath $adb -ArgumentList 'logcat', '-v', 'brief', 'flutter:I', '*:S' -WindowStyle Hidden `
    -RedirectStandardOutput (Join-Path $env:TEMP 'flutter.log')

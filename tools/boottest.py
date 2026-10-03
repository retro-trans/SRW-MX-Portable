"""Launch an ISO in PPSSPP, wait, and report whether the game started (threads + screenshot)."""
import subprocess, sys, time
from ppsspp_dbg import Dbg
iso, shot = sys.argv[1], sys.argv[2]
subprocess.run(['powershell', '-NoProfile', '-Command',
                'Get-Process PPSSPPWindows64 -ErrorAction SilentlyContinue | Stop-Process -Force'])
time.sleep(2)
subprocess.Popen([r'C:\Program Files\PPSSPP\PPSSPPWindows64.exe', iso])
time.sleep(18)
with Dbg() as d:
    th = d.call('hle.thread.list').get('threads', [])
    print('threads:', [(t['name'], t['status']) for t in th])
Dbg.grab_window(shot)

"""Minimal client for the PPSSPP remote debugger (WebSocket, JSON events).

Enable in ppsspp.ini: RemoteDebuggerOnStartup = True, RemoteDebuggerLocal = True, RemoteISOPort = 45373.
Protocol: https://github.com/hrydgard/ppsspp/tree/master/Core/Debugger (WebSocket/*.cpp).

usage as a module:
    from ppsspp_dbg import Dbg
    with Dbg() as d:
        print(d.call('game.status'))
CLI:
    python ppsspp_dbg.py <event> [json-args]
"""
import asyncio, base64, json, sys
import websockets

URL = 'ws://127.0.0.1:45373/debugger'


class Dbg:
    def __init__(self, url=URL):
        self.url = url
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.ws = None
        self.n = 0

    def __enter__(self):
        self.ws = self.loop.run_until_complete(websockets.connect(self.url, max_size=64 << 20))
        return self

    def __exit__(self, *a):
        self.loop.run_until_complete(self.ws.close())

    def call(self, event, timeout=10, expect=None, **args):
        """Send an event; return the reply with our ticket (or, for broadcast-style replies
        such as cpu.stepping / cpu.resume, the first event named `expect`)."""
        self.n += 1
        ticket = str(self.n)
        msg = dict(args, event=event, ticket=ticket)
        expect = expect or {'cpu.stepping': 'cpu.stepping', 'cpu.resume': 'cpu.resume'}.get(event)

        async def go():
            await self.ws.send(json.dumps(msg))
            while True:
                r = json.loads(await asyncio.wait_for(self.ws.recv(), timeout))
                if r.get('ticket') == ticket or (expect and r.get('event') == expect) \
                        or (r.get('event') == 'error' and r.get('ticket') in (None, ticket)):
                    return r
        return self.loop.run_until_complete(go())

    def wait_event(self, name, timeout=30):
        async def go():
            while True:
                r = json.loads(await asyncio.wait_for(self.ws.recv(), timeout))
                if r.get('event') == name:
                    return r
        return self.loop.run_until_complete(go())

    # helpers
    def read(self, addr, size):
        r = self.call('memory.read', address=addr, size=size)
        return base64.b64decode(r['base64'])

    def write(self, addr, data):
        return self.call('memory.write', address=addr, base64=base64.b64encode(data).decode())

    def regs(self):
        """GPRs (+pc/hi/lo) as {name: value}."""
        r = self.call('cpu.getAllRegs')
        gpr = r['categories'][0]
        return dict(zip(gpr['registerNames'], gpr['uintValues']))

    def press(self, button, frames=6):
        """Tap a PSP button (cross, circle, square, triangle, start, select, up, down, left, right, ltrigger, rtrigger).
        Does not wait for the reply (it only arrives after the frames run, which never happens
        if a breakpoint stops the CPU first)."""
        self.n += 1
        msg = {'event': 'input.buttons.press', 'button': button, 'duration': frames, 'ticket': str(self.n)}
        self.loop.run_until_complete(self.ws.send(json.dumps(msg)))

    def tap(self, button, hold=0.15, wait=1.0):
        """Press and release a button with explicit state changes (more reliable than press())."""
        import time
        self.call('input.buttons.send', buttons={button: True})
        time.sleep(hold)
        self.call('input.buttons.send', buttons={button: False})
        time.sleep(wait)

    def is_stepping(self):
        return self.call('cpu.status').get('stepping')

    @staticmethod
    def grab_window(path):
        """Screen-capture the PPSSPP window client area (works with any GPU backend)."""
        import ctypes
        from ctypes import wintypes
        from PIL import ImageGrab
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        hwnds = []

        @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        def enum(h, _):
            buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(h, buf, 256)
            if buf.value.startswith('PPSSPP') and user32.IsWindowVisible(h):
                hwnds.append(h)
            return True
        user32.EnumWindows(enum, 0)
        if not hwnds:
            raise RuntimeError('PPSSPP window not found')
        h = hwnds[0]
        rc = wintypes.RECT()
        user32.GetClientRect(h, ctypes.byref(rc))
        w, hgt = rc.right, rc.bottom
        # PrintWindow(PW_CLIENTONLY|PW_RENDERFULLCONTENT) renders the window even when it is covered
        from PIL import Image
        gdi32 = ctypes.windll.gdi32
        hdc = user32.GetDC(h)
        mdc = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, hgt)
        gdi32.SelectObject(mdc, bmp)
        user32.PrintWindow(h, mdc, 3)

        class BMI(ctypes.Structure):
            _fields_ = [('biSize', ctypes.c_uint32), ('biWidth', ctypes.c_int32), ('biHeight', ctypes.c_int32),
                        ('biPlanes', ctypes.c_uint16), ('biBitCount', ctypes.c_uint16),
                        ('biCompression', ctypes.c_uint32), ('biSizeImage', ctypes.c_uint32),
                        ('biXPelsPerMeter', ctypes.c_int32), ('biYPelsPerMeter', ctypes.c_int32),
                        ('biClrUsed', ctypes.c_uint32), ('biClrImportant', ctypes.c_uint32)]
        bmi = BMI(ctypes.sizeof(BMI), w, -hgt, 1, 32, 0, 0, 0, 0, 0, 0)
        buf = ctypes.create_string_buffer(w * hgt * 4)
        gdi32.GetDIBits(mdc, bmp, 0, hgt, buf, ctypes.byref(bmi), 0)
        gdi32.DeleteObject(bmp)
        gdi32.DeleteDC(mdc)
        user32.ReleaseDC(h, hdc)
        img = Image.frombuffer('RGBA', (w, hgt), buf.raw, 'raw', 'BGRA', 0, 1).convert('RGB')
        img.save(path)
        return img.size

    def screenshot(self, path, resume=True):
        """Screenshots need the CPU paused: pause, grab the display buffer as PNG, resume."""
        self.call('cpu.stepping')
        r = self.call('gpu.buffer.screenshot', type='uri', timeout=20)
        if resume:
            self.call('cpu.resume')
        if 'uri' in r:
            open(path, 'wb').write(base64.b64decode(r['uri'].split(',', 1)[1]))
            return r.get('width'), r.get('height')
        return r


if __name__ == '__main__':
    with Dbg() as d:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(json.dumps(d.call(sys.argv[1], **args), ensure_ascii=False)[:4000])

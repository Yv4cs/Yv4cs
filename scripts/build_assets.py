"""Rebuild the README graphics. Standard library only: python scripts/build_assets.py

telemetry-*.svg  plotted from assets/h100-qwen3-8b.csv (measured runs)
lidar-*.svg      ray-cast of a small synthetic scene (simulated, not a recording)
"""
import csv
import math
from collections import defaultdict
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace"

THEMES = {
    "light": dict(bg="#ffffff", ink="#1f2328", mute="#59636e", grid="#d8dee4",
                  fp8="#d9480f", bf16="#2b6cb0",
                  ramp=["#b7c9dc", "#7fa3c7", "#4a7fb3", "#1d4f86"]),
    "dark": dict(bg="#0d1117", ink="#f0f6fc", mute="#9198a1", grid="#2a313c",
                 fp8="#e8632b", bf16="#4a90d9",
                 ramp=["#2f5a89", "#4079b3", "#5b9bd8", "#b4d8fb"]),
}

REDUCED = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


# --- telemetry -------------------------------------------------------------

def load_means():
    runs = defaultdict(list)
    with open(ASSETS / "h100-qwen3-8b.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            runs[row["precision"].lower(), int(row["concurrency"])].append(
                (float(row["tokens_per_s"]), float(row["joules_per_token"])))
    out = defaultdict(list)
    for (prec, conc), vals in sorted(runs.items()):
        n = len(vals)
        out[prec].append((conc, sum(v[0] for v in vals) / n, sum(v[1] for v in vals) / n))
    return out


def telemetry(t, data):
    x0, x1, y0, y1, top = 12, 930, 410, 72, 18000

    def px(c):
        return x0 + math.log2(c) / 8 * (x1 - x0)

    def py(v):
        return y0 - v / top * (y0 - y1)

    s = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 500" role="img" aria-labelledby="t d">
<title id="t">Charles Quan Tran, AI engineer: measured LLM throughput on one H100</title>
<desc id="d">Line chart of output tokens per second against concurrent requests for Qwen3-8B. FP8 reaches {data["fp8"][-1][1]:,.0f} and BF16 {data["bf16"][-1][1]:,.0f} tokens per second at 256 concurrent requests.</desc>
<style>
text{{font-family:{SANS};fill:{t["ink"]}}}
.m{{font-family:{MONO};fill:{t["mute"]};font-size:20px}}
.l{{fill:none;stroke-width:4;stroke-linejoin:round;stroke-linecap:round;stroke-dasharray:1;animation:draw 2.4s cubic-bezier(.6,0,.2,1) backwards}}
.e{{animation:show .6s ease-out 2.1s backwards}}
@keyframes draw{{from{{stroke-dashoffset:1}}}}
@keyframes show{{from{{opacity:0}}}}
{REDUCED}
</style>''']
    for v in (5000, 10000, 15000):  # upper gridlines stay clear of the name
        gx = {5000: x0, 10000: 660, 15000: 720}[v]
        s.append(f'<path d="M{gx} {py(v):.1f}H{x1}" stroke="{t["grid"]}" stroke-width="1.5"/>')
        s.append(f'<text class="m" x="{gx - 12 if v > 5000 else gx}" y="{py(v) + (7 if v > 5000 else -9):.1f}" text-anchor="{"end" if v > 5000 else "start"}">{v // 1000}k</text>')
    s.append(f'<path d="M{x0} {y0}H{x1}" stroke="{t["mute"]}" stroke-width="1.5"/>')
    for c in (1, 16, 64, 256):
        anchor = "start" if c == 1 else "middle"
        s.append(f'<path d="M{px(c):.1f} {y0}v8" stroke="{t["mute"]}" stroke-width="1.5"/>'
                 f'<text class="m" x="{px(c):.1f}" y="{y0 + 34}" text-anchor="{anchor}">{c}</text>')
    s.append(f'<text class="m" x="{x0}" y="{y0 + 74}">output tokens/s vs concurrent requests (log scale)</text>')
    s.append('<text x="8" y="92" font-size="76" font-weight="700" letter-spacing="-2">Charles Quan Tran</text>')
    s.append(f'<text x="12" y="146" font-size="31" style="fill:{t["mute"]}">AI engineer: 3D perception, GPU efficiency</text>')
    for prec in ("bf16", "fp8"):
        pts = [(px(c), py(v)) for c, v, _ in data[prec]]
        line = "L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        s.append(f'<path class="l" pathLength="1" stroke="{t[prec]}" d="M{line}"/>')
        s.append('<g class="e">' + "".join(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{t[prec]}" stroke="{t["bg"]}" stroke-width="3"/>'
            for x, y in pts))
        _, v, j = data[prec][-1]
        y = pts[-1][1]
        size = 46 if prec == "fp8" else 32
        s.append(f'<text x="{x1 + 22}" y="{y + 8:.1f}" font-size="{size}" font-weight="700">{v:,.0f}</text>'
                 f'<text class="m" x="{x1 + 22}" y="{y + 38:.1f}">{prec.upper()}, {j:.3f} J/token</text></g>')
    s.append("</svg>")
    return "\n".join(s)


# --- lidar -----------------------------------------------------------------

BOXES = [  # x0,x1,y0,y1,z0,z1 in metres; sensor at the origin, ground at z=-0.8
    (2.4, 3.6, -3.4, -2.2, -.8, .5), (4.6, 5.8, 1.0, 2.6, -.8, .9),
    (-3.2, -2.2, 1.8, 2.8, -.8, .3), (-5.2, -3.8, -3.2, -1.8, -.8, 1.0),
    (.2, 1.2, 3.0, 4.0, -.8, .2), (7.4, 8.2, -1.6, -.6, -.8, 1.4),
    (-8.0, -7.2, .6, 1.6, -.8, 1.4),
]
WALLS = (-10.5, 10.5, -5.5, 5.5)
MAX_Z = 1.5


def ray(dx, dy, dz):
    """Distance from the sensor to the first surface hit, or inf."""
    best = -.8 / dz if dz < 0 else math.inf
    for lim, d in ((WALLS[0], dx), (WALLS[1], dx), (WALLS[2], dy), (WALLS[3], dy)):
        if abs(d) > 1e-9 and 0 < lim / d < best and lim / d * dz <= MAX_Z:
            best = lim / d
    for b in BOXES:
        near, far = 0.0, best
        for lo, hi, d in ((b[0], b[1], dx), (b[2], b[3], dy), (b[4], b[5], dz)):
            if abs(d) < 1e-9:
                if not lo <= 0 <= hi:
                    near, far = 1.0, 0.0
                continue
            a, c = sorted((lo / d, hi / d))
            near, far = max(near, a), min(far, c)
        if 0 < near <= far:
            best = near
    return best


def project(x, y, z):
    yaw, pitch, cam = math.radians(-14), math.radians(33), 19
    x, y = x * math.cos(yaw) - y * math.sin(yaw), x * math.sin(yaw) + y * math.cos(yaw)
    depth = cam + y * math.cos(pitch) - z * math.sin(pitch)
    up = y * math.sin(pitch) + z * math.cos(pitch)
    return 560 + 810 * x / depth, 216 - 810 * up / depth


def lidar(t, rings=26, azimuths=300, sectors=30):
    groups = defaultdict(list)
    for r in range(rings):
        el = math.radians(-27 + 37 * r / (rings - 1))
        for a in range(azimuths):
            az = 2 * math.pi * a / azimuths
            d = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
            dist = ray(*d)
            if math.isinf(dist):
                continue
            x, y, z = (dist * k for k in d)
            level = min(3, int((z + .8) / 2.3 * 3) + (z > -.79))
            groups[a * sectors // azimuths, level].append(project(x, y, z))
    ox, oy = project(0, 0, 0)
    s = [f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 540" role="img" aria-labelledby="t d">
<title id="t">Simulated LiDAR scan</title>
<desc id="d">Point cloud from a simulated {rings}-ring LiDAR in a synthetic walled scene with box obstacles. Colour encodes height.</desc>
<style>
path{{fill:none;stroke-linecap:round;stroke-width:2.6}}
.s{{animation:sweep 9s linear infinite}}
@keyframes sweep{{0%{{opacity:1}}70%,97%{{opacity:.5}}100%{{opacity:1}}}}
{REDUCED}
</style>''']
    for sec in range(sectors):
        s.append(f'<g class="s" style="animation-delay:{(sec / sectors - 1) * 9:.2f}s">')
        for level in range(4):
            pts = groups.get((sec, level))
            if pts:
                d = "".join(f"M{x:.0f} {y:.0f}h0" for x, y in pts)
                s.append(f'<path stroke="{t["ramp"][level]}" d="{d}"/>')
        s.append("</g>")
    s.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="8" fill="{t["fp8"]}" stroke="{t["bg"]}" stroke-width="3"/>')
    s.append("</svg>")
    return "\n".join(s)


if __name__ == "__main__":
    means = load_means()
    for name, theme in THEMES.items():
        for kind, svg in (("telemetry", telemetry(theme, means)), ("lidar", lidar(theme))):
            path = ASSETS / f"{kind}-{name}.svg"
            path.write_text(svg + "\n", encoding="utf-8", newline="\n")
            print(path.name, path.stat().st_size // 1024, "KB")

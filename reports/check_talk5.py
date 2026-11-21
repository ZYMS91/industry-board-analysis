import subprocess, sys, io, os

AUDIO = sys.argv[1] if len(sys.argv) > 1 else r"reports\talk5-part.m4a"
MD = r"reports\talk-3min-600.md"
ok = True

if not os.path.exists(AUDIO):
    print(f"FAIL 录音不存在：{AUDIO}")
    sys.exit(1)

d = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "csv=p=0", AUDIO]).decode().strip())
print(f"时长 = {d:.1f}s")
if not (80 <= d <= 110):
    print("FAIL 时长不在 80-110s")
    ok = False

t = io.open(MD, encoding="utf-8").read()
for s, want in [("十七个模块", True), ("四十二条测试", True), ("五类错数字", True),
                ("十六个模块", False), ("三十八条测试", False)]:
    hit = s in t
    print(f"{'含' if hit else '不含'}「{s}」")
    if hit != want:
        ok = False

print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)

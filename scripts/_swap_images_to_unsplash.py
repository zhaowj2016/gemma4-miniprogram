"""把 3 个高质量黄金样例里的 /assets/library/*.jpg 占位路径，换成精选真实 Unsplash 链接。
按文件名判断 头像(people) vs 场景(scene)，每个不同占位路径分到一个尽量不重复的真实图。"""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
HQ = ROOT / "golden_examples" / "high_quality"
U = "https://images.unsplash.com/photo-{}?w=600&q=80"

PEOPLE = [
    "1494790108377-be9c29b29330", "1507003211169-0a1dd7228f2d",
    "1517841905240-472988babdf9", "1527980965255-d3b416303d12",
    "1520813792240-56fc4a3765a7", "1556228453-efd6c1ff04f6",
    "1500648767791-00dcc994a43e", "1534528741775-53994a69daeb",
]
SCENE = {
    "product_detail": [  # 咖啡 / 咖啡机 / 饮品
        "1497515114629-f71d768fd07c", "1559056199-641a0ac8b55e",
        "1497636577773-f1231844b336", "1481833761820-0509d3217039",
        "1498804103079-a6351b050096", "1495774856032-8b90bbb32b32",
        "1559305616-3f99cd43e353", "1442550528053-c431ecb55509",
        "1514432324607-a09d9b4aefdd", "1461023058943-07fcbe16d735",
    ],
    "event_signup": [  # 大会 / 演讲 / 商务现场
        "1497366216548-37526070297c", "1497366811353-6870744d04b2",
        "1486406146926-c627a92ad1ab", "1507679799987-c73779587ccf",
        "1521017432531-fbd92d768814", "1505373877841-8d25f7d46678",
        "1540575467063-178a50c2df87", "1531058020387-3be344556be6",
    ],
    "store_booking": [  # 沙龙 / 造型 / 美学空间
        "1521590832167-7bcbfaa6381f", "1560066984-138dadb4c035",
        "1522337660859-02fbefca4702", "1503951914875-452162b0f3f1",
        "1599387737838-626bf0d1f1f3", "1633681926022-84c23e8cb2d6",
        "1487412947147-5cebf100ffc2", "1492106087820-71f1a00d2b11",
    ],
}
PEOPLE_MARK = ("user", "spk", "sty", "voice", "avatar", "guest")

def is_people(path: str) -> bool:
    return any(m in path for m in PEOPLE_MARK)

for name, scene_ids in SCENE.items():
    d = HQ / name
    wxml = (d / "index.wxml").read_text(encoding="utf-8")
    js = (d / "index.js").read_text(encoding="utf-8")
    blob = wxml + "\n" + js
    paths = sorted(set(re.findall(r"/assets/library/[^\"']+\.jpg", blob)))
    mapping = {}
    pe = sc = 0
    for p in paths:
        if is_people(p):
            mapping[p] = U.format(PEOPLE[pe % len(PEOPLE)]); pe += 1
        else:
            mapping[p] = U.format(scene_ids[sc % len(scene_ids)]); sc += 1
    for p, url in mapping.items():
        wxml = wxml.replace(p, url)
        js = js.replace(p, url)
    (d / "index.wxml").write_text(wxml, encoding="utf-8")
    (d / "index.js").write_text(js, encoding="utf-8")
    print(f"{name}: 替换 {len(paths)} 个占位路径（people {pe} / scene {sc}）")

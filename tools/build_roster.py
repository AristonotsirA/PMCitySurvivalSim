# -*- coding: utf-8 -*-
"""tools/personas/*.json → data/characters.json

페르소나를 모아 검증하고 하나의 명단으로 만든다. 시나리오 오프닝 대사가
캐릭터의 높임·호칭 설정과 어긋나지 않는지도 함께 점검한다.
  python tools/build_roster.py
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REQ = ['id', 'name', 'faction', 'color', 'p', 's', 't', 'r', 'h', 'c']
POLITE = ('합쇼체', '해요체', '하오체')
BANMAL_YOU = re.compile(r'(^|[\s"“])(너는|너를|너도|너한테|너에게|너의|너랑|네가|너)(?=[\s,.!?…~"”]|$)')
NAME_YA = re.compile(r'\{name\}(아|야)(?=[\s,.!?…~"”]|$)')


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    errs, warns = [], []
    factions = {f['id'] for f in load(os.path.join(ROOT, 'data', 'factions.json'))}
    chars = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'tools', 'personas', '*.json'))):
        c = load(p)
        for k in REQ:
            if not c.get(k):
                errs.append(f'{os.path.basename(p)}: {k} 비어 있음')
        if c.get('faction') not in factions:
            errs.append(f"{c.get('id')}: 알 수 없는 세력 {c.get('faction')}")
        if c['id'] != os.path.splitext(os.path.basename(p))[0]:
            errs.append(f"{p}: 파일 이름과 id가 다름")
        if c.get('h', '').startswith(POLITE) and c.get('c') == '너':
            errs.append(f"{c['id']}: 존댓말 인물인데 호칭이 '너'")
        chars.append(c)
    ids = [c['id'] for c in chars]
    if len(set(ids)) != len(ids):
        errs.append('id 중복')
    names = {c['name']: c for c in chars}

    # 시나리오 오프닝 점검 (설정을 바꾸면 오프닝도 함께 점검 — 잘못된 말투를 가르치지 않도록)
    world = load(os.path.join(ROOT, 'data', 'world.json'))
    locs = {l['id'] for l in world['locations']}
    for l in world['locations']:
        for cid in l['chars']:
            if cid not in ids:
                errs.append(f"장소 {l['id']}: 없는 인물 {cid}")
    for sc in load(os.path.join(ROOT, 'data', 'scenarios.json')):
        if sc['loc'] not in locs:
            errs.append(f"시나리오 {sc['id']}: 없는 장소 {sc['loc']}")
        for cid in sc['cast']:
            if cid not in ids:
                errs.append(f"시나리오 {sc['id']}: 없는 인물 {cid}")
        if len(sc['cast']) > 6:
            errs.append(f"시나리오 {sc['id']}: 등장 인물이 6명을 넘음")
        for line in sc['opening']:
            m = re.match(r'^([가-힣 ]{1,12}?)(?:\(([^)]{1,4})\))?\s*:\s*"(.*)"$', line)
            if not m:
                continue
            c = names.get(m.group(1).strip())
            if not c:
                errs.append(f"시나리오 {sc['id']}: 모르는 화자 {m.group(1)}")
                continue
            if c['id'] not in sc['cast']:
                warns.append(f"시나리오 {sc['id']}: {c['name']}이(가) cast에 없음")
            said = m.group(3)
            if c['h'].startswith(POLITE):
                if BANMAL_YOU.search(said):
                    errs.append(f"시나리오 {sc['id']}: 존댓말 인물 {c['name']}이(가) '너'라고 부름 → {said}")
                if NAME_YA.search(said):
                    errs.append(f"시나리오 {sc['id']}: 존댓말 인물 {c['name']}이(가) 이름에 '아/야'를 붙임 → {said}")
            call = c['c']
            if '{name}' in said and '{name}' in call:
                # 호칭이 '{name} 님'인데 '{name} 씨'로 부르는 식의 어긋남
                for suf in ('님', '씨', '공'):
                    if re.search(r'\{name\} ' + suf, said) and not call.endswith(suf):
                        errs.append(f"시나리오 {sc['id']}: {c['name']}의 호칭은 '{call}'인데 '{{name}} {suf}' 사용")
    for w in warns:
        print('경고:', w)
    if errs:
        for e in errs:
            print('오류:', e)
        sys.exit(1)
    order = {f: i for i, f in enumerate(['lcb', 'library'])}
    chars.sort(key=lambda c: (order.get(c['faction'], 9), c.get('order', 99)))
    with open(os.path.join(ROOT, 'data', 'characters.json'), 'w', encoding='utf-8') as f:
        json.dump(chars, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'인물 {len(chars)}명 → data/characters.json')


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
"""artifact/template.html + data/*.json → index.html (GitHub Pages 루트)

  python tools/build_roster.py && python tools/build_artifact.py
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = '<!--__DATA__-->'


def load(name):
    with open(os.path.join(ROOT, 'data', name), encoding='utf-8') as f:
        return json.load(f)


def main():
    data = {
        'world': load('world.json'),
        'factions': load('factions.json'),
        'scenarios': load('scenarios.json'),
        'characters': load('characters.json'),
    }
    with open(os.path.join(ROOT, 'artifact', 'template.html'), encoding='utf-8') as f:
        tpl = f.read()
    assert tpl.count(MARK) == 1, 'template.html에 데이터 자리표시가 하나여야 합니다'
    blob = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    out = tpl.replace(MARK, '<script>window.__PMC_DATA__=' + blob + ';</script>')
    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(out)
    print(f'index.html {len(out.encode("utf-8")) // 1024} KB')


if __name__ == '__main__':
    main()

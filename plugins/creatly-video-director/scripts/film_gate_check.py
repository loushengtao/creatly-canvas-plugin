"""生成前门禁：读取 getCanvasContext(detail="full") 的快照，逐节点检查强制关卡。

用法：
    python3 scripts/film_gate_check.py canvas.json
    python3 scripts/film_gate_check.py canvas.json --nodes <id>,<id> --skip blocking,axis

canvas.json 可以是 MCP 返回的 output（含 nodes）、完整响应，或工具结果落盘的 [{type,text}] 数组。
FAIL 为强制关卡，存在未豁免的 FAIL 时退出码为 1；WARN 只提示。
用户明确要求跳过某项时，用 --skip 传入关卡名，输出里会标为「用户豁免」。
"""
import argparse
import json
import re
import sys

FAIL, WARN = 'FAIL', 'WARN'
COLOR_CARD = '色卡'
MENTION = re.compile(r'\[@([^\]]+)\]')
IMG_INDEX = re.compile(r'【图(\d+)】')
AUDIO_INDEX = re.compile(r'【音频(\d+)】')
BLOCK = re.compile(r'(\d+(?:\.\d+)?)\s*[—–\-~至到]\s*(\d+(?:\.\d+)?)\s*(?:秒|s)')
CUT = re.compile(r'HARD CUT|Cut on action', re.I)
PATH = re.compile(r'/Users/|[A-Za-z]:[\\/]|\S+\.(?:png|jpe?g|webp|mp4|mov|wav|mp3)\b', re.I)
CONTEXT_WORDS = ('上一段', '上一镜', '同上', '保持之前', '和前面一样', '如前所述')
AXIS_WORDS = ('轴线', '画面左', '画面右', '画左', '画右')
MUSIC = re.compile(r'(背景音乐|配乐|BGM)', re.I)


def load_nodes(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, list):
        for item in data:
            try:
                data = json.loads(item.get('text', ''))
                break
            except (ValueError, AttributeError):
                continue
    for key in ('structuredContent', 'output'):
        if isinstance(data, dict) and key in data and isinstance(data[key], dict):
            data = data[key]
    return data['nodes']


def norm(text):
    return re.sub(r'[\W_]+', '', text or '').lower()


def prompt_of(node):
    gp = node.get('generationParams') or {}
    return gp.get('prompt') or node.get('content') or ''


class Checker:
    def __init__(self, nodes, max_images, max_audios, max_duration, skip):
        self.nodes = nodes
        self.by = {n['id']: n for n in nodes}
        self.max_images, self.max_audios, self.max_duration = max_images, max_audios, max_duration
        self.skip = skip
        self.results = []
        self.elements = {n['label']: n for n in nodes if n['type'] == 'element'}
        self.element_by_ref = dict(self.elements)
        self.element_by_ref.update({e['id']: e for e in self.elements.values()})
        self.subject_ids = set(e['id'] for e in self.elements.values())
        self.subject_ids |= {n['id'] for n in nodes if n.get('parentNode') in self.subject_ids}
        self.card = next((e for name, e in self.elements.items() if COLOR_CARD in name), None)

    def add(self, level, gate, node, msg):
        if gate in self.skip:
            level = 'SKIP'
        self.results.append((level, gate, node['label'] if node else '项目', msg))

    def children(self, element):
        return [n for n in self.nodes if n.get('parentNode') == element['id'] and n['type'] == 'frame']

    def mentions(self, text):
        return [self.element_by_ref.get(m) for m in MENTION.findall(text)], MENTION.findall(text)

    def check_project(self):
        for e in self.elements.values():
            if not self.children(e) and not e.get('frameFiles'):
                self.add(WARN, 'subject-images', e, '快照里看不到这个主体的图片（主体库图片不随快照返回），生成前请在画布上确认已上传')
        if self.card is not None and self.children(self.card) \
                and not any(n.get('frameFiles') for n in self.children(self.card)):
            self.add(FAIL, 'color-card', self.card, '色卡主体里没有已生成的图片，分镜前必须先有色卡')
        for e in self.elements.values():
            if e.get('subType') != 'character' or not self.children(e):
                continue
            views = 0
            for n in self.children(e):
                if n.get('frameFiles'):
                    views += 3 if n.get('subType') == 'tri_view' else 1
            if views < 3:
                self.add(FAIL, 'character-views', e, f'只有 {views} 个视角，视频前每个角色至少 3 个视角')

    def check_common(self, node):
        text = prompt_of(node)
        found, raw = self.mentions(text)
        for element, name in zip(found, raw):
            if element is None:
                self.add(FAIL, 'unknown-subject', node, f'提及的主体 [@{name}] 不存在')
        if self.card is not None and self.card not in found:
            self.add(FAIL, 'color-card-mention', node, f'提示词没有 [@{self.card["label"]}]')
        parent = self.by.get(node.get('parentNode') or '')
        if not parent or parent['type'] != 'group':
            self.add(FAIL, 'group', node, '没有放进本镜组')
        for pid in node.get('parentIds') or []:
            if pid in self.subject_ids:
                self.add(FAIL, 'subject-edge', node, f'连线到了主体「{self.by[pid]["label"]}」，主体只 @ 不连线')
        if PATH.search(text):
            self.add(FAIL, 'prompt-hygiene', node, '提示词里出现了本地路径或文件名')
        for word in CONTEXT_WORDS:
            if word in text:
                self.add(WARN, 'standalone', node, f'出现依赖上下文的说法「{word}」，每段提示词应独立成立')

    def check_video(self, node):
        text = prompt_of(node)
        gp = node.get('generationParams') or {}
        refs = gp.get('referenceResources') or []
        images = [r for r in refs if r.get('mediaType') == 'IMAGE']
        audios = [r for r in refs if r.get('mediaType') == 'AUDIO']
        if len(images) > self.max_images:
            self.add(FAIL, 'ref-limit', node, f'参考图 {len(images)} 张，超过上限 {self.max_images}')
        if len(audios) > self.max_audios:
            self.add(FAIL, 'ref-limit', node, f'参考音频 {len(audios)} 条，超过上限 {self.max_audios}')
        top_img = max(map(int, IMG_INDEX.findall(text)), default=0)
        top_audio = max(map(int, AUDIO_INDEX.findall(text)), default=0)
        if top_img > len(images):
            self.add(FAIL, 'ref-index', node, f'提示词引用到【图{top_img}】，实际只传了 {len(images)} 张图')
        if top_audio > len(audios):
            self.add(FAIL, 'ref-index', node, f'提示词引用到【音频{top_audio}】，实际只传了 {len(audios)} 条音频')
        labels = []
        for r in images:
            src = self.by.get(r.get('sourceNodeId') or '')
            label = (src or {}).get('label') or r.get('label') or ''
            labels.append(label)
            if src and src['type'] == 'frame' and src['id'] not in self.subject_ids and '站位' not in label:
                self.add(WARN, 'shot-frame-ref', node, f'垫了镜头画面「{label[:20]}」；默认只垫资产，正反打写进提示词')
        if not any('站位' in lb for lb in labels):
            self.add(WARN, 'blocking', node, '没有垫站位图')
        characters = {e['id'] for e in self.mentions(text)[0] if e and e.get('subType') == 'character'}
        if len(characters) >= 2 and not any(w in text for w in AXIS_WORDS):
            self.add(WARN, 'axis', node, '多人戏没有写轴线或谁在画左、谁在画右')
        for m in MUSIC.finditer(text):
            before = text[max(0, m.start() - 6):m.start()]
            if not re.search(r'无|禁止|不要|不|没有', before):
                self.add(WARN, 'music', node, '提示词要求了背景音乐；默认不加音乐')
                break
        self.check_timing(node, text, gp.get('duration'))
        for r in audios:
            src = self.by.get(r.get('sourceNodeId') or '')
            line = re.sub(r'^[^:：]{1,20}[:：]\s*', '', (src or {}).get('content') or '')
            if line and norm(line) not in norm(text):
                self.add(WARN, 'dialogue', node, f'音频「{(src or {}).get("label", "")[:16]}」的台词没有逐字出现在提示词里')

    def check_timing(self, node, text, duration):
        blocks = [(float(a), float(b)) for a, b in BLOCK.findall(text)]
        if duration and duration > self.max_duration:
            self.add(FAIL, 'duration-limit', node, f'时长 {duration} 秒，超过模型上限 {self.max_duration} 秒')
        if not blocks:
            return
        if abs(blocks[0][0]) > 0.05:
            self.add(FAIL, 'timing', node, f'第一个镜头块从 {blocks[0][0]} 秒开始，应从 0 开始')
        for (a1, b1), (a2, b2) in zip(blocks, blocks[1:]):
            if abs(b1 - a2) > 0.05:
                self.add(FAIL, 'timing', node, f'镜头块 {a1}-{b1} 与 {a2}-{b2} 不连续')
        if duration and abs(blocks[-1][1] - duration) > 0.05:
            self.add(FAIL, 'timing', node, f'镜头块结束于 {blocks[-1][1]} 秒，节点时长是 {duration} 秒')
        lengths = [round(b - a, 2) for a, b in blocks]
        if len(lengths) >= 3 and len(set(lengths)) == 1:
            self.add(WARN, 'equal-durations', node, f'{len(lengths)} 个镜头都是 {lengths[0]} 秒，时长应随台词和动作错落')
        for length in lengths:
            if length > 8 or length < 1.5:
                self.add(WARN, 'shot-length', node, f'有镜头块 {length} 秒，单镜通常 2–8 秒')
                break
        if len(blocks) >= 2 and 'NO CUT' not in text and len(CUT.findall(text)) < len(blocks) - 1:
            self.add(WARN, 'hard-cut', node, f'{len(blocks)} 个镜头块，镜头块之间应独立一行写 HARD CUT')

    def is_shot_frame(self, node):
        shots = {n['id'] for n in self.nodes if n['type'] == 'shot'}
        if any(p in shots for p in node.get('parentIds') or []):
            return True
        group = node.get('parentNode')
        return any(n.get('parentNode') == group and any(p in shots for p in n.get('parentIds') or [])
                   for n in self.nodes)

    def run(self, only=None):
        self.check_project()
        for node in self.nodes:
            if only and node['id'] not in only:
                continue
            if node['type'] == 'video':
                self.check_common(node)
                self.check_video(node)
            elif node['type'] == 'frame' and not node.get('subType') and node['id'] not in self.subject_ids \
                    and self.is_shot_frame(node):
                self.check_common(node)
        return self.results


def main(argv=None):
    parser = argparse.ArgumentParser(description='分镜与视频生成前门禁')
    parser.add_argument('canvas', help='getCanvasContext(detail="full") 的 JSON 文件')
    parser.add_argument('--nodes', help='只检查这些节点 ID（逗号分隔），默认检查全部分镜与视频')
    parser.add_argument('--skip', default='', help='用户明确豁免的关卡名（逗号分隔）')
    parser.add_argument('--max-images', type=int, default=30, help='模型参考图上限，以 listGenerationModels 为准')
    parser.add_argument('--max-audios', type=int, default=10)
    parser.add_argument('--max-duration', type=float, default=30)
    parser.add_argument('--json', action='store_true', help='以 JSON 输出结果')
    args = parser.parse_args(argv)
    skip = {s.strip() for s in args.skip.split(',') if s.strip()}
    only = {s.strip() for s in args.nodes.split(',')} if args.nodes else None
    results = Checker(load_nodes(args.canvas), args.max_images, args.max_audios, args.max_duration, skip).run(only)
    fails = [r for r in results if r[0] == FAIL]
    if args.json:
        print(json.dumps([dict(zip(('level', 'gate', 'node', 'message'), r)) for r in results], ensure_ascii=False, indent=2))
    else:
        for level, gate, label, msg in results:
            tag = '用户豁免' if level == 'SKIP' else level
            print(f'{tag}\t{gate}\t{label}\t{msg}')
        warns = sum(1 for r in results if r[0] == WARN)
        print(f'\n结论：{"未通过" if fails else "通过"}（FAIL {len(fails)}，WARN {warns}，豁免 {sum(1 for r in results if r[0] == "SKIP")}）')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())

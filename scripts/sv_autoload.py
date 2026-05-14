#!/usr/bin/env python3
"""
sv_autoload.py - Viking Memory System: Auto-load relevant memories
Scans memory layers and loads relevant ones based on current context/keywords.

Usage:
  python sv_autoload.py <memories_dir> [--context "task description"] [--max N]
  python sv_autoload.py <memories_dir> --promote [--threshold 0.7]
  python sv_autoload.py <memories_dir> --update-weight
"""
import sys, os, re, json, math
from datetime import datetime

def parse_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}
    fm_text = match.group(1)
    meta = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            if val.lower() in ('true', 'false'):
                val = val.lower() == 'true'
            elif val.replace('.', '').isdigit():
                val = float(val) if '.' in val else int(val)
            elif val.lower() == 'null':
                val = None
            elif val.startswith('[') and val.endswith(']'):
                try:
                    val = json.loads(val)
                except:
                    pass
            meta[key] = val
    return meta

def get_importance_factor(importance):
    return {'high': 3.0, 'important': 5.0, 'medium': 1.5, 'low': 0.5}.get(importance, 1.0)

def calc_weight(meta):
    importance_factor = get_importance_factor(meta.get('importance', 'medium'))
    try:
        dt_str = meta.get('created', '')[:19].replace('T', ' ')
        created_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        days = max(0, (datetime.now() - created_dt).days)
    except:
        days = 0
    time_decay = 1.0 / ((days + 1) ** 0.3)
    access_count = meta.get('access_count', 1)
    log_factor = math.log(access_count + 1)
    context_correlation = meta.get('context_correlation', 1.0)
    weight = importance_factor * time_decay * log_factor * context_correlation
    return round(weight, 4)

def simple_relevance(meta, body, context):
    """Calculate relevance score based on keyword matching."""
    if not context:
        return calc_weight(meta)
    title = meta.get('title', '').lower()
    tags = ' '.join(meta.get('tags', [])).lower()
    text = f"{title} {tags} {body[:300].lower()}"
    context_words = set(w.lower() for w in context.split() if len(w) > 2)
    text_words = set(text.split())
    if not context_words:
        return calc_weight(meta)
    overlap = context_words & text_words
    relevance = len(overlap) / len(context_words)
    return round(calc_weight(meta) * (1 + relevance), 4)

def load_memories(memories_dir, context='', max_files=10, update_weight=False):
    """Load and rank memories by relevance/weight."""
    results = []
    # Scan Viking layers in order: L0 > L1 > L2 > L4
    # Also support legacy layer names for backward compatibility
    layer_order = ['viking-L0-hot', 'viking-L1-warm', 'viking-L2-cold', 'viking-L4-archive',
                   'hot', 'warm', 'cold', 'archive', 'daily', 'meetings']
    for layer in layer_order:
        layer_dir = os.path.join(memories_dir, layer)
        if not os.path.isdir(layer_dir):
            continue
        for fname in sorted(os.listdir(layer_dir)):
            if not fname.endswith('.md'):
                continue
            fp = os.path.join(layer_dir, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                meta = parse_frontmatter(content)
                if not meta:
                    continue
                body_start = content.find('---', 3)
                body = content[body_start+3:].strip() if body_start > 0 else ''
                score = simple_relevance(meta, body, context)
                results.append((fp, meta, body[:200], score))
            except:
                continue
    # Sort by score descending
    results.sort(key=lambda x: x[3], reverse=True)
    return results[:max_files]

def update_weights(memories_dir):
    """Batch update weights for all memories."""
    count = 0
    for root, dirs, files in os.walk(memories_dir):
        for fname in files:
            if not fname.endswith('.md'):
                continue
            fp = os.path.join(root, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                meta = parse_frontmatter(content)
                if not meta:
                    continue
                body_start = content.find('---', 3)
                body = content[body_start+3:].strip() if body_start > 0 else ''
                new_weight = calc_weight(meta)
                # Update weight in frontmatter
                lines = content.split('\n')
                new_lines = []
                in_fm = False
                for line in lines:
                    if line.strip() == '---':
                        in_fm = not in_fm
                        new_lines.append(line)
                    elif in_fm and line.strip().startswith('weight:'):
                        new_lines.append(f"weight: {new_weight}")
                    else:
                        new_lines.append(line)
                with open(fp, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                count += 1
            except:
                continue
    return count

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    memories_dir = args[0]
    context = ''
    max_files = 10
    do_promote = '--promote' in args
    do_update_weight = '--update-weight' in args

    if '--context' in args:
        idx = args.index('--context')
        if idx + 1 < len(args):
            context = args[idx+1]
    if '--max' in args:
        idx = args.index('--max')
        if idx + 1 < len(args):
            max_files = int(args[idx+1])

    if not os.path.isdir(memories_dir):
        print(f"Error: directory not found: {memories_dir}")
        sys.exit(1)

    if do_update_weight:
        count = update_weights(memories_dir)
        print(f"✅ Updated weights for {count} memories")
        return

    if do_promote:
        # Run sv_promote logic
        import subprocess
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), 'sv_promote.py'), memories_dir]
        if context:
            cmd.extend(['--context', context])
        subprocess.run(cmd)
        return

    # Auto-load: print top memories
    results = load_memories(memories_dir, context, max_files)
    if not results:
        print("No memories found.")
        return

    print(f"=== Auto-loaded {len(results)} memories (context: '{context[:40]}') ===\n")
    for fp, meta, body_preview, score in results:
        rel = os.path.relpath(fp, memories_dir)
        print(f"  [{meta.get('current_layer','?')}] {rel}")
        print(f"    Score: {score} | Weight: {meta.get('weight', 0)} | Access: {meta.get('access_count', 0)}")
        print(f"    {body_preview[:80]}...")
        print()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
sv_decompress.py - Viking Memory System: Decompress/restore from archive
Phase 3 feature: archive keeps multi-granularity summary + full content.
Supports viewing summary, showing full content, or restoring to hot layer.

Usage:
  python sv_decompress.py <file_path>                     # show summary + preview
  python sv_decompress.py <file_path> --show            # show full content (from .full file or body)
  python sv_decompress.py <file_path> --restore [--target-layer hot|warm]
"""
import sys, os, re, json

def parse_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}, text
    fm_text = match.group(1)
    body = text[match.end():].strip()
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
    return meta, body

def load_full_content(file_path, meta):
    """Load full content from .full file if exists, otherwise return body."""
    full_file = meta.get('full_content_file')
    if full_file:
        full_path = os.path.join(os.path.dirname(file_path), full_file)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
    # Try .full extension
    for ext in ['.full', '.archive.full', '_full.md']:
        fp = file_path + ext
        if os.path.exists(fp):
            with open(fp, 'r', encoding='utf-8') as f:
                return f.read()
    return None

def restore_to_layer(file_path, memories_dir, target_layer='hot'):
    """Restore a memory from archive/cold to target layer (hot/warm)."""
    target_dir = os.path.join(memories_dir, target_layer)
    os.makedirs(target_dir, exist_ok=True)
    new_path = os.path.join(target_dir, os.path.basename(file_path))

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    meta, body = parse_frontmatter(content)

    # Update metadata
    layer_map = {'hot': 'L0', 'warm': 'L1', 'cold': 'L2', 'archive': 'L4'}
    meta['current_layer'] = layer_map.get(target_layer, 'L0')
    meta['target_layer'] = target_layer
    meta['last_restored'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    meta['restored_from'] = os.path.relpath(file_path, memories_dir)

    # Write to new location
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif v is None:
            lines.append(f"{k}: null")
        else:
            lines.append(f"{k}: {v}")
    lines.append('---\n')
    lines.append(body)

    with open(new_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    # Also restore full content if exists
    full_content = load_full_content(file_path, meta)
    if full_content:
        full_path = new_path + '.full'
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(full_content)

    print(f"✅ Restored to {target_layer}/: {os.path.basename(new_path)}")
    return new_path

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sv_decompress.py <file_path> [--show] [--restore] [--target-layer hot|warm]")
        sys.exit(1)

    file_path = args[0]
    show_full = '--show' in args
    do_restore = '--restore' in args
    target_layer = 'hot'

    if '--target-layer' in args:
        idx = args.index('--target-layer')
        if idx + 1 < len(args):
            target_layer = args[idx+1]

    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    meta, body = parse_frontmatter(content)

    print(f"=== {meta.get('title', os.path.basename(file_path))} ===")
    print(f"Layer: {meta.get('current_layer', '?')}")
    print(f"Summary: {meta.get('summary', '(none)')[:100]}")
    print()

    if show_full:
        full = load_full_content(file_path, meta)
        if full:
            print("=== FULL CONTENT ===")
            print(full[:2000])
            if len(full) > 2000:
                print(f"\n... ({len(full)} chars total)")
        else:
            print("No full content file found. Showing body:")
            print(body[:2000])
        return

    if do_restore:
        # Need memories_dir - find it by walking up from file_path
        abs_path = os.path.abspath(file_path)
        memories_dir = None
        check = os.path.dirname(abs_path)
        for _ in range(5):
            if os.path.basename(check) == 'memories':
                memories_dir = check
                break
            check = os.path.dirname(check)
            if not check or check == os.path.dirname(check):
                break
        if not memories_dir:
            print("Error: cannot determine memories_dir (need to restore)")
            print("Please specify memories_dir as second argument")
            sys.exit(1)
        new_path = restore_to_layer(file_path, memories_dir, target_layer)
        return

    # Default: show summary + preview
    print("=== PREVIEW (body) ===")
    print(body[:500])
    if len(body) > 500:
        print("...")
    print(f"\nFull content available: {'Yes' if load_full_content(file_path, meta) else 'No (body only)'}")
    print(f"\nUse --show to view full content")
    print(f"Use --restore to restore to {target_layer}/")

if __name__ == '__main__':
    # Need datetime import for restore function
    from datetime import datetime
    main()

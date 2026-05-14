#!/usr/bin/env python3
"""
sv_read.py - Viking Memory System: Read memory file with frontmatter parsing
Usage:
  python sv_read.py <file_path>
  python sv_read.py <file_path> --update-access  (update last_access and access_count)
"""
import sys, os, re, json
from datetime import datetime, timedelta

def parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text."""
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return {}, text
    fm_text = match.group(1)
    body = text[match.end():]
    
    meta = {}
    for line in fm_text.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' in line:
            key, _, val = line.partition(':')
            key = key.strip()
            val = val.strip()
            # Parse booleans
            if val.lower() in ('true', 'false'):
                val = val.lower() == 'true'
            # Parse numbers
            elif val.replace('.', '').isdigit():
                val = float(val) if '.' in val else int(val)
            # Parse lists (simple JSON-like)
            elif val.startswith('[') and val.endswith(']'):
                try:
                    val = json.loads(val)
                except:
                    pass
            meta[key] = val
    return meta, body.strip()

def update_access_metadata(file_path):
    """Update last_access and increment access_count."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    meta, body = parse_frontmatter(content)
    now = datetime.now().astimezone()
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S") + now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:]
    
    meta['last_access'] = now_str
    meta['access_count'] = meta.get('access_count', 0) + 1
    
    # Rebuild file
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
    lines.append("---\n")
    lines.append(body)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return meta

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sv_read.py <file_path> [--update-access]")
        sys.exit(1)
    
    file_path = args[0]
    update_access = '--update-access' in args
    
    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    
    if update_access:
        meta = update_access_metadata(file_path)
        print(f"✅ Updated access: count={meta['access_count']}, last={meta['last_access']}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    meta, body = parse_frontmatter(content)
    
    print(f"=== {meta.get('title', os.path.basename(file_path))} ===")
    print(f"ID: {meta.get('id', 'N/A')}")
    print(f"Event Time: {meta.get('event_time', meta.get('created', 'N/A'))}")  # Show event_time
    print(f"Insert Time: {meta.get('insert_time', meta.get('last_access', 'N/A'))}")  # Show insert_time
    print(f"Importance: {meta.get('importance', 'N/A')}")
    print(f"Tags: {meta.get('tags', [])}")
    print(f"Weight: {meta.get('weight', 'N/A')}")
    print(f"Review Status: {meta.get('review_status', 'N/A')}")
    print(f"\n{body}")

if __name__ == '__main__':
    main()

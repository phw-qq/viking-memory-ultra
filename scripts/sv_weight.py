#!/usr/bin/env python3
"""
sv_weight.py - Viking Memory System: Calculate and update memory weight
Weight Formula: W = importance_factor × (1/(days+1)^0.3) × ln(access_count+1) × context_correlation

Usage:
  python sv_weight.py <file_path> [--update] [--context-correlation 0.5-1.5]
  python sv_weight.py --batch <memory_dir> [--update]
"""
import sys, os, re, json, math
from datetime import datetime, timedelta, timezone

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
            elif val.startswith('[') and val.endswith(']'):
                try: val = json.loads(val)
                except: pass
            meta[key] = val
    return meta

def write_frontmatter(file_path, meta, body):
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

def get_importance_factor(importance):
    return {'high': 3.0, 'important': 5.0, 'medium': 1.5, 'low': 0.5}.get(importance, 1.0)

def calc_weight(meta):
    importance = meta.get('importance', 'medium')
    importance_factor = get_importance_factor(importance)
    
    # Time decay
    created_str = meta.get('created', '')
    try:
        # Parse ISO format: 2026-03-27T15:30:00+08:00
        dt_str = created_str.replace('T', ' ').replace('+', '+').strip()
        if '+' in dt_str:
            dt_str = dt_str.split('+')[0].strip()
        created_dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        days = max(0, (datetime.now() - created_dt).days)
    except:
        days = 0
    time_decay = 1.0 / ((days + 1) ** 0.3)
    
    # Access count (logarithmic growth)
    access_count = meta.get('access_count', 1)
    log_factor = math.log(access_count + 1)
    
    # Context correlation
    context_correlation = meta.get('context_correlation', 1.0)
    
    weight = importance_factor * time_decay * log_factor * context_correlation
    return round(weight, 4), {
        'importance_factor': importance_factor,
        'time_decay': round(time_decay, 4),
        'log_factor': round(log_factor, 4),
        'context_correlation': context_correlation,
        'days': days,
        'access_count': access_count
    }

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sv_weight.py <file_path> [--update] [--context-correlation V]")
        print("       sv_weight.py --batch <dir> [--update]")
        sys.exit(1)
    
    if args[0] == '--batch':
        mem_dir = args[1] if len(args) > 1 else ''
        update = '--update' in args
        if not os.path.isdir(mem_dir):
            print(f"Error: directory not found: {mem_dir}")
            sys.exit(1)
        total = 0
        for root, dirs, files in os.walk(mem_dir):
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
                    weight, details = calc_weight(meta)
                    if update:
                        body_start = content.find('---', 3)
                        if body_start > 0:
                            body = content[body_start+3:].strip()
                            meta['weight'] = weight
                            write_frontmatter(fp, meta, body)
                    total += 1
                    print(f"  {fname}: weight={weight}")
                except Exception as e:
                    continue
        print(f"\n✅ Processed {total} files" + (" (updated weights)" if update else ""))
    else:
        file_path = args[0]
        update = '--update' in args
        ctx_corr = 1.0
        if '--context-correlation' in args:
            idx = args.index('--context-correlation')
            if idx + 1 < len(args):
                ctx_corr = float(args[idx+1])
        
        if not os.path.exists(file_path):
            print(f"Error: file not found: {file_path}")
            sys.exit(1)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        meta = parse_frontmatter(content)
        if not meta:
            print("Error: no frontmatter found")
            sys.exit(1)
        
        if ctx_corr != 1.0:
            meta['context_correlation'] = ctx_corr
        
        weight, details = calc_weight(meta)
        
        print(f"=== Weight Calculation: {os.path.basename(file_path)} ===")
        print(f"  Importance Factor: {details['importance_factor']}")
        print(f"  Time Decay (days={details['days']}): {details['time_decay']}")
        print(f"  Log Factor (count={details['access_count']}): {details['log_factor']}")
        print(f"  Context Correlation: {details['context_correlation']}")
        print(f"  → Final Weight: {weight}")
        
        if update:
            body_start = content.find('---', 3)
            body = content[body_start+3:].strip() if body_start > 0 else content
            meta['weight'] = weight
            write_frontmatter(file_path, meta, body)
            print(f"\n✅ Weight updated to {weight}")

if __name__ == '__main__':
    main()

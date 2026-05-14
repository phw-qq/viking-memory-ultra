#!/usr/bin/env python3
"""
sv_promote.py - Viking Memory System: Promote cold/archive memories back to hot layer
Dynamic backflow: when current task is semantically similar to cold/archive memories,
automatically promote them to hot layer.

Usage:
  python sv_promote.py <memories_dir> --context "current task description"
  python sv_promote.py <memories_dir> --dry-run [--threshold 0.7]
  python sv_promote.py <memories_dir> --file <specific_file>  # promote specific file
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
            elif val.startswith('[') and val.endswith(']'):
                try:
                    val = json.loads(val)
                except:
                    pass
            meta[key] = val
    return meta

def simple_similarity(text1, text2):
    """Simple keyword-based similarity (Jaccard index)."""
    words1 = set(w.lower() for w in text1.split() if len(w) > 2)
    words2 = set(w.lower() for w in text2.split() if len(w) > 2)
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union) if union else 0.0

def should_promote(file_path, context, threshold=0.7):
    """Check if a memory file should be promoted based on semantic similarity."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        meta = parse_frontmatter(content)
        if not meta:
            return False, 0.0
        
        # Skip important memories (they stay where they are)
        if meta.get('important') or meta.get('importance') in ('high', 'important'):
            return False, 0.0
        
        # Get body (content after frontmatter)
        body_start = content.find('---', 3)
        body = content[body_start+3:].strip() if body_start > 0 else content
        
        # Calculate similarity
        title = meta.get('title', '')
        tags = ' '.join(meta.get('tags', []))
        full_text = f"{title} {tags} {body[:500]}"
        
        similarity = simple_similarity(full_text, context)
        return similarity >= threshold, similarity
    except Exception as e:
        return False, 0.0

def promote_file(file_path, memories_dir, dry_run=False):
    """Promote a file to hot layer."""
    rel_path = os.path.relpath(file_path, memories_dir)
    parts = rel_path.replace('\\', '/').split('/')
    
    # Find target hot path
    hot_dir = os.path.join(memories_dir, 'hot')
    os.makedirs(hot_dir, exist_ok=True)
    new_path = os.path.join(hot_dir, os.path.basename(file_path))
    
    if dry_run:
        return file_path, new_path, 'would promote'
    
    # Update metadata
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    meta = parse_frontmatter(content)
    body_start = content.find('---', 3)
    body = content[body_start+3:].strip() if body_start > 0 else content
    
    meta['current_layer'] = 'L0'
    meta['target_layer'] = 'hot'
    meta['last_promoted'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    meta['promotion_count'] = meta.get('promotion_count', 0) + 1
    
    # Write updated metadata
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
    
    # Write to new location
    with open(new_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    # Remove old file
    if os.path.exists(file_path) and file_path != new_path:
        os.remove(file_path)
    
    return file_path, new_path, 'promoted'

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sv_promote.py <memories_dir> --context 'task description'")
        print("       sv_promote.py <memories_dir> --dry-run [--threshold 0.7]")
        sys.exit(1)
    
    memories_dir = args[0]
    dry_run = '--dry-run' in args
    threshold = 0.7
    
    if '--threshold' in args:
        idx = args.index('--threshold')
        if idx + 1 < len(args):
            threshold = float(args[idx+1])
    
    if not os.path.isdir(memories_dir):
        print(f"Error: directory not found: {memories_dir}")
        sys.exit(1)
    
    # Specific file promotion
    if '--file' in args:
        idx = args.index('--file')
        if idx + 1 < len(args):
            file_path = args[idx+1]
            result = promote_file(file_path, memories_dir, dry_run)
            print(f"{'[] DRY RUN] ' if dry_run else '✅'} Promoted: {os.path.basename(file_path)}")
            return
    
    # Context-based promotion
    context = ''
    if '--context' in args:
        idx = args.index('--context')
        if idx + 1 < len(args):
            context = args[idx+1]
    
    if not context:
        print("Error: --context required for automatic promotion")
        sys.exit(1)
    
    # Scan cold and archive layers
    results = []
    for layer in ['cold', 'archive']:
        layer_dir = os.path.join(memories_dir, layer)
        if not os.path.isdir(layer_dir):
            continue
        for fname in os.listdir(layer_dir):
            if not fname.endswith('.md'):
                continue
            fp = os.path.join(layer_dir, fname)
            should, sim = should_promote(fp, context, threshold)
            if should:
                result = promote_file(fp, memories_dir, dry_run)
                results.append((result, sim))
    
    if not results:
        print(f"No memories found to promote (threshold={threshold}, context='{context[:30]}...')")
        return
    
    print(f"{'[] DRY RUN] ' if dry_run else '✅'} Promoting {len(results)} memories:")
    for (old_path, new_path, status), sim in results:
        print(f"  {os.path.basename(old_path)} → hot/ (similarity={sim:.2f})")
    
    if dry_run:
        print("\nRun without --dry-run to actually promote these files.")

if __name__ == '__main__':
    main()

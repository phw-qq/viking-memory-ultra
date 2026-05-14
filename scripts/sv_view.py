#!/usr/bin/env python3
"""
sv_view.py - Viking Memory System: View (视图) Layer
Provides dynamic memory views based on context.
Part of the Agentic Memory Triplet (Ledger + View + Policy).

Usage:
  python sv_view.py <memories_dir> [--context "task"] [--view time|importance|relevance|review]
  python sv_view.py <memories_dir> --compare <file1> <file2>
  python sv_view.py <memories_dir> --stats
"""

import sys, os, re, json, math
from datetime import datetime, timezone, timedelta

def parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text."""
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
        dt_str = meta.get('event_time', meta.get('created', ''))[:19].replace('T', ' ')
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
        return 0.5  # neutral score when no context
    
    title = meta.get('title', '').lower()
    tags = ' '.join(meta.get('tags', [])).lower()
    text = f"{title} {tags} {body[:300].lower()}"
    
    context_words = set(w.lower() for w in context.split() if len(w) > 2)
    text_words = set(text.split())
    
    if not context_words:
        return 0.5
    
    overlap = context_words & text_words
    relevance = len(overlap) / len(context_words)
    return round(relevance, 4)

def load_memories(memories_dir):
    """Load all memories from the directory structure."""
    results = []
    
    # Scan all layers
    layer_order = ['viking-L0-hot', 'viking-L1-warm', 'viking-L2-cold', 'viking-L4-archive',
                   'hot', 'warm', 'cold', 'archive', 'daily', 'meetings', 'facts']
    
    for layer in layer_order:
        layer_dir = os.path.join(memories_dir, layer)
        if not os.path.isdir(layer_dir):
            continue
        
        for fname in sorted(os.listdir(layer_dir)):
            if not (fname.endswith('.md') or fname.endswith('.json')):
                continue
            
            fp = os.path.join(layer_dir, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if fname.endswith('.json'):
                    # JSON fact file
                    meta = json.loads(content)
                    body = json.dumps(meta, ensure_ascii=False)
                else:
                    # Markdown file with frontmatter
                    meta = parse_frontmatter(content)
                    if not meta:
                        continue
                    body_start = content.find('---', 3)
                    body = content[body_start+3:].strip() if body_start > 0 else ''
                
                # Calculate weight and relevance
                weight = calc_weight(meta)
                meta['_weight'] = weight
                meta['_file_path'] = fp
                meta['_body'] = body[:200]
                meta['_layer'] = layer
                
                results.append(meta)
            except:
                continue
    
    return results

def view_by_time(memories, reverse=True):
    """View memories sorted by event_time."""
    # Sort by event_time (or insert_time as fallback)
    sorted_mem = sorted(memories, 
                        key=lambda x: x.get('event_time', 
                                             x.get('insert_time', 
                                                    x.get('created', ''))), 
                        reverse=reverse)
    
    print(f"=== View: By Time ({len(sorted_mem)} memories) ===\n")
    for i, meta in enumerate(sorted_mem[:20]):  # Show top 20
        event_time = meta.get('event_time', meta.get('created', '?'))
        title = meta.get('title', os.path.basename(meta['_file_path']))
        layer = meta.get('_layer', '?')
        
        print(f"  {i+1}. [{layer}] {title[:40]}")
        print(f"     Event: {event_time[:19] if event_time != '?' else '?'}")
        print(f"     {meta['_body'][:60]}...")
    
    return sorted_mem

def view_by_importance(memories, reverse=True):
    """View memories sorted by importance and weight."""
    # Sort by importance factor, then by weight
    def importance_sort_key(m):
        imp = m.get('importance', 'medium')
        factor = {'important': 5, 'high': 3, 'medium': 2, 'low': 1}.get(imp, 0)
        return (factor, m.get('_weight', 0))
    
    sorted_mem = sorted(memories, key=importance_sort_key, reverse=reverse)
    
    print(f"=== View: By Importance ({len(sorted_mem)} memories) ===\n")
    for i, meta in enumerate(sorted_mem[:20]):
        title = meta.get('title', os.path.basename(meta['_file_path']))
        layer = meta.get('_layer', '?')
        importance = meta.get('importance', 'medium')
        weight = meta.get('_weight', 0)
        
        print(f"  {i+1}. [{layer}] {title[:40]}")
        print(f"     Importance: {importance} | Weight: {weight}")
        print(f"     {meta['_body'][:60]}...")
    
    return sorted_mem

def view_by_relevance(memories, context):
    """View memories sorted by relevance to context."""
    if not context:
        print("⚠️  No context provided for relevance view")
        return memories
    
    # Calculate relevance for each memory
    for meta in memories:
        body = meta.get('_body', '')
        meta['_relevance'] = simple_relevance(meta, body, context)
    
    # Sort by relevance
    sorted_mem = sorted(memories, key=lambda x: x.get('_relevance', 0), reverse=True)
    
    print(f"=== View: By Relevance to '{context[:40]}' ({len(sorted_mem)} memories) ===\n")
    for i, meta in enumerate(sorted_mem[:20]):
        title = meta.get('title', os.path.basename(meta['_file_path']))
        layer = meta.get('_layer', '?')
        relevance = meta.get('_relevance', 0)
        
        print(f"  {i+1}. [{layer}] {title[:40]}")
        print(f"     Relevance: {relevance:.3f}")
        print(f"     {meta['_body'][:60]}...")
    
    return sorted_mem

def view_by_review(memories):
    """View memories sorted by review status."""
    # Group by review status
    pending = [m for m in memories if m.get('review_status') == 'pending_review']
    reviewed = [m for m in memories if m.get('review_status') == 'reviewed']
    mastered = [m for m in memories if m.get('review_status') == 'mastered']
    
    print(f"=== View: By Review Status ({len(memories)} memories) ===\n")
    print(f"Pending Review: {len(pending)}")
    print(f"Reviewed: {len(reviewed)}")
    print(f"Mastered: {len(mastered)}\n")
    
    # Show pending first
    if pending:
        print(f"--- Pending Review ({len(pending)}) ---")
        for i, meta in enumerate(pending[:10]):
            title = meta.get('title', os.path.basename(meta['_file_path']))
            next_review = meta.get('next_review', '?')
            
            print(f"  {i+1}. {title[:40]}")
            print(f"     Next Review: {next_review}")
    
    return {'pending': pending, 'reviewed': reviewed, 'mastered': mastered}

def compare_memories(file1, file2):
    """Compare two memory files."""
    try:
        with open(file1, 'r', encoding='utf-8') as f:
            content1 = f.read()
        with open(file2, 'r', encoding='utf-8') as f:
            content2 = f.read()
        
        meta1 = parse_frontmatter(content1)
        meta2 = parse_frontmatter(content2)
        
        print(f"=== Compare Memories ===\n")
        print(f"File 1: {os.path.basename(file1)}")
        print(f"  Weight: {meta1.get('weight', '?')}")
        print(f"  Importance: {meta1.get('importance', '?')}")
        print(f"  Access Count: {meta1.get('access_count', '?')}")
        
        print(f"\nFile 2: {os.path.basename(file2)}")
        print(f"  Weight: {meta2.get('weight', '?')}")
        print(f"  Importance: {meta2.get('importance', '?')}")
        print(f"  Access Count: {meta2.get('access_count', '?')}")
        
        # Compare weights
        w1 = meta1.get('weight', 0)
        w2 = meta2.get('weight', 0)
        
        if w1 > w2:
            print(f"\nResult: File 1 has higher weight ({w1} vs {w2})")
        elif w2 > w1:
            print(f"\nResult: File 2 has higher weight ({w2} vs {w1})")
        else:
            print(f"\nResult: Both files have equal weight ({w1})")
        
        return True
    except Exception as e:
        print(f"Error comparing files: {e}")
        return False

def show_stats(memories):
    """Show statistics about memories."""
    print(f"=== Memory Statistics ({len(memories)} total) ===\n")
    
    # Count by layer
    layer_counts = {}
    for meta in memories:
        layer = meta.get('_layer', 'unknown')
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    
    print(f"By Layer:")
    for layer, count in sorted(layer_counts.items()):
        print(f"  {layer}: {count}")
    
    # Count by importance
    imp_counts = {}
    for meta in memories:
        imp = meta.get('importance', 'unknown')
        imp_counts[imp] = imp_counts.get(imp, 0) + 1
    
    print(f"\nBy Importance:")
    for imp, count in sorted(imp_counts.items()):
        print(f"  {imp}: {count}")
    
    # Count by review status
    review_counts = {}
    for meta in memories:
        status = meta.get('review_status', 'unknown')
        review_counts[status] = review_counts.get(status, 0) + 1
    
    print(f"\nBy Review Status:")
    for status, count in sorted(review_counts.items()):
        print(f"  {status}: {count}")
    
    # Average weight
    if memories:
        avg_weight = sum(m.get('_weight', 0) for m in memories) / len(memories)
        print(f"\nAverage Weight: {avg_weight:.3f}")
    
    return layer_counts

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    memories_dir = args[0]
    
    if not os.path.isdir(memories_dir):
        print(f"Error: directory not found: {memories_dir}")
        sys.exit(1)
    
    # Load all memories
    memories = load_memories(memories_dir)
    
    if '--view' in args:
        idx = args.index('--view')
        if idx + 1 < len(args):
            view_mode = args[idx + 1]
            
            if view_mode == 'time':
                view_by_time(memories)
            elif view_mode == 'importance':
                view_by_importance(memories)
            elif view_mode == 'relevance':
                context = ''
                if '--context' in args:
                    cidx = args.index('--context')
                    if cidx + 1 < len(args):
                        context = args[cidx + 1]
                view_by_relevance(memories, context)
            elif view_mode == 'review':
                view_by_review(memories)
            else:
                print(f"Unknown view mode: {view_mode}")
        else:
            print("Usage: --view time|importance|relevance|review")
    elif '--compare' in args:
        idx = args.index('--compare')
        if idx + 2 < len(args):
            file1 = args[idx + 1]
            file2 = args[idx + 2]
            compare_memories(file1, file2)
        else:
            print("Usage: --compare <file1> <file2>")
    elif '--stats' in args:
        show_stats(memories)
    else:
        # Default: show time view
        view_by_time(memories)

if __name__ == '__main__':
    main()

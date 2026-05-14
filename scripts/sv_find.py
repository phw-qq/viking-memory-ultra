#!/usr/bin/env python3
"""
sv_find.py - Viking Memory System: Find/search memories by tag, keyword, or status
Usage:
  python sv_find.py --dir <memory_dir> [options]
"""

import os, re, json, glob, argparse, sys
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

def matches_filters(meta, args):
    """Check if memory matches all filter criteria"""
    if args.tags:
        tag_list = [t.strip() for t in args.tags.split(',')]
        meta_tags = meta.get('tags', [])
        if not any(t in meta_tags for t in tag_list):
            return False
    
    if args.importance:
        if meta.get('importance') != args.importance:
            return False
    
    if args.review_status:
        if meta.get('review_status') != args.review_status:
            return False
    
    if args.min_weight:
        if meta.get('weight', 0) < args.min_weight:
            return False
    
    if args.keyword:
        # Search in title and content
        search_content = meta.get('title', '') + '\n' + meta.get('_content', '')
        if args.keyword.lower() not in search_content.lower():
            return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Viking Memory System - Find/Search memories')
    parser.add_argument('--dir', required=True, help='Memory directory to search')
    parser.add_argument('--keyword', help='Search keyword in title and content')
    parser.add_argument('--tags', help='Filter by tags (comma-separated)')
    parser.add_argument('--importance', choices=['high', 'medium', 'low', 'important'], 
                        help='Filter by importance level')
    parser.add_argument('--review-status', dest='review_status',
                        help='Filter by review status (pending_review/reviewed/mastered)')
    parser.add_argument('--min-weight', type=float, help='Minimum weight filter')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results (default: 10)')
    parser.add_argument('--layer', help='Filter by layer (L0/L1/L2/L4)')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.dir):
        print(f"Error: directory not found: {args.dir}")
        return 1
    
    results = []
    
    for pattern in ['**/*.md', '**/*.markdown']:
        for fp in glob.glob(os.path.join(args.dir, pattern), recursive=True):
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                meta = parse_frontmatter(content)
                if not meta:
                    continue
                
                # Store content for keyword search
                meta['_content'] = content
                
                # Filter by layer
                if args.layer:
                    if meta.get('current_layer') != args.layer:
                        continue
                
                if not matches_filters(meta, args):
                    continue
                
                results.append((fp, meta))
            except Exception as e:
                continue
    
    if not results:
        print("No matching memories found.")
        return 0
    
    # Sort by weight (descending)
    results.sort(key=lambda x: x[1].get('weight', 0), reverse=True)
    
    # Limit results
    results = results[:args.limit]
    
    print(f"Found {len(results)} matching memories:\n")
    for fp, meta in results:
        rel_path = os.path.relpath(fp, args.dir)
        print(f"  [{meta.get('current_layer', '?')}] {rel_path}")
        print(f"    ID: {meta.get('id', 'N/A')} | Weight: {meta.get('weight', 0):.4f} | Status: {meta.get('review_status', 'N/A')}")
        print(f"    Tags: {meta.get('tags', [])}")
        print(f"    Title: {meta.get('title', '')[:60]}")
        print()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

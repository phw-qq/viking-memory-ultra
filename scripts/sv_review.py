#!/usr/bin/env python3
"""
sv_review.py - Viking Memory System: Review status management (Phase 4)
Implements Ebbinghaus forgetting curve: 1d, 3d, 7d, 15d, 30d
"""

import sys, os, re, json, argparse
from datetime import datetime, timedelta

INTERVALS = [1, 3, 7, 15, 30]  # Ebbinghaus intervals in days

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

def get_next_review_date(review_count):
    """Calculate next review date based on Ebbinghaus curve"""
    idx = min(review_count, len(INTERVALS) - 1)
    days = INTERVALS[idx]
    return datetime.now() + timedelta(days=days)

def mark_review_status(file_path, status):
    """Mark a memory file with review status"""
    if not os.path.isfile(file_path):
        print(f"Error: file not found: {file_path}")
        return False
    
    if status not in ('pending_review', 'reviewing', 'reviewed', 'mastered'):
        print(f"Error: invalid status: {status}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        meta = parse_frontmatter(content)
        if not meta:
            print(f"Error: no frontmatter found in {file_path}")
            return False
        
        meta['review_status'] = status
        meta['last_reviewed'] = datetime.now().isoformat()
        meta['review_count'] = meta.get('review_count', 0) + 1
        
        if status == 'reviewed':
            # Calculate next review date
            next_date = get_next_review_date(meta['review_count'])
            meta['next_review'] = next_date.isoformat()
            print(f"✅ Marked as reviewed. Next review: {next_date.strftime('%Y-%m-%d')}")
        elif status == 'mastered':
            # Move to archive layer
            meta['current_layer'] = 'L4'
            meta['target_layer'] = 'archive'
            print(f"✅ Marked as mastered. Moved to archive layer.")
        
        # Write back
        # Remove frontmatter from content
        body = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        write_frontmatter(file_path, meta, body)
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def list_by_status(mem_dir, status=None):
    """List memories by review status"""
    if not os.path.isdir(mem_dir):
        print(f"Error: directory not found: {mem_dir}")
        return False
    
    count = 0
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
                
                if status is None or meta.get('review_status') == status:
                    count += 1
                    rel = os.path.relpath(fp, mem_dir)
                    print(f"  {rel}")
                    print(f"    Status: {meta.get('review_status', 'N/A')} | Review Count: {meta.get('review_count', 0)}")
                    if meta.get('next_review'):
                        print(f"    Next Review: {meta['next_review']}")
                    print()
            except:
                continue
    
    print(f"\nTotal: {count} memories")
    return True

def show_stats(mem_dir):
    """Show review statistics"""
    if not os.path.isdir(mem_dir):
        print(f"Error: directory not found: {mem_dir}")
        return False
    
    stats = {
        'pending_review': 0,
        'reviewing': 0,
        'reviewed': 0,
        'mastered': 0,
        'total': 0
    }
    
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
                
                status = meta.get('review_status', 'pending_review')
                if status in stats:
                    stats[status] += 1
                stats['total'] += 1
            except:
                continue
    
    print("=== Review Statistics ===")
    for status, count in stats.items():
        print(f"  {status}: {count}")
    
    return True

def list_due(mem_dir):
    """List memories due for review today"""
    if not os.path.isdir(mem_dir):
        print(f"Error: directory not found: {mem_dir}")
        return False
    
    today = datetime.now().date()
    count = 0
    
    print(f"=== Due for Review ({today}) ===\n")
    
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
                
                next_review = meta.get('next_review')
                if next_review:
                    try:
                        review_date = datetime.fromisoformat(next_review).date()
                        if review_date <= today:
                            count += 1
                            rel = os.path.relpath(fp, mem_dir)
                            print(f"  {rel}")
                            print(f"    Status: {meta.get('review_status')} | Next Review: {next_review}")
                            print()
                    except:
                        pass
            except:
                continue
    
    if count == 0:
        print("  No memories due for review today.")
    else:
        print(f"\nTotal: {count} memories due")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Viking Memory System - Review Status Management')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # mark command
    mark_parser = subparsers.add_parser('mark', help='Mark review status')
    mark_parser.add_argument('file', help='Memory file path')
    mark_parser.add_argument('status', choices=['pending_review', 'reviewing', 'reviewed', 'mastered'],
                            help='Review status')
    
    # list command
    list_parser = subparsers.add_parser('list', help='List memories by status')
    list_parser.add_argument('status', nargs='?', choices=['pending_review', 'reviewing', 'reviewed', 'mastered'],
                            help='Filter by status (optional)')
    list_parser.add_argument('--dir', required=True, help='Memories directory')
    
    # stats command
    stats_parser = subparsers.add_parser('stats', help='Show review statistics')
    stats_parser.add_argument('--dir', required=True, help='Memories directory')
    
    # due command
    due_parser = subparsers.add_parser('due', help='List due reviews')
    due_parser.add_argument('--dir', required=True, help='Memories directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'mark':
        return 0 if mark_review_status(args.file, args.status) else 1
    elif args.command == 'list':
        return 0 if list_by_status(args.dir, args.status) else 1
    elif args.command == 'stats':
        return 0 if show_stats(args.dir) else 1
    elif args.command == 'due':
        return 0 if list_due(args.dir) else 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

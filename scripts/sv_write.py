#!/usr/bin/env python3
"""
sv_write.py - Viking Memory System: Write memory with frontmatter
Usage:
  python sv_write.py <file_path> <content> [--importance high|medium|low|important] [--tags tag1,tag2]
"""
import sys, os, re, json
from datetime import datetime, timedelta

def parse_args(args):
    file_path = None
    content = None
    importance = "medium"
    tags = []
    title = ""
    event_time = None
    
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--importance" and i + 1 < len(args):
            importance = args[i+1]; i += 2
        elif arg == "--tags" and i + 1 < len(args):
            tags = [t.strip() for t in args[i+1].split(",")]; i += 2
        elif arg == "--title" and i + 1 < len(args):
            title = args[i+1]; i += 2
        elif arg == "--event_time" and i + 1 < len(args):
            event_time = args[i+1]; i += 2
        elif not file_path:
            file_path = arg
        else:
            content = (content + " " + arg) if content else arg
        i += 1
    return file_path, content, importance, tags, title, event_time

def gen_id():
    return "mem_" + datetime.now().strftime("%Y%m%d_%H%M%S")

def calc_retention(importance):
    return 0 if importance == "important" else (365 if importance == "high" else (90 if importance == "medium" else 30))

def calc_weight(importance):
    return {"high": 3.0, "important": 5.0, "medium": 1.5, "low": 0.5}[importance]

def get_target_layer(file_path):
    p = file_path.replace("\\", "/").lower()
    if "/hot/" in p: return "L0", "hot"
    if "/warm/" in p: return "L1", "warm"
    if "/cold/" in p: return "L2", "cold"
    if "/archive/" in p: return "L4", "archive"
    if "/daily/" in p: return "L0", "hot"
    return "L0", "hot"

def build_frontmatter(meta):
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---\n")
    return "\n".join(lines)

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sv_write.py <file_path> <content> [--importance X] [--tags t1,t2] [--title T] [--event_time T]")
        sys.exit(1)
    
    file_path, content, importance, tags, title, event_time = parse_args(args)
    if not file_path or not content:
        print("Error: file_path and content required"); sys.exit(1)
    
    now = datetime.now().astimezone()
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S") + now.strftime("%z")[:3] + ":" + now.strftime("%z")[3:]
    
    # Parse event_time (when the memory event occurred)
    if event_time:
        try:
            # Try ISO format
            if '+' in event_time or event_time.endswith('Z'):
                event_dt = datetime.fromisoformat(event_time.replace('Z', '+00:00'))
            else:
                event_dt = datetime.fromisoformat(event_time)
        except:
            event_dt = now
    else:
        event_dt = now
    
    event_time_str = event_dt.strftime("%Y-%m-%dT%H:%M:%S") + event_dt.strftime("%z")[:3] + ":" + event_dt.strftime("%z")[3:] if event_dt.utcoffset() else event_dt.strftime("%Y-%m-%dT%H:%M:%S")
    
    current_layer, target_layer = get_target_layer(file_path)
    
    meta = {
        "id": gen_id(),
        "title": title or content[:50].replace("\n", " "),
        "importance": importance,
        "important": importance == "important",
        "tags": tags,
        "event_time": event_time_str,  # When the event occurred
        "insert_time": now_str,  # When this memory was inserted
        "last_access": now_str,
        "access_count": 1,
        "context_correlation": 1.0,
        "retention": calc_retention(importance),
        "current_layer": current_layer,
        "target_layer": target_layer,
        "weight": calc_weight(importance),
        "review_status": "pending_review",
        "last_reviewed": None,
        "next_review": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
        "review_count": 0
    }
    
    frontmatter = build_frontmatter(meta)
    full_content = frontmatter + content
    
    # Ensure directory exists
    dir_path = os.path.dirname(file_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_content)
    
    print(f"✅ Written: {file_path}")
    print(f"   ID: {meta['id']}, Layer: {current_layer}, Weight: {meta['weight']}")

if __name__ == "__main__":
    main()

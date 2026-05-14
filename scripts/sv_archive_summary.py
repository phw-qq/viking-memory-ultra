#!/usr/bin/env python3
"""
sv_archive_summary.py - Viking Memory System: Generate multi-granularity summary for archive layer
Phase 3 feature: archive is no longer "forget everything", but keeps multi-granularity summary + full content.

Usage:
  python sv_archive_summary.py <file_path> [--keep]  # --keep: keep full content file
  python sv_archive_summary.py --batch <memories_dir/archive>
"""
import sys, os, re, json
from datetime import datetime

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

def generate_summary(body, granularities=3):
    """
    Generate multi-granularity summary:
    - Level 1: one-line summary
    - Level 2: paragraph summary (key points)
    - Level 3: structured summary (headings + key details)
    """
    lines = [l.strip() for l in body.split('\n') if l.strip()]
    headings = [l for l in lines if l.startswith('#')]
    
    # Level 1: one-line
    first_line = next((l for l in lines if not l.startswith('#')), '')
    one_line = (headings[0].lstrip('#').strip() if headings else first_line)[:100]
    
    # Level 2: paragraph (extract key sentences)
    key_sentences = []
    for l in lines:
        if l.startswith('#'):
            key_sentences.append(l.lstrip('#').strip())
        elif len(l) > 30 and l[0].isalnum():
            key_sentences.append(l[:80])
            if len(key_sentences) >= 5:
                break
    paragraph = '; '.join(key_sentences[:5])
    
    # Level 3: structured (headings with first sub-paragraph)
    structured_parts = []
    current_heading = None
    current_content = []
    for l in lines:
        if l.startswith('#'):
            if current_heading:
                structured_parts.append(f"{current_heading}: {'; '.join(current_content[:2])}")
            current_heading = l
            current_content = []
        elif current_heading and len(current_content) < 3:
            current_content.append(l[:60])
    if current_heading:
        structured_parts.append(f"{current_heading}: {'; '.join(current_content[:2])}")
    
    summary_text = f"1-line: {one_line}\n\nParagraph: {paragraph}\n\nStructured:\n- " + "\n- ".join(structured_parts[:5])
    return summary_text

def write_full_content(body, file_path):
    """Save full content to a separate .full file."""
    full_path = file_path + '.full'
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(body)
    return full_path

def update_meta_with_summary(file_path, summary, full_path=None):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    meta, body = parse_frontmatter(content)
    
    meta['summary'] = summary.replace('\n', ' | ')
    if full_path:
        meta['full_content_file'] = os.path.basename(full_path)
    meta['archive_summary_generated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')
    
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
        print("Usage: sv_archive_summary.py <file_path> [--keep]")
        print("       sv_archive_summary.py --batch <archive_dir>")
        sys.exit(1)
    
    keep_full = '--keep' in args
    
    if args[0] == '--batch':
        archive_dir = args[1] if len(args) > 1 else ''
        if not archive_dir or not os.path.isdir(archive_dir):
            print(f"Error: archive directory not found: {archive_dir}")
            sys.exit(1)
        count = 0
        for fname in os.listdir(archive_dir):
            if not fname.endswith('.md'):
                continue
            fp = os.path.join(archive_dir, fname)
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                meta, body = parse_frontmatter(content)
                if not meta:
                    continue
                summary = generate_summary(body)
                full_path = write_full_content(body, fp) if keep_full else None
                update_meta_with_summary(fp, summary, full_path)
                count += 1
                print(f"  ✅ {fname}: summary generated")
            except Exception as e:
                print(f"  ❌ {fname}: {e}")
        print(f"\n✅ Processed {count} files in archive/")
        return
    
    file_path = args[0]
    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    meta, body = parse_frontmatter(content)
    
    summary = generate_summary(body)
    full_path = write_full_content(body, file_path) if keep_full else None
    update_meta_with_summary(file_path, summary, full_path)
    
    print(f"✅ Summary generated for {os.path.basename(file_path)}")
    print(f"\nSummary preview:\n{summary[:200]}...")
    if full_path:
        print(f"\nFull content saved to: {full_path}")

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
sv_compress.py - Viking Memory System: Procedural Memory Compression
Compresses successful paths into triggerable skills.
Part of the production-grade AI memory system (video topic #6).

Usage:
  python sv_compress.py <memories_dir> [--task-description "task"]
  python sv_compress.py <memories_dir> --extract <task_id>
  python sv_compress.py <memories_dir> --compress <task_id> [--output skill_name]
  python sv_compress.py <memories_dir> --list
"""

import sys, os, json, re
from datetime import datetime, timezone, timedelta

COMpressed_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'compressed')
SKILLS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'skills')

def ensure_dirs():
    os.makedirs(COMpressed_DIR, exist_ok=True)
    os.makedirs(SKILLS_DIR, exist_ok=True)

def load_memories(memories_dir):
    """Load all memories from directory structure."""
    results = []
    
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
                    meta = json.loads(content)
                else:
                    meta = parse_frontmatter(content)
                    if not meta:
                        continue
                    body_start = content.find('---', 3)
                    body = content[body_start+3:].strip() if body_start > 0 else ''
                    meta['_body'] = body
                
                meta['_file_path'] = fp
                meta['_layer'] = layer
                
                results.append(meta)
            except:
                continue
    
    return results

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

def identify_successful_tasks(memories):
    """Identify memories that represent successful task completions."""
    successful = []
    
    for meta in memories:
        title = meta.get('title', '').lower()
        tags = ' '.join(meta.get('tags', [])).lower()
        body = meta.get('_body', '')[:500].lower()
        
        text = f"{title} {tags} {body}"
        
        # Indicators of successful completion
        success_indicators = ['✅', '完成', 'completed', 'success', 'done', 'finished', 
                           'implemented', 'fixed', 'resolved', 'working', 'tested']
        
        # Indicators of failure or incomplete
        failure_indicators = ['❌', 'failed', 'error', 'bug', 'issue', 'problem', 
                           'incomplete', 'pending', 'todo']
        
        success_count = sum(1 for ind in success_indicators if ind in text)
        failure_count = sum(1 for ind in failure_indicators if ind in text)
        
        if success_count > failure_count and success_count > 0:
            meta['_success_score'] = success_count
            successful.append(meta)
    
    return successful

def extract_procedure(task_memory):
    """Extract the procedure/steps from a task memory."""
    body = task_memory.get('_body', '')
    
    # Try to extract steps from body
    steps = []
    
    # Pattern 1: Numbered steps (1. 2. 3. or 1) 2) 3))
    numbered_pattern = r'^\s*(\d+)[.)]\s*(.+)$'
    for line in body.split('\n'):
        match = re.match(numbered_pattern, line)
        if match:
            step_num = int(match.group(1))
            step_desc = match.group(2).strip()
            steps.append({'step': step_num, 'description': step_desc})
    
    # Pattern 2: Bullet points (- or *)
    if not steps:
        bullet_pattern = r'^\s*[-*]\s*(.+)$'
        for i, line in enumerate(body.split('\n')):
            match = re.match(bullet_pattern, line)
            if match:
                steps.append({'step': i+1, 'description': match.group(1).strip()})
    
    # Pattern 3: Just split by lines and use non-empty lines
    if not steps:
        lines = [line.strip() for line in body.split('\n') if line.strip()]
        steps = [{'step': i+1, 'description': line} for i, line in enumerate(lines[:20])]  # Max 20 steps
    
    # Create procedure object
    procedure = {
        'task_id': task_memory.get('id', 'unknown'),
        'task_title': task_memory.get('title', ''),
        'extracted_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'steps': steps,
        'tags': task_memory.get('tags', []),
        'importance': task_memory.get('importance', 'medium')
    }
    
    return procedure

def compress_to_skill(procedure, skill_name=None):
    """Compress a procedure into a triggerable skill."""
    if not skill_name:
        # Generate skill name from task title
        title = procedure['task_title']
        # Clean title to make valid skill name
        skill_name = re.sub(r'[^a-z0-9]+', '-', title.lower())[:50].strip('-')
    
    # Create skill directory
    skill_dir = os.path.join(SKILLS_DIR, skill_name)
    os.makedirs(skill_dir, exist_ok=True)
    
    # Create SKILL.md
    skill_content = f"""# {procedure['task_title']}

## Description
Automatically generated skill from successful task completion.
Source: {procedure['task_id']}
Compressed at: {procedure['extracted_at']}

## When to Use
{', '.join(['When ' + tag for tag in procedure['tags']]) if procedure['tags'] else 'When this task needs to be performed again.'}

## Procedure

"""
    
    for step in procedure['steps']:
        skill_content += f"**Step {step['step']}:** {step['description']}\n\n"
    
    skill_content += f"""
## Notes
- Importance: {procedure['importance']}
- Auto-generated by sv_compress.py
- Test thoroughly before using in production

## Source Memory
- ID: {procedure['task_id']}
- Title: {procedure['task_title']}
"""
    
    # Write SKILL.md
    skill_path = os.path.join(skill_dir, 'SKILL.md')
    with open(skill_path, 'w', encoding='utf-8') as f:
        f.write(skill_content)
    
    # Create _meta.json
    meta = {
        'name': skill_name,
        'displayName': procedure['task_title'][:50],
        'description': f"Auto-generated skill: {procedure['task_title'][:100]}",
        'version': '1.0.0',
        'auto_generated': True,
        'source_task_id': procedure['task_id'],
        'compressed_at': procedure['extracted_at']
    }
    
    meta_path = os.path.join(skill_dir, '_meta.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    
    # Save compression record
    ensure_dirs()
    compression_record = {
        'task_id': procedure['task_id'],
        'skill_name': skill_name,
        'skill_path': skill_dir,
        'compressed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'procedure': procedure
    }
    
    record_file = os.path.join(COMpressed_DIR, f"compress_{procedure['task_id']}.json")
    with open(record_file, 'w', encoding='utf-8') as f:
        json.dump(compression_record, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Compressed to skill: {skill_name}")
    print(f"   Skill path: {skill_dir}")
    print(f"   Steps: {len(procedure['steps'])}")
    print(f"   Record: {record_file}")
    
    return skill_name

def list_compressed():
    """List all compressed skills."""
    ensure_dirs()
    
    records = []
    for fname in os.listdir(COMpressed_DIR):
        if fname.startswith('compress_') and fname.endswith('.json'):
            file_path = os.path.join(COMpressed_DIR, fname)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    record = json.load(f)
                records.append(record)
            except:
                continue
    
    if not records:
        print("No compressed skills found.")
    else:
        print(f"=== Compressed Skills ({len(records)}) ===")
        for record in sorted(records, key=lambda x: x.get('compressed_at', ''), reverse=True):
            print(f"  Skill: {record.get('skill_name', '?')}")
            print(f"    Source: {record.get('source_task_id', '?')}")
            print(f"    Compressed: {record.get('compressed_at', '?')[:19]}")
            print()
    
    return records

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    memories_dir = args[0]
    
    if not os.path.isdir(memories_dir):
        print(f"Error: directory not found: {memories_dir}")
        sys.exit(1)
    
    if '--task-description' in args:
        idx = args.index('--task-description')
        if idx + 1 < len(args):
            task_desc = args[idx + 1]
            
            # Load memories and find relevant ones
            memories = load_memories(memories_dir)
            relevant = [m for m in memories if task_desc.lower() in m.get('title', '').lower()]
            
            if not relevant:
                print(f"No memories found matching: {task_desc}")
                sys.exit(1)
            
            print(f"=== Found {len(relevant)} relevant memories ===")
            for i, meta in enumerate(relevant[:10]):
                print(f"  {i+1}. {meta.get('title', '?')}")
            
            # Identify successful tasks
            successful = identify_successful_tasks(relevant)
            print(f"\n=== Successful Tasks ({len(successful)}) ===")
            for meta in successful[:10]:
                print(f"  - {meta.get('title', '?')} (score: {meta.get('_success_score', 0)})")
    
    elif '--extract' in args:
        idx = args.index('--extract')
        if idx + 1 < len(args):
            task_id = args[idx + 1]
            
            # Load memories and find the task
            memories = load_memories(memories_dir)
            target = [m for m in memories if m.get('id') == task_id]
            
            if not target:
                print(f"Task not found: {task_id}")
                sys.exit(1)
            
            procedure = extract_procedure(target[0])
            
            print(f"=== Extracted Procedure ===")
            print(f"Task: {procedure['task_title']}")
            print(f"Steps: {len(procedure['steps'])}")
            for step in procedure['steps'][:10]:
                print(f"  {step['step']}. {step['description'][:60]}...")
            
            # Save procedure
            ensure_dirs()
            procedure_file = os.path.join(COMpressed_DIR, f"procedure_{task_id}.json")
            with open(procedure_file, 'w', encoding='utf-8') as f:
                json.dump(procedure, f, ensure_ascii=False, indent=2)
            
            print(f"\nProcedure saved: {procedure_file}")
        else:
            print("Usage: --extract <task_id>")
    
    elif '--compress' in args:
        idx = args.index('--compress')
        if idx + 1 < len(args):
            task_id = args[idx + 1]
            skill_name = None
            
            if '--output' in args:
                oidx = args.index('--output')
                if oidx + 1 < len(args):
                    skill_name = args[oidx + 1]
            
            # Load memories and find the task
            memories = load_memories(memories_dir)
            target = [m for m in memories if m.get('id') == task_id]
            
            if not target:
                print(f"Task not found: {task_id}")
                sys.exit(1)
            
            procedure = extract_procedure(target[0])
            compress_to_skill(procedure, skill_name)
        else:
            print("Usage: --compress <task_id> [--output skill_name]")
    
    elif '--list' in args:
        list_compressed()
    
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()

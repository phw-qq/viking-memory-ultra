#!/usr/bin/env python3
"""
sv_policy.py - Viking Memory System: Policy (策略) Control Layer
Defines memory management policies and decision engine.
Part of the Agentic Memory Triplet (Ledger + View + Policy).

Usage:
  python sv_policy.py <memories_dir> [--policy time|importance|context|adaptive]
  python sv_policy.py <memories_dir> --decide <operation> <file_path> [--context "task"]
  python sv_policy.py <memories_dir> --configure <policy_type> <config_json>
  python sv_policy.py <memories_dir> --list-policies
"""

import sys, os, json, math, re
from datetime import datetime, timezone, timedelta

POLICIES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'facts', 'policies')

def ensure_policies_dir():
    os.makedirs(POLICIES_DIR, exist_ok=True)

def load_memories(memories_dir):
    """Load all memories from directory structure."""
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
                else:
                    # Markdown file with frontmatter
                    meta = parse_frontmatter(content)
                    if not meta:
                        continue
                
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

def policy_time_based(memory, current_time=None):
    """Time-based retention policy.
    
    Rules:
    - Hot (0-7 days): Always keep
    - Warm (8-29 days): Keep if accessed in last 7 days
    - Cold (30-89 days): Keep if important or accessed in last 30 days
    - Archive (90+ days): Archive if not important
    """
    if not current_time:
        current_time = datetime.now(timezone(timedelta(hours=8)))
    
    # Get event_time or created time
    time_str = memory.get('event_time', memory.get('created', ''))[:19].replace('T', ' ')
    if not time_str:
        return {'action': 'keep', 'reason': 'No timestamp'}
    
    try:
        event_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone(timedelta(hours=8)))
    except:
        return {'action': 'keep', 'reason': 'Invalid timestamp'}
    
    days_old = (current_time - event_time).days
    importance = memory.get('importance', 'medium')
    last_access_str = memory.get('last_access', '')[:19].replace('T', ' ')
    
    try:
        last_access = datetime.strptime(last_access_str, '%Y-%m-%d %H:%M:%S')
        if last_access.tzinfo is None:
            last_access = last_access.replace(tzinfo=timezone(timedelta(hours=8)))
        days_since_access = (current_time - last_access).days
    except:
        days_since_access = days_old
    
    # Policy decision
    if days_old <= 7:
        return {'action': 'keep', 'layer': 'hot', 'reason': f'Recent (≤7 days)'}
    elif days_old <= 29:
        if days_since_access <= 7:
            return {'action': 'keep', 'layer': 'warm', 'reason': 'Accessed recently'}
        else:
            return {'action': 'archive', 'reason': 'Not accessed in 7 days'}
    elif days_old <= 89:
        if importance in ['high', 'important']:
            return {'action': 'keep', 'layer': 'cold', 'reason': f'Important ({importance})'}
        elif days_since_access <= 30:
            return {'action': 'keep', 'layer': 'cold', 'reason': 'Accessed in last 30 days'}
        else:
            return {'action': 'archive', 'reason': 'Not accessed in 30 days'}
    else:  # 90+ days
        if importance == 'important':
            return {'action': 'keep', 'layer': 'archive', 'reason': 'Marked as important'}
        else:
            return {'action': 'delete', 'reason': 'Too old (90+ days)'}

def policy_importance_based(memory):
    """Importance-based policy.
    
    Rules:
    - Important: Never delete, archive after 1 year
    - High: Keep for 180 days, then archive
    - Medium: Keep for 90 days, then archive
    - Low: Keep for 30 days, then delete
    """
    importance = memory.get('importance', 'medium')
    retention_days = {'important': 365, 'high': 180, 'medium': 90, 'low': 30}.get(importance, 90)
    
    # Get event_time or created time
    time_str = memory.get('event_time', memory.get('created', ''))[:19].replace('T', ' ')
    if not time_str:
        return {'action': 'keep', 'reason': 'No timestamp'}
    
    try:
        event_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        if event_time.tzinfo is None:
            event_time = event_time.replace(tzinfo=timezone(timedelta(hours=8)))
    except:
        return {'action': 'keep', 'reason': 'Invalid timestamp'}
    
    now = datetime.now(timezone(timedelta(hours=8)))
    days_old = (now - event_time).days
    
    if days_old > retention_days:
        if importance == 'important':
            return {'action': 'archive', 'reason': f'Important: Archive after {retention_days} days'}
        else:
            return {'action': 'delete', 'reason': f'{importance}: Expired after {retention_days} days'}
    else:
        layer = 'hot' if days_old <= 7 else ('warm' if days_old <= 29 else ('cold' if days_old <= 89 else 'archive'))
        return {'action': 'keep', 'layer': layer, 'reason': f'{importance}: {days_old}/{retention_days} days'}

def policy_context_based(memory, context):
    """Context-based policy.
    
    Rules:
    - If memory is relevant to current context, keep it hot
    - If not relevant, apply time-based policy
    """
    if not context:
        return policy_time_based(memory)
    
    # Calculate relevance
    title = memory.get('title', '').lower()
    tags = ' '.join(memory.get('tags', [])).lower()
    body = memory.get('_body', '')[:300].lower()
    
    text = f"{title} {tags} {body}"
    context_words = set(w.lower() for w in context.split() if len(w) > 2)
    text_words = set(text.split())
    
    if not context_words:
        return policy_time_based(memory)
    
    overlap = context_words & text_words
    relevance = len(overlap) / len(context_words)
    
    if relevance >= 0.7:
        return {'action': 'promote', 'layer': 'hot', 'reason': f'Highly relevant to context ({relevance:.2f})'}
    elif relevance >= 0.3:
        return {'action': 'keep', 'layer': 'warm', 'reason': f'Somewhat relevant to context ({relevance:.2f})'}
    else:
        return policy_time_based(memory)

def policy_adaptive(memory, context=None):
    """Adaptive policy that combines multiple factors.
    
    Considers:
    - Importance
    - Age (time since event)
    - Access frequency
    - Context relevance
    """
    importance = memory.get('importance', 'medium')
    access_count = memory.get('access_count', 0)
    
    # Get event_time
    time_str = memory.get('event_time', memory.get('created', ''))[:19].replace('T', ' ')
    if time_str:
        try:
            event_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=timezone(timedelta(hours=8)))
            now = datetime.now(timezone(timedelta(hours=8)))
            days_old = (now - event_time).days
        except:
            days_old = 0
    else:
        days_old = 0
    
    # Context relevance
    relevance = 0.5  # neutral
    if context:
        title = memory.get('title', '').lower()
        tags = ' '.join(memory.get('tags', [])).lower()
        body = memory.get('_body', '')[:300].lower()
        
        text = f"{title} {tags} {body}"
        context_words = set(w.lower() for w in context.split() if len(w) > 2)
        text_words = set(text.split())
        
        if context_words:
            overlap = context_words & text_words
            relevance = len(overlap) / len(context_words)
    
    # Decision logic
    # Important memories: keep longer
    if importance == 'important':
        if days_old <= 365:
            return {'action': 'keep', 'layer': 'hot' if days_old <= 7 else ('warm' if days_old <= 29 else 'cold'), 
                    'reason': 'Important: Extended retention'}
        else:
            return {'action': 'archive', 'reason': 'Important: Archive after 1 year'}
    
    # High importance: keep for 180 days
    elif importance == 'high':
        if days_old <= 180:
            layer = 'hot' if days_old <= 7 else ('warm' if days_old <= 29 else 'cold')
            return {'action': 'keep', 'layer': layer, 'reason': 'High importance: 180 days retention'}
        else:
            return {'action': 'archive', 'reason': 'High importance: Archive after 180 days'}
    
    # Medium importance: keep for 90 days, promote if relevant
    elif importance == 'medium':
        if relevance >= 0.7:
            return {'action': 'promote', 'layer': 'hot', 'reason': f'Relevant to context ({relevance:.2f})'}
        elif days_old <= 90:
            layer = 'hot' if days_old <= 7 else ('warm' if days_old <= 29 else 'cold')
            return {'action': 'keep', 'layer': layer, 'reason': 'Medium importance: 90 days retention'}
        else:
            return {'action': 'archive', 'reason': 'Medium importance: Archive after 90 days'}
    
    # Low importance: keep for 30 days, delete after
    else:  # low
        if days_old <= 30:
            return {'action': 'keep', 'layer': 'hot' if days_old <= 7 else 'warm', 
                    'reason': 'Low importance: 30 days retention'}
        else:
            return {'action': 'delete', 'reason': 'Low importance: Delete after 30 days'}

def decide(memories_dir, operation, file_path, context=None, policy_type='adaptive'):
    """Make a policy decision for a memory operation."""
    # Load the specific memory
    target_memory = None
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if file_path.endswith('.json'):
                target_memory = json.loads(content)
            else:
                target_memory = parse_frontmatter(content)
            
            target_memory['_file_path'] = file_path
        except:
            pass
    
    if not target_memory:
        return {'decision': 'unknown', 'reason': 'Memory not found'}
    
    # Apply policy
    if policy_type == 'time':
        return policy_time_based(target_memory)
    elif policy_type == 'importance':
        return policy_importance_based(target_memory)
    elif policy_type == 'context':
        return policy_context_based(target_memory, context)
    elif policy_type == 'adaptive':
        return policy_adaptive(target_memory, context)
    else:
        return {'decision': 'unknown', 'reason': f'Unknown policy: {policy_type}'}

def apply_policy(memories_dir, policy_type='adaptive', context=None, dry_run=True):
    """Apply policy to all memories and show actions."""
    memories = load_memories(memories_dir)
    
    actions = {
        'keep': [],
        'promote': [],
        'archive': [],
        'delete': [],
        'unknown': []
    }
    
    for memory in memories:
        if policy_type == 'time':
            result = policy_time_based(memory)
        elif policy_type == 'importance':
            result = policy_importance_based(memory)
        elif policy_type == 'context':
            result = policy_context_based(memory, context)
        else:  # adaptive
            result = policy_adaptive(memory, context)
        
        action = result['action']
        actions[action].append((memory, result))
    
    # Display results
    print(f"=== Policy: {policy_type} ({len(memories)} memories) ===")
    print(f"Context: {context[:50] if context else '(none)'}")
    print(f"Dry Run: {dry_run}\n")
    
    for action in ['keep', 'promote', 'archive', 'delete', 'unknown']:
        items = actions[action]
        if items:
            print(f"--- {action.upper()} ({len(items)}) ---")
            for memory, result in items[:10]:  # Show first 10
                title = memory.get('title', os.path.basename(memory['_file_path']))
                reason = result['reason']
                layer = result.get('layer', '?')
                
                print(f"  {title[:40]}")
                print(f"    Reason: {reason}")
                if layer != '?':
                    print(f"    Target Layer: {layer}")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")
            print()
    
    return actions

def configure_policy(policy_type, config_json):
    """Configure a policy with custom parameters."""
    ensure_policies_dir()
    
    try:
        config = json.loads(config_json) if isinstance(config_json, str) else config_json
    except:
        print("Error: Invalid JSON config")
        return False
    
    # Save config
    config_file = os.path.join(POLICIES_DIR, f"policy_{policy_type}.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Configured policy: {policy_type}")
    print(f"   Config file: {config_file}")
    return True

def list_policies():
    """List all configured policies."""
    ensure_policies_dir()
    
    policies = []
    for fname in os.listdir(POLICIES_DIR):
        if fname.startswith('policy_') and fname.endswith('.json'):
            policy_type = fname[7:-5]  # Remove 'policy_' prefix and '.json' suffix
            policies.append(policy_type)
    
    if not policies:
        print("No policies configured yet.")
    else:
        print(f"=== Configured Policies ({len(policies)}) ===")
        for policy in sorted(policies):
            print(f"  - {policy}")
    
    return policies

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    memories_dir = args[0]
    
    if not os.path.isdir(memories_dir):
        print(f"Error: directory not found: {memories_dir}")
        sys.exit(1)
    
    # Determine policy type
    policy_type = 'adaptive'  # default
    if '--policy' in args:
        idx = args.index('--policy')
        if idx + 1 < len(args):
            policy_type = args[idx + 1]
    
    # Determine context
    context = None
    if '--context' in args:
        idx = args.index('--context')
        if idx + 1 < len(args):
            context = args[idx + 1]
    
    if '--decide' in args:
        idx = args.index('--decide')
        if idx + 2 < len(args):
            operation = args[idx + 1]
            file_path = args[idx + 2]
            
            result = decide(memories_dir, operation, file_path, context, policy_type)
            print(f"=== Policy Decision ===")
            print(f"Operation: {operation}")
            print(f"File: {os.path.basename(file_path)}")
            print(f"Decision: {result['action']}")
            print(f"Reason: {result['reason']}")
            if 'layer' in result:
                print(f"Target Layer: {result['layer']}")
        else:
            print("Usage: --decide <operation> <file_path>")
    
    elif '--configure' in args:
        idx = args.index('--configure')
        if idx + 2 < len(args):
            policy_type = args[idx + 1]
            config_json = args[idx + 2]
            configure_policy(policy_type, config_json)
        else:
            print("Usage: --configure <policy_type> <config_json>")
    
    elif '--list-policies' in args:
        list_policies()
    
    else:
        # Default: apply policy
        dry_run = '--dry-run' in args
        apply_policy(memories_dir, policy_type, context, dry_run)

if __name__ == '__main__':
    main()

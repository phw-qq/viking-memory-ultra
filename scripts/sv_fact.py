#!/usr/bin/env python3
"""
sv_fact.py - Viking Memory System: JSON Structured Fact Layer
Manages precise JSON facts storage and retrieval (replacing fuzzy vector search)

Usage:
  python sv_fact.py add <fact_json_file> [--event_time "2026-05-15T10:30:00+08:00"]
  python sv_fact.py query <query_json> [--limit N]
  python sv_fact.py update <fact_id> <new_data_json>
  python sv_fact.py delete <fact_id>
  python sv_fact.py list [--type fact_type] [--limit N]
"""

import sys, os, json, re
from datetime import datetime, timezone, timedelta

FACTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'facts')

def ensure_facts_dir():
    os.makedirs(FACTS_DIR, exist_ok=True)

def gen_fact_id():
    return "fact_" + datetime.now().strftime("%Y%m%d_%H%M%S")

def parse_datetime(s):
    """Parse datetime string with timezone."""
    try:
        # Try ISO format with timezone
        if '+' in s or s.endswith('Z'):
            return datetime.fromisoformat(s.replace('Z', '+00:00'))
        # Try without timezone, assume local
        return datetime.fromisoformat(s)
    except:
        return datetime.now(timezone(timedelta(hours=8)))

def add_fact(fact_data, event_time_str=None):
    """Add a new fact with dual timestamps."""
    ensure_facts_dir()
    
    now = datetime.now(timezone(timedelta(hours=8)))
    insert_time = now.isoformat()
    
    # Parse event_time (when the fact occurred)
    if event_time_str:
        event_time = parse_datetime(event_time_str)
    else:
        event_time = now
    
    # Generate fact ID if not provided
    if 'id' not in fact_data:
        fact_data['id'] = gen_fact_id()
    
    # Add dual timestamps
    fact_data['event_time'] = event_time.isoformat()
    fact_data['insert_time'] = insert_time
    fact_data['last_access'] = insert_time
    fact_data['access_count'] = 0
    
    # Determine file path based on fact type
    fact_type = fact_data.get('type', 'general')
    fact_id = fact_data['id']
    file_path = os.path.join(FACTS_DIR, f"{fact_type}_{fact_id}.json")
    
    # Save fact
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(fact_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Added fact: {file_path}")
    print(f"   ID: {fact_id}")
    print(f"   Event Time: {event_time.isoformat()}")
    print(f"   Insert Time: {insert_time}")
    return fact_id

def query_facts(query_json, limit=10):
    """Query facts with precise JSON matching (not fuzzy vector search)."""
    ensure_facts_dir()
    
    try:
        query = json.loads(query_json) if isinstance(query_json, str) else query_json
    except:
        print("Error: Invalid JSON query")
        return []
    
    results = []
    for fname in os.listdir(FACTS_DIR):
        if not fname.endswith('.json'):
            continue
        
        file_path = os.path.join(FACTS_DIR, fname)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                fact = json.load(f)
            
            # Precise matching (not fuzzy)
            match = True
            for key, value in query.items():
                if key not in fact or fact[key] != value:
                    match = False
                    break
            
            if match:
                # Update access metadata
                fact['last_access'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
                fact['access_count'] = fact.get('access_count', 0) + 1
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(fact, f, ensure_ascii=False, indent=2)
                
                results.append(fact)
        except:
            continue
    
    # Sort by event_time descending
    results.sort(key=lambda x: x.get('event_time', ''), reverse=True)
    
    print(f"✅ Found {len(results)} matching facts (limit={limit}):")
    for i, fact in enumerate(results[:limit]):
        print(f"  {i+1}. [{fact.get('type', '?')}] {fact.get('id', '?')}")
        print(f"     Event: {fact.get('event_time', '?')[:19]}")
        print(f"     {json.dumps(fact, ensure_ascii=False)[:100]}...")
    
    return results[:limit]

def update_fact(fact_id, new_data_json):
    """Update an existing fact."""
    ensure_facts_dir()
    
    try:
        new_data = json.loads(new_data_json) if isinstance(new_data_json, str) else new_data_json
    except:
        print("Error: Invalid JSON data")
        return False
    
    # Find fact file
    target_file = None
    for fname in os.listdir(FACTS_DIR):
        if fname.endswith('.json') and fact_id in fname:
            target_file = os.path.join(FACTS_DIR, fname)
            break
    
    if not target_file:
        print(f"Error: Fact {fact_id} not found")
        return False
    
    # Read existing fact
    with open(target_file, 'r', encoding='utf-8') as f:
        fact = json.load(f)
    
    # Update fields (preserve timestamps)
    for key, value in new_data.items():
        if key not in ['id', 'event_time', 'insert_time']:
            fact[key] = value
    
    fact['last_updated'] = datetime.now(timezone(timedelta(hours=8))).isoformat()
    
    # Save updated fact
    with open(target_file, 'w', encoding='utf-8') as f:
        json.dump(fact, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Updated fact: {fact_id}")
    return True

def delete_fact(fact_id):
    """Delete a fact."""
    ensure_facts_dir()
    
    # Find fact file
    target_file = None
    for fname in os.listdir(FACTS_DIR):
        if fname.endswith('.json') and fact_id in fname:
            target_file = os.path.join(FACTS_DIR, fname)
            break
    
    if not target_file:
        print(f"Error: Fact {fact_id} not found")
        return False
    
    os.remove(target_file)
    print(f"✅ Deleted fact: {fact_id}")
    return True

def list_facts(fact_type=None, limit=50):
    """List all facts, optionally filtered by type."""
    ensure_facts_dir()
    
    results = []
    for fname in sorted(os.listdir(FACTS_DIR)):
        if not fname.endswith('.json'):
            continue
        
        if fact_type and not fname.startswith(fact_type + '_'):
            continue
        
        file_path = os.path.join(FACTS_DIR, fname)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                fact = json.load(f)
            results.append(fact)
        except:
            continue
    
    print(f"✅ Found {len(results)} facts:")
    for i, fact in enumerate(results[:limit]):
        print(f"  {i+1}. [{fact.get('type', '?')}] {fact.get('id', '?')}")
        print(f"     {json.dumps(fact, ensure_ascii=False)[:80]}...")
    
    return results[:limit]

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    command = args[0].lower()
    
    if command == 'add' and len(args) >= 2:
        fact_data = json.loads(args[1])
        event_time = None
        if '--event_time' in args:
            idx = args.index('--event_time')
            if idx + 1 < len(args):
                event_time = args[idx + 1]
        add_fact(fact_data, event_time)
    
    elif command == 'query' and len(args) >= 2:
        query_json = args[1]
        limit = 10
        if '--limit' in args:
            idx = args.index('--limit')
            if idx + 1 < len(args):
                limit = int(args[idx + 1])
        query_facts(query_json, limit)
    
    elif command == 'update' and len(args) >= 3:
        fact_id = args[1]
        new_data = json.loads(args[2])
        update_fact(fact_id, new_data)
    
    elif command == 'delete' and len(args) >= 2:
        delete_fact(args[1])
    
    elif command == 'list':
        fact_type = None
        limit = 50
        if '--type' in args:
            idx = args.index('--type')
            if idx + 1 < len(args):
                fact_type = args[idx + 1]
        if '--limit' in args:
            idx = args.index('--limit')
            if idx + 1 < len(args):
                limit = int(args[idx + 1])
        list_facts(fact_type, limit)
    
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()

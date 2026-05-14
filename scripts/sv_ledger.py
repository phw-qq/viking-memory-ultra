#!/usr/bin/env python3
"""
sv_ledger.py - Viking Memory System: Ledger (账本) Layer
Records all memory operations for audit and rollback capabilities.
Part of the Agentic Memory Triplet (Ledger + View + Policy).

Usage:
  python sv_ledger.py log <operation> <file_path> [--meta JSON]
  python sv_ledger.py audit [--operation TYPE] [--limit N]
  python sv_ledger.py rollback <transaction_id>
  python sv_ledger.py stats
"""

import sys, os, json
from datetime import datetime, timezone, timedelta

LEDGER_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'facts', 'ledger')

def ensure_ledger_dir():
    os.makedirs(LEDGER_DIR, exist_ok=True)

def gen_transaction_id():
    return "txn_" + datetime.now().strftime("%Y%m%d_%H%M%S")

def log_operation(operation, file_path, meta=None):
    """Log a memory operation to the ledger."""
    ensure_ledger_dir()
    
    now = datetime.now(timezone(timedelta(hours=8)))
    txn_id = gen_transaction_id()
    
    # Create ledger entry
    entry = {
        "transaction_id": txn_id,
        "timestamp": now.isoformat(),
        "operation": operation,  # add, update, delete, move, promote, compress
        "file_path": file_path,
        "file_name": os.path.basename(file_path),
        "meta": meta or {}
    }
    
    # Save to ledger file (one file per day)
    ledger_file = os.path.join(LEDGER_DIR, f"ledger_{now.strftime('%Y-%m-%d')}.json")
    
    # Load existing entries or create new
    if os.path.exists(ledger_file):
        with open(ledger_file, 'r', encoding='utf-8') as f:
            entries = json.load(f)
    else:
        entries = []
    
    entries.append(entry)
    
    # Save updated entries
    with open(ledger_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Logged: {operation} → {txn_id}")
    print(f"   File: {os.path.basename(file_path)}")
    print(f"   Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return txn_id

def audit_operations(operation_type=None, limit=50):
    """Audit memory operations, optionally filtered by type."""
    ensure_ledger_dir()
    
    all_entries = []
    
    # Load all ledger files
    for fname in sorted(os.listdir(LEDGER_DIR)):
        if not fname.startswith('ledger_') or not fname.endswith('.json'):
            continue
        
        file_path = os.path.join(LEDGER_DIR, fname)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            all_entries.extend(entries)
        except:
            continue
    
    # Filter by operation type if specified
    if operation_type:
        all_entries = [e for e in all_entries if e.get('operation') == operation_type]
    
    # Sort by timestamp descending
    all_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Display results
    print(f"✅ Found {len(all_entries)} operations (limit={limit}):")
    for i, entry in enumerate(all_entries[:limit]):
        op = entry.get('operation', '?')
        txn_id = entry.get('transaction_id', '?')
        file_name = entry.get('file_name', '?')
        timestamp = entry.get('timestamp', '?')[:19]
        
        print(f"  {i+1}. [{op.upper()}] {txn_id}")
        print(f"     File: {file_name}")
        print(f"     Time: {timestamp}")
        
        # Show meta if available
        meta = entry.get('meta', {})
        if meta:
            print(f"     Meta: {json.dumps(meta, ensure_ascii=False)[:60]}...")
    
    return all_entries[:limit]

def rollback(transaction_id):
    """Rollback a specific transaction (where possible)."""
    ensure_ledger_dir()
    
    # Find the transaction
    target_entry = None
    ledger_file = None
    
    for fname in os.listdir(LEDGER_DIR):
        if not fname.startswith('ledger_') or not fname.endswith('.json'):
            continue
        
        file_path = os.path.join(LEDGER_DIR, fname)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            for entry in entries:
                if entry.get('transaction_id') == transaction_id:
                    target_entry = entry
                    ledger_file = file_path
                    break
            
            if target_entry:
                break
        except:
            continue
    
    if not target_entry:
        print(f"Error: Transaction {transaction_id} not found")
        return False
    
    # Perform rollback based on operation type
    operation = target_entry.get('operation')
    file_path = target_entry.get('file_path')
    
    print(f"🔄 Rolling back: {operation} (TXN: {transaction_id})")
    
    if operation == 'delete':
        # Cannot rollback delete (file no longer exists)
        print(f"⚠️  Cannot rollback 'delete' operation (file no longer exists)")
        print(f"   File: {file_path}")
        return False
    
    elif operation == 'add':
        # Rollback add = delete the file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"✅ Rolled back 'add': deleted {file_path}")
            
            # Log the rollback
            log_operation('rollback', file_path, {
                'rolled_back_txn': transaction_id,
                'original_operation': operation
            })
            return True
        else:
            print(f"⚠️  File already deleted: {file_path}")
            return False
    
    elif operation in ['update', 'move', 'promote']:
        # For update/move/promote, we need to restore previous state
        # This requires storing before/after snapshots in meta
        print(f"⚠️  Rollback for '{operation}' requires before/after snapshots")
        print(f"   This feature is not yet implemented")
        return False
    
    else:
        print(f"⚠️  Unknown operation: {operation}")
        return False

def show_stats():
    """Show ledger statistics."""
    ensure_ledger_dir()
    
    stats = {
        'total_operations': 0,
        'operations_by_type': {},
        'files_affected': set(),
        'first_entry': None,
        'last_entry': None
    }
    
    # Process all ledger files
    for fname in sorted(os.listdir(LEDGER_DIR)):
        if not fname.startswith('ledger_') or not fname.endswith('.json'):
            continue
        
        file_path = os.path.join(LEDGER_DIR, fname)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                entries = json.load(f)
            
            for entry in entries:
                stats['total_operations'] += 1
                
                # Count by operation type
                op = entry.get('operation', 'unknown')
                stats['operations_by_type'][op] = stats['operations_by_type'].get(op, 0) + 1
                
                # Track affected files
                stats['files_affected'].add(entry.get('file_path', ''))
                
                # Track first/last entry
                timestamp = entry.get('timestamp', '')
                if not stats['first_entry'] or timestamp < stats['first_entry']:
                    stats['first_entry'] = timestamp
                if not stats['last_entry'] or timestamp > stats['last_entry']:
                    stats['last_entry'] = timestamp
        except:
            continue
    
    # Display stats
    print(f"=== Ledger Statistics ===")
    print(f"Total Operations: {stats['total_operations']}")
    print(f"Unique Files Affected: {len(stats['files_affected'])}")
    print(f"First Entry: {stats['first_entry'][:19] if stats['first_entry'] else 'N/A'}")
    print(f"Last Entry: {stats['last_entry'][:19] if stats['last_entry'] else 'N/A'}")
    
    print(f"\nOperations by Type:")
    for op, count in sorted(stats['operations_by_type'].items()):
        print(f"  {op}: {count}")
    
    return stats

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    command = args[0].lower()
    
    if command == 'log' and len(args) >= 3:
        operation = args[1]
        file_path = args[2]
        meta = None
        
        if '--meta' in args:
            idx = args.index('--meta')
            if idx + 1 < len(args):
                meta = json.loads(args[idx + 1])
        
        log_operation(operation, file_path, meta)
    
    elif command == 'audit':
        operation_type = None
        limit = 50
        
        if '--operation' in args:
            idx = args.index('--operation')
            if idx + 1 < len(args):
                operation_type = args[idx + 1]
        
        if '--limit' in args:
            idx = args.index('--limit')
            if idx + 1 < len(args):
                limit = int(args[idx + 1])
        
        audit_operations(operation_type, limit)
    
    elif command == 'rollback' and len(args) >= 2:
        transaction_id = args[1]
        rollback(transaction_id)
    
    elif command == 'stats':
        show_stats()
    
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()

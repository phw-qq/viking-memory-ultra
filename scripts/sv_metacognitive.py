#!/usr/bin/env python3
"""
sv_metacognitive.py - Viking Memory System: Metacognitive Trigger
Implements System 2 deep thinking trigger for complex problems.
Part of the production-grade AI memory system.

Usage:
  python sv_metacognitive.py analyze <task_description>
  python sv_metacognitive.py trigger <task_description> [--threshold 0.7]
  python sv_metacognitive.py status
  python sv_metacognitive.py config <config_json>
"""

import sys, os, json, re
from datetime import datetime, timezone, timedelta

METACOGNITIVE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'memory', 'metacognitive')

# Complexity indicators (keywords that suggest complex tasks)
COMPLEXITY_INDICATORS = [
    'analyze', 'analysis', 'complex', 'difficult', 'challenging', 'deep',
    'reasoning', 'think', 'consider', 'evaluate', 'compare', 'contrast',
    'integrate', 'synthesize', 'design', 'architect', 'optimize', 'refactor',
    'debug', 'troubleshoot', 'investigate', 'research', 'study', 'explore',
    'multiple', 'steps', 'stages', 'phases', 'components', 'modules',
    'system', 'architecture', 'framework', 'algorithm', 'data structure',
    'performance', 'scalability', 'security', 'reliability', 'maintainability',
    # Chinese keywords
    '分析', '复杂', '困难', '挑战', '深度', '推理', '思考', '考虑',
    '评估', '比较', '对比', '整合', '综合', '设计', '架构', '优化',
    '重构', '调试', '排查', '调查', '研究', '学习', '探索', '多层',
    '系统', '框架', '算法', '性能', '可扩展性', '安全', '可靠性'
]

# Simple task indicators (keywords that suggest simple tasks)
SIMPLE_INDICATORS = [
    'create', 'add', 'update', 'delete', 'remove', 'change', 'modify',
    'list', 'show', 'display', 'print', 'output', 'get', 'fetch', 'retrieve',
    'simple', 'quick', 'easy', 'straightforward', 'basic', 'minor', 'small',
    # Chinese keywords
    '创建', '添加', '更新', '删除', '移除', '修改', '改变',
    '列出', '显示', '展示', '打印', '输出', '获取', '取回',
    '简单', '快速', '容易', '直接', '基础', '小'
]

def ensure_metacognitive_dir():
    os.makedirs(METACOGNITIVE_DIR, exist_ok=True)

def calculate_complexity(task_description):
    """Calculate task complexity score (0.0 - 1.0)."""
    if not task_description:
        return 0.5  # neutral
    
    text = task_description.lower()
    words = set(text.split())
    
    # Count complexity indicators
    complexity_count = sum(1 for indicator in COMPLEXITY_INDICATORS if indicator in text)
    
    # Count simple indicators
    simple_count = sum(1 for indicator in SIMPLE_INDICATORS if indicator in text)
    
    # Calculate length factor (longer descriptions tend to be more complex)
    length_factor = min(len(text.split()) / 50, 1.0)  # Normalize to 0-1
    
    # Calculate complexity score
    if complexity_count == 0 and simple_count == 0:
        # Neutral
        score = 0.5 + (length_factor * 0.2)
    elif complexity_count > simple_count:
        # More complex indicators
        score = 0.7 + min(complexity_count / 10, 0.3) + (length_factor * 0.2)
    else:
        # More simple indicators
        score = 0.3 - min(simple_count / 10, 0.3) + (length_factor * 0.1)
    
    # Ensure score is between 0 and 1
    return max(0.0, min(1.0, score))

def analyze_task(task_description):
    """Analyze task and provide detailed complexity analysis."""
    ensure_metacognitive_dir()
    
    complexity_score = calculate_complexity(task_description)
    
    # Determine complexity level
    if complexity_score >= 0.7:
        level = "HIGH"
        recommendation = "Trigger System 2 deep thinking"
    elif complexity_score >= 0.4:
        level = "MEDIUM"
        recommendation = "Use standard thinking"
    else:
        level = "LOW"
        recommendation = "Use quick response"
    
    # Identify indicators
    text = task_description.lower()
    found_complex = [ind for ind in COMPLEXITY_INDICATORS if ind in text]
    found_simple = [ind for ind in SIMPLE_INDICATORS if ind in text]
    
    # Create analysis result
    result = {
        'task': task_description,
        'complexity_score': round(complexity_score, 3),
        'complexity_level': level,
        'recommendation': recommendation,
        'indicators': {
            'complexity': found_complex[:5],  # Show first 5
            'simple': found_simple[:5]
        },
        'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat()
    }
    
    # Save analysis
    analysis_file = os.path.join(METACOGNITIVE_DIR, f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # Display result
    print(f"=== Metacognitive Analysis ===")
    print(f"Task: {task_description[:60]}...")
    print(f"Complexity Score: {complexity_score:.3f}")
    print(f"Level: {level}")
    print(f"Recommendation: {recommendation}")
    
    if found_complex:
        print(f"\nComplexity Indicators: {', '.join(found_complex[:5])}")
    if found_simple:
        print(f"Simple Indicators: {', '.join(found_simple[:5])}")
    
    print(f"\nAnalysis saved: {os.path.basename(analysis_file)}")
    
    return result

def should_trigger(task_description, threshold=0.7):
    """Determine if System 2 deep thinking should be triggered."""
    complexity_score = calculate_complexity(task_description)
    
    if complexity_score >= threshold:
        return {
            'trigger': True,
            'score': complexity_score,
            'threshold': threshold,
            'reason': f'Complexity score {complexity_score:.3f} >= threshold {threshold}'
        }
    else:
        return {
            'trigger': False,
            'score': complexity_score,
            'threshold': threshold,
            'reason': f'Complexity score {complexity_score:.3f} < threshold {threshold}'
        }

def trigger_system2(task_description, threshold=0.7):
    """Trigger System 2 deep thinking for complex tasks."""
    result = should_trigger(task_description, threshold)
    
    print(f"=== System 2 Trigger Check ===")
    print(f"Task: {task_description[:60]}...")
    print(f"Complexity Score: {result['score']:.3f}")
    print(f"Threshold: {threshold}")
    
    if result['trigger']:
        print(f"\n✅ TRIGGER ACTIVATED")
        print(f"Reason: {result['reason']}")
        print(f"\nSystem 2 deep thinking mode engaged.")
        print(f"Recommendations:")
        print(f"  1. Break down the task into smaller sub-tasks")
        print(f"  2. Analyze each sub-task thoroughly")
        print(f"  3. Consider multiple approaches and trade-offs")
        print(f"  4. Verify each step before proceeding")
        print(f"  5. Document reasoning process")
        
        # Log the trigger event
        ensure_metacognitive_dir()
        trigger_log = os.path.join(METACOGNITIVE_DIR, 'trigger_log.json')
        
        log_entry = {
            'timestamp': datetime.now(timezone(timedelta(hours=8))).isoformat(),
            'task': task_description,
            'score': result['score'],
            'threshold': threshold,
            'triggered': True
        }
        
        # Load existing log or create new
        if os.path.exists(trigger_log):
            with open(trigger_log, 'r', encoding='utf-8') as f:
                log = json.load(f)
        else:
            log = []
        
        log.append(log_entry)
        
        with open(trigger_log, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        
        print(f"\nTrigger logged to: {trigger_log}")
        
        return True
    else:
        print(f"\n⭕ TRIGGER NOT ACTIVATED")
        print(f"Reason: {result['reason']}")
        print(f"\nSystem 1 (fast thinking) is sufficient for this task.")
        
        return False

def show_status():
    """Show metacognitive system status."""
    ensure_metacognitive_dir()
    
    print(f"=== Metacognitive System Status ===")
    
    # Count analysis files
    analysis_files = [f for f in os.listdir(METACOGNITIVE_DIR) if f.startswith('analysis_') and f.endswith('.json')]
    
    # Load trigger log
    trigger_log = os.path.join(METACOGNITIVE_DIR, 'trigger_log.json')
    trigger_count = 0
    if os.path.exists(trigger_log):
        with open(trigger_log, 'r', encoding='utf-8') as f:
            log = json.load(f)
        trigger_count = len([entry for entry in log if entry.get('triggered')])
    
    print(f"Total Analyses: {len(analysis_files)}")
    print(f"System 2 Triggers: {trigger_count}")
    
    # Show recent analyses
    if analysis_files:
        print(f"\nRecent Analyses:")
        for fname in sorted(analysis_files)[-5:]:
            file_path = os.path.join(METACOGNITIVE_DIR, fname)
            with open(file_path, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
            
            print(f"  {analysis['timestamp'][:19]} | Score: {analysis['complexity_score']:.3f} | {analysis['complexity_level']}")
    
    # Show config
    config_file = os.path.join(METACOGNITIVE_DIR, 'config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"\nCurrent Config:")
        print(f"  Threshold: {config.get('threshold', 0.7)}")
        print(f"  Auto-trigger: {config.get('auto_trigger', False)}")
    
    return {
        'total_analyses': len(analysis_files),
        'system2_triggers': trigger_count
    }

def configure(config_json):
    """Configure metacognitive system."""
    ensure_metacognitive_dir()
    
    try:
        config = json.loads(config_json) if isinstance(config_json, str) else config_json
    except:
        print("Error: Invalid JSON config")
        return False
    
    # Validate config
    if 'threshold' in config:
        threshold = config['threshold']
        if not (0.0 <= threshold <= 1.0):
            print(f"Error: threshold must be between 0.0 and 1.0 (got {threshold})")
            return False
    
    # Save config
    config_file = os.path.join(METACOGNITIVE_DIR, 'config.json')
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Configured metacognitive system:")
    print(f"   Config file: {config_file}")
    
    if 'threshold' in config:
        print(f"   Threshold: {config['threshold']}")
    if 'auto_trigger' in config:
        print(f"   Auto-trigger: {config['auto_trigger']}")
    
    return True

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    
    command = args[0].lower()
    
    if command == 'analyze' and len(args) >= 2:
        task_description = ' '.join(args[1:])
        analyze_task(task_description)
    
    elif command == 'trigger' and len(args) >= 2:
        task_description = ' '.join(args[1:])
        threshold = 0.7
        
        if '--threshold' in args:
            idx = args.index('--threshold')
            if idx + 1 < len(args):
                threshold = float(args[idx + 1])
        
        trigger_system2(task_description, threshold)
    
    elif command == 'status':
        show_status()
    
    elif command == 'config' and len(args) >= 2:
        config_json = ' '.join(args[1:])
        configure(config_json)
    
    else:
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()

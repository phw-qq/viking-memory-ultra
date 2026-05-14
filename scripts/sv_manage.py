#!/usr/bin/env python3
"""
Viking Memory System Ultra - Unified Management CLI
统一管理系统：提供所有功能的总入口
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# 获取脚本所在目录
SCRIPT_DIR = Path(__file__).parent
MEMORY_ROOT = Path.home() / ".workbuddy" / "memory"

class VikingManager:
    """Viking记忆系统统一管理器"""
    
    def __init__(self):
        self.scripts = {
            "write": SCRIPT_DIR / "sv_write.py",
            "read": SCRIPT_DIR / "sv_read.py",
            "weight": SCRIPT_DIR / "sv_weight.py",
            "compress": SCRIPT_DIR / "sv_compress.py",
            "promote": SCRIPT_DIR / "sv_promote.py",
            "review": SCRIPT_DIR / "sv_review.py",
            "find": SCRIPT_DIR / "sv_find.py",
            "autoload": SCRIPT_DIR / "sv_autoload.py",
            "archive": SCRIPT_DIR / "sv_archive_summary.py",
            "decompress": SCRIPT_DIR / "sv_decompress.py",
        }
    
    def check_status(self):
        """检查系统状态"""
        print("=== Viking Memory System Ultra - 系统状态 ===\n")
        
        # 检查脚本完整性
        print("【脚本状态】")
        all_ok = True
        for name, path in self.scripts.items():
            if path.exists():
                print(f"  ✅ {name:15s} - {path.name}")
            else:
                print(f"  ❌ {name:15s} - 缺失")
                all_ok = False
        
        # 检查记忆目录结构
        print("\n【记忆目录结构】")
        layers = {
            "L0-hot": MEMORY_ROOT / "viking-L0-hot",
            "L1-warm": MEMORY_ROOT / "viking-L1-warm",
            "L2-cold": MEMORY_ROOT / "viking-L2-cold",
            "L4-archive": MEMORY_ROOT / "viking-L4-archive",
        }
        
        for layer_name, layer_path in layers.items():
            if layer_path.exists():
                file_count = len(list(layer_path.glob("*.md")))
                size = sum(f.stat().st_size for f in layer_path.glob("*.md")) / 1024
                print(f"  ✅ {layer_name:15s} - {file_count:3d} 文件, {size:.1f} KB")
            else:
                print(f"  ⚠️  {layer_name:15s} - 未创建")
        
        # 检查现有记忆
        print("\n【现有记忆迁移检查】")
        mempalace_path = MEMORY_ROOT / "mempalace-rooms"
        if mempalace_path.exists():
            rooms = list(mempalace_path.glob("*/"))
            print(f"  ℹ️  发现MemPalace数据: {len(rooms)} 个房间")
            for room in rooms[:5]:  # 只显示前5个
                files = list(room.glob("**/*.md"))
                print(f"      - {room.name}: {len(files)} 文件")
        
        print("\n" + "="*50)
        if all_ok:
            print("✅ 系统状态正常")
        else:
            print("⚠️  部分组件缺失，请检查")
        
        return all_ok
    
    def init_layers(self):
        """初始化Viking分层目录结构"""
        print("=== 初始化Viking记忆分层结构 ===\n")
        
        layers = {
            "L0-hot": MEMORY_ROOT / "viking-L0-hot",
            "L1-warm": MEMORY_ROOT / "viking-L1-warm",
            "L2-cold": MEMORY_ROOT / "viking-L2-cold",
            "L4-archive": MEMORY_ROOT / "viking-L4-archive",
        }
        
        for layer_name, layer_path in layers.items():
            if not layer_path.exists():
                layer_path.mkdir(parents=True, exist_ok=True)
                print(f"  ✅ 创建 {layer_name}: {layer_path}")
            else:
                print(f"  ℹ️  已存在 {layer_name}: {layer_path}")
        
        print("\n✅ 分层结构初始化完成")
        return True
    
    def migrate_from_mempalace(self, dry_run=True):
        """从MemPalace迁移记忆到Viking分层
        
        Args:
            dry_run: 如果为True，只显示会做什么，不实际执行
        """
        print("=== 从MemPalace迁移记忆到Viking分层 ===")
        print(f"模式: {'模拟运行 (dry-run)' if dry_run else '实际执行'}\n")
        
        mempalace_path = MEMORY_ROOT / "mempalace-rooms"
        if not mempalace_path.exists():
            print("❌ 未找到MemPalace数据目录")
            return False
        
        # 权重计算脚本
        weight_script = self.scripts["weight"]
        
        # 遍历所有房间和抽屉
        for room in mempalace_path.glob("*/"):
            if not room.is_dir():
                continue
            
            print(f"\n📁 房间: {room.name}")
            
            for drawer in room.glob("*.md"):
                if not drawer.is_file():
                    continue
                
                # 读取文件内容
                with open(drawer, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析frontmatter获取创建时间
                import re
                match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
                if not match:
                    print(f"    ⚠️  跳过 {drawer.name} (无frontmatter)")
                    continue
                
                try:
                    # 简单解析日期
                    frontmatter = match.group(1)
                    date_match = re.search(r'date:\s*(\S+)', frontmatter)
                    if not date_match:
                        print(f"    ⚠️  跳过 {drawer.name} (无日期)")
                        continue
                    
                    date_str = date_match.group(1)
                    created_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    days_old = (datetime.now() - created_date).days
                    
                    # 根据天数决定目标层级
                    if days_old <= 7:
                        target_layer = "L0-hot"
                    elif days_old <= 29:
                        target_layer = "L1-warm"
                    elif days_old <= 89:
                        target_layer = "L2-cold"
                    else:
                        target_layer = "L4-archive"
                    
                    target_path = MEMORY_ROOT / f"viking-{target_layer.lower()}" / drawer.name
                    
                    print(f"    📄 {drawer.name}")
                    print(f"       创建于 {date_str} ({days_old}天前) → {target_layer}")
                    
                    if not dry_run:
                        # 实际迁移（复制，不删除原文件）
                        import shutil
                        shutil.copy2(drawer, target_path)
                        print(f"       ✅ 已复制到 {target_path}")
                    else:
                        print(f"       ℹ️  将复制到 {target_path}")
                
                except Exception as e:
                    print(f"    ❌ 处理 {drawer.name} 失败: {e}")
        
        if dry_run:
            print("\n" + "="*50)
            print("⚠️  这是模拟运行，未实际执行")
            print("如需实际执行，请使用: python sv_manage.py migrate --execute")
        
        return True
    
    def run_compress(self):
        """执行压缩/迁移"""
        print("=== 执行记忆压缩/层级迁移 ===\n")
        
        compress_script = self.scripts["compress"]
        if not compress_script.exists():
            print(f"❌ 压缩脚本不存在: {compress_script}")
            return False
        
        # 调用压缩脚本
        import subprocess
        result = subprocess.run(
            [sys.executable, str(compress_script)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_promote(self, query, threshold=0.1):
        """执行动态回流"""
        print(f"=== 执行动态回流 (查询: {query}) ===\n")
        
        promote_script = self.scripts["promote"]
        if not promote_script.exists():
            print(f"❌ 回流脚本不存在: {promote_script}")
            return False
        
        # 调用回流脚本
        import subprocess
        result = subprocess.run(
            [sys.executable, str(promote_script), "--query", query, "--threshold", str(threshold)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
    
    def run_review(self):
        """执行复习调度"""
        print("=== 执行Ebbinghaus复习调度 ===\n")
        
        review_script = self.scripts["review"]
        if not review_script.exists():
            print(f"❌ 复习脚本不存在: {review_script}")
            return False
        
        # 调用复习脚本
        import subprocess
        result = subprocess.run(
            [sys.executable, str(review_script)],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0
    
    def search(self, keyword):
        """搜索记忆"""
        print(f"=== 搜索记忆 (关键词: {keyword}) ===\n")
        
        find_script = self.scripts["find"]
        if not find_script.exists():
            print(f"❌ 搜索脚本不存在: {find_script}")
            return False
        
        # 调用搜索脚本
        import subprocess
        result = subprocess.run(
            [sys.executable, str(find_script), "--keyword", keyword],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(
        description="Viking Memory System Ultra - Unified Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python sv_manage.py status                    # 检查系统状态
  python sv_manage.py init                       # 初始化分层目录
  python sv_manage.py migrate                    # 模拟迁移（不实际执行）
  python sv_manage.py migrate --execute         # 执行迁移
  python sv_manage.py compress                  # 执行压缩/迁移
  python sv_manage.py promote "关键词"           # 动态回流
  python sv_manage.py review                    # 复习调度
  python sv_manage.py search "关键词"             # 搜索记忆
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # status命令
    subparsers.add_parser("status", help="检查系统状态")
    
    # init命令
    subparsers.add_parser("init", help="初始化Viking分层目录结构")
    
    # migrate命令
    migrate_parser = subparsers.add_parser("migrate", help="从MemPalace迁移记忆")
    migrate_parser.add_argument("--execute", action="store_true", help="实际执行迁移（默认仅模拟）")
    
    # compress命令
    subparsers.add_parser("compress", help="执行记忆压缩/层级迁移")
    
    # promote命令
    promote_parser = subparsers.add_parser("promote", help="执行动态回流")
    promote_parser.add_argument("query", help="查询关键词")
    promote_parser.add_argument("--threshold", type=float, default=0.1, help="相似度阈值 (默认: 0.1)")
    
    # review命令
    subparsers.add_parser("review", help="执行Ebbinghaus复习调度")
    
    # search命令
    search_parser = subparsers.add_parser("search", help="搜索记忆")
    search_parser.add_argument("keyword", help="搜索关键词")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    manager = VikingManager()
    
    if args.command == "status":
        manager.check_status()
    elif args.command == "init":
        manager.init_layers()
    elif args.command == "migrate":
        manager.migrate_from_mempalace(dry_run=not args.execute)
    elif args.command == "compress":
        manager.run_compress()
    elif args.command == "promote":
        manager.run_promote(args.query, args.threshold)
    elif args.command == "review":
        manager.run_review()
    elif args.command == "search":
        manager.search(args.keyword)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

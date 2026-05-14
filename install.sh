#!/bin/bash
# Viking Memory Ultra - Installation Script
# For WorkBuddy / OpenClaw / Hermes / Claw-Code

set -e

SKILL_NAME="viking-memory-ultra"
GITHUB_REPO="phw-qq/viking-memory-ultra"
BRANCH="main"

# Detect agent type and set install path
if [ -n "$WORKBUDDY_ROOT" ]; then
    INSTALL_DIR="$WORKBUDDY_ROOT/.workbuddy/skills/$SKILL_NAME"
    AGENT_TYPE="WorkBuddy"
elif [ -n "$OPENCLAW_ROOT" ]; then
    INSTALL_DIR="$OPENCLAW_ROOT/skills/$SKILL_NAME"
    AGENT_TYPE="OpenClaw"
elif [ -d "$HOME/.workbuddy" ]; then
    INSTALL_DIR="$HOME/.workbuddy/skills/$SKILL_NAME"
    AGENT_TYPE="WorkBuddy"
elif [ -d "$HOME/.openclaw" ]; then
    INSTALL_DIR="$HOME/.openclaw/skills/$SKILL_NAME"
    AGENT_TYPE="OpenClaw"
else
    echo "❌ Unknown agent type. Please install manually."
    echo "   Clone: git clone https://github.com/$GITHUB_REPO.git"
    exit 1
fi

echo "🎯 Detected Agent: $AGENT_TYPE"
echo "📦 Installing $SKILL_NAME to: $INSTALL_DIR"

# Create directory
mkdir -p "$INSTALL_DIR"

# Download and install
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"
git clone --depth 1 --branch "$BRANCH" https://github.com/$GITHUB_REPO.git
cp -r $SKILL_NAME/* "$INSTALL_DIR/"

# Cleanup
rm -rf "$TMP_DIR"

echo "✅ Installation complete!"
echo ""
echo "📖 Usage:"
echo "   1. Restart your agent"
echo "   2. The skill will auto-load on next session"
echo "   3. Check installation: ls $INSTALL_DIR"
echo ""
echo "🔗 GitHub: https://github.com/$GITHUB_REPO"
echo "📦 SkillHub: https://lightmake.site/skill/tsangho/viking-memory-ultra"

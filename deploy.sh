#!/bin/bash
# ============================================
# ペンギンマルシェ GitHub デプロイスクリプト
# ============================================
# 使い方: Terminal でこのフォルダを開いて
#   chmod +x deploy.sh
#   ./deploy.sh
# ============================================

set -e

echo ""
echo "🐧 ペンギンマルシェ GitHub デプロイ"
echo "======================================"
echo ""

# GitHubユーザー名を入力
read -p "GitHubユーザー名を入力してください: " GH_USER
if [ -z "$GH_USER" ]; then
  echo "❌ ユーザー名が空です。終了します。"
  exit 1
fi

# リポジトリ名（固定）
REPO_NAME="penguin-marche"
BRANCH="main"

echo ""
echo "📋 設定確認:"
echo "   ユーザー: $GH_USER"
echo "   リポジトリ: $REPO_NAME"
echo "   ブランチ: $BRANCH"
echo "   URL: https://github.com/$GH_USER/$REPO_NAME"
echo ""
echo "⚠️  GitHubに '$REPO_NAME' リポジトリが先に作成されている必要があります。"
echo "   まだの場合は https://github.com/new から作成してください。"
echo "   ※「Add a README file」のチェックは外してください"
echo ""
read -p "続けますか？ (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
  echo "キャンセルしました。"
  exit 0
fi

echo ""
echo "🔗 リモート設定中..."
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$GH_USER/$REPO_NAME.git"

echo "📤 GitHubへプッシュ中..."
git push -u origin $BRANCH

echo ""
echo "✅ プッシュ完了！"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📌 次のステップ：GitHub Pages を有効化"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. ブラウザで以下を開く："
echo "   https://github.com/$GH_USER/$REPO_NAME/settings/pages"
echo ""
echo "2. 「Source」→「Deploy from a branch」を選択"
echo "3. Branch: main / フォルダ: / (root) を選択"
echo "4. 「Save」をクリック"
echo ""
echo "5. 数分後にサイトが公開されます："
echo "   https://$GH_USER.github.io/$REPO_NAME/"
echo ""
echo "🐧 完了！"

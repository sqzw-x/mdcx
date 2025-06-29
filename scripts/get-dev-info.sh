#!/bin/bash

# 获取最后一个commit的信息
echo 'LAST_COMMIT<<END_LAST_COMMIT'
git log -1 --pretty=format:"**Latest Commit:** %s%n%nAuthor: %an%nDate: %ai%nSHA: %H%n"
echo 'END_LAST_COMMIT'

# 获取最后一个tag
LAST_TAG=$(git describe --tags --match '120*' --abbrev=0 2>/dev/null || echo "No tags found")
echo "last_tag=$LAST_TAG"

# 获取自最后一个tag以来的commit历史
echo 'COMMITS_SINCE_TAG<<END_COMMITS_SINCE_TAG'
echo '<details>'
if [ "$LAST_TAG" != "No tags found" ]; then
    echo "**Commits since $LAST_TAG:**"
    echo ""
    git log $LAST_TAG..HEAD --pretty=format:"- %s (%an, %ar)"
else
    echo "**All commits:**"
    echo ""
    git log --pretty=format:"- %s (%an, %ar)"
fi
echo '</details>'
echo ''
echo 'END_COMMITS_SINCE_TAG'

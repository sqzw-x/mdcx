tags=$(git tag -l '120*' --sort=-v:refname)
last=$(echo "$tags" | sed -n '1p')
commitlog=$(git log --pretty=format:"%h %s" $last..HEAD)

echo "## 新增
*

## 修复
*

<details>
<summary>Full Changelog</summary>

$commitlog

</details>" > changelog.md # use "" to keep \n in $commitlog

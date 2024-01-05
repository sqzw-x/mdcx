$last = git describe --tags --abbrev=0
(git log --pretty=format:"%h %s" "$last..") > changelog.txt

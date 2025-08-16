## 修复

* actor, director, tag 等字段数据丢失

## 优化

* all_actors 补全逻辑
* aws image url 生成

<details>
<summary>Full Changelog</summary>

1b309b7 fix: 未能正确处理 v1 crawler 返回结果 (fix #581)
a7a3e35 fix: all_actors 不全时未能使用 actors 补全; 统一二者的后处理 (fix #583 #582)
ac5419f feat: 尝试生成 aws image url (fix #584)
dc2e123 Ready for 2.0-beta-6
8844975 fix: aws image; 优化 crawl 日志输出
a0e8f43 feat!: 新的 crawler 框架; 重新实现 dmm/javdb (#574)
104e5f7 fix: 无 all_actor 字段时应从 actor 获取 (fix #565)
bedc22f Ready for 2.0-beta-5
cd52f02 合并 digital 和 video 类别
f8b779e fix: 降低 dmm ditigal 优先级 (#549)
2828565 feat: crawl cli
444eefd feat: config get_website_base_url

</details>

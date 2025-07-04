## 新增

* 演员映射表更新

## 修复

* 读取配置文件出错时不再静默崩溃
* 不再丢弃配置文件中的未知字段
* 无法正确处理网站优先级
* 其它代码错误

<details>
<summary>Full Changelog</summary>

4a27cec fix: get_checkboxes 未正确处理 QRadioButton 组件值 (fix #450)
d0a1818 chore: update mapping_actor.xml (#443)
3b9dc0f CI: add --cleanup-tag option to gh release delete commands
e1508b8 fix: missing import for IS_MAC
07418ba feat: 保留配置文件中的未知字段
761e5f8 chore: mapping_actor.xml 数据修正 (#440)
b52c195 fix: 配置读取异常处理
abe07cf CI: cherry-pick from 'dev'
6ee537a feat: 映射表更新 (#428)

</details>

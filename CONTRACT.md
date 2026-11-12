# 筛查发布联立披露审计归档
本目录是一次已经完成的门户采集/RPA导出归档；没有个人明细，也没有可补抓的外部接口。URL仅为证据标识。所有可用信息均在本目录。source.py是归档读取和候选见证核对器，不是披露推断器；不得改写它、checks.py及data/来得到结论。

## 已有入口与证据来源
python3 source.py normalize 向stdout输出单个JSON对象：release、rows、trace。
python3 source.py demo 展示真实归档摘要、来源链和单元格。
python3 checks.py normal 核对归档重放、RPA一致性及候选见证核对器的正常业务回归。
data/http.json按顺序记录200/304；缓存按(url,accept)绑定，304继承所指200实体。select标记本次分析版本，不能把两个版本相加。
data/rpa.json的use和release是本轮既定归档归属；旧版仅包含P01预览，留作来源证据，不参加推断。RPA列序和行序均无意义，按id对账。
trace把所选304请求追溯到200原始实体；报告引用原文件与行号，CSV行号包括表头。
data/capture-final.json中的rows每项为id、panel、metric、display；id唯一。CSV四列同名。
此处“现有发布”指全部历史public面板加全部draft面板组成的拟发整体，不表示draft已经对外发送。

## 联合人群与显示规则（既有统计口径）
data/model.json的groups为互不重叠且两轮成员固定的片区，各片区人数n精确公开。每人有两轮二进制状态，00/01/10/11依次表示两轮均阴性、转阳、转阴、持续阳性。
世界格式为{"counts":{"片区":{"00":整数,"01":整数,"10":整数,"11":整数}},"noise":{"扰动ID":整数}}；必须包含全部片区、全部状态与全部扰动ID，不允许负人数，每片区四格之和等于n。
metrics列出每项指标包含的联合状态；panel.groups是不同片区的并集，不能当作互不重叠的面板。model.targets列出本轮全部待保护量。
每个noise整数均在[min,max]内；所有ID同时满足sum及l1_max（绝对值和上界），包括已撤面板不再使用的扰动ID。它们是本批同一组未知数，不能按面板、指标或见证中的单元格分别取值。
一个面板的first/second共享一个扰动e；changed使用2e，persistent使用0e。先求指标真实人数t：若t<=2，显示*；若t>=3，显示十进制整数t+系数×e。不裁剪、不四舍五入。数字即使小于3也不能据显示值判作星号；星号约束的是扰动前人数。
历史public面板与保留draft面板的所有行同时约束同一个世界；撤版只去掉该draft面板全部行的显示约束，不改变人口、全局预算及历史。没有额外背景知识、概率先验、跨期人员迁移或独立性假设。
每个目标的支持集是满足全部约束的完整整数世界在该目标上的投影，需列出每个值，不能只给上下界。不同目标或不同取值可以使用不同世界。
安全表示每个目标的支持集大小至少为minimum_support；不要求一份世界同时实现所有目标的各种取值。
撤版损失为撤下draft面板cost之和。同成本按升序撤版ID序列的Python字典序选唯一结果。public不可撤。若完整材料本身无世界，先报告材料矛盾，不得借撤版掩盖；若仅历史已经不安全，撤完draft也不能宣称安全。

## 本轮分析交付接口
新增analysis.py仅作为这批材料的可重跑分析入口；不开发通用发布平台、采集服务或优化器产品。
python3 analysis.py run 从上述归档生成REPORT.md和result.json，不接受人工写入答案作为输入。
python3 analysis.py verify 从原始材料重新核对报告结果、支持集见证及全局最优性，发现错误退出非零；不能只检查JSON字段齐全或拿输出和自身副本比较。
result.json包含release、source_refs、full、decision。source_refs列出使用/排除的归档来源及原因。
full对象包含status（consistent或inconsistent）、supports和witnesses。supports映射目标ID到升序完整人数列表；witnesses映射目标ID到人数十进制字符串到完整world。矛盾时支持集及见证为空并给出contradiction说明。
decision对象包含status（safe或impossible或inconsistent）、removed、loss、supports、witnesses、proof。safe时removed升序，支持集与见证格式同full；impossible时给历史公开面板的支持集及见证、removed为空、loss为null；inconsistent时按full处理。proof引用报告中可复核的最优性或不可行论证及重算证据，不规定求解算法或证明编码。
REPORT.md给出结论、归档版本归属、精确支持集、导致推断收紧的跨表约束、最优撤版损失及同成本裁决，区分材料直接公开和联立才能推出的事实。支持集完整性、不可行性及全局最优性都须论证，不能以找到若干见证或启发式局部最优代替证明。排除项和更低成本方案的否定结论须有可用整数或有理数运算核对的证据；verify不能只采信第三方优化器的返回状态。
更新.pointwise-runtime.json：verify调用分析核对，demo调用能展示真实分析结果的入口，保留normal回归。setup可保持空列表，若使用额外依赖须如实登记且可重跑。

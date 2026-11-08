# DMA 补考研习室

面向 NM6004 **Design Methodology and Automation（设计方法学与自动化）** 的中文学习课程。以 2025-10-31 讲义/习题为主，配合历史题、手算和有限教学模型；不预测本次补考题目。

[公开网站](https://andyzr-coder.github.io/dma-learning-lab/) · [PDF 手册](https://andyzr-coder.github.io/dma-learning-lab/downloads/dma-handbook.pdf) · [离线 HTML](https://andyzr-coder.github.io/dma-learning-lab/downloads/dma-handbook.html) · [完整来源索引](https://andyzr-coder.github.io/dma-learning-lab/downloads/source-index.json)

13 章、79 道分层练习、6 个交互实验、5 场去重历史试卷索引、10 题原创 60 分模拟卷。默认 10 天、49 小时净学习，可调整开始日、每日预算和复习间隔。

## 如何学习

1. 进入「10 天学习路线」，做 Day 1 的短诊断，定位最早出错的步骤。
2. 逐章按示范 → 补全 → 独立 → 迁移学习。熟悉内容先用新题验证后跳过。
3. 实验按预测 → 参数 → 状态 → 解释 → 变式进行；每个实验注明模型、假设、手算和边界。
4. 完成阅读与独立能力分开记录。数值核对不自动授予推导分；开放题按量表自评。至少两道独立/迁移题达到80%，章节才显示有独立证据。
5. 留 F088 给 Day 8，F055 给 Day 9；前七天避免接触这两份卷的解答。若已经做过，记为复练，不能冒充盲测。
6. 换设备前在「笔记与备份」导出 JSON；新设备再导入。没有云同步。

## 内容

- 设计流程与三种视角、布尔空间/cube/cofactor/Shannon。
- 精确两级综合、启发式、函数分解/kernel、多级逻辑、ROBDD、FSM。
- 事件与delta、transport/inertial、VHDL信号/变量与建模边界。
- 故障覆盖、布尔差分、D算法/global implication、故障仿真、scan/LFSR/BIST。

资料核验截至 **2026-11-08**。本地101份真实PDF已去除资源分叉文件，包含重复副本与合订本；原文件共1710个PDF页，不能视为全部逐页精读。手写及合订文件的具体抽样页在来源审计中明示。原PDF保持本地，公开仓库只含原创讲解、来源定位和教学代码。

文件名不是考试日期：“19_retake”卷内2020-06-29；“21_retake”卷内2022-05-06且含答案；“DMA22_retake”卷内2023-06-20。历史样本均60分钟/60分，本次考试安排、及格线与允许资料以学校正式通知为准。

## 本地运行

需要 Node.js 22 或更新版本。使用 Node.js 24 验证。

```sh
npm ci
npm run build
npm test
npm run check
npm run dev
```

访问 `http://127.0.0.1:4174/`。默认服务器仅绑定本机。前端不依赖外部CDN；KaTeX在构建时生成公式，字体随站点分发。

下载的独立 `dma-handbook.html` 可直接双击离线阅读，包含可折叠答案和全部模考。整个网站也可下载 `dma-offline-website.zip`：解压后用 Node.js 执行 `node tools/serve.mjs`，不需要 npm 安装。ES模块网站不适合直接用 file:// 打开。

## 改内容与生成手册

`content/modules/*.json` 是课程唯一内容源；`src/` 仅负责界面和模型。`content/plan.json`、`exam-map.json`、`exam-guide.json`、`labs.json`、`cases.json`、`source-registry.json` 与 `external-*.json` 描述路线、练习、实验与证据。

`npm run build` 生成 `dist/`、离线 HTML、可编辑 Markdown 和数据下载。已生成PDF随仓库交付；修改课程后要重新执行PDF命令，构建网站不会自动调用TeX。

Windows 本机生成中文 PDF（已安装 Pandoc、XeLaTeX、Eisvogel，字体 Cambria/Segoe UI/Consolas/Microsoft YaHei）：

```powershell
pandoc public/downloads/dma-handbook.md -o public/downloads/dma-handbook.pdf --pdf-engine=xelatex --template="F:\office_beautify\pandoc\templates\eisvogel.latex" --toc --number-sections --toc-depth=2 --syntax-highlighting=tango
npm run build
```

其他系统替换为本机Eisvogel路径及存在的中英文字体；也可从离线HTML打印PDF。手册答案在PDF附录集中列出，网站和离线HTML默认折叠。

`python tools/package.py` 生成源码ZIP与离线网站ZIP。Python标准库即可打包。`tools/check-synthesis.py` 和 `tools/test-teaching-examples.py` 是独立算例检查，使用Python标准库。

## 验证与模型边界

`npm test` 包含28个测试组：QM独立精确oracle、全部6561种三变量On/Off/DC规范、160个四变量样本；BDD全部三变量函数与6种变量顺序；事件阈值和同刻队列；完整检测矩阵及最少4向量证明；全部16种LFSR mask×16种seed；导入数据边界等。另有68项后半课程算例检查及综合章节独立验证。

`qa/` 保存验收记录。浏览器手工核验覆盖手机布局、搜索、章节跳转、折叠答案、数值核对、自评、笔记持久化、JSON导入导出和交互实验。

这些实验不是工业综合器、完整IEEE VHDL仿真器、协议验证器或硬件预测工具。literal数不等于芯片面积；零延迟逻辑故障覆盖不等于制造缺陷覆盖；LFSR递推不证明MISR实测混叠率。

## 发布与参考

`main` 分支保存源码及手册；`gh-pages` 保存 `dist/` 静态输出，GitHub Pages从其根目录发布。原参考站 [memory-architecture-lab](https://github.com/andyzr-coder/memory-architecture-lab) 保持不变。复用其静态内容分离、章节hash导航、知识树、笔记和离线下载的结构思路，本项目课程与实验单独实现。

论文和原始课程资料版权归原作者/机构。本仓库不镜像原文，来源索引明示实际阅读范围与访问限制。

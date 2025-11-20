# 详解格式化指南

## 📖 概述

从 v3.2 开始，`\explain` 宏支持**段落分隔**和**步骤标记**，用于改善长解析的可读性。

---

## ✨ 新增功能

### 1. 段落分隔支持

可以在 `\explain` 中使用**空行**来分段，每段会自动首行缩进 2em，段间距 0.4 倍行距。

**示例**：

```latex
\explain{
由题意可知双曲线满足 $c^2 = 2a^2$。

因为焦点为 $(\pm 2, 0)$，所以 $c = 2$，进而 $a^2 = 2$，$b^2 = 2$。

双曲线方程为 $\frac{x^2}{2} - \frac{y^2}{2} = 1$。
}
```

**效果**：
- 第一段：由题意可知...（首行缩进）
- （空行间距）
- 第二段：因为焦点...（首行缩进）
- （空行间距）
- 第三段：双曲线方程...（首行缩进）

---

### 2. 步骤标记命令 `\exstep`

用于在解析中标记主要步骤，支持两种模式：

#### a) 自动编号模式

```latex
\explain{
由题意可知双曲线满足 $c^2 = 2a^2$。
\exstep 因为焦点为 $(\pm 2, 0)$，所以 $c = 2$，进而 $a^2 = 2$，$b^2 = 2$。
\exstep 双曲线方程为 $\frac{x^2}{2} - \frac{y^2}{2} = 1$。
\exstep 设直线 $l$ 的方程为 $x = ty + 2$...
}
```

**效果**：
- 【详解】 由题意可知...
- 
- **(1)** 因为焦点...
- 
- **(2)** 双曲线方程...
- 
- **(3)** 设直线...

#### b) 自定义标签模式

```latex
\explain{
法一：直接计算

由题意可知 $f(x) = x^2$...

\exstep[法二：利用导数]
对 $f(x)$ 求导得 $f'(x) = 2x$...

\exstep[小结]
综上所述，两种方法得到相同结果。
}
```

**效果**：
- 【详解】 法一：直接计算
- 
- 由题意可知...
- 
- **法二：利用导数** 对 $f(x)$ 求导...
- 
- **小结** 综上所述...

---

### 3. 混合使用

段落分隔和步骤标记可以**混合使用**：

```latex
\explain{
由余弦函数的性质得 $\cos x \leq \cos\theta$ 的解为 $[2k\pi + \theta, 2k\pi + 2\pi - \theta]$，$k \in \mathbb{Z}$。

\exstep[假设]
若任意 $[2k\pi + \theta, 2k\pi + 2\pi - \theta], k \in \mathbb{Z}$ 与 $[a - \theta, a + \theta]$ 交集为空...

此时 $a$ 无解，矛盾。

\exstep[结论]
故存在 $k \in \mathbb{Z}$，使得交集非空。
}
```

---

### 4. 嵌套列表支持

`\explain` 内部仍然支持 `enumerate` 和 `itemize` 环境：

```latex
\explain{
法一：分类讨论
\begin{enumerate}[label=(\arabic*)]
\item 由题意知 $c^2 = 2a^2$，又 $2c = 4$，所以 $c = 2$，$a^2 = 2$。
\item 因此双曲线方程为 $x^2 - y^2 = 2$。
\item 设直线 $l: x = ty + 2$，代入双曲线方程...
\end{enumerate}
}
```

---

## 📋 使用建议

### 何时使用段落分隔

- ✅ 解析超过 5 行时
- ✅ 包含多个逻辑步骤时
- ✅ 需要区分"已知→推导→结论"时

**示例场景**：
- 解析题（第 15-19 题）
- 证明题
- 多步骤计算题

### 何时使用 `\exstep`

- ✅ 解析超过 10 行时
- ✅ 包含多种解法时（法一、法二...）
- ✅ 需要清晰标记步骤时

**示例场景**：
- 第 17 题（立体几何证明 + 计算）
- 第 18 题（椭圆综合题）
- 第 19 题（导数证明题）

### 何时保持简洁

- ✅ 短解析（1-3 行）保持原样
- ✅ 单选题、填空题的简单解析

---

## 🎯 实际案例

### 案例 1：中等长度解析（使用段落分隔）

```latex
\begin{question}
已知 $f(x) = 5\cos x - \cos 5x$ 在区间 $[0, \frac{\pi}{4}]$ 的最大值为多少？
\begin{choices}
  \item $3\sqrt{2}$
  \item $3\sqrt{3}$
  \item $4$
  \item $5$
\end{choices}
\topics{导数求最值；三角函数}
\difficulty{0.65}
\answer{B}
\explain{
对 $f(x)$ 求导：$f'(x) = -5\sin x + 5\sin 5x = 10\cos 3x\sin 2x$。

因为 $x \in [0, \frac{\pi}{4}]$，故 $\sin 2x \geq 0$。当 $0 < x < \frac{\pi}{6}$ 时，$\cos 3x > 0$ 即 $f'(x) > 0$；当 $\frac{\pi}{6} < x < \frac{\pi}{4}$ 时，$\cos 3x < 0$ 即 $f'(x) < 0$。

故 $f(x)$ 在 $[0, \frac{\pi}{6})$ 上递增，在 $(\frac{\pi}{6}, \frac{\pi}{4}]$ 上递减。

因此最大值为 $f(\frac{\pi}{6}) = 5\cos\frac{\pi}{6} - \cos\frac{5\pi}{6} = 3\sqrt{3}$。
}
\end{question}
```

### 案例 2：超长解析（使用 `\exstep` 自动编号）

```latex
\begin{question}
（立体几何综合题）...
\topics{面面垂直；外接球；异面直线夹角}
\difficulty{0.65}
\answer{(1)证明见解析；(2)(i)证明见解析；(ii)$\frac{\sqrt{2}}{3}$}
\explain{
(1) 在四棱锥 $P-ABCD$ 中，$PA \perp$ 平面 $ABCD$，$AB \bot AD$。

\exstep
因为 $AB \subset$ 平面 $ABCD$，$AD \subset$ 平面 $ABCD$，所以 $AP \bot AB$，$AP \bot AD$。

\exstep
因为 $AP \subset$ 平面 $PAD$，$AD \subset$ 平面 $PAD$，$AP \cap AD = A$，所以 $AB \bot$ 平面 $PAD$。

\exstep
因为 $AB \subset$ 平面 $PAB$，所以平面 $PAB \bot$ 平面 $PAD$。

(2)(i) 建立空间直角坐标系...

\exstep
设球心为 $O(0, y_0, 0)$，由 $|OP| = |OB| = |OC| = |OD|$ 可得...

\exstep
解得 $y_0 = 1$，故点 $O$ 在平面 $ABCD$ 内。

(2)(ii) 向量法计算...

\exstep
$\vec{AC} = (\sqrt{2}, 2, 0)$，$\vec{PO} = (0, 1, -\sqrt{2})$。

\exstep
$\cos\theta = \frac{|\vec{AC} \cdot \vec{PO}|}{|\vec{AC}||\vec{PO}|} = \frac{2}{\sqrt{6} \times \sqrt{3}} = \frac{\sqrt{2}}{3}$。
}
\end{question}
```

### 案例 3：多解法（使用自定义标签）

```latex
\explain{
\exstep[法一：导数法]
对 $f(x)$ 求导得 $f'(x) = -5\sin x + 5\sin 5x$...

计算得最大值为 $3\sqrt{3}$。

\exstep[法二：五倍角公式]
利用 $\cos 5x = 16\cos^5 x - 20\cos^3 x + 5\cos x$...

同样得到最大值 $3\sqrt{3}$。

\exstep[小结]
两种方法验证了答案的正确性。
}
```

---

## 🔧 技术细节

### 格式参数

当前 `\explain` 的段落格式设置：

```latex
\parskip=0.4\baselineskip  % 段间距
\parindent=2em             % 首行缩进
```

### `\exstep` 间距

每个 `\exstep` 前自动添加 `0.25\baselineskip` 的垂直间距。

### 计数器作用域

步骤计数器 `\l__qmeta_step_int` 在每个题目开始时重置，确保编号从 (1) 开始。

---

## ⚠️ 注意事项

1. **向后兼容**：不使用 `\exstep` 的解析仍然正常工作
2. **命名冲突**：原计划使用 `\step`，但与某些包冲突，改用 `\exstep`（explanation step）
3. **花括号平衡**：`\explain` 使用 `+m` 参数，支持段落分隔，但仍需保持花括号平衡
4. **数学环境**：`\exstep` 可以在数学公式外使用，但不能在行内数学 `\(...\)` 内使用

---

## 📚 相关文档

- `qmeta.sty` - 元信息系统核心文件
- `features.md` - 功能特性总览
- `WORKFLOW_TESTING_PROMPT.md` - 工作流程文档

---

**版本**：v3.2  
**更新日期**：2025-11-20

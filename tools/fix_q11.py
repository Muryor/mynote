#!/usr/bin/env python3
"""Fix Q11 in hunan_yali_2026_mock3/converted_exam.tex"""

import re

file_path = 'content/exams/auto/hunan_yali_2026_mock3/converted_exam.tex'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# New Q11 content with proper structure
q11_new = r'''\begin{question}
如图，在正方体\(ABCD - A_{1}B_{1}C_{1}D_{1}\)中，
点\(E,F,G\)分别在棱\(AA_{1},AB,AD\)上(不与棱的端点重合)，
\(M\)为棱\(CC_{1}\)的中点，则下列说法正确的是(    )

\begin{center}
% PNG: hunan_yali_2026_mock3-Q11-img1
\includegraphics[width=0.6\textwidth]{images/image3.png}
\end{center}

\begin{choices}
  \choice 若平面\(EFG\)与正方体的每条棱的夹角都相同，则直线\(BD\) \(\parallel\)平面\(EFG\)
  \choice 三角形\(EFG\)不可能为直角三角形
  \choice 若\(G,F\)分别为棱\(AD,AB\)的中点，则存在点\(E\)，使得\(AM\bot\)平面\(EGF\)
  \choice 若二面角\(A - GF - E\)的余弦值为\(\frac{1}{2}\)，二面角\(A - EF - G\)的余弦值为\(\frac{\sqrt{3}}{3}\)，则二面角\(A - EG - F\)的余弦值为\(\frac{\sqrt{15}}{6}\)
\end{choices}

\begin{center}
% PNG: hunan_yali_2026_mock3-Q11-img2
\includegraphics[width=0.6\textwidth]{images/image4.png}
\end{center}

\begin{center}
% PNG: hunan_yali_2026_mock3-Q11-img3
\includegraphics[width=0.6\textwidth]{images/image5.png}
\end{center}

\topics{面面平行证明线面平行；空间位置关系的向量证明；已知线面角求其他量；面面角的向量求法}
\difficulty{0.4}
\answer{ABD}
\explain{对于A，在正方体\(ABCD - A_{1}B_{1}C_{1}D_{1}\)中，
令点\(A\)到平面\(EFG\)的距离为\(h\)，\par
由平面\(EFG\)与正方体每条棱的夹角都相同，
得棱\(AB,AD,AA_{1}\)与平面\(EFG\)所成角都相等，\par
则\(\frac{h}{AF} = \frac{h}{AG} = \frac{h}{AE}\)，
于是\(AF = AG = AE\)，而\(AB = AD\)，
则\(\frac{AF}{AB} = \frac{AG}{AD}\)，\(FG//BD\)，\par
而\(BD \not\subset\)平面\(EFG\)，
\(FG \subset\)平面\(EFG\)，因此\(BD//\)平面\(EFG\)，
A正确；\par
对于B，设\(AF = a,AE = b,AG = c\)，
则\(EF^{2} = b^{2} + a^{2},GF^{2} = c^{2} + a^{2},EG^{2} = b^{2} + c^{2}\)，\par
从而\(EF^{2} < GF^{2} + EG^{2}\)，
则\(\angle EGF < 90^{\circ}\)，同理，
\(\angle EFG < 90^{\circ},\angle GEF < 90^{\circ}\)，\par
因此三角形\(EFG\)为锐角三角形，B正确；\par
对于C，以\(A\)为坐标原点建立空间直角坐标系，如图，不妨设正方体棱长为2，\par
则\(A(0,0,0),M(2,2,1),E(0,0,t),F(1,0,0)\)，
\(\overrightarrow{AM} = (2,2,1),\overrightarrow{EF} = (1,0, - t)\)，\par
假设存在点\(E\)，使得\(AM\bot\)平面\(EGF\)，
则\(AM\bot EF\)，
\(\overrightarrow{AM} \cdot \overrightarrow{EF} = 2 - t = 0\)，\par
解得\(t = 2\)，即\(E\)与\(A_{1}\)重合，不符合题意，
因此不存在点\(E\)，使得\(AM\bot\)平面\(EGF\)，C错误；\par
对于D，由选项C得，
平面\(AEF\)的法向量为\(\overrightarrow{a} = (0,1,0)\)，
平面\(AGF\)的法向量为\(\overrightarrow{b} = (0,0,1)\)，\par
平面\(AEG\)的法向量为\(\overrightarrow{t} = (1,0,0)\)，
设平面\(EFG\)的法向量为\(\overrightarrow{c} = (x,y,z),x,y,z > 0\)，\par
则\(\frac{\sqrt{3}}{3} = \frac{\overrightarrow{a} \cdot \overrightarrow{c}}{|\overrightarrow{a}||\overrightarrow{c}|} = \frac{y}{\sqrt{x^{2} + y^{2} + z^{2}}}\)，
解得\(2y^{2} = x^{2} + z^{2}\)，\par
\(\frac{1}{2} = \frac{\overrightarrow{b} \cdot \overrightarrow{c}}{|\overrightarrow{b}||\overrightarrow{c}|} = \frac{z}{\sqrt{x^{2} + y^{2} + z^{2}}}\)，
解得\(3z^{2} = x^{2} + y^{2}\)，
因此\(y^{2} = \frac{4}{5}x^{2},z^{2} = \frac{3}{5}x^{2}\)，\par
则\(\cos\langle t,\overrightarrow{c}\rangle = \frac{\overrightarrow{t} \cdot \overrightarrow{c}}{|\overrightarrow{t}||\overrightarrow{c}|} = \frac{x}{\sqrt{x^{2} + y^{2} + z^{2}}} = \frac{x}{\sqrt{\frac{12}{5}x^{2}}} = \frac{\sqrt{15}}{6}\)，\par
所以二面角\(A - EG - F\)的余弦值为\(\frac{\sqrt{15}}{6}\)，
D正确．}
\end{question}

'''

# Pattern to find Q11 (from 正方体 question to before 填空题 section)
q11_pattern = r'(\\begin\{question\}\n如图，在正方体.*?\\end\{question\}\n\n)(\\section\{填空题\})'

match = re.search(q11_pattern, content, re.DOTALL)
if match:
    old_text = match.group(1)
    section_header = match.group(2)
    print(f"Found Q11, length: {len(old_text)} chars")
    
    # Replace
    new_content = content.replace(old_text + section_header, q11_new + section_header)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✓ Q11 replaced successfully")
else:
    print("Pattern not found!")

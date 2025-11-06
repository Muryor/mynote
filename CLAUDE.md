# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MyNote is a dual-purpose LaTeX document generation system for creating Chinese-English mathematics educational materials. It generates two types of documents:

- **Exam papers (试卷)**: Mathematical exam/quiz documents with questions and multiple-choice answers
- **Lecture handouts (讲义)**: Educational textbook-style materials with theorems, definitions, and examples

**Key Innovation**: Single-source, dual-output system that automatically generates both teacher and student versions from the same source files:
- **Teacher version**: Includes solutions, difficulty ratings, topic tags, and source information
- **Student version**: Automatically hides all teacher-only content

## Common Build Commands

```bash
# Build exam documents
./build.sh exam teacher    # Teacher version with solutions
./build.sh exam student    # Student version without solutions
./build.sh exam both       # Generate both versions

# Build handout documents
./build.sh handout teacher
./build.sh handout student
./build.sh handout both
```

All output PDFs are generated in the `./output/` directory.

## Architecture

### Build System

The build process follows this pipeline:

```
build.sh → Creates wrapper file → latexmk -xelatex → PDF in ./output/
```

1. `build.sh` creates a temporary wrapper file in `/output/` directory
2. Passes `teacher` or `student` option to the `examx.sty` package
3. Inputs the main document (`main-exam.tex` or `main-handout.tex`)
4. Compiles with XeLaTeX engine (forced by `.latexmkrc`)
5. Outputs final PDF to `./output/`

**Note**: `.latexmkrc` forces XeLaTeX as the default engine. LuaLaTeX can be used with `USE_LUALATEX=1` environment variable.

### Key Style Packages (`styles/`)

#### `examx.sty` - Teacher/Student Mode Controller

This package controls teacher/student mode and provides convenience macros. It:

**Package Options**:
- `[teacher]` - Enable teacher mode (show answers and metadata)
- `[student]` - Enable student mode (hide answers and metadata, default)

**Convenience Macros**:
- `\mcq[answer]{stem}{A}{B}{C}{D}` - Quick multiple-choice question macro
- `\examxtitle{title}` - Set per-exam header title

**How It Works**:
- Loads `qmeta.sty` with appropriate version option
- Configures `exam-zh` settings based on teacher/student mode
- Provides fallback `choices` environment when exam-zh is not loaded

**Important Implementation Details**:
- Uses LaTeX3 (`expl3`) syntax - keep `\ExplSyntaxOn` sections clean
- Mode is controlled by build.sh via `\PassOptionsToPackage{teacher|student}{styles/examx}`

#### `qmeta.sty` - Question Metadata System

This package handles metadata capture and rendering. It provides:

**Metadata Commands** (used within question environments):
- `\answer{...}` - Answer (captured automatically by `\mcq` or `\paren`)
- `\topics{topic1；topic2}` - Topic tags (semicolon-separated for Chinese)
- `\difficulty{0.0-1.0}` - Difficulty as decimal (displays as decimal by default)
- `\explain{...}` - Detailed solution explanation
- `\source{...}` - Question source (optional, hidden by default)

**How It Works**:
- Hooks into `exam-zh`'s `question` environment and `elegantbook`'s `problem` environment
- Automatically resets metadata at the start of each question
- In **teacher mode**: Renders metadata block after the question automatically
- In **student mode**: All metadata is silently discarded
- Only renders metadata box when at least one field is non-empty (prevents empty boxes)

**Configuration Options**:
- `version=teacher|student` - Control metadata visibility
- `show-source=true|false` - Show/hide source information (default: false)
- `difficulty-format=decimal|percent` - Display format for difficulty (default: decimal)

**Important Implementation Details**:
- Uses LaTeX3 (`expl3`) syntax
- Difficulty formatting uses `\fp_eval:n` for decimal calculations (NOT `\numexpr`)
- Metadata box uses `tcolorbox` with breakable support

#### `handoutx.sty` - Handout Theorem Boxes

Provides styled `tcolorbox` environments for handouts:
- `definitionx` - Definition boxes
- `propertyx` - Property/theorem boxes
- `examplex` - Example boxes
- `notebox` - Note/remark boxes

All use consistent green color scheme with numbered labels.

### Configuration Files (`settings/`)

#### `preamble.sty` - Font Configuration

Implements a robust font system with extensive fallback chains to prevent compilation failures:

- **Latin Fonts**: STIX Two Text → TeX Gyre Termes → Times New Roman → Latin Modern
- **Math Fonts**: STIX Two Math → Libertinus Math → XITS Math → Latin Modern Math
- **CJK Fonts**: PingFang SC / Noto Serif CJK SC / Source Han fonts / STSong/STHeiti

Uses `\IfFontExistsTF` for automatic font detection and provides synthetic bold/italic for missing font faces.

#### `metadata.tex`

Simple document metadata (title, author, date) loaded by both main documents.

### Document Structure

**Entry Points**:
- `main-exam.tex` - Uses `exam-zh` document class (CTAN package for Chinese exams)
- `main-handout.tex` - Uses `elegantbook` document class (elegant Chinese book template)

**Content Organization**:
- `content/exams/` - Individual exam question files
- `content/handouts/` - Chapter files for handouts

To add new content, edit the appropriate main file to `\input{content/.../yourfile.tex}`.

## Typical Question Format

MyNote supports two authoring patterns for multiple-choice questions:

### Pattern 1: Using `\mcq` Macro (Recommended)

```tex
\mcq[B]{已知集合 $A=\{x\mid \log_2 x < 1\},\, B=\{x\mid x<1\}$，则 $A\cap B$ 等于}
{$(-\infty,1)$}{$(0,1)$}{$(-\infty,2)$}{$(0,2)$}
\topics{交集；不等式与函数单调性}
\difficulty{0.40}
\explain{由 $\log_2 x<1\Rightarrow 0<x<2$，与 $x<1$ 取交得 $(0,1)$。}
\source{自编}
```

### Pattern 2: Using Traditional exam-zh Syntax

```tex
\begin{question}
  已知集合 $A=\{x\mid \log_2 x < 1\}$，则 $A\cap B$ 等于 \paren[B]
  \begin{choices}[columns=2]
    \choice $(-\infty,1)$
    \choice $(0,1)$
    \choice $(-\infty,2)$
    \choice $(0,2)$
  \end{choices}
  \topics{交集；不等式与函数单调性}
  \difficulty{0.40}
  \explain{由 $\log_2 x<1\Rightarrow 0<x<2$，与 $x<1$ 取交得 $(0,1)$。}
  \source{自编}
\end{question}
```

**Key Points**:
- `\mcq[answer]{stem}{optionA}{optionB}{optionC}{optionD}` - Convenience macro for simple MCQs
- `\paren[answer]` - Shows answer in teacher version, empty parentheses in student version
- Metadata commands (`\topics`, `\difficulty`, `\explain`, `\source`, `\answer`) work with both patterns
- Metadata is automatically hidden in student version
- No manual conditionals needed - the `examx` and `qmeta` packages handle everything

## Development Workflow

1. **Create/edit content files** in `content/exams/` or `content/handouts/`
2. **Update main file** (`main-exam.tex` or `main-handout.tex`) to include new content files
3. **Build both versions** to verify compilation:
   ```bash
   ./build.sh exam both
   ./build.sh handout both
   ```
4. **Check output** in `./output/` directory for both teacher and student PDFs
5. **Commit** using conventional commit format:
   ```bash
   git commit -m "fix(examx): correct metadata rendering"
   git commit -m "feat(handout): add new theorem box style"
   git commit -m "docs(readme): update build instructions"
   ```

## Important Development Constraints

1. **Compatibility**: Code must compile on TeX Live 2024+. Avoid bleeding-edge features.

2. **Decimal Math**: Always use `\fp_eval:n` for decimal/floating-point calculations, NOT `\numexpr` (which only handles integers).

3. **Testing**: Always test both teacher AND student versions before committing. Metadata rendering bugs often only appear in one version.

4. **LaTeX3 Syntax**: When editing `examx.sty`, keep `\ExplSyntaxOn`/`\ExplSyntaxOff` sections clean. Don't toggle mid-file unnecessarily.

5. **Font Fallbacks**: The font system is designed to be robust. When adding new fonts, always provide fallback chains using `\IfFontExistsTF`.

## Conversion Tools

The `tools/` directory contains Python scripts for converting external content:

- `convert_tex_exam.py` - Converts formatted text files to exam LaTeX format
- Supports format with markers like `【答案】`, `【难度】`, `【知识点】`, `【详解】`

Usage:
```bash
python3 tools/convert_tex_exam.py input.txt output.tex
```

## System Requirements

- TeX Live 2024+ (2025 recommended)
- XeLaTeX or LuaLaTeX engine
- Python 3 (for conversion tools only)

**Key LaTeX Packages**:
- `exam-zh` - Chinese exam document class
- `elegantbook` - Handout book class
- `fontspec`, `unicode-math` - Font management
- `xeCJK` / `ctex` - Chinese typesetting
- `tcolorbox` - Colored boxes with page breaks
- `expl3` / `xparse` - LaTeX3 programming

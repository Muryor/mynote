#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaseConverter - shared conversion skeleton for Markdown → LaTeX pipelines.

Phase-A: thin wrapper around legacy converters; provides unified interface for
future handout/exam implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ConversionResult:
    tex: str
    output_path: Optional[Path] = None


class BaseConverter:
    def __init__(self, input_md: Path, output_tex: Path, *, title: str, slug: str, enable_issue_detection: bool = True, figures_dir: str = ""):
        self.input_md = Path(input_md)
        self.output_tex = Path(output_tex)
        self.title = title or self.input_md.stem
        self.slug = slug or self.input_md.stem
        self.enable_issue_detection = enable_issue_detection
        self.figures_dir = figures_dir

    def convert_text(self, md_text: str) -> ConversionResult:
        """Convert markdown string to LaTeX. To be implemented by subclasses."""
        raise NotImplementedError

    def convert(self) -> ConversionResult:
        if not self.input_md.is_file():
            raise FileNotFoundError(f"Input Markdown not found: {self.input_md}")

        md_text = self.input_md.read_text(encoding="utf-8")
        result = self.convert_text(md_text)

        # Write output
        self.output_tex.parent.mkdir(parents=True, exist_ok=True)
        self.output_tex.write_text(result.tex, encoding="utf-8")
        result.output_path = self.output_tex
        return result

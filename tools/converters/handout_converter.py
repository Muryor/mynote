#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HandoutConverter - placeholder for future handout pipeline.
"""
from __future__ import annotations

from pathlib import Path

from .base_converter import BaseConverter, ConversionResult


class HandoutConverter(BaseConverter):
    def __init__(self, input_md: Path, output_tex: Path, *, title: str = "", slug: str = "", enable_issue_detection: bool = True, figures_dir: str = ""):
        super().__init__(input_md, output_tex, title=title, slug=slug, enable_issue_detection=enable_issue_detection, figures_dir=figures_dir)

    def convert_text(self, md_text: str) -> ConversionResult:
        raise NotImplementedError("HandoutConverter is not implemented yet")

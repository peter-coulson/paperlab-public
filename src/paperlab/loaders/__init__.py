"""Shared loading infrastructure for papers, marks, and test cases.

This module provides generic utilities for loading data from JSON files:
- JSON parsing and validation
- Update/replace framework for existing records
- Diff calculation and confirmation prompts

Used by both:
- loading/ (paper and mark scheme loaders)
- evaluation/ (test case and test suite loaders)
"""

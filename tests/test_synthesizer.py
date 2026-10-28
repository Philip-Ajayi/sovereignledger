"""
Tests dynamic AST security validator and Python code isolation.
"""
from src.skills.synthesizer import SecurityASTValidator, AutonomousSkillSynthesizer
import ast

def test_ast_validator_rejects_forbidden_imports():
    unsafe_code = """
import os
import sys
import subprocess

def dangerous():
    os.system('rm -rf /')
"""
    tree = ast.parse(unsafe_code)
    validator = SecurityASTValidator()
    validator.visit(tree)
    assert len(validator.violations) >= 3

def test_ast_validator_approves_safe_parser():
    safe_code = """
import re
from datetime import datetime
from decimal import Decimal
from typing import List

class SafeParser:
    pass
"""
    tree = ast.parse(safe_code)
    validator = SecurityASTValidator()
    validator.visit(tree)
    assert len(validator.violations) == 0

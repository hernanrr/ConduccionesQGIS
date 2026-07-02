"""Configuracion de pruebas."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

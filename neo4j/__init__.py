"""Local Neo4j loader utilities for the medication safety project."""

import os
import sys
from importlib.util import module_from_spec, spec_from_file_location

_package_dir = os.path.dirname(os.path.abspath(__file__))

for entry in sys.path:
    if not entry:
        continue

    normalized = os.path.abspath(entry)
    if normalized.startswith(os.path.abspath(_package_dir)):
        continue

    candidate = os.path.join(normalized, "neo4j", "__init__.py")
    if os.path.isfile(candidate) and os.path.abspath(candidate) != __file__:
        spec = spec_from_file_location("_real_neo4j", candidate)
        if spec and spec.loader:
            real_module = module_from_spec(spec)
            sys.modules[spec.name] = real_module
            spec.loader.exec_module(real_module)
            for attribute in ("GraphDatabase", "basic_auth", "Driver", "Session"):
                if hasattr(real_module, attribute):
                    globals()[attribute] = getattr(real_module, attribute)
            break

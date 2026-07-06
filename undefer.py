import re

with open(r'f:\Synaptix\tests\COVERAGE_MANIFEST.yaml', 'r', encoding='utf-8') as f:
    content = f.read()

tests_to_undefer = [
    'ATT-003', 'ATT-004', 'ATT-005', 'ATT-006', 'ATT-007',
    'ATT-SYNC-001', 'ATT-SYNC-002', 'ATT-SYNC-003', 'ATT-SYNC-004', 'ATT-SYNC-005', 'ATT-SYNC-006', 'ATT-SYNC-007',
    'ATT-E002', 'ATT-E017', 'ATT-E018', 'ATT-E019', 'ATT-E020'
]

for t in tests_to_undefer:
    pattern = r'(- id: "' + t + r'"[\s\S]*?)\n\s+deferred_to:.*?(?=\n\s+- id:|\n\n|\Z)'
    content = re.sub(pattern, r'\1', content)

with open(r'f:\Synaptix\tests\COVERAGE_MANIFEST.yaml', 'w', encoding='utf-8') as f:
    f.write(content)

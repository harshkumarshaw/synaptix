with open(r'f:\Synaptix\tests\COVERAGE_MANIFEST.yaml', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_deferred = False
for line in lines:
    if '- id: "ATT-0' in line or '- id: "ATT-E' in line:
        tests_to_remove_defer = ['ATT-003', 'ATT-004', 'ATT-005', 'ATT-006', 'ATT-007', 'ATT-E002', 'ATT-E017', 'ATT-E018', 'ATT-E019', 'ATT-E020']
        if any(t in line for t in tests_to_remove_defer):
            skip_deferred = True
        else:
            skip_deferred = False
    
    if skip_deferred and 'deferred_to:' in line:
        continue # Skip this line
    new_lines.append(line)

with open(r'f:\Synaptix\tests\COVERAGE_MANIFEST.yaml', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

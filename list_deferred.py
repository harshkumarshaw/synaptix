import yaml
with open(r'f:\Synaptix\tests\COVERAGE_MANIFEST.yaml', 'r', encoding='utf-8') as f:
    manifest = yaml.safe_load(f)
    for module, module_data in manifest.items():
        for category in ['critical_tests', 'nmc_compliance_tests', 'edge_cases', 'security_tests', 'tests']:
            if category in module_data:
                for test in module_data[category]:
                    if 'deferred_to' in test:
                        print(f"{test['id']}: {test['description']} (deferred to {test['deferred_to']})")

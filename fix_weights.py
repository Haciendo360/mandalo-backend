import os
import re

weight_map = {
    '"900"': '"bold"',
    '"800"': '"bold"',
    '"700"': '"bold"',
    '"600"': '"medium"',
    '"500"': '"medium"',
    '"400"': '"regular"',
    '"300"': '"light"'
}

directory = 'mandalo_app/components'
for root, _, files in os.walk(directory):
    for filename in files:
        if filename.endswith('.py'):
            filepath = os.path.join(root, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for k, v in weight_map.items():
                content = re.sub(r'weight=' + k, 'weight=' + v, content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

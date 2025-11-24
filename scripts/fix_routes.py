import re

FILE_PATH = 'app/routes.py'
EXCLUDE = {'static', 'main.'} # main. already prefixed

def fix_routes_url_for(content):
    # Pattern: url_for('endpoint'
    # We want to find endpoints that don't have a dot (or aren't static)
    pattern = r"url_for\(['\"]([^'\"]+)['\"]"

    def replace_match(match):
        endpoint = match.group(1)
        if endpoint == 'static' or '.' in endpoint:
            return match.group(0)
        return f"url_for('main.{endpoint}'"

    return re.sub(pattern, replace_match, content)

with open(FILE_PATH, 'r') as f:
    content = f.read()

new_content = fix_routes_url_for(content)

if new_content != content:
    with open(FILE_PATH, 'w') as f:
        f.write(new_content)
    print(f"Updated {FILE_PATH}")
else:
    print(f"No changes needed for {FILE_PATH}")

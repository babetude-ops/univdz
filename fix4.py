content = open('app/__init__.py', 'r', encoding='utf-8').read()
content = content.replace(
    '        admin = Admin(username=admin_username)',
    '        admin = Admin(username=admin_username, email=os.environ.get("ADMIN_EMAIL", "admin@univdz.dz"))'
)
open('app/__init__.py', 'w', encoding='utf-8').write(content)
print('Done!')
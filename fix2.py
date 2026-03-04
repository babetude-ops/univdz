content = open('app/__init__.py', 'r', encoding='utf-8').read()
content = content.replace('        db.create_all()\n    return app', '        db.create_all()\n        _create_admin()\n    return app')
open('app/__init__.py', 'w', encoding='utf-8').write(content)
print('Done!')
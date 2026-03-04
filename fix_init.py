content = open('app/__init__.py', 'r', encoding='utf-8').read()

new_content = content.replace(
    '    with app.app_context():\n        db.create_all()\n    return app',
    '    with app.app_context():\n        db.create_all()\n        _create_admin()\n    return app'
)

new_content += '''

def _create_admin():
    import os
    from app.models.event import Admin
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")
    admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")
    if not Admin.query.filter_by(username=admin_username).first():
        admin = Admin(username=admin_username)
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
'''

open('app/__init__.py', 'w', encoding='utf-8').write(new_content)
print('Done!')

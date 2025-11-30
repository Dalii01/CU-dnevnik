class AdminUserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository

    def get_all_users_for_admin(self):
        """Возвращает список ВСЕХ пользователей с ролью и статусом"""
        users = self.user_repo.get_all()

        result = []
        for u in users:
            role_labels = {
                'admin': 'Админ',
                'teacher': 'Учитель',
                'parent': 'Родитель',
                'student': 'Ученик'
            }
            role_key = u.role.value 
            role_display = role_labels.get(role_key, role_key)

            result.append({
                'id': u.id,
                'last_name': u.last_name or "",
                'first_name': u.first_name or "",
                'email': u.email,
                'role': role_display,
                'is_active': bool(u.is_active),
                'role_key': role_key
            })
        return result
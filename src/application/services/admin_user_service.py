from domain.entities.user import UserRole


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

    def get_non_admin_users(self):
        """Возвращает список всех пользователей кроме админов с ролью и статусом"""
        users = self.user_repo.get_all()

        # Фильтруем пользователей, исключая админов
        non_admin_users = [u for u in users if u.role != UserRole.ADMIN]

        result = []
        for u in non_admin_users:
            role_labels = {
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

    def toggle_user_status(self, user_id: int) -> tuple[bool, str]:
        """Изменяет статус пользователя (активен/деактивирован)

        Args:
            user_id: ID пользователя

        Returns:
            tuple: (успех операции, сообщение)
        """
        try:
            # Получаем пользователя
            user = self.user_repo.get_by_id(user_id)
            if not user:
                return False, "Пользователь не найден"

            # Изменяем статус на противоположный
            user.is_active = not user.is_active

            # Сохраняем изменения
            self.user_repo.update(user)

            # Формируем сообщение
            status_text = "активирован" if user.is_active else "деактивирован"
            return True, f"Пользователь {user.get_full_name()} был {status_text}"

        except Exception as e:
            return False, f"Ошибка при изменении статуса пользователя: {str(e)}"
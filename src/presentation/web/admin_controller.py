from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required


class AdminController:
    
    def __init__(self, admin_user_service):
        self.admin_user_service = admin_user_service
        self.bp = Blueprint('admin', __name__, url_prefix='/admin')
        self._register_routes()
    
    def _register_routes(self):

        @self.bp.route('/users')
        @login_required
        def admin_users():
            # Проверяем, что пользователь - администратор
            if not current_user.is_admin():
                flash('У вас нет прав для доступа к этой странице', 'error')
                return redirect(url_for('main.index'))

            # Получаем всех пользователей кроме админов
            users = self.admin_user_service.get_non_admin_users()

            # Подсчитываем статистику
            total_users = len(users)
            active_users = sum(1 for u in users if u['is_active'])
            blocked_users = total_users - active_users

            return render_template(
                'user_management.html',
                users=users,
                total_users=total_users,
                active_users=active_users,
                blocked_users=blocked_users,
                current_user_id=current_user.id
            )

        @self.bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
        @login_required
        def toggle_user_status(user_id):
            # Проверяем, что пользователь - администратор
            if not current_user.is_admin():
                flash('У вас нет прав для выполнения этого действия', 'error')
                return redirect(url_for('main.index'))

            # Администратор не может деактивировать сам себя
            if user_id == current_user.id:
                flash('Вы не можете изменить свой собственный статус', 'error')
                return redirect(url_for('admin.admin_users'))

            # Получаем результат изменения статуса
            success, message = self.admin_user_service.toggle_user_status(user_id)

            if success:
                flash(message, 'success')
            else:
                flash(message, 'error')

            return redirect(url_for('admin.admin_users'))

    def get_blueprint(self):
        return self.bp
from flask import Blueprint, render_template
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
            if not current_user.is_admin:
                return "Доступ запрещен", 403
    
            # ВРЕМЕННАЯ ЗАГЛУШКА — проверяем, что код исполняется
            return "<h1 style='color:red'>✅ ДА! Контроллер работает!</h1>"
    
    def get_blueprint(self):
        return self.bp
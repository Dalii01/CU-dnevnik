from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from application.services.student_service import StudentService


class MainController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('main', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/')
        def index():
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            students = self.student_service.get_all_students(current_user)
            
            students_statistics = {} 
            for student in students: 
                statistics = self.student_service.calculate_student_statistics(student.id, current_user) 
                students_statistics[student.id] = statistics 
                
            return render_template('index.html', students=students, students_statistics=students_statistics)
        
        @self.bp.route('/admin/users')
        @login_required
        def admin_user_management():
            # Временный маршрут для управления пользователями
            return render_template('user_management.html')
    
    def get_blueprint(self):
        return self.bp
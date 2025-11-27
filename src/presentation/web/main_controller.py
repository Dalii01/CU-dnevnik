from flask import Blueprint, render_template, redirect, url_for
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
            
            students_with_means = []
            for student in students:
                student_stats = self.student_service.calculate_student_statistics(student.id, current_user)
                
                print(f"DEBUG student {student.id} ({student.name}): stats={student_stats}")
                if student_stats:
                    print(f"DEBUG: total_grades = {student_stats.get('total_grades')}")
                
                students_with_means.append({
                    'student': student,
                    'statistics': student_stats
                })
            
            return render_template('index.html', students_with_means=students_with_means)
    
    def get_blueprint(self):
        return self.bp
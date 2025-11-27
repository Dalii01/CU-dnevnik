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

                data = self.student_service.get_student_diary_data(student.id, current_user)
        
                print(f"=== DEBUG STUDENT {student.id} ===")
                print(f"Data type: {type(data)}")
                if data:
                    print(f"Data keys: {list(data.keys())}")
                    if 'statistics' in data:
                        student_stats = data['statistics']
                        print(f"Statistics: {student_stats}")
                    else:
                        student_stats = None
                else:
                    student_stats = None
                    print("Data is None or empty")
        
                students_with_means.append({
                    'student': student,
                    'statistics': student_stats
                })
    
            return render_template('index.html', students_with_means=students_with_means)
    def get_blueprint(self):
        return self.bp
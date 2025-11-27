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
                
                print(f"DEBUG student {student.id} ({student.name}): data={data is not None}")
                if data:
                    print(f"DEBUG: statistics key exists = {'statistics' in data}")
                    if 'statistics' in data:
                        print(f"DEBUG: total_grades = {data['statistics'].get('total_grades')}")
                    else:
                        print(f"DEBUG: available keys = {list(data.keys())}")
                
                student_stats = data.get('statistics') if data else None
                
                students_with_means.append({
                    'student': student,
                    'statistics': student_stats
                })
            
            return render_template('index.html', students_with_means=students_with_means)
    
    def get_blueprint(self):
        return self.bp
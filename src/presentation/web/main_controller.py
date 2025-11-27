from flask import Blueprint, render_template, redirect, url_for
from application.services.student_service import StudentService


class MainController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('main', __name__)
        self._register_routes()
    
    def _calculate_student_statistics(self, student_id: int, current_user):
        grades = self.student_service.get_student_grades(student_id)  
        
        if not grades:
            return {
                'mean_grade': 0,
                'median_grade': 0,
                'total_grades': 0,
                'grade_distribution': {}    
            }
        
        grade_values = [grade.grade for grade in grades]
        total = sum(grade_values)
        mean_grade = round(total / len(grade_values), 2)
        
        return {
            'mean_grade': mean_grade,
            'median_grade': 0,  
            'total_grades': len(grades),
            'grade_distribution': {}
        }
    
    def _register_routes(self):
        
        @self.bp.route('/')
        def index():
            from flask_login import current_user
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            
            students = self.student_service.get_all_students(current_user)
            
            students_with_means = []
            for student in students:
                student_stats = self._calculate_student_statistics(student.id, current_user)
                
                students_with_means.append({
                    'student': student,
                    'statistics': student_stats
                })
            
            return render_template('index.html', students_with_means=students_with_means)
    
    def get_blueprint(self):
        return self.bp
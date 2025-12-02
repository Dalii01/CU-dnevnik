from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from application.services.student_service import StudentService


class ReportsController:
    
    def __init__(self, student_service: StudentService):
        self.student_service = student_service
        self.bp = Blueprint('reports', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/reports')
        @login_required
        def reports():
            # Проверка прав доступа
            if not (current_user.is_teacher() or current_user.is_parent() or current_user.is_admin()):
                return render_template('reports.html')
            
            # Получаем список предметов
            subjects = self.student_service.subject_repo.get_all()
            
            # Получаем выбранный предмет
            subject_id = request.args.get('subject_id', type=int)
            selected_subject = None
            report_data = None
            
            if subject_id:
                selected_subject = self.student_service.subject_repo.get_by_id(subject_id)
                
                if selected_subject:
                    # Формируем данные отчёта
                    report_data = self._generate_report_data(subject_id, current_user)
            
            return render_template('reports.html', 
                                 subjects=subjects,
                                 selected_subject=selected_subject,
                                 report_data=report_data)
    
    def _generate_report_data(self, subject_id: int, user) -> dict:
        # Получаем студентов в зависимости от роли
        students = self.student_service.get_all_students(user)
        
        if not students:
            return None
        
        # Собираем все даты и данные
        all_dates = set()
        students_data = {}
        
        for student in students:
            # Получаем оценки по предмету
            grades = self.student_service.grade_repo.get_by_student_and_subject(student.id, subject_id)
            # Получаем посещаемость
            attendance = self.student_service.attendance_repo.get_by_student(student.id)
            
            student_dates = {}
            
            for grade in grades:
                all_dates.add(grade.date)
                if grade.date not in student_dates:
                    student_dates[grade.date] = {}
                student_dates[grade.date]['grade'] = grade.grade
            
            for att in attendance:
                # Фильтруем посещаемость по предмету, если есть subject_id
                if hasattr(att, 'subject_id') and att.subject_id != subject_id:
                    continue
                all_dates.add(att.date)
                if att.date not in student_dates:
                    student_dates[att.date] = {}
                student_dates[att.date]['present'] = att.present
            
            if student_dates:  # Добавляем только если есть данные
                students_data[student.id] = {
                    'student': student,
                    'dates': student_dates
                }
        
        if not all_dates:
            return None
        
        return {
            'dates': sorted(all_dates),
            'students_data': students_data
        }
    
    def get_blueprint(self):
        return self.bp

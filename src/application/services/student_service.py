from typing import Any
from datetime import date
from domain.entities.student import Student
from domain.entities.grade import Grade
from domain.entities.attendance import Attendance
from domain.entities.schedule import Schedule
from domain.entities.subject import Subject
from domain.repositories.student_repository import IStudentRepository
from domain.repositories.grade_repository import IGradeRepository
from domain.repositories.attendance_repository import IAttendanceRepository
from domain.repositories.schedule_repository import IScheduleRepository
from domain.repositories.subject_repository import ISubjectRepository
from application.services.auth_service import AuthService
from application.services.telegram_service import TelegramService


class StudentService:
    
    def __init__(self,
                 student_repo: IStudentRepository,
                 grade_repo: IGradeRepository,
                 attendance_repo: IAttendanceRepository,
                 schedule_repo: IScheduleRepository,
                 subject_repo: ISubjectRepository,
                 auth_service: AuthService,
                 telegram_service: TelegramService = None):
        self.student_repo = student_repo
        self.grade_repo = grade_repo
        self.attendance_repo = attendance_repo
        self.schedule_repo = schedule_repo
        self.subject_repo = subject_repo
        self.auth_service = auth_service
        self.telegram_service = telegram_service or TelegramService()
    
    def get_all_students(self, current_user) -> list[Student]:
        if not current_user or not hasattr(current_user, 'id'):
            return []
        return self.auth_service.get_user_students(current_user)
    
    def get_student_by_id(self, student_id: int) -> Student | None:
        return self.student_repo.get_by_id(student_id)
    
    def get_student_diary_data(self, student_id: int, current_user) -> dict[str, Any] | None:
        if not current_user or not hasattr(current_user, 'id'):
            return None
            
        if not self.auth_service.can_view_student_data(current_user, student_id):
            return None
            
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return None
            
        grades = self.grade_repo.get_by_student(student_id)
        attendance = self.attendance_repo.get_by_student(student_id)
        schedule = self.schedule_repo.get_all()
        subjects = self.subject_repo.get_all()
        
        # Создаем словарь предметов для быстрого поиска
        subjects_dict = {subject.id: subject for subject in subjects}
        
        # Добавляем объект предмета к каждой оценке
        for grade in grades:
            grade.subject = subjects_dict.get(grade.subject_id)
        
        # Добавляем объект предмета к каждой записи посещаемости
        for att in attendance:
            att.subject = subjects_dict.get(att.subject_id)
        
        # Добавляем объект предмета к каждому элементу расписания
        for sched in schedule:
            sched.subject = subjects_dict.get(sched.subject_id)

            statistics = self.calculate_student_statistics(student_id, current_user)
        
        return {
            'student': student,
            'grades': grades,
            'attendance': attendance,
            'schedule': schedule,
            'subjects': subjects,
            'statistics': statistics
        }
    
    def calculate_student_statistics(self, student_id: int, current_user) -> dict[str, Any] | None:
        if not self.auth_service.can_view_student_data(current_user, student_id):
            return None
            
        grades = self.grade_repo.get_by_student(student_id)
        grade_values = [grade.grade for grade in grades]
        
        if not grade_values:
            return {
                'mean_grade': 0,
                'median_grade': 0,
                'total_grades': 0,
                'grade_distribution': {}    
            }
        
        # Расчет среднего балла
        total = sum(grade_values)
        mean_grade = total / len(grade_values)
        mean_grade = round(mean_grade, 2) 
        
        # Расчет медианного балла
        sorted_grades = sorted(grade_values)
        n = len(sorted_grades)
        if n % 2 == 1:
            median_grade = sorted_grades[n // 2]
        else:
            median_grade = (sorted_grades[n // 2 - 1] + sorted_grades[n // 2]) / 2
        
        # Распределение оценок
        grade_distribution = {}
        for grade_value in grade_values:
            grade_distribution[grade_value] = grade_distribution.get(grade_value, 0) + 1
        
        return {
            'mean_grade': mean_grade,
            'median_grade': median_grade,
            'total_grades': len(grades),
            'grade_distribution': grade_distribution
        }
    
    def add_grade(self, student_id: int, subject_id: int, grade: int,
                  comment: str, current_user) -> Grade | None:
        if not current_user or not hasattr(current_user, 'id'):
            return None

        if not self.auth_service.can_edit_student_data(current_user, student_id):
            return None

        new_grade = Grade(
            id=None,
            student_id=student_id,
            subject_id=subject_id,
            grade=grade,
            date=date.today(),
            comment=comment
        )

        created_grade = self.grade_repo.create(new_grade)

        # Отправляем уведомление в Telegram если оценка создана успешно
        if created_grade:
            self._send_grade_notification(created_grade)

        return created_grade

    def _send_grade_notification(self, grade: Grade) -> None:
        try:
            # Получаем студента и связанного с ним пользователя
            student = self.student_repo.get_by_id(grade.student_id)
            if not student or not student.user_id:
                return

            # Получаем пользователя из репозитория auth_service
            user = self.auth_service.user_repo.get_by_id(student.user_id)
            if not user:
                return

            if not user.telegram_id:
                return

            # Получаем предмет
            subject = self.subject_repo.get_by_id(grade.subject_id)
            if not subject:
                return

            # Отправляем уведомление
            self.telegram_service.send_grade_notification(user, grade, subject)

        except Exception as e:
            print(f"❌ Ошибка при отправке уведомления о оценке: {e}")
    
    def add_attendance(self, student_id: int, subject_id: int, present: bool, 
                      reason: str, current_user) -> Attendance | None:
        if not current_user or not hasattr(current_user, 'id'):
            return None
            
        if not self.auth_service.can_edit_student_data(current_user, student_id):
            return None
            
        new_attendance = Attendance(
            id=None,
            student_id=student_id,
            subject_id=subject_id,
            date=date.today(),
            present=present,
            reason=reason
        )
        
        return self.attendance_repo.create(new_attendance)
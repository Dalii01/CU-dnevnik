from datetime import datetime, timedelta
from typing import List, Dict, Any


class AnalyticsService:    
    def __init__(self, student_repo, grade_repo, attendance_repo, subject_repo):
        self.student_repo = student_repo
        self.grade_repo = grade_repo
        self.attendance_repo = attendance_repo
        self.subject_repo = subject_repo
    
    def get_class_leaderboard(self, class_name: str, subject_id: int = None) -> List[Dict[str, Any]]:
        # Получаем всех студентов класса
        students = self.student_repo.get_by_class(class_name)
        
        leaderboard = []
        for student in students:
            # Получаем оценки студента
            if subject_id:
                grades = self.grade_repo.get_by_student_and_subject(student.id, subject_id)
            else:
                grades = self.grade_repo.get_by_student(student.id)
            
            if not grades:
                avg_grade = 0
                total_grades = 0
            else:
                avg_grade = sum(g.grade for g in grades) / len(grades)
                total_grades = len(grades)
            
            leaderboard.append({
                'student': student,
                'avg_grade': round(avg_grade, 2),
                'total_grades': total_grades
            })
        
        # Сортируем по среднему баллу (от большего к меньшему)
        leaderboard.sort(key=lambda x: x['avg_grade'], reverse=True)
        
        # Добавляем места
        for rank, entry in enumerate(leaderboard, start=1):
            entry['rank'] = rank
        
        return leaderboard
    
    def get_student_rank(self, student_id: int) -> Dict[str, Any]:
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return None
        
        leaderboard = self.get_class_leaderboard(student.class_name)
        
        # Находим студента в рейтинге
        for entry in leaderboard:
            if entry['student'].id == student_id:
                return {
                    'rank': entry['rank'],
                    'total_students': len(leaderboard),
                    'avg_grade': entry['avg_grade'],
                    'percentile': round((1 - (entry['rank'] - 1) / len(leaderboard)) * 100, 1)
                }
        
        return None
    
    def get_student_recommendations(self, student_id: int) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Получаем данные студента
        student = self.student_repo.get_by_id(student_id)
        if not student:
            return recommendations
        
        grades = self.grade_repo.get_by_student(student_id)
        attendance = self.attendance_repo.get_by_student(student_id)
        
        # 1. Анализ тренда оценок (падение/рост)
        trend_rec = self._analyze_grade_trend(grades)
        if trend_rec:
            recommendations.append(trend_rec)
        
        # 2. Анализ по предметам (слабые предметы)
        weak_subjects = self._find_weak_subjects(grades, student_id)
        if weak_subjects:
            recommendations.extend(weak_subjects)
        
        # 3. Анализ посещаемости
        attendance_rec = self._analyze_attendance(attendance)
        if attendance_rec:
            recommendations.append(attendance_rec)
        
        # 4. Достижения (серии хороших оценок)
        achievements = self._find_achievements(grades)
        if achievements:
            recommendations.extend(achievements)
        
        return recommendations
    
    def _analyze_grade_trend(self, grades: List) -> Dict[str, Any] | None:
        if len(grades) < 4:
            return None
        
        # Сортируем по дате
        sorted_grades = sorted(grades, key=lambda g: g.date)
        
        # Берем последнюю половину оценок для сравнения
        half_point = len(sorted_grades) // 2
        older_grades = sorted_grades[:half_point]
        recent_grades = sorted_grades[half_point:]
        
        if not older_grades or not recent_grades:
            return None
        
        # Сравниваем среднее за последние оценки с более старыми
        recent_avg = sum(g.grade for g in recent_grades) / len(recent_grades)
        older_avg = sum(g.grade for g in older_grades) / len(older_grades)
        
        diff = recent_avg - older_avg
        
        if diff < -0.3:  # Падение
            return {
                'type': 'warning',
                'icon': '⚠️',
                'title': 'Внимание',
                'text': f'Оценки снижаются. Средний балл упал с {older_avg:.2f} до {recent_avg:.2f}'
            }
        elif diff > 0.3:  # Рост
            return {
                'type': 'success',
                'icon': '✨',
                'title': 'Прогресс',
                'text': f'Студент улучшил средний балл на {diff:.1f}! Так держать!'
            }
        
        return None
    
    def _find_weak_subjects(self, grades: List, student_id: int) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Группируем оценки по предметам
        subjects_grades = {}
        for grade in grades:
            if grade.subject_id not in subjects_grades:
                subjects_grades[grade.subject_id] = []
            subjects_grades[grade.subject_id].append(grade)
        
        # Анализируем каждый предмет
        for subject_id, subject_grades in subjects_grades.items():
            if len(subject_grades) < 2:  
                continue
            
            # Берем все оценки по предмету
            recent = sorted(subject_grades, key=lambda g: g.date)
            recent_avg = sum(g.grade for g in recent) / len(recent)
            
            if recent_avg < 3.5:  
                subject = self.subject_repo.get_by_id(subject_id)
                grades_str = ", ".join(str(g.grade) for g in recent[-3:])  
                recommendations.append({
                    'type': 'recommendation',
                    'icon': '💡',
                    'title': 'Рекомендация',
                    'text': f'Уделить внимание предмету {subject.name}. Средний балл: {recent_avg:.2f} (последние оценки: {grades_str})'
                })
        
        return recommendations
    
    def _analyze_attendance(self, attendance: List) -> Dict[str, Any] | None:
        if not attendance:
            return None
        
        # Считаем общее количество пропусков
        absences = [a for a in attendance if not a.present]
        total_records = len(attendance)
        
        if not total_records:
            return None
        
        absence_rate = len(absences) / total_records
        
        # Если пропущено более 30% занятий
        if absence_rate > 0.3:
            return {
                'type': 'risk',
                'icon': '📉',
                'title': 'Риск',
                'text': f'Пропущено {len(absences)} из {total_records} занятий ({absence_rate*100:.0f}%). Возможно отставание по программе'
            }
        # Если отличная посещаемость
        elif absence_rate == 0:
            return {
                'type': 'success',
                'icon': '✅',
                'title': 'Отлично',
                'text': f'Идеальная посещаемость! Все {total_records} занятий посещены'
            }
        
        return None
    
    def _find_achievements(self, grades: List) -> List[Dict[str, Any]]:
        achievements = []
        
        if len(grades) < 3:
            return achievements
        
        # Сортируем по дате
        sorted_grades = sorted(grades, key=lambda g: g.date)
        
        # Группируем по предметам
        subjects_grades = {}
        for grade in sorted_grades:
            if grade.subject_id not in subjects_grades:
                subjects_grades[grade.subject_id] = []
            subjects_grades[grade.subject_id].append(grade)
        
        # Ищем серии пятерок (минимум 2 подряд)
        for subject_id, subject_grades in subjects_grades.items():
            if len(subject_grades) < 2:
                continue
            
            # Проверяем последние оценки
            recent = subject_grades[-2:]
            
            if all(g.grade == 5 for g in recent):
                subject = self.subject_repo.get_by_id(subject_id)
                achievements.append({
                    'type': 'achievement',
                    'icon': '🏆',
                    'title': 'Достижение',
                    'text': f'{len(recent)} пятерки подряд по предмету {subject.name}!'
                })
        
        # Общая статистика: если средний балл выше 4.5
        if grades:
            avg_grade = sum(g.grade for g in grades) / len(grades)
            if avg_grade >= 4.5:
                achievements.append({
                    'type': 'achievement',
                    'icon': '⭐',
                    'title': 'Отличник',
                    'text': f'Средний балл {avg_grade:.2f} - отличная успеваемость!'
                })
        
        return achievements


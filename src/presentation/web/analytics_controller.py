from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user


class AnalyticsController:    
    def __init__(self, analytics_service, student_service):
        self.analytics_service = analytics_service
        self.student_service = student_service
        self.bp = Blueprint('analytics', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/leaderboard')
        @login_required
        def leaderboard():            
            # Определяем, какой класс показывать
            if current_user.is_student():
                # Студент видит только свой класс
                student = self.analytics_service.student_repo.get_by_user_id(current_user.id)
                if not student:
                    flash('Студент не найден', 'error')
                    return redirect(url_for('main.index'))
                class_name = student.class_name
                can_filter = False
                
            elif current_user.is_parent():
                # Родитель видит класс своего ребенка
                from infrastructure.repositories.user_repository import UserRepository
                user_repo = UserRepository(self.analytics_service.student_repo.db)
                children_ids = user_repo.get_children_ids(current_user.id)
                if not children_ids:
                    flash('У вас нет привязанных детей', 'error')
                    return redirect(url_for('main.index'))
                
                child = self.analytics_service.student_repo.get_by_id(children_ids[0])
                class_name = child.class_name
                can_filter = False
                
            else:  # Учитель или админ
                class_name = request.args.get('class', '10А')  # По умолчанию 10А
                can_filter = True
            
            # Получаем фильтр по предмету (если есть)
            subject_id = request.args.get('subject')
            if subject_id:
                subject_id = int(subject_id)
            
            # Получаем рейтинг
            leaderboard_data = self.analytics_service.get_class_leaderboard(class_name, subject_id)
            
            # Получаем список всех классов (для фильтра)
            all_classes = []
            if can_filter:
                all_students = self.analytics_service.student_repo.get_all()
                all_classes = sorted(set(s.class_name for s in all_students))
            
            # Получаем список предметов (для фильтра)
            all_subjects = self.analytics_service.subject_repo.get_all()
            
            # Находим текущего пользователя в рейтинге (если студент или родитель)
            current_student_id = None
            if current_user.is_student():
                student = self.analytics_service.student_repo.get_by_user_id(current_user.id)
                current_student_id = student.id if student else None
            elif current_user.is_parent():
                # Получаем детей родителя через user_repository
                from infrastructure.repositories.user_repository import UserRepository
                user_repo = UserRepository(self.analytics_service.student_repo.db)
                children_ids = user_repo.get_children_ids(current_user.id)
                current_student_id = children_ids[0] if children_ids else None
            
            # Получаем персональные рекомендации для текущего студента
            recommendations = None
            if current_student_id:
                recommendations = self.analytics_service.get_student_recommendations(current_student_id)
            
            return render_template('analytics/leaderboard.html',
                                 leaderboard=leaderboard_data,
                                 class_name=class_name,
                                 can_filter=can_filter,
                                 all_classes=all_classes,
                                 all_subjects=all_subjects,
                                 selected_subject=subject_id,
                                 current_student_id=current_student_id,
                                 recommendations=recommendations)
        
        @self.bp.route('/api/student/<int:student_id>/rank')
        @login_required
        def get_student_rank(student_id):            
            # Проверка прав доступа
            if current_user.is_student():
                student = self.analytics_service.student_repo.get_by_user_id(current_user.id)
                if not student or student.id != student_id:
                    return jsonify({'error': 'Access denied'}), 403
            
            elif current_user.is_parent():
                from infrastructure.repositories.user_repository import UserRepository
                user_repo = UserRepository(self.analytics_service.student_repo.db)
                children_ids = user_repo.get_children_ids(current_user.id)
                if student_id not in children_ids:
                    return jsonify({'error': 'Access denied'}), 403
            
            # Получаем место в рейтинге
            rank_info = self.analytics_service.get_student_rank(student_id)
            
            if not rank_info:
                return jsonify({'error': 'Student not found'}), 404
            
            return jsonify(rank_info)
    
    def get_blueprint(self):
        return self.bp


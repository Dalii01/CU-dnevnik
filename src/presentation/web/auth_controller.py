from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from application.services.auth_service import AuthService
from domain.entities.user import UserRole
from presentation.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm, UpdateTelegramForm
from infrastructure.repositories.user_repository import UserRepository


class AuthController:

    def __init__(self, auth_service: AuthService, user_repo: UserRepository):
        self.auth_service = auth_service
        self.user_repo = user_repo
        self.bp = Blueprint('auth', __name__)
        self._register_routes()
    
    def _register_routes(self):
        
        @self.bp.route('/login', methods=['GET', 'POST'])
        def login():
            form = LoginForm()
            if form.validate_on_submit():
                user, error = self.auth_service.authenticate_user(form.username.data, form.password.data)
                if user:
                    from flask_login import login_user
                    login_user(user, remember=form.remember_me.data)
                    flash('Вы успешно вошли в систему!', 'success')
                    return redirect(url_for('main.index'))
                else:
                    flash(error, 'error')
            
            return render_template('auth/login.html', form=form)

        @self.bp.route('/logout')
        def logout():
            from flask_login import logout_user
            logout_user()
            flash('Вы вышли из системы', 'info')
            return redirect(url_for('auth.login'))

        @self.bp.route('/register', methods=['GET', 'POST'])
        def register():
            form = RegisterForm()
            if form.validate_on_submit():
                user, error = self.auth_service.register_user(
                    form.username.data, form.email.data, form.password.data, 
                    form.first_name.data, form.last_name.data, UserRole(form.role.data)
                )
                
                if user:
                    flash('Регистрация прошла успешно!', 'success')
                    return redirect(url_for('auth.login'))
                else:
                    flash(f'Ошибка регистрации: {error}', 'error')
            
            return render_template('auth/register.html', form=form)

        @self.bp.route('/profile')
        @login_required
        def profile():
            from flask_login import current_user
            return render_template('auth/profile.html', user=current_user)

        @self.bp.route('/change_password', methods=['GET', 'POST'])
        @login_required
        def change_password():
            from flask_login import current_user
            form = ChangePasswordForm()
            
            if form.validate_on_submit():
                if not current_user.check_password(form.current_password.data):
                    flash('Неверный текущий пароль', 'error')
                else:
                    current_user.set_password(form.new_password.data)
                    # TODO: Обновить в репозитории
                    flash('Пароль успешно изменен', 'success')
                    return redirect(url_for('auth.profile'))
            
            return render_template('auth/change_password.html', form=form)

        @self.bp.route('/setup_relationships')
        @login_required
        def setup_relationships():
            from flask_login import current_user
            return render_template('auth/setup_relationships.html', user=current_user)

        @self.bp.route('/update_telegram', methods=['GET', 'POST'])
        @login_required
        def update_telegram():
            form = UpdateTelegramForm()

            if form.validate_on_submit():
                current_user.telegram_id = form.telegram_id.data.strip() if form.telegram_id.data else None

                try:
                    self.user_repo.update(current_user)
                    flash('Telegram ID успешно обновлен!', 'success')
                    return redirect(url_for('auth.profile'))
                except Exception as e:
                    flash(f'Ошибка при обновлении Telegram ID: {str(e)}', 'error')

            # Предзаполняем форму текущим значением
            if current_user.telegram_id:
                form.telegram_id.data = current_user.telegram_id

            return render_template('auth/update_telegram.html', form=form, user=current_user)

    def get_blueprint(self):
        return self.bp

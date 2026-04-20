import os
import requests
from datetime import date
from domain.entities.user import User
from domain.entities.grade import Grade
from domain.entities.subject import Subject


class TelegramService:

    def __init__(self):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
        self.base_url = f'https://api.telegram.org/bot{self.bot_token}'

    def send_grade_notification(self, user: User, grade: Grade, subject: Subject) -> bool:
        if not user.telegram_id:
            return False

        if not self.bot_token or self.bot_token == 'YOUR_BOT_TOKEN_HERE':
            print("⚠️ Telegram bot token not configured")
            return False

        message = self._format_grade_message(grade, subject)

        return self._send_message(user.telegram_id, message)

    def _format_grade_message(self, grade: Grade, subject: Subject) -> str:
        # Форматирует сообщение об оценке
        formatted_date = grade.date.strftime('%d.%m.%Y') if grade.date else date.today().strftime('%d.%m.%Y')

        message = f"📚 Новая оценка!\n\n"
        message += f"Предмет: {subject.name}\n"
        message += f"Оценка: {grade.grade}\n"
        message += f"Дата: {formatted_date}\n"

        if grade.comment:
            message += f"Комментарий: {grade.comment}"

        return message

    def _send_message(self, chat_id: str, message: str) -> bool:
        try:
            url = f'{self.base_url}/sendMessage'
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            return result.get('ok', False)

        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка отправки Telegram сообщения: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка при отправке в Telegram: {e}")
            return False

    def validate_telegram_id(self, telegram_id: str) -> bool:

        if not telegram_id:
            return False

        if telegram_id.startswith('@'):
            return len(telegram_id) > 1

        try:
            int(telegram_id)
            return True
        except ValueError:
            return False

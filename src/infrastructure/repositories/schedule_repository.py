from datetime import time
from domain.entities.schedule import Schedule
from domain.repositories.schedule_repository import IScheduleRepository
from infrastructure.database.connection import DatabaseConnection


class ScheduleRepository(IScheduleRepository):
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    def create(self, schedule: Schedule) -> Schedule:
        query = """
        INSERT INTO schedule (subject_id, day_of_week, time_start, time_end, classroom)
        VALUES (?, ?, ?, ?, ?)
        """
        schedule_id = self.db.execute_update(
            query,
            (schedule.subject_id, schedule.day_of_week, 
             schedule.time_start.strftime('%H:%M'), schedule.time_end.strftime('%H:%M'),
             schedule.classroom)
        )
        schedule.id = schedule_id
        return schedule
    
    def get_by_id(self, schedule_id: int) -> Schedule | None:
        query = "SELECT * FROM schedule WHERE id = ?"
        rows = self.db.execute_query(query, (schedule_id,))
        if rows:
            return self._row_to_schedule(rows[0])
        return None
    
    def get_all(self) -> list[Schedule]:
        query = "SELECT * FROM schedule ORDER BY day_of_week, time_start"
        rows = self.db.execute_query(query)
        return [self._row_to_schedule(row) for row in rows]
    
    def get_by_day(self, day_of_week: int) -> list[Schedule]:
        query = "SELECT * FROM schedule WHERE day_of_week = ? ORDER BY time_start"
        rows = self.db.execute_query(query, (day_of_week,))
        return [self._row_to_schedule(row) for row in rows]
    
    def get_by_subject(self, subject_id: int) -> list[Schedule]:
        query = "SELECT * FROM schedule WHERE subject_id = ? ORDER BY day_of_week, time_start"
        rows = self.db.execute_query(query, (subject_id,))
        return [self._row_to_schedule(row) for row in rows]
    
    def get_filtered(self, day_of_week: int = None, subject_id: int = None,
                    time_start: time = None) -> list[Schedule]:
        # Начинаем с базового запроса
        conditions = []
        params = []
        
        # Добавляем условие фильтрации по дню недели
        if day_of_week is not None:
            conditions.append("day_of_week = ?")
            params.append(day_of_week)
        
        # Добавляем условие фильтрации по предмету
        if subject_id is not None:
            conditions.append("subject_id = ?")
            params.append(subject_id)
        
        # Добавляем условие фильтрации по времени начала
        if time_start is not None:
            conditions.append("time_start >= ?")
            params.append(time_start.strftime('%H:%M'))
        
        # Формируем WHERE-часть запроса
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        
        # Выполняем запрос с динамическими условиями
        query = f"SELECT * FROM schedule{where_clause} ORDER BY day_of_week, time_start"
        rows = self.db.execute_query(query, params)
        return [self._row_to_schedule(row) for row in rows]
    
    def update(self, schedule: Schedule) -> Schedule:
        query = """
        UPDATE schedule 
        SET subject_id = ?, day_of_week = ?, time_start = ?, time_end = ?, classroom = ?
        WHERE id = ?
        """
        self.db.execute_update(
            query,
            (schedule.subject_id, schedule.day_of_week,
             schedule.time_start.strftime('%H:%M'), schedule.time_end.strftime('%H:%M'),
             schedule.classroom, schedule.id)
        )
        return schedule
    
    def delete(self, schedule_id: int) -> bool:
        query = "DELETE FROM schedule WHERE id = ?"
        self.db.execute_update(query, (schedule_id,))
        return True
    
    def _row_to_schedule(self, row) -> Schedule:
        return Schedule(
            id=row['id'],
            subject_id=row['subject_id'],
            day_of_week=row['day_of_week'],
            time_start=time.fromisoformat(row['time_start']),
            time_end=time.fromisoformat(row['time_end']),
            classroom=row['classroom']
        )

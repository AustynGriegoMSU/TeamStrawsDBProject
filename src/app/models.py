from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, role, record_id, username, first_name, last_name=None):
        self.role = role
        self.record_id = str(record_id)
        self.username = username
        self.first_name = first_name
        self.last_name = last_name or ""
        self.name = " ".join(part for part in (self.first_name, self.last_name) if part)

    def get_id(self):
        return f"{self.role}:{self.record_id}"

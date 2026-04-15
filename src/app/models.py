from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name, about, passwd):
        self.id = id
        self.name = name
        self.about = about
        self.passwd = passwd

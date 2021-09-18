from . import db
from . import datetime

class DL_Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(255), nullable=False, default='h5')
    is_used = db.Column(db.Boolean())
    upload_at = db.Column(db.DateTime(), default=datetime.now)
    upload_by = db.Column(db.String(255))
from . import FlaskForm
from . import datetime

from . import StringField, SubmitField, BooleanField, FileField
from . import DataRequired, Length, ValidationError

from app.models.dl_models import DL_Model

class DLModelsForm(FlaskForm):
    name = StringField('Model Name',
                           validators=[DataRequired(), Length(min=2, max=255)])
    is_used = BooleanField('Set as default Model?')
    file_model = FileField('Model File (.h5)')
    submit = SubmitField('Save')

    def validate_name(self, name):
        dl_model = DL_Model.query.filter_by(name=name.data).first()
        if dl_model and name.data == dl_model.name:
            raise ValidationError('That name is taken. Please choose a different one.')
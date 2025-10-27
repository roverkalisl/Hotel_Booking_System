from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('පරිශීලක නාමය', validators=[DataRequired()])
    password = PasswordField('මුරපදය', validators=[DataRequired()])
    remember = BooleanField('මතක තබා ගන්න')
    submit = SubmitField('පිවිසෙන්න')

class RegistrationForm(FlaskForm):
    username = StringField('පරිශීලක නාමය', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('ඊමේල්', validators=[DataRequired(), Email()])
    password = PasswordField('මුරපදය', validators=[DataRequired()])
    confirm_password = PasswordField('මුරපදය තහවුරු කරන්න', 
                                    validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('සම්පූර්ණ නම', validators=[DataRequired()])
    phone = StringField('දුරකථන අංකය', validators=[DataRequired()])
    user_type = SelectField('ගිණුමේ වර්ගය', 
                           choices=[('hotel_admin', 'හොටෙල් අයිතිකරු'), ('customer', 'ගනුදෙනුකරු')],
                           validators=[DataRequired()])
    submit = SubmitField('ලියාපදිංචි වන්න')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('මෙම පරිශීලක නාමය දැනටමත් භාවිතා කර ඇත.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('මෙම ඊමේල් ලිපිනය දැනටමත් භාවිතා කර ඇත.')

class HotelForm(FlaskForm):
    name = StringField('හොටෙල් නම', validators=[DataRequired()])
    location = StringField('ස්ථානය', validators=[DataRequired()])
    description = TextAreaField('විස්තරය')
    owner_name = StringField('හිමිකරුගේ නම', validators=[DataRequired()])
    owner_email = StringField('ඊමේල්', validators=[DataRequired(), Email()])
    contact_number = StringField('දුරකථන අංකය', validators=[DataRequired()])
    price_per_night = FloatField('රාත්‍රියක මිල', validators=[DataRequired()])
    total_rooms = IntegerField('මුළු කාමර ගණන', validators=[DataRequired()])
    amenities = TextAreaField('සුවිශේෂී සේවා')
    submit = SubmitField('හොටෙල් ලියාපදිංචි කරන්න')
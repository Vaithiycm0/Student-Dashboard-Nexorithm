from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, SubmitField,
    TextAreaField, IntegerField, SelectField, DateTimeLocalField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Optional, NumberRange, URL
)


class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    year = IntegerField('Academic Year', validators=[Optional(), NumberRange(min=1, max=5, message='Year must be between 1 and 5')])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register as Student')


class ProfileForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email Address', validators=[DataRequired(), Email(), Length(max=120)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    year = IntegerField('Academic Year', validators=[Optional(), NumberRange(min=1, max=5)])
    current_password = PasswordField('Current Password (only needed if changing password)')
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6, message='New password must be at least 6 characters long')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='New passwords must match')
    ])
    submit = SubmitField('Update Profile')


class CourseForm(FlaskForm):
    code = StringField('Course Code', validators=[DataRequired(), Length(min=2, max=20)])
    title = StringField('Course Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Course Description', validators=[Optional()])
    submit = SubmitField('Save Course')


class AssignmentForm(FlaskForm):
    course_id = SelectField('Course', coerce=int, validators=[DataRequired()])
    title = StringField('Assignment Title', validators=[DataRequired(), Length(min=3, max=200)])
    description = TextAreaField('Assignment Description', validators=[Optional()])
    deadline = DateTimeLocalField('Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField('Create Assignment')


class SubmissionForm(FlaskForm):
    link = StringField('Submission Link / URL', validators=[Optional(), Length(max=500)])
    notes = TextAreaField('Submission Notes / Text', validators=[Optional()])
    submit = SubmitField('Submit Assignment')


class ReviewForm(FlaskForm):
    status = SelectField('Review Status', choices=[
        ('reviewed', 'Mark as Reviewed'),
        ('submitted', 'Needs Re-submission / Keep Submitted')
    ], validators=[DataRequired()])
    remarks = TextAreaField('Faculty Feedback / Remarks', validators=[Optional()])
    submit = SubmitField('Save Review')

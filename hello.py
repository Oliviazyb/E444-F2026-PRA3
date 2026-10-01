import re

from datetime import datetime, timezone

from flask import (
    Flask, flash, redirect, render_template,
    request, session, url_for
)
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields import EmailField
from wtforms.validators import DataRequired, Email, ValidationError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-development-key-for-pra3'

bootstrap = Bootstrap(app)
moment = Moment(app)


class NameForm(FlaskForm):
    name = StringField(
        'What is your name?',
        validators=[DataRequired()]
    )

    email = EmailField(
        'What is your UofT Email address?',
        validators=[
            DataRequired()
        ],
        render_kw={
            'pattern': '.*[Uu][Tt][Oo][Rr][Oo][Nn][Tt][Oo].*',
            'oninvalid': (
                "this.setCustomValidity('');"
                "if (!this.validity.typeMismatch && "
                "this.validity.patternMismatch) {"
                "this.setCustomValidity("
                "'Please enter a UofT email address.');"
                "}"
            ),
            'oninput': "this.setCustomValidity('');"
        }
    )

    submit = SubmitField('Submit')

    def validate_email(self, field):
        if 'utoronto' not in field.data.lower():
            raise ValidationError(
                'Please enter a UofT email address.'
            )


@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()

    if form.validate_on_submit():
        old_name = session.get('name')
        old_email = session.get('email')

        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')

        if old_email is not None and old_email != form.email.data:
            flash('Looks like you have changed your email!')

        session['name'] = form.name.data
        session['email'] = form.email.data

        return redirect(url_for('chat_page'))

    return render_template(
        'index.html',
        form=form,
        name=session.get('name'),
        email=session.get('email'),
        current_time=datetime.now(timezone.utc)
    )
    
@app.route('/chat', methods=['GET'])
def chat_page():
    if not session.get('email'):
        return redirect(url_for('index'))

    return render_template(
        'chat.html',
        name=session.get('name'),
        email=session.get('email')
    )


@app.route('/chat', methods=['POST'])
def chat():
    if not session.get('email'):
        return {'reply': 'Please submit the home form first.'}, 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {'reply': 'Please send a JSON object.'}, 400

    message = data.get('message')

    if not isinstance(message, str) or not message.strip():
        return {'reply': 'Please enter a message.'}, 400

    message = message.strip()

    name_match = re.fullmatch(
        r'my name is\s+(.+)',
        message,
        flags=re.IGNORECASE
    )

    if name_match:
        remembered_name = name_match.group(1).strip().rstrip('.!').strip()

        if not remembered_name:
            reply = 'Please tell me a name.'
        elif len(remembered_name) > 100:
            reply = 'Please use a shorter name.'
        else:
            session['chat_name'] = remembered_name
            reply = f'Nice to meet you, {remembered_name}!'

    elif message.lower().rstrip('?.!') == 'what is my name':
        remembered_name = session.get('chat_name')

        if remembered_name:
            reply = f'Your name is {remembered_name}.'
        else:
            reply = "You haven't told me your name in this conversation yet."

    elif 'hello' in message.lower():
        reply = 'Hello!'

    else:
        reply = (
            "Try saying 'My name is Alice.' "
            "Then ask 'What is my name?'"
        )

    return {'reply': reply}


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)
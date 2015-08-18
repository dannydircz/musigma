
from flask import Flask, g, render_template, flash, redirect, url_for, abort
from flask.ext.bcrypt import check_password_hash, generate_password_hash
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user

from flask_mail import Mail

import config
import forms
import models

import app_email
from decorators import check_confirmed
from app_token import generate_confirmation_token, confirm_token




app = Flask(__name__)
app.config.from_object('config.BaseConfig')
app.secret_key = config.BaseConfig.SECRET_KEY
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'



@login_manager.user_loader
def user_loader(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """connect to db before each request."""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(reponse):
    """close the db connection after each request"""
    g.db.close()
    return reponse


@app.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():

        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            confirmed=False
        )
        user = models.User.get(models.User.email == form.email.data)
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        html = render_template('activate.html', confirm_url=confirm_url)
        subject = "Confirm new user: %s: %s" % (user.email, user.username)
        app_email.send_email("musigmaapp@gmail.com", subject, html)

        flash('A confirmation email has been sent to Danny via email.', 'success')
        return redirect(url_for('unconfirmed'))
    return render_template('register.html', form=form)

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
    user = models.User.select().order_by(models.User.id.desc()).get()
    if user.confirmed:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.confirmed = True
        user.save()
        flash('You have confirmed this account. Thanks!', 'success')
    return redirect(url_for('index'))

@app.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect(url_for("index"))
    flash('You account has not been confirmed!', 'error')
    return render_template('unconfirmed.html')


@app.route('/login', methods=('GET', 'POST'))
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password doesn't match!", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("Login Success.", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password doesn't match!", "error")
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have successfully been logged out.", "success")
    return redirect(url_for('index'))


@app.route('/new_post', methods=('GET', 'POST'))
@login_required
def post():
    form = forms.PostForm()
    if form.validate_on_submit():
        models.Post.create(user=g.user._get_current_object(),
                           content=form.content.data.strip())
        flash("Message posted.", "success")
        return redirect(url_for('stream'))
    return render_template('post.html', form=form)


@app.route('/stream')
@app.route('/stream/<username>')
@login_required
def stream(username=None):
    template = 'stream.html'
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username ** username).get()
        except models.DoesNotExist:
            abort(404)
        else:
            stream = user.posts.limit(100)
    else:
        stream = current_user.get_stream().limit(100)
        user = current_user
    if username:
        template = 'user_stream.html'
    return render_template(template, stream=stream, user=user)


@app.route('/new_contact', methods=('GET', 'POST'))
@login_required
def contact():
    form = forms.ContactForm()
    if form.validate_on_submit():
        models.Contact.create(user=g.user._get_current_object(),
                              name=form.name.data.strip(),
                              email=form.email.data.strip(),
                              number=form.number.data.strip(),
                              position=form.position.data.strip())
        flash("You have successfully created a contact", "success")
        return redirect(url_for('contactList'))
    return render_template('new_contact.html', form=form)


@app.route('/contact')
@login_required
def contactList(username=None):
    if username and username != current_user.username:
        try:
            user = models.User.select().where(models.User.username ** username).get()
        except models.DoesNotExist:
            abort(404)
        else:
            contactList = user.contact.limit(100)
    else:
        contactList = current_user.get_contactList().limit(100)
        user = current_user
    return render_template('contact.html', contactList=contactList, user=user)


@app.route('/post/<int:post_id>')
@login_required
def view_post(post_id):
    posts = models.Post.select().where(models.Post.id == post_id)
    if posts.count() == 0:
        abort(404)
    return render_template('stream.html', stream=posts)


@app.route('/delete_post/<int:post_id>')
@login_required
def delete_post(post_id):
    try:
        post = models.Post.select().where(models.Post.id == post_id).get()
    except models.DoesNotExist:
        abort(404)
    post.delete_instance()
    flash("This post has successfully been deleted.", "success")
    return redirect(url_for('stream', stream=stream))

@app.route('/delete_contact/<int:contact_id>')
@login_required
def delete_contact(contact_id):
    try:
        contact = models.Contact.select().where(models.Contact.id == contact_id).get()
    except models.DoesNotExist:
        abort(404)
    contact.delete_instance()
    flash("This contact has successfully been deleted.", "success")
    return redirect(url_for('contactList', contactList=contactList))


@app.route('/follow/<username>')
@login_required
def follow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.create(
                from_user=g.user._get_current_object(),
                to_user=to_user
            )
        except models.IntegrityError:
            pass
        else:
            flash("You're now following %s." % str(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    try:
        to_user = models.User.get(models.User.username ** username)
    except models.DoesNotExist:
        abort(404)
    else:
        try:
            models.Relationship.get(
                from_user=g.user._get_current_object(),
                to_user=to_user
            ).delete_instance()
        except models.IntegrityError:
            pass
        else:
            flash("You have unfollowed %s." % str(to_user.username), "success")
    return redirect(url_for('stream', username=to_user.username))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = forms.ChangePasswordForm()
    if form.validate_on_submit():
        user = models.User.get(models.User.email == form.email.data)
        if user:
            user.password = generate_password_hash(form.password.data)
            user.save()
            flash('Password successfully changed.', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Password change was unsuccessful.', 'error')
            return redirect(url_for('profile'))
    return render_template('profile.html', form=form)

@app.route('/docs')
@login_required
def docs():
    return render_template('docs.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')


@app.route('/transaction')
@login_required
def form():
    return render_template('transaction.html')
    #return render_template('404.html'), 404

@app.route('/')
@login_required
@check_confirmed
def index():
    return render_template('home.html')



if __name__ == '__main__':
    models.initialize()
    try:
        models.User.create_user(
            username="DDircz",
            email="dircz009@umn.edu",
            password="pacman13",
            admin=True,
            confirmed = True
        )
    except:
        pass
    app.run(debug=config.BaseConfig.DEBUG)

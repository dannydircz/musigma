from flask import Flask, g, render_template, flash, redirect, url_for, abort
from flask.ext.bcrypt import check_password_hash
from flask.ext.login import LoginManager, login_user, logout_user, login_required, current_user

import forms
import models

DEBUG = True

app = Flask(__name__)
app.secret_key = 'asdklakdnksalnd.232,ihsadnndn'

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
        flash("You have successfully registered.", "success")
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


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
        return redirect(url_for('index'))
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


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')


@app.route('/transaction')
@login_required
def transaction():
    pass


@app.route('/')
@login_required
def index():
    stream = models.Post.select().limit(100)
    return render_template('stream.html', stream=stream)


if __name__ == '__main__':
    models.initialize()
    app.run(debug=DEBUG)

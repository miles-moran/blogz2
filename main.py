import cgi

from flask import Flask, redirect, render_template, request, session

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz4:blogz4@localhost:8889/blogz4'
app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    blogs = db.relationship('Blog', backref="blog_owner") 
    comments = db.relationship('Comment', backref="comment_owner")
    settings = db.relationship('Setting', backref="setting_owner")  
    username = db.Column(db.String(120), unique=True)
    password = db.Column(db.String(120)) 

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    owner = db.Column(db.Integer, db.ForeignKey('user.id')) 
    comments = db.relationship('Comment', backref="blog_comment") 
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    photo = db.Column(db.String(1000))    

    def __init__(self, title, body, photo, owner):
        self.title = title
        self.body = body
        self.photo = photo
        self.owner = owner

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True) 
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))   
    blog = db.Column(db.Integer, db.ForeignKey('blog.id')) 
    body = db.Column(db.String(1000)) 

    def __init__(self, owner, blog, body):
        self.blog = blog
        self.body = body
        self.owner = owner

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.Integer, db.ForeignKey('user.id')) 
    color_scheme = db.Column(db.String(120))
    photo = db.Column(db.String(120))

    def __init__(self, color_scheme, photo, owner):
        self.color_scheme = color_scheme
        self.photo = photo
        self.owner = owner

@app.route('/create', methods=['POST', 'GET'])
def create():
    owner = User.query.filter_by(username=session['username']).first()
    blogs = Blog.query.all()
    users = User.query.all()
    comments = Comment.query.all()
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        if not title or not body:
            error = True
            return render_template('create.html', owner=owner, blogs=blogs, comments=comments, users=users, error=error)
        photo = request.form['photo']
        if not photo:
            photo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSrW8v2X1OC3ZVW0lv2w_KniOgVRR8BDhS3LFGlfR2GcuEtxNfl"
        blog = Blog(title, body, photo, owner.id) 
        db.session.add(blog)
        #comment_body = request.form['comment_body'] #comment is set to first and only post by root
        #comment = Comment(1, comment_body, owner)
        #db.session.add(comment)
        db.session.commit()
        return redirect("./?id="+ str(blog.id))
    else:
        return render_template('create.html', owner=owner, blogs=blogs, comments=comments, users=users)
 
@app.route('/', methods=['POST', 'GET'])
def main():
    owner = User.query.filter_by(username=session['username']).first()
    blogs = Blog.query.all()
    users = User.query.all()
    blog_query = request.args.get('id')
    user_query = request.args.get('user')
    if blog_query:
        blogs = [Blog.query.filter_by(id=int(blog_query)).first()] #THIS WONT WORK WITH NO ITEMS IN LIST
        comments = Comment.query.filter_by(blog=blog_query).all()
        if request.method == 'POST':
            body = request.form['comment']
            comment = Comment(owner.id, int(blog_query), body)
            db.session.add(comment)
            db.session.commit()
        return render_template("main.html", owner=owner, blogs=blogs, comments=comments, blog_query=blog_query, users=users)
    elif user_query: 
        user_query_object = User.query.filter_by(username=user_query).first()
        blogs = Blog.query.filter_by(owner=user_query_object.id).all()
        return render_template("main.html", owner=owner, blogs=blogs, user_query=user_query_object)
    return render_template("main.html", owner=owner, blogs=blogs, users=users)
    

@app.route('/register', methods=['POST', 'GET'])
def register():
    users = User.query.all()
    if session:
        del session['username']
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        username_error = False
        password_error = False
        confirm_error = False
        existing_username = False
        #errors begin
        #password error
        user_with_username = User.query.filter_by(username=username).first()
        if user_with_username:
            existing_username = True
        if len(password) < 3 or len(password) > 20:
            password_error = True
        for char in password:
            if char == " ":
                password_error = True
        #confirm error
        if password != confirm:
            confirm_error = True
        #username errors
        period_check = False
        at_check = False
        for char in username:
            if char == " ":
                username_error = True
            if char == ".":
                period_check = True
            if char == "@":
                at_check = True
        if period_check == False or at_check == False:
            username_error = True
        if username_error == False and password_error == False and confirm_error == False and existing_username == False:
            user = User(username, password)
            db.session.add(user)
            db.session.commit()
            default_setting = Setting("test", "https://www.sparklabs.com/forum/styles/comboot/theme/images/default_avatar.jpg", user.id)
            db.session.add(default_setting)
            db.session.commit()
            session['username'] = username
            return redirect('/create')
        else:
            return render_template('register.html', users=users, username = username, username_error = username_error, password_error = password_error, confirm_error = confirm_error, existing_username = existing_username)
    else:
        return render_template('register.html', users=users)
@app.route('/login', methods=['POST', 'GET'])
def login():
    users = User.query.all()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['username'] = username
            return redirect('/create')
        else: 
            return render_template('login.html', users=users, username=username, error=True)
    return render_template('login.html', users=users)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')

@app.before_request
def require_login():
    allowed_routes = ['login', 'register']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')

@app.route('/settings', methods=['POST', 'GET'])
def settings():
    owner = User.query.filter_by(username=session['username']).first()
    users = User.query.all()
    if request.method == 'POST':
        photo_change = request.form['photo_change']
        owner.settings[0].photo = photo_change
        db.session.commit()
    return render_template('settings.html', users=users, owner=owner)

@app.route('/about', methods=['POST', 'GET'])
def about():
    return render_template('about.html')
if __name__ == "__main__":
    app.run()

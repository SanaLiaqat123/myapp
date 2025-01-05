from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///video_platform.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_creator = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    hashtags = db.Column(db.String(200), nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    video_id = db.Column(db.Integer, db.ForeignKey('video.id'), nullable=False)

# Routes
@app.route('/')
def index():
    videos = Video.query.order_by(Video.id.desc()).all()
    return render_template('index.html', videos=videos)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        is_creator = 'is_creator' in request.form

        if User.query.filter_by(username=username).first():
            return "User already exists."

        user = User(username=username, is_creator=is_creator)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('signup.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        hashtags = request.form['hashtags']
        file_path = request.form['video_file']  # Simplified for demo purposes
        uploaded_by = request.form['uploaded_by']

        video = Video(title=title, description=description, hashtags=hashtags, file_path=file_path, uploaded_by=uploaded_by)
        db.session.add(video)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/video/<int:video_id>', methods=['GET', 'POST'])
def video_details(video_id):
    video = Video.query.get_or_404(video_id)
    if request.method == 'POST':
        content = request.form['comment']
        user_id = request.form['user_id']

        comment = Comment(content=content, user_id=user_id, video_id=video_id)
        db.session.add(comment)
        db.session.commit()
        
    comments = Comment.query.filter_by(video_id=video_id).all()
    return render_template('video.html', video=video, comments=comments)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q')
    videos = Video.query.filter(Video.title.contains(query) | Video.hashtags.contains(query)).all()
    return render_template('search.html', videos=videos)

# REST API for static content
@app.route('/api/videos', methods=['GET'])
def api_videos():
    videos = Video.query.all()
    return jsonify([{
        'id': video.id,
        'title': video.title,
        'description': video.description,
        'hashtags': video.hashtags,
        'file_path': video.file_path
    } for video in videos])

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

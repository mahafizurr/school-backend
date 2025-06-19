from flask import Flask, jsonify, request, session
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_api.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'cx0002nx'  # একটা ভালো গোপন key দিন
jwt = JWTManager(app)

db = SQLAlchemy(app)
CORS(app, supports_credentials=True)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(200))

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    roll = db.Column(db.Integer, unique=True)
    grade = db.Column(db.String(20))
    results = db.relationship('Result', backref='student', lazy=True)
    attendance = db.relationship('Attendance', backref='student', lazy=True)

class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100))
    mark = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(50))
    present = db.Column(db.Boolean)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))

@app.before_request
def create_tables():
    db.create_all()
    if not User.query.first():
        admin_user = User(username="admin", password_hash=generate_password_hash("admin123"))
        db.session.add(admin_user)
        db.session.commit()

def login_required(f):
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        token = create_access_token(identity=user.id)
        return jsonify({"access_token": token})
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out"})

@app.route('/api/students', methods=['GET'])
@jwt_required()
def get_students():
    current_user = get_jwt_identity()  # user_id
    students = Student.query.all()
    return jsonify([{ "id": s.id, "name": s.name, "age": s.age, "roll": s.roll, "grade": s.grade } for s in students])


@app.route('/api/students', methods=['POST'])
@jwt_required()
def add_student():
    data = request.json
    s = Student(
        name=data.get('name'),
        age=data.get('age'),
        roll=data.get('roll'),
        grade=data.get('grade')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"message": "Student added", "student": {
        "id": s.id,
        "name": s.name,
        "age": s.age,
        "roll": s.roll,
        "grade": s.grade
    }}), 201

@app.route('/api/results', methods=['GET'])
@jwt_required()
def get_results():
    results = Result.query.all()
    return jsonify([{
        "id": r.id,
        "subject": r.subject,
        "mark": r.mark,
        "student_id": r.student_id
    } for r in results])

@app.route('/api/results', methods=['POST'])
@jwt_required()
def add_result():
    data = request.json
    r = Result(
        subject=data.get('subject'),
        mark=data.get('mark'),
        student_id=data.get('student_id')
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"message": "Result added", "result": {
        "id": r.id,
        "subject": r.subject,
        "mark": r.mark,
        "student_id": r.student_id
    }}), 201

@app.route('/api/attendance', methods=['GET'])
@jwt_required()
def get_attendance():
    records = Attendance.query.all()
    return jsonify([{
        "id": a.id,
        "day": a.day,
        "present": a.present,
        "student_id": a.student_id
    } for a in records])

@app.route('/api/attendance', methods=['POST'])
@jwt_required()
def add_attendance():
    data = request.json
    a = Attendance(
        day=data.get('day'),
        present=data.get('present'),
        student_id=data.get('student_id')
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({"message": "Attendance added", "attendance": {
        "id": a.id,
        "day": a.day,
        "present": a.present,
        "student_id": a.student_id
    }}), 201

if __name__ == '__main__':
    app.run(debug=True)

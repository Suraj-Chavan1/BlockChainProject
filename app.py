from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # Import Flask-Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
from web3 import Web3

# Initialize Flask application
app = Flask(__name__)
app.config.from_object('config') # Load configuration from config.py
# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db) 

sender_address = "0xD066619974d601543CBb332dE75E8fb468e5cAFe"
sender_private_key = "0x3b864be47890df0fc1b134911a8f4983ae3b6ae357be6ee71bbd3270fc9b2854"
recipient_address = "0x5C431Af9ff60DbbaA67fc8d2Bc94B50F5d24B67e"

def transaction():
    # Connect to Ganache
    ganache_url = "http://127.0.0.1:7545"  # Ensure Ganache UI is running on this URL
    web3 = Web3(Web3.HTTPProvider(ganache_url))

    if not web3.is_connected():
        print("Failed to connect to Ganache. Ensure Ganache UI is running.")
        return

    # Define sender and recipient details
    sender_address = "0xD066619974d601543CBb332dE75E8fb468e5cAFe"
    sender_private_key = "0x3b864be47890df0fc1b134911a8f4983ae3b6ae357be6ee71bbd3270fc9b2854"
    recipient_address = "0x5C431Af9ff60DbbaA67fc8d2Bc94B50F5d24B67e"

    # Contract address (already deployed)
    contract_address = "0x5dCDbBba739d62c7c7d932caf361EB3d25e25F98"

    # Load ABI from file
    abi_file_path = "I:\\Blockchain\\edi5\\TransactionHandler_abi.json"  # Path to ABI file
    with open(abi_file_path, 'r') as file:
        contract_abi = json.load(file)

    # Load the deployed contract
    transaction_handler = web3.eth.contract(
        address=contract_address,
        abi=contract_abi
    )

    # Interact with the contract
    try:
        amount = web3.to_wei(0.1, 'ether')  # Amount to send (0.1 Ether)
        print(f"Sending {amount} Wei from {sender_address} to {recipient_address}...")

        # Build transaction
        transaction = transaction_handler.functions.makeTransaction(recipient_address).build_transaction({
            'from': sender_address,
            'value': amount,
            'gas': 3000000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': web3.eth.get_transaction_count(sender_address),
        })

        # Sign transaction with private key
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=sender_private_key)

        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction successful with hash: {tx_hash.hex()}")
        print(f"Transaction receipt: {tx_receipt}")
    except Exception as e:
        print(f"Error during transaction: {e}")

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'student'

class Exam(db.Model):
    __tablename__ = 'exams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    age_min = db.Column(db.Integer, nullable=False)
    age_max = db.Column(db.Integer, nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    eligible_colleges = db.Column(db.Text, nullable=True)
    mcqs = db.relationship('MCQ', backref='exam', lazy=True)
    start_time = db.Column(db.Time, nullable=True)  # Start time
    results_published = db.Column(db.Boolean, default=False)  # New field to track result publication

    # New fields
    date = db.Column(db.Date, nullable=True)  # Exam date
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes


class ExamRegistration(db.Model):
    __tablename__ = 'exam_registrations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    college_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    aadhaar_number = db.Column(db.String(12), nullable=False)
    age = db.Column(db.Integer, nullable=False)

class MCQ(db.Model):
    __tablename__ = 'mcqs'
    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(
        db.Integer,
        db.ForeignKey('exams.id', name='fk_mcqs_exam_id'),  # Explicitly named foreign key
        nullable=False
    )
    question = db.Column(db.String(255), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    option4 = db.Column(db.String(100), nullable=False)
    correct_answer = db.Column(db.String(100), nullable=False)


class Query(db.Model):
    __tablename__ = 'queries'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)  # Admin's response
    timestamp = db.Column(db.DateTime, default=db.func.now())

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    rank = db.Column(db.Integer, nullable=True)

    # Add relationships
    student = db.relationship('User', backref='results', lazy=True)
    exam = db.relationship('Exam', backref='results', lazy=True)


def register_user(username, role):
    nonce = web3.eth.get_transaction_count(sender_address)
    tx = contract.functions.registerUser(username, role).buildTransaction({
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': web3.to_wei('10', 'gwei'),
    })
    signed_tx = web3.eth.account.sign_transaction(tx, sender_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction hash: {web3.toHex(tx_hash)}")

# Function to add an exam
def add_exam(name, description, age_min, age_max, education_level, eligible_colleges, date, time_limit):
    nonce = web3.eth.get_transaction_count(sender_address)
    tx = contract.functions.addExam(name, description, age_min, age_max, education_level, eligible_colleges, date, time_limit).buildTransaction({
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': web3.toWei('10', 'gwei'),
    })
    signed_tx = web3.eth.account.sign_transaction(tx, sender_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction hash: {web3.toHex(tx_hash)}")

# Function to register for an exam
def register_for_exam(exam_id, name, college_name, address_detail, aadhaar_number, age):
    nonce = web3.eth.get_transaction_count(sender_address)
    tx = contract.functions.registerForExam(exam_id, name, college_name, address_detail, aadhaar_number, age).buildTransaction({
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': web3.toWei('10', 'gwei'),
    })
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Transaction hash: {web3.toHex(tx_hash)}")

# Function to get exam registrations
def get_exam_registrations(exam_id):
    registrations = contract.functions.getExamRegistrations(exam_id).call()
    for reg in registrations:
        print(f"Student: {reg[0]}, Name: {reg[2]}, College: {reg[3]}, Age: {reg[6]}")

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Choose a different one.', 'warning')
            return redirect(url_for('register'))
        
        user = User(username=username, password=password, role=role)
        transaction()
        db.session.add(user)
        db.session.commit()

        flash(f'{role.capitalize()} registered successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            session['role'] = user.role
            session['user_id'] = user.id  # Add user_id to session
            transaction()
            flash('Login successful!', 'success')
            return redirect(url_for(f'{user.role}_dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        exams = Exam.query.all()
        return render_template('admin_dashboard.html', exams=exams)
    flash('Access unauthorized. Please log in as an admin.', 'danger')
    return redirect(url_for('login'))

@app.route('/admin/add_exam', methods=['GET', 'POST'])
def add_exam():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        age_min = int(request.form['age_min'])
        age_max = int(request.form['age_max'])
        education_level = request.form['education_level']
        eligible_colleges = request.form['eligible_colleges']
        
        # Convert date string to Python date object
        date_str = request.form['date']
        exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()  # Parse to date
        
        time_limit = int(request.form['time_limit'])

        exam = Exam(
            name=name,
            description=description,
            age_min=age_min,
            age_max=age_max,
            education_level=education_level,
            eligible_colleges=eligible_colleges,
            date=exam_date,  # Use the parsed date object
            time_limit=time_limit
        )

        transaction()
        db.session.add(exam)
        db.session.commit()
        flash('Exam added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('add_exam.html')
@app.route('/take_exam/<int:exam_id>', methods=['GET', 'POST'])
def take_exam(exam_id):
    # Ensure user is logged in and is a student
    if 'role' not in session or session['role'] != 'student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    # Fetch the exam and validate its existence
    exam = Exam.query.get_or_404(exam_id)

    # Fetch current time for schedule validation
    current_time = datetime.now()
    exam_start_time = datetime.combine(exam.date, exam.start_time)
    exam_end_time = exam_start_time + timedelta(minutes=exam.time_limit)

    # Check if the exam is scheduled
    if not exam.date or current_time < exam_start_time:
        flash('The exam has not started yet.', 'danger')
        return redirect(url_for('student_dashboard'))

    # Check if the exam is within the allowed time range
    if current_time > exam_end_time:
        flash('The exam has ended.', 'danger')
        return redirect(url_for('student_dashboard'))

    # Check if the student is registered for the exam
    student_id = session['user_id']
    registration = ExamRegistration.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if not registration:
        flash('You are not registered for this exam.', 'danger')
        return redirect(url_for('student_dashboard'))

    # Check if the student has already attempted the exam
    existing_result = Result.query.filter_by(student_id=student_id, exam_id=exam_id).first()
    if existing_result:
        flash('You have already attempted this exam.', 'danger')
        return redirect(url_for('student_dashboard'))

    # Fetch the exam questions (MCQs)
    mcqs = MCQ.query.filter_by(exam_id=exam_id).all()

    # Handle POST request for submitting the exam
    if request.method == 'POST':
        # Check if the exam time limit has been exceeded
        exam_start_time_in_session = session.get('exam_start_time')
        if not exam_start_time_in_session:
            flash('Exam session not started properly. Please try again.', 'danger')
            return redirect(url_for('student_dashboard'))

        start_time = datetime.strptime(exam_start_time_in_session, '%Y-%m-%d %H:%M:%S')
        if current_time > start_time + timedelta(minutes=exam.time_limit):
            flash('Time is up! The exam is over.', 'danger')
            return redirect(url_for('student_dashboard'))

        # Calculate the score based on submitted answers
        answers = request.form
        score = 0
        for key, value in answers.items():
            mcq_id = int(key.split('_')[1])  # Assuming keys are in the format "mcq_<id>"
            mcq = MCQ.query.get(mcq_id)
            transaction()
            if mcq and mcq.correct_answer == value:
                score += 1

        # Save the exam result
        result = Result(student_id=student_id, exam_id=exam_id, score=score)
        db.session.add(result)
        db.session.commit()

        flash(f'You completed the exam! Your score is {score}.', 'success')
        return redirect(url_for('student_dashboard'))

    # Store the exam start time in the session
    session['exam_start_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')

    return render_template('take_exam.html', exam=exam, mcqs=mcqs)

@app.route('/admin/review_results/<int:exam_id>', methods=['GET', 'POST'])
def review_results(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    results = Result.query.filter_by(exam_id=exam_id).all()
    if request.method == 'POST':
        action = request.form['action']
        student_id = int(request.form['student_id'])
        result = Result.query.filter_by(student_id=student_id, exam_id=exam_id).first()

        if action == 'accept':
            result.status = 'accepted'
        elif action == 'reject':
            result.status = 'rejected'
        elif action == 'second_chance':
            result.status = 'second_chance'
            # Allow the student to retake the exam
            db.session.delete(result)

        db.session.commit()
        flash('Result updated successfully!', 'success')

    return render_template('review_results.html', results=results)


@app.route('/contact_admin', methods=['GET', 'POST'])
def contact_admin():
    if 'role' not in session or session['role'] != 'student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        message = request.form['message']
        query = Query(student_id=session['user_id'], message=message)
        db.session.add(query)
        db.session.commit()
        flash('Your query has been sent to the admin.', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('contact_admin.html')

@app.route('/view_results/<int:exam_id>')
def view_results(exam_id):
    if 'role' not in session or session['role'] != 'student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    if not exam.results_published:
        flash('Results for this exam are not yet published.', 'info')
        return redirect(url_for('student_dashboard'))

    student_id = session['user_id']
    student_result = Result.query.filter_by(student_id=student_id, exam_id=exam_id).first()

    rankings = (
        db.session.query(
            Result,
            User.username,
            ExamRegistration.aadhaar_number,
            ExamRegistration.college_name
        )
        .join(User, User.id == Result.student_id)
        .join(ExamRegistration, (ExamRegistration.student_id == Result.student_id) & (ExamRegistration.exam_id == exam_id))
        .filter(Result.exam_id == exam_id)
        .order_by(Result.score.desc())
        .all()
    )

    rank = next((idx + 1 for idx, (result, _, _, _) in enumerate(rankings) if result.student_id == student_id), None)

    return render_template(
        'view_results.html', 
        exam=exam, 
        student_result=student_result, 
        rankings=rankings, 
        rank=rank,
        enumerate=enumerate  # Pass enumerate to the template
    )

@app.route('/admin/edit_exam/<int:exam_id>', methods=['GET', 'POST'])
def edit_exam(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        exam.name = request.form['name']
        exam.description = request.form['description']
        exam.age_min = int(request.form['age_min'])
        exam.age_max = int(request.form['age_max'])
        exam.education_level = request.form['education_level']
        exam.eligible_colleges = request.form['eligible_colleges']
        exam.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        exam.time_limit = int(request.form['time_limit'])

        db.session.commit()
        flash('Exam details updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_exam.html', exam=exam)

# Route to delete an exam
@app.route('/admin/delete_exam/<int:exam_id>')
def delete_exam(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash('Exam deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

# Route to manage questions for an exam
@app.route('/admin/manage_questions/<int:exam_id>', methods=['GET', 'POST'])
def manage_questions(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_answer = request.form['correct_answer']

        mcq = MCQ(
            exam_id=exam_id,
            question=question,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_answer
        )
        db.session.add(mcq)
        db.session.commit()
        flash('Question added successfully!', 'success')

    mcqs = MCQ.query.filter_by(exam_id=exam_id).all()
    return render_template('manage_questions.html', exam=exam, mcqs=mcqs)
@app.route('/schedule_exam/<int:exam_id>', methods=['GET', 'POST'])
def schedule_exam(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        # Convert date and time strings to appropriate Python objects
        date_str = request.form['exam_date']  # Format: YYYY-MM-DD
        start_time_str = request.form['start_time']  # Format: HH:MM
        end_time_str = request.form['end_time']  # Format: HH:MM

        try:
            exam_date = datetime.strptime(date_str, '%Y-%m-%d').date()  # Convert to date object
            start_time = datetime.strptime(start_time_str, '%H:%M').time()  # Convert to time object
            end_time = datetime.strptime(end_time_str, '%H:%M').time()  # Convert to time object

            # Update the exam with the schedule
            exam.date = exam_date
            exam.start_time = start_time
            exam.end_time = end_time
            db.session.commit()
            flash('Exam schedule updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        except ValueError as e:
            flash(f'Invalid date or time format: {e}', 'danger')

    return render_template('schedule_exam.html', exam=exam)


@app.route('/publish_results/<int:exam_id>')
def publish_results(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    # Fetch the exam
    exam = Exam.query.get_or_404(exam_id)

    # Update the results_published flag
    exam.results_published = True
    db.session.commit()

    flash('Results published successfully!', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/view_queries', methods=['GET', 'POST'])
def view_queries():
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    queries = Query.query.filter(Query.response == None).all()  # Unanswered queries

    if request.method == 'POST':
        query_id = request.form['query_id']
        response = request.form['response']
        query = Query.query.get(query_id)
        if query:
            query.response = response
            db.session.commit()
            flash('Query responded successfully!', 'success')
        return redirect(url_for('view_queries'))

    return render_template('view_queries.html', queries=queries)

@app.route('/admin/set_mcqs/<int:exam_id>', methods=['GET', 'POST'])
def set_mcqs(exam_id):
    if 'role' not in session or session['role'] != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        question = request.form['question']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_answer = request.form['correct_answer']

        mcq = MCQ(
            exam_id=exam_id,
            question=question,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_answer=correct_answer
        )
        transaction()
        db.session.add(mcq)
        db.session.commit()
        flash('MCQ added successfully!', 'success')
        return redirect(url_for('set_mcqs', exam_id=exam_id))

    mcqs = MCQ.query.filter_by(exam_id=exam_id).all()
    return render_template('set_mcqs.html', exam=exam, mcqs=mcqs)

from datetime import datetime

@app.route('/student_dashboard')
def student_dashboard():
    if 'role' in session and session['role'] == 'student':
        student_id = session['user_id']
        exams = Exam.query.all()
        registrations = ExamRegistration.query.filter_by(student_id=student_id).all()

        # Fetch registered and attempted exams
        registered_exam_ids = {reg.exam_id for reg in registrations}
        attempted_exam_ids = {
            result.exam_id for result in Result.query.filter_by(student_id=student_id).all()
        }

        # Precompute exam statuses
        current_time = datetime.now()
        exam_statuses = {}
        for exam in exams:
            if exam.start_time is None:
                exam_statuses[exam.id] = 'invalid_time'
            else:
                exam_start = datetime.combine(exam.date, exam.start_time)
                if exam.id in attempted_exam_ids:
                    exam_statuses[exam.id] = 'submitted'
                elif current_time < exam_start:
                    exam_statuses[exam.id] = 'not_started'
                else:
                    exam_statuses[exam.id] = 'available'

        return render_template(
            'student_dashboard.html',
            exams=exams,
            registered_exam_ids=registered_exam_ids,
            exam_statuses=exam_statuses
        )
    flash('Access unauthorized. Please log in as a student.', 'danger')
    return redirect(url_for('login'))

@app.route('/register_exam/<int:exam_id>', methods=['GET', 'POST'])
def register_exam(exam_id):
    if 'role' not in session or session['role'] != 'student':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    exam = Exam.query.get_or_404(exam_id)

    if request.method == 'POST':
        name = request.form['name']
        college_name = request.form['college_name']
        address = request.form['address']
        aadhaar_number = request.form['aadhaar_number']
        age = int(request.form['age'])

        # Check eligibility
        if age < exam.age_min or age > exam.age_max:
            flash('You are not eligible for this exam due to age criteria.', 'danger')
            return redirect(url_for('register_exam', exam_id=exam_id))
        if exam.education_level != request.form['education_level']:
            flash('You are not eligible for this exam due to education criteria.', 'danger')
            return redirect(url_for('register_exam', exam_id=exam_id))
        if exam.eligible_colleges and college_name not in exam.eligible_colleges.split(','):
            flash('Your college is not eligible for this exam.', 'danger')
            return redirect(url_for('register_exam', exam_id=exam_id))

        registration = ExamRegistration(
            student_id=session['user_id'],
            exam_id=exam_id,
            name=name,
            college_name=college_name,
            address=address,
            aadhaar_number=aadhaar_number,
            age=age
        )
        db.session.add(registration)
        db.session.commit()  # Ensure changes are saved to the database
        flash('You have successfully registered for the exam!', 'success')
        return redirect(url_for('student_dashboard'))  # Redirect to refresh data

    return render_template('register_exam.html', exam=exam)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Run the application
if __name__ == '__main__':
    app.run(debug=True)


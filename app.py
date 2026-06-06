from flask import Flask,request,render_template,redirect,url_for,session,send_file
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
import os
from dotenv import load_dotenv
load_dotenv()
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from werkzeug.utils import secure_filename
app = Flask(__name__)

app.secret_key = os.getenv("FLASK_SECRET_KEY")

print("FROM EMAIL:", os.getenv("FROM_EMAIL"))
print("SENDGRID KEY EXISTS:", os.getenv("SENDGRID_API_KEY") is not None)

UPLOAD_FOLDER = 'uploads'
RESUME_FOLDER = os.path.join(UPLOAD_FOLDER,'resumes')
COVER_LETTER_FOLDER = os.path.join(UPLOAD_FOLDER,'cover_letters')



os.makedirs(RESUME_FOLDER, exist_ok=True)
os.makedirs(COVER_LETTER_FOLDER, exist_ok=True)

allowed_files = {'pdf','doc','docx'}

def allowed_file(filename):
    if not filename or "." not in filename:
        return False
    return filename.rsplit('.',1)[1].lower() in allowed_files
     

def get_file_extension(filename):
    return filename.rsplit(".", 1)[1].lower()


def build_interview_email(candidate,daycare,interview_date,interview_time,interview_location):
            email={
                  'to_email' : candidate['email'],
                   'subject' : "Interview Invitation",
                   'email_body' : f"""
            Hi {candidate['name']},

            Thank you for applying to {daycare['name']}.
            We would like to invite you for an interview.
            Date: {interview_date}
            Time: {interview_time}
            Location: {interview_location}
            
            Please reply to confirm if this time works for you.

            Thank you,
            {daycare['name']}"""
            }
            return email
def send_email_with_sendgrid(email):
    message = Mail(
        from_email=os.getenv("FROM_EMAIL"),
        to_emails=email["to_email"],
        subject=email["subject"],
        plain_text_content=email["email_body"]
    )

    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    response = sg.send(message)

    return response.status_code
def get_db():
    conn = sqlite3.connect('hiring_tracker.db')
    conn.row_factory=sqlite3.Row
    return conn

@app.route('/daycares',methods=['GET','POST'])
def daycares():
    if request.method == 'POST':
        name = request.form.get('name','').strip()
         
        conn=get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO daycare(name) VALUES(?)',(name,))
        conn.commit()
        conn.close()
    return render_template('daycare.html')

@app.route('/apply/<int:daycare_id>',methods=['GET','POST'])
def candidate_info(daycare_id):
    name=''
    email=''
    phone=''
    experience=''

    conn=get_db()
    cursor = conn.cursor()
    daycare_existence = cursor.execute('SELECT * FROM daycare WHERE id=?',(daycare_id,)).fetchone()
    if not daycare_existence:
        conn.close()
        return 'No daycare exists',404
        
    errors=[]
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        name_check= name.replace(" ","").replace("-","").replace("'","")   #removed all the spaces and hyphens
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        clean_phone= phone.replace('(','').replace(')','').replace('-','').replace(' ','')
        classification = request.form.get('level','').strip()
        experience = request.form.get('experience','').strip()
        resume = request.files.get('resume')    #here default value is NONE.
        cover_letter = request.files.get('cover_letter')   # here default value is None becoz we cant use empty string for files
        
        
        if not name:
            errors.append('Name required')
        elif not name_check.isalpha():    # check if its only alphabets
            errors.append('Please type valid name')
        if not email or '@' not in email:
            errors.append('Please enter valid email')
        elif ' ' in email:
            errors.append('Email cannot contain spaces')
        elif email.count('@') !=1:
            errors.append('Please enter valid email.')
        else:
            local_part,domain=email.split('@')   #unpacking now local_part=abc123 , domain=gmail.com
            
            if not local_part:
                errors.append('Please enter a valid email.')
            elif not domain:
                errors.append('Please enter a valid email')
            elif '.' not in domain:
                errors.append('Please enter a valid email')
        if not phone:
            errors.append('Please enter valid Phone number')
        elif not clean_phone.isdigit():
            errors.append('Phone must conatain only numbers')
        elif len(clean_phone) !=10:
            errors.append('Phone must be 10 digists')
        if not classification:
            errors.append('Please enter ECE classification')
        if not experience:
            errors.append('Please write the age group you worked with before')
        if not resume or resume.filename == "":
            errors.append('Please attach resume.')
        elif not allowed_file(resume.filename):
            errors.append('File not allowed !!. Upload pdf,doc,docx files.')
        if cover_letter and cover_letter.filename != '':   #becoz cover letter is optional
            if not allowed_file(cover_letter.filename):
             errors.append('File not allowed. Upload pdf,doc,docx files.')
        
        
        if not errors:
            cursor.execute('INSERT INTO candidates(daycare_id,name,email,phone,classification,experience,resume_path,cover_letter_path) VALUES(?,?,?,?,?,?,?,?)',(daycare_id,name,email,phone,classification,experience,None,None))
            
            candidate_id = cursor.lastrowid
            original_resume_name = secure_filename(resume.filename)
            resume_extension = get_file_extension(original_resume_name)
            resume_filename = f"candidate_{candidate_id}_resume.{resume_extension}"
            resume_path = os.path.join(RESUME_FOLDER, resume_filename)

            resume.save(resume_path)

            cover_letter_path = None

            # Save cover letter only if uploaded
            if cover_letter and cover_letter.filename != "":
                original_cover_name = secure_filename(cover_letter.filename)
                cover_extension = get_file_extension(original_cover_name)
                cover_filename = f"candidate_{candidate_id}_cover_letter.{cover_extension}"
                cover_letter_path = os.path.join(COVER_LETTER_FOLDER, cover_filename)

                cover_letter.save(cover_letter_path)
            # Update candidate row with file paths
            cursor.execute(
                """
                UPDATE candidates
                SET resume_path = ?, cover_letter_path = ?
                WHERE id = ?
                """,
                (resume_path, cover_letter_path, candidate_id)
            )

            conn.commit()
            conn.close()
            
            
            return redirect(url_for('success_message'))
            
        
    conn.close()
    return render_template('candidate_info.html',errors=errors,name=name,phone=phone,email=email,experience=experience)

@app.route('/success_message')
def success_message():

    return render_template('sucess_message.html')

@app.route('/admin/daycares/<int:daycare_id>/create-user', methods=['GET','POST'])
def registration_page(daycare_id):
    conn = get_db()
    cursor = conn.cursor()
    check_daycare = cursor.execute('SELECT * FROM daycare WHERE id=?',(daycare_id,)).fetchone()
    if check_daycare is None:
        return 'No daycare found.'
    
    errors = []
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        password = request.form.get('password','').strip()
        role = request.form.get('role','').strip()
        
        if not name:
            errors.append('Name required.')
        if not email or '@' not in email:
            errors.append('email required.')
        if not password:
            errors.append('password required.')
        
        if not role:
            errors.append('role required.')
        
        
        if not errors:
            password_hash= generate_password_hash(password)
            
            cursor.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',(name,email,password_hash,role))
            
            new_user_id = cursor.lastrowid   # ID got from the last person saved
            cursor.execute('INSERT INTO daycare_membership(daycare_id,user_id) VALUES(?,?)',(daycare_id,new_user_id))
            
        
            conn.commit()
            conn.close()
    return render_template('register.html',errors=errors,daycare=check_daycare)

@app.route('/login',methods=['GET','POST'])
def login():
    
    errors=[]
    if request.method == 'POST':
      email = request.form.get('email','').strip().lower()
      password = request.form.get('password','')

      if not email or '@' not in email:
          errors.append('invalid email')
      if not password:
          errors.append('password required')
      
      if not errors:
        conn = get_db()
        cursor = conn.cursor()
        
        user = cursor.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        if user is None:
            conn.close()
            errors.append('Invalid email or password.')
        
        else:
            password_check=check_password_hash(user['password_hash'],password)
            if not password_check:
              errors.append('Invalid email or password.')
              conn.close()
            else:
             membership_check = cursor.execute('SELECT * FROM daycare_membership WHERE user_id=?',(user['id'],)).fetchone()
             if not membership_check:
                 conn.close()
                 return 'access denied'
             session['user_id']= user['id'] 
             session['role'] =user['role'] 
        
             conn.close()
             return redirect(url_for('director_dashboard',daycare_id=membership_check['daycare_id']))
    return render_template('login.html', errors=errors)

@app.route('/director_dashboard/<int:daycare_id>',methods=['GET','POST'])
def director_dashboard(daycare_id):

    user_id =session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    conn=get_db()
    cursor=conn.cursor()
    daycare_existence = cursor.execute('SELECT * FROM daycare WHERE id=?',(daycare_id,)).fetchone()
    if daycare_existence is None:
        conn.close()
        return 'No daycare found', 404
    membership_check =cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id=? AND user_id=?',(daycare_id,user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access Denied',403
    document_filter=request.args.get('document_filter','all')
     
    if document_filter=='complete':   
        applications=cursor.execute('SELECT * FROM candidates WHERE daycare_id=? AND first_aid_cpr_status=? AND police_check_status=? AND child_abuse_check_status=? AND status =? ORDER BY created_at DESC',(daycare_id,'available','available','available','interviewed')).fetchall()
    elif document_filter=='pending':
        applications=cursor.execute('SELECT * FROM candidates WHERE daycare_id=? AND status=? AND(first_aid_cpr_status !=? OR police_check_status !=? OR child_abuse_check_status !=? ) ORDER BY created_at DESC',(daycare_id,'interviewed','available','available','available')).fetchall()
    else:
        document_filter= 'all'
        applications=cursor.execute('''SELECT * FROM candidates WHERE daycare_id=? ORDER BY created_at DESC''', (daycare_id,) ).fetchall()
    
    conn.close()
    return render_template('director_dashboard.html',applications=applications,daycare_existence=daycare_existence,document_filter=document_filter,daycare_id=daycare_id)
          
@app.route('/view_resume/<int:candidate_id>')
def view_resume(candidate_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    conn = get_db()
    cursor=conn.cursor()
    candidate = cursor.execute('SELECT * FROM candidates WHERE id=?',(candidate_id,)).fetchone()
    if candidate is None:
        return 'No candidate exists.',404
    membership_check= cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id =? AND user_id=?',(candidate['daycare_id'],user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access denied',403
    resume_path = candidate['resume_path']
    
    conn.close()
    if not resume_path or not os.path.exists(resume_path):    #check of resume exists
        return 'Resume file not found', 404
    return send_file(resume_path) 
    

@app.route('/view_coverletter/<int:candidate_id>')
def view_coverletter(candidate_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    conn = get_db()
    cursor=conn.cursor()
    candidate = cursor.execute('SELECT * FROM candidates WHERE id=?',(candidate_id,)).fetchone()
    if candidate is None:
        return 'No candidate exists.',404
    membership_check= cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id =? AND user_id=?',(candidate['daycare_id'],user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access denied',403
    
    cover_letter_path =candidate['cover_letter_path']
    conn.close()
    if not cover_letter_path or not os.path.exists(cover_letter_path):
        return 'Resume file not found', 404
    return send_file(cover_letter_path) 

@app.route('/viewdetails_2/<int:candidate_id>',methods=['GET','POST'])
def viewdetails_2(candidate_id):
    
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    print("ROUTE HIT:", request.method)
    conn = get_db()
    cursor=conn.cursor()
    candidate = cursor.execute('SELECT * FROM candidates WHERE id=?',(candidate_id,)).fetchone()
    
    if candidate is None:
        conn.close()
        return 'No candidate exists.',404
    candidate_email = (candidate['email'] or '').strip()
    membership_check= cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id =? AND user_id=?',(candidate['daycare_id'],user_id)).fetchone()
    if not membership_check:
         conn.close()
         return 'Access denied',403
    
    if request.method =='POST':
        allowed_status=['shortlisted','interview_scheduled','interviewed','rejected','selected']
        
        new_status = request.form.get('status','').strip()
        if new_status not in allowed_status:
            conn.close()
            return 'not allowed status',400
        
        cursor.execute('''UPDATE candidates SET status=? WHERE id =? AND daycare_id=?''',(new_status,candidate['id'],candidate['daycare_id']) )
        conn.commit()
        conn.close()
        return redirect(url_for('viewdetails_2', candidate_id=candidate_id))
    conn.close()
    return render_template('viewdetails_2.html',candidate=candidate)

@app.route('/interview_setup/<int:candidate_id>',methods=['GET','POST'])
def interview_setup(candidate_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    conn = get_db()
    cursor=conn.cursor()
    candidate = cursor.execute('SELECT * FROM candidates WHERE id=?',(candidate_id,)).fetchone()
    if candidate is None:
        conn.close()
        return 'No candidate exists.',404
    candidate_email = (candidate['email'] or '').strip()
    membership_check= cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id =? AND user_id=?',(candidate['daycare_id'],user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access denied',403
    errors=[]
    if request.method =='POST':
        interview_date = request.form.get('interview_date','').strip()
        interview_time = request.form.get('interview_time','').strip()
        interview_location = request.form.get('interview_location','').strip()
        
        if not interview_date:
            errors.append('Interview date required.')
        if not interview_time:
            errors.append('Interview time required.')
        if not interview_location:
            errors.append('Interview Location required.')
        if not candidate_email:
            errors.append('Candidate email is missing. Cannot send interview email.')
        if not errors:
            interview_email_sent_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            daycare = cursor.execute( 'SELECT * FROM daycare WHERE id=?', (candidate['daycare_id'],)).fetchone()
            if daycare is None:
             conn.close()
             return 'Daycare not found.', 404

            email= build_interview_email(candidate, daycare, interview_date, interview_time,interview_location)
            print("To:", email["to_email"])
            print("Subject:", email["subject"])
            print(email["email_body"])
            try:
               status_code = send_email_with_sendgrid(email)
               if status_code < 200 or status_code >= 300:
                 errors.append("Email could not be sent. Please try again.")
                 conn.close()
                 return render_template(
                    'interview_setup.html',candidate=candidate,errors=errors)
            
            except Exception as e:
               errors.append("Email could not be sent. Please try again.")
               print("SENDGRID ERROR:", e)
               conn.close()
               return render_template( 'interview_setup.html',candidate=candidate,errors=errors)
            
            cursor.execute('''UPDATE candidates SET interview_date=?,interview_time=?,interview_location=?,interview_email_sent_at=?,status=? WHERE id=?''',(interview_date,interview_time,interview_location,interview_email_sent_at,'interview_scheduled',candidate['id']))
            conn.commit()
            conn.close()
            return redirect(url_for('viewdetails_2',candidate_id=candidate['id']))
    return render_template('interview_setup.html',candidate=candidate,errors=errors)
@app.route('/post_interview_details/<int:candidate_id>',methods=['GET','POST'])
def post_interview_details(candidate_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    
    conn = get_db()
    cursor=conn.cursor()
    candidate = cursor.execute('SELECT * FROM candidates WHERE id=?',(candidate_id,)).fetchone()
    if candidate is None:
        conn.close()
        return 'No candidate exists.',404
    membership_check= cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id =? AND user_id=?',(candidate['daycare_id'],user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access denied',403
    
    if candidate['interview_date'] is None:
        conn.close()
        return render_template('schedule_interview_required.html',candidate=candidate)
    
    if request.method=='POST':
        form_type = request.form.get("form_type")
        if form_type != 'interview_review' and form_type != 'hiring_checklist':
            conn.close()
            return 'invalid form action',400
        elif form_type == 'interview_review':
          notes = request.form.get('notes','').strip()
          rating = request.form.get('rating','').strip()
          
          allowed_ratings=['1','2','3','4','5']
          if rating not in allowed_ratings:
            conn.close()
            return 'Invalid rating', 400
          cursor.execute('UPDATE candidates SET interview_notes=?,interview_rating=?,status=? WHERE id=? AND daycare_id=?',(notes,rating,'interviewed',candidate['id'],candidate['daycare_id']))
          conn.commit()
          conn.close()
          return redirect(url_for('post_interview_details', candidate_id=candidate_id))

        elif form_type == 'hiring_checklist': 
          first_aid_cpr= request.form.get('first_aid_cpr','').strip()
          police_clearance = request.form.get('police_clearance','').strip()
          child_abuse_registry = request.form.get('child_abuse_registry','').strip()
          
          allowed_checklist_values=['available','not_available','pending','requested']
          if first_aid_cpr not in allowed_checklist_values:
              conn.close()
              return 'Invalid First Aid/CPR status',400
          if police_clearance not in allowed_checklist_values:
              conn.close()
              return 'Invalid Police Check status',400
          if child_abuse_registry not in allowed_checklist_values:
              conn.close()
              return 'Invalid Child Abuse Registry status',400
          cursor.execute('UPDATE candidates SET first_aid_cpr_status=?,police_check_status=?,child_abuse_check_status=?  WHERE id=? AND daycare_id=?',(first_aid_cpr,police_clearance,child_abuse_registry,candidate['id'],candidate['daycare_id']))
          conn.commit()
          conn.close()
          return redirect(url_for('post_interview_details', candidate_id=candidate_id))

    conn.close()
    return render_template('post_interview_details.html',candidate=candidate)
@app.route('/interviewed_candidates/<int:daycare_id>')
def interviewed_candidates(daycare_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect('/login')
    conn=get_db()
    cursor=conn.cursor()
    daycare_existence = cursor.execute('SELECT * FROM daycare WHERE id=?',(daycare_id,)).fetchone()
    if daycare_existence is None:
        conn.close()
        return 'No daycare found', 404
    membership_check =cursor.execute('SELECT * FROM daycare_membership WHERE daycare_id=? AND user_id=?',(daycare_id,user_id)).fetchone()
    if not membership_check:
        conn.close()
        return 'Access Denied',403
    
    checklist_lables=  {'available':'Available',     
            'not_available' :'Not available',
            'not_requested':'Not Requested',
            'pending':'Pending',
            'requested':'requested'}
    candidates_interviewed = cursor.execute('SELECT * FROM candidates WHERE status=? AND daycare_id=?',('interviewed',daycare_id)).fetchall()
    conn.close()
    return render_template('interviewed_candidates.html',candidates_interviewed=candidates_interviewed,checklist_lables=checklist_lables,daycare_id=daycare_id)
    
@app.route('/logout')
def logout():
    session.pop('user_id',None)
    return redirect(url_for('login'))

if __name__ == "__main__":
   debug_mode = os.getenv("FLASK_DEBUG", "False") == "True"
   app.run(debug=debug_mode)
   
                           
                                                             
        



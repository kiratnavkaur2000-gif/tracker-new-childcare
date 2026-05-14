from flask import Flask,request,render_template,redirect,url_for
import sqlite3
import os
from werkzeug.utils import secure_filename
app = Flask(__name__)

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
def home(daycare_id):
    name=''
    errors=[]
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        clean_phone= phone.replace('(','').replace(')','').replace('-','').replace(' ','')
        classification = request.form.get('level','').strip()
        experience = request.form.get('experience','').strip()
        resume = request.files.get('resume')    #here default value is NONE.
        cover_letter = request.files.get('cover_letter')   # here default value is None becoz we cant use empty string for files
        
        print("FILES:", request.files)
        print("RESUME:", resume)
        print("RESUME FILENAME:", resume.filename if resume else None)
        if not name:
            errors.append('Name required')
        if not email or '@' not in email:
            errors.append('Please enter valid email')
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
            conn=get_db()
            cursor = conn.cursor()
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
            
        

    return render_template('candidate_info.html',errors=errors,name=name)

@app.route('/success_message')
def success_message():
    return render_template('sucess_message.html')
if __name__ == "__main__":
    app.run(debug=True)
                                                             
        



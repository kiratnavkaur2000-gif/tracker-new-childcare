from flask import Flask,request,render_template,redirect,url_for
import sqlite3
app = Flask(__name__)

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

@app.route('/apply/daycare_id',methods=['GET','POST'])
def home():
    name=''
    errors=[]
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        clean_phone= phone.replace('(','').replace(')','').replace('-','').replace(' ','')
        classification = request.form.get('level','').strip()
        experience = request.form.get('experience','').strip()
        

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
        
        if not errors:
            conn=get_db()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO candidates(name,email,phone,classification,experience,) VALUES(?,?,?,?,?)',(name,email,phone,classification,experience))
            conn.commit()
            conn.close()
            return redirect(url_for('success_message'))
            
        

    return render_template('candidate_info.html',errors=errors,name=name)

@app.route('/success_message')
def success_message():
    return render_template('sucess_message.html')
if __name__ == "__main__":
    app.run(debug=True)
                                                             
        



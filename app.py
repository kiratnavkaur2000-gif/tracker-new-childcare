from flask import Flask,request,render_template
app = Flask(__name__)

@app.route('/',methods=['GET','POST'])
def home():
    name=''
    errors=[]
    if request.method == 'POST':
        name = request.form.get('name','').strip()
        email = request.form.get('email','').strip()
        phone = request.form.get('phone','').strip()
        clean_phone= phone.replace('(','').replace(')','').replace('-','').replace(' ','')
        ece_level = request.form.get('level','').strip()
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
        if not ece_level:
            errors.append('Please enter ECE classification')
        if not experience:
            errors.append('Please write the age group you worked with before')
        

    return render_template('candidate_info.html',errors=errors,name=name)
if __name__ == "__main__":
    app.run(debug=True)
                                                             
        



from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "flash_message"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'plantvision'
mysql = MySQL(app)

############################
#registration logic
############################
@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur.execute("SELECT password FROM users WHERE email = %s", (email,))
        check_password = cur.fetchone()
        cur.close()

        if role is None:
            flash("Invalid user ID.")
            return redirect(url_for('login_page'))
        
        # Verify password
        if check_password and bcrypt.check_password_hash(check_password[0], password):
            session['user_id'] = id
            session['role'] = role[0]
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login_page'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['new-password']
        retype_password = request.form['retype-password']
        
        if password != retype_password:
            flash("Passwords do not match!")
            return redirect(url_for('register'))
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            flash("Email is already registered!")
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed_password))
        mysql.connection.commit()
        cur.close()
        
        flash("Registration successful!")
        return redirect(url_for('profileinfo'))
    
    return render_template('Register.html')

@app.route('/profile-info', methods=['GET', 'POST'])
def profileinfo():
    if request.method == 'POST':
        description = request.form['description']
        usertype = request.form['usertype']
        state = request.form['state']
        contact_number = request.form['contact_number']
        instagram = request.form['instagram']
        facebook = request.form['facebook']
        
        user_id = session.get('user_id')
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO profiles (user_id, description, usertype, state, contact_number, instagram, facebook)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            description = VALUES(description),
            usertype = VALUES(usertype),
            state = VALUES(state),
            contact_number = VALUES(contact_number),
            instagram = VALUES(instagram),
            facebook = VALUES(facebook)
        """, (user_id, description, usertype, state, contact_number, instagram, facebook))
        mysql.connection.commit()
        cur.close()
        
        flash("Profile updated successfully!")
        return redirect(url_for('index'))
    
    return render_template('profile-info.html')

############################
#main website
############################
@app.route('/index')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/identify')
def identify():
    return render_template('identify.html')

@app.route('/viewplant')
def viewplant():
    return render_template('view-plant.html')

@app.route('/discover')
def discover():
    return render_template('discover.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)

import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = "flash_message"
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'plantvision'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
mysql = MySQL(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#####################################################################
# Login Page
#####################################################################
@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()

        if user is None:
            flash("Account not registered!", "danger")
            return redirect(url_for('login'))

        user_id, name, stored_password = user

        if password == stored_password:
            session['user_id'] = user_id
            session['username'] = name  # Store the username in the session
            return redirect(url_for('index'))
        else:
            flash("email/password unmatch", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

#####################################################################
# Register Page
#####################################################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['new-password']
        retype_password = request.form['retype-password']
        description = request.form['description']
        usertype = request.form['usertype']
        state = request.form['state']
        contact_number = request.form['contact_number']
        instagram = request.form['instagram']
        facebook = request.form['facebook']
        
        if password != retype_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('register'))
        
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        if user:
            flash("Email is already registered!", "danger")
            return redirect(url_for('register'))
        
        cur.execute("""
            INSERT INTO users (name, email, password, description, usertype, state, contact_number, instagram, facebook)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, email, password, description, usertype, state, contact_number, instagram, facebook))
        mysql.connection.commit()
        cur.close()
        
        flash("Registration successful!", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

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
            UPDATE users SET description = %s, usertype = %s, state = %s, contact_number = %s, instagram = %s, facebook = %s
            WHERE id = %s
        """, (description, usertype, state, contact_number, instagram, facebook, user_id))
        mysql.connection.commit()
        cur.close()
        
        flash("Profile updated successfully!", "success")
        return redirect(url_for('index'))
    
    return render_template('profile-info.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

#####################################################################
# Index Page
#####################################################################
@app.route('/index')
def index():
    username = session.get('username')
    user_id = session.get('user_id')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT id, gallery_name, plant_description, gallery_tags FROM gallery WHERE user_id = %s", (user_id,))
    plants = cur.fetchall()
    cur.close()

    return render_template('index.html', username=username, plants=plants)

#####################################################################
# Gallery Page
#####################################################################
@app.route('/gallery/<int:gallery_id>')
def gallery(gallery_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT gallery_name, plant_description, gallery_tags FROM gallery WHERE id = %s", (gallery_id,))
    gallery = cur.fetchone()
    cur.execute("SELECT id, image_path, description FROM images WHERE gallery_id = %s", (gallery_id,))
    images = cur.fetchall()
    cur.close()

    if gallery is None:
        flash("Gallery not found!", "danger")
        return redirect(url_for('index'))

    gallery_name, plant_description, gallery_tags = gallery

    return render_template('gallery.html', gallery_id=gallery_id, gallery_name=gallery_name, plant_description=plant_description, gallery_tags=gallery_tags, images=images)

@app.route('/edit-gallery/<int:gallery_id>', methods=['POST'])
def edit_gallery(gallery_id):
    if request.method == 'POST':
        gallery_name = request.form['gallery_name']
        plant_description = request.form['plant_description']
        gallery_tags = request.form['gallery_tags']

        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE gallery SET gallery_name = %s, plant_description = %s, gallery_tags = %s
            WHERE id = %s
        """, (gallery_name, plant_description, gallery_tags, gallery_id))
        mysql.connection.commit()
        cur.close()
        
        return jsonify(success=True)

@app.route('/add-image/<int:gallery_id>', methods=['POST'])
def add_image(gallery_id):
    if request.method == 'POST':
        image = request.files['plant_image']
        description = request.form['plant_description']
        filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(filename)
        
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO images (gallery_id, image_path, description)
            VALUES (%s, %s, %s)
        """, (gallery_id, filename, description))
        mysql.connection.commit()
        image_id = cur.lastrowid
        cur.close()
        
        return jsonify(success=True, image_path=url_for('uploaded_file', filename=image.filename), image_id=image_id)

@app.route('/delete-image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    if request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT image_path FROM images WHERE id = %s", (image_id,))
        image_path = cur.fetchone()[0]
        cur.execute("DELETE FROM images WHERE id = %s", (image_id,))
        mysql.connection.commit()
        cur.close()

        if os.path.exists(image_path):
            os.remove(image_path)

        return jsonify(success=True, image_path=image_path)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

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

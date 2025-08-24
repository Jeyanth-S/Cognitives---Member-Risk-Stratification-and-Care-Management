from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # ⚠️ Change this to a strong random key for production!

# Dummy users for demo (replace with DB + hashing later)
users = {'caremanager': 'password123', 'admin': 'adminpass'}

# Sample member data
sample_members = [
    {
        'member_id': f'MID{n:04d}',
        'name': f'Member {n}',
        'risk_tier': 'High' if n % 5 == 0 else 'Medium' if n % 3 == 0 else 'Low',
        'risk_30': f'{80 - n % 60}%',
        'risk_60': f'{70 - n % 60}%',
        'risk_90': f'{60 - n % 60}%',
        'avatar': 'default.png'
    }
    for n in range(1, 101)
]

@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('home'))
    error = None
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['user'] = username
            return redirect(url_for('home'))
        else:
            error = "Invalid username or password."
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/member_data')
def member_data():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    page = int(request.args.get('page', 1))
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    members = sample_members[start:end]
    has_more = end < len(sample_members)

    return render_template(
        'member_data.html',
        members=members,
        page=page,
        has_more=has_more
    )

@app.route('/predict')
def predict():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    # Placeholder
    return render_template("predict.html")

if __name__ == "__main__":
    app.run(debug=True)

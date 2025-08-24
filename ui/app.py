from flask import Flask, render_template, request, redirect, url_for, session
import duckdb

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # ⚠️ Change this in production

# Dummy users (replace with DB + hashing later)
users = {'caremanager': 'password123', 'admin': 'adminpass'}

# Connect to DuckDB (⚠️ update this path to your actual .duckdb file)
con = duckdb.connect(
    r"C:\Users\kesh2\OneDrive\Documents\Cognitives---Member-Risk-Stratification-and-Care-Management\pipeline\db\synpuf.duckdb",
    read_only=True
)

# Columns to display from combined_features
COLUMNS = [
    "DESYNPUF_ID", "BENE_BIRTH_DT",
    "SP_ALZHDMTA", "SP_CHF", "SP_CHRNKIDN", "SP_CNCR", "SP_COPD",
    "SP_DEPRESSN", "SP_DIABETES", "SP_ISCHMCHT", "SP_OSTEOPRS",
    "SP_RA_OA", "SP_STRKETIA",
    "chronic_count_2008", "chronic_count_2009", "chronic_count_2010",
    "total_visits", "total_amount"
]

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return redirect(url_for('home'))

# ------------------- LOGIN -------------------
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

# ------------------- HOME -------------------
@app.route('/home')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('home.html', user=session.get('user'))

# ------------------- MEMBERS -------------------
@app.route('/members')
def members():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bene_id = request.args.get("bene_id", "").strip()
    page = int(request.args.get("page", 1))
    per_page = 20
    offset = (page - 1) * per_page

    if bene_id:
        query = f"""
            SELECT {",".join(COLUMNS)}
            FROM combined_features
            WHERE DESYNPUF_ID = '{bene_id}'
            LIMIT 1
        """
        rows = con.execute(query).fetchdf().to_dict(orient="records")
        total_pages = 1
    else:
        query = f"""
            SELECT {",".join(COLUMNS)}
            FROM combined_features
            LIMIT {per_page} OFFSET {offset}
        """
        rows = con.execute(query).fetchdf().to_dict(orient="records")

        total_count = con.execute("SELECT COUNT(*) FROM combined_features").fetchone()[0]
        total_pages = (total_count // per_page) + (1 if total_count % per_page else 0)

    return render_template(
        "member_data.html",
        columns=COLUMNS,
        rows=rows,
        page=page,
        total_pages=total_pages,
        bene_id=bene_id
    )

# ------------------- PREDICT -------------------
@app.route('/predict')
def predict():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template("predict.html")

# Existing user route (submit Bene ID)
@app.route('/predict/existing', methods=['POST'])
def predict_existing():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    bene_id = request.form['bene_id'].strip()
    # redirect to members page with Bene ID filtered
    return redirect(url_for('members', bene_id=bene_id))

# New user route (display form)
@app.route('/predict/new', methods=['GET', 'POST'])
def predict_new():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        # handle new user data submission here
        # e.g., save data and compute prediction
        data = request.form.to_dict()
        # Redirect to results page or show prediction
        return render_template("new_user_result.html", data=data)

    return render_template("new_user_form.html")

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    app.run(debug=True)

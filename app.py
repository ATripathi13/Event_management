from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import csv
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'No tickets available for this event'

# Initialize Database
def init_db():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Create the 'events' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS events 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT, 
                       date TEXT NOT NULL, location TEXT, capacity INTEGER, tickets_sold INTEGER DEFAULT 0)''')

    # Create the 'attendees' table
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendees 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL, 
                       event_id INTEGER, FOREIGN KEY(event_id) REFERENCES events(id) ON DELETE CASCADE)''')

    conn.commit()
    conn.close()

init_db()

# Route: Homepage (View Events)
@app.route('/')
def index():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return render_template('index.html', events=events)

# Route: Create Event
@app.route('/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']

        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (title, description, date, location, capacity) VALUES (?, ?, ?, ?, ?)",
                       (title, description, date, location, capacity))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create_event.html')


@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    if event is None:
        flash('Event not found')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Check if tickets are available
        capacity = event[5]
        tickets_sold = event[6]

        if capacity is not None and tickets_sold is not None and capacity > tickets_sold:
            cursor.execute("INSERT INTO attendees (name, email, event_id) VALUES (?, ?, ?)", (name, email, event_id))
            cursor.execute("UPDATE events SET tickets_sold = tickets_sold + 1 WHERE id=?", (event_id,))
            conn.commit()
        else:
            flash('No tickets available for this event')
            print("Capacity full, no tickets available")

    cursor.execute("SELECT * FROM attendees WHERE event_id=?", (event_id,))
    attendees = cursor.fetchall()

    conn.close()
    return render_template('event_details.html', event=event, attendees=attendees)



UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route: Upload CSV for Event Import
@app.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # Ensure the uploads directory exists
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            import_csv(filepath)
            return redirect(url_for('index'))

    return render_template('upload_csv.html')


def import_csv(filepath):
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()

        for row in reader:
            cursor.execute('''INSERT INTO events (title, description, date, location, capacity) 
                              VALUES (?, ?, ?, ?, ?)''',
                           (row['Event Title'], row['Description'], row['Date'], row['Location'], row['Capacity']))
        
        conn.commit()
        conn.close()


@app.route('/report')
def ticket_sales_report():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    
    # Assuming each ticket is $50
    cursor.execute("SELECT title, capacity, tickets_sold, tickets_sold * 50 AS revenue FROM events")
    report_data = cursor.fetchall()

    conn.close()
    return render_template('report.html', report_data=report_data)

# Route: Update Event
@app.route('/update/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Fetch current event details
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    if request.method == 'POST':
        # Get updated details from the form
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']

        # Update event details in the database
        cursor.execute('''UPDATE events 
                          SET title=?, description=?, date=?, location=?, capacity=? 
                          WHERE id=?''', (title, description, date, location, capacity, event_id))
        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    conn.close()
    return render_template('update_event.html', event=event)

# Route: Delete Event
@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Delete the event from the database
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

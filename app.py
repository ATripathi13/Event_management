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
# Read events from CSV
def read_events_from_csv():
    events = []
    with open('events.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            events.append(row)
    return events

@app.route('/')
def index():
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()

    # Also read events from CSV
    csv_events = read_events_from_csv()

    conn.close()
    return render_template('index.html', events=events, csv_events=csv_events)


# Route: Create Event
# Append event details to CSV file
# Append event details to CSV
def save_event_to_csv(event):
    with open('events.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(event)

# Append attendee details to CSV
def save_attendee_to_csv(attendee):
    with open('attendees.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(attendee)

# Adding event to both SQLite and CSV
@app.route('/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']

        # Insert into SQLite database
        conn = sqlite3.connect('events.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO events (title, description, date, location, capacity) VALUES (?, ?, ?, ?, ?)",
                       (title, description, date, location, capacity))
        conn.commit()

        # Fetch the last inserted event and add to CSV
        event_id = cursor.lastrowid
        cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
        event = cursor.fetchone()
        save_event_to_csv(event)
        
        conn.close()
        return redirect(url_for('index'))

    return render_template('create_event.html')


# Append attendee details to CSV file
def save_attendee_to_csv(attendee):
    with open('attendees.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(attendee)

@app.route('/event/<int:event_id>', methods=['GET', 'POST'])
def event_details(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']

        # Check if tickets are available
        if event[5] is not None and event[6] is not None and event[5] > event[6]:  # capacity > tickets_sold
            cursor.execute("INSERT INTO attendees (name, email, event_id) VALUES (?, ?, ?)", (name, email, event_id))
            cursor.execute("UPDATE events SET tickets_sold = tickets_sold + 1 WHERE id=?", (event_id,))
            conn.commit()

            # Fetch the last inserted attendee
            attendee_id = cursor.lastrowid
            cursor.execute("SELECT * FROM attendees WHERE id=?", (attendee_id,))
            attendee = cursor.fetchone()

            # Save the attendee details to CSV
            save_attendee_to_csv(attendee)
        else:
            flash("No tickets available for this event")

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

# Update event in CSV file
def update_event_in_csv(event_id, updated_event):
    events = read_events_from_csv()
    with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for event in events:
            if int(event[0]) == event_id:
                writer.writerow(updated_event)
            else:
                writer.writerow(event)

# Updating event in SQLite and CSV
@app.route('/update/<int:event_id>', methods=['GET', 'POST'])
def update_event(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Fetch current event details
    cursor.execute("SELECT * FROM events WHERE id=?", (event_id,))
    event = cursor.fetchone()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']
        location = request.form['location']
        capacity = request.form['capacity']

        # Update in SQLite
        cursor.execute('''UPDATE events 
                          SET title=?, description=?, date=?, location=?, capacity=? 
                          WHERE id=?''', (title, description, date, location, capacity, event_id))
        conn.commit()

        # Update in CSV
        updated_event = (event_id, title, description, date, location, capacity, event[6])  # event[6] is tickets_sold
        update_event_in_csv(event_id, updated_event)

        conn.close()
        return redirect(url_for('index'))

    conn.close()
    return render_template('update_event.html', event=event)


# Route: Delete Event
# Remove event from CSV
def delete_event_from_csv(event_id):
    events = read_events_from_csv()
    with open('events.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for event in events:
            if int(event[0]) != event_id:  # Skip the event to be deleted
                writer.writerow(event)

# Deleting event in SQLite and CSV
@app.route('/delete/<int:event_id>', methods=['POST'])
def delete_event(event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Delete from SQLite
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()

    # Delete from CSV
    delete_event_from_csv(event_id)

    conn.close()
    return redirect(url_for('index'))

# Read attendees from CSV
def read_attendees_from_csv():
    attendees = []
    with open('attendees.csv', 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            attendees.append(row)
    return attendees

# Remove attendee from CSV
def delete_attendee_from_csv(attendee_id):
    attendees = read_attendees_from_csv()
    with open('attendees.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for attendee in attendees:
            if int(attendee[0]) != attendee_id:  # Skip the attendee to be deleted
                writer.writerow(attendee)

@app.route('/delete_attendee/<int:attendee_id>/<int:event_id>', methods=['POST'])
def delete_attendee(attendee_id, event_id):
    conn = sqlite3.connect('events.db')
    cursor = conn.cursor()

    # Delete attendee from the SQLite database
    cursor.execute("DELETE FROM attendees WHERE id=?", (attendee_id,))
    
    # Decrease the ticket count for the event
    cursor.execute("UPDATE events SET tickets_sold = tickets_sold - 1 WHERE id=?", (event_id,))
    conn.commit()
    conn.close()

    # Delete attendee from CSV
    delete_attendee_from_csv(attendee_id)

    return redirect(url_for('event_details', event_id=event_id))


if __name__ == '__main__':
    app.run(debug=True)

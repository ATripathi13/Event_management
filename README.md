# Event Management Web Application


A Python-based web application designed for event planners to manage events, attendees, and ticket sales efficiently. Built using Flask for the backend and SQLite for database management, this application provides core functionalities like event creation, attendee registration, and viewing event details.

**Features**


**Event Management:** Create, read, update, and delete events.
![Event list](https://github.com/user-attachments/assets/fedc26a3-9566-41e9-88a1-86642edba006)

**Attendee Management:** Register attendees for specific events and view attendee details.
![attendee_register](https://github.com/user-attachments/assets/f9011722-0fe6-48a5-9603-b11321865a1d)

![attendee_list](https://github.com/user-attachments/assets/a71d28d1-bc2d-4c48-9763-a5179e2608de)

**Database:** Stores event and attendee information using SQLite and CSV.
![upload_csv](https://github.com/user-attachments/assets/d6c72101-99ae-4e0e-9fe8-3c359059dc84)


**User-Friendly Interface:** Simple and intuitive interface for managing event-related data for the event planning company.

**Report for tickes**
![ticket_sale_report](https://github.com/user-attachments/assets/5105383b-3bf4-441b-a67a-4b1b26402331)


**Tech Stack :**


Backend: Flask (Python)
Database: SQLite, CSV
Frontend: HTML, CSS (for templating), Bootstrap
Other Tools: Jinja2 (for templating with Flask)

**How It Works :**


Home Page:


+ Lists all the events.
+ You can view event details and manage them (edit or delete).
+ Create New Event:

Add a new event with fields such as title, description, date, location, and capacity.
Event Details:

View the event information.
Register new attendees for the event and see the list of registered attendees.

**Required libraries are mentioned in the required.txt**


**Running the Application :**


+ Ensure the requirements are installed
+ Start the Flask development server:  **python app.py**
+ Open your browser and navigate to: **http://localhost:5000**

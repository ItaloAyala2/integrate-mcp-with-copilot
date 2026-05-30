# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a registered student for an activity                        |
| GET    | `/students`                                                       | List students, optionally filter by `name` or `admission_number`    |
| GET    | `/students/{email}`                                               | View a student's profile and registered activities                  |
| POST   | `/students`                                                       | Create a new student profile (requires admin token)                 |
| PATCH  | `/students/{email}`                                               | Update a student profile (requires admin token)                     |
| DELETE | `/students/{email}`                                               | Delete a student profile and assignments (requires admin token)     |

## Data Model

The application now stores student records in a persistent SQLite database (`students.db`).

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of registered student emails

2. **Students** - Uses email as identifier:
   - Name
   - Admission number
   - Grade
   - Faculty assignment
   - Enrollment year
   - Town
   - Date of birth
   - Gender
   - Notes
   - Registered activities

### Persistence

Student records and activity assignments are stored in SQLite, so data now persists across server restarts.

### Admin operations

Sensitive profile changes are protected by an admin token using the `X-Admin-Token` request header.

All other activity and student profile queries remain public.

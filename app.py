import streamlit as st
import sqlite3
import hashlib
from datetime import datetime

# Database setup
def connect_db():
    conn = sqlite3.connect('leave_management.db')
    return conn

def create_tables():
    conn = connect_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT UNIQUE,
                    password TEXT,
                    role TEXT,
                    manager_id INTEGER,
                    FOREIGN KEY(manager_id) REFERENCES users(id))''')

    c.execute('''CREATE TABLE IF NOT EXISTS leave_requests (
                    id INTEGER PRIMARY KEY,
                    employee_id INTEGER,
                    manager_id INTEGER,
                    leave_type TEXT,
                    comment TEXT,
                    status TEXT,
                    date_of_application TEXT,
                    FOREIGN KEY(employee_id) REFERENCES users(id),
                    FOREIGN KEY(manager_id) REFERENCES users(id))''')
    conn.commit()
    conn.close()

# Authentication Functions
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def verify_password(input_password, stored_password):
    return hash_password(input_password) == stored_password

def add_user(name, email, password, role, manager_id=None):
    conn = connect_db()
    c = conn.cursor()
    c.execute('INSERT INTO users (name, email, password, role, manager_id) VALUES (?, ?, ?, ?, ?)',
              (name, email, hash_password(password), role, manager_id))
    conn.commit()
    conn.close()

def login_user(email, password):
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email=?', (email,))
    user = c.fetchone()
    conn.close()
    if user and verify_password(password, user[3]):
        return user
    return None

def get_managers():
    conn = connect_db()
    c = conn.cursor()
    c.execute('SELECT id, name FROM users WHERE role="Manager"')
    managers = c.fetchall()
    conn.close()
    return managers

# Leave Request Functions
def apply_leave(employee_id, manager_id, leave_type, comment, date_of_application):
    conn = connect_db()
    c = conn.cursor()
    c.execute('INSERT INTO leave_requests (employee_id, manager_id, leave_type, comment, status, date_of_application) VALUES (?, ?, ?, ?, ?, ?)',
              (employee_id, manager_id, leave_type, comment, 'Waiting', date_of_application))
    conn.commit()
    conn.close()

def get_leave_requests(employee_id=None, manager_id=None):
    conn = connect_db()
    c = conn.cursor()
    if employee_id:
        c.execute('SELECT * FROM leave_requests WHERE employee_id=?', (employee_id,))
    elif manager_id:
        c.execute('SELECT leave_requests.*, users.name FROM leave_requests JOIN users ON leave_requests.employee_id = users.id WHERE leave_requests.manager_id=?', (manager_id,))
    else:
        return []
    leave_requests = c.fetchall()
    conn.close()
    return leave_requests

def update_leave_status(leave_request_id, status):
    conn = connect_db()
    c = conn.cursor()
    c.execute('UPDATE leave_requests SET status=? WHERE id=?', (status, leave_request_id))
    conn.commit()
    conn.close()

# Streamlit Application
def main():
    create_tables()
    
    st.title("Leave Management System")
    menu = ["Home", "Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Home":
        st.subheader("Home")
        st.write("Welcome to the Leave Management System")

    elif choice == "Sign Up":
        st.subheader("Create New Account")
        name = st.text_input("Name")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Employee", "Manager"])
        managers = get_managers()
        manager_id = None
        if role == "Employee" and managers:
            manager_choice = st.selectbox("Select Manager", managers)
            manager_id = manager_choice[0]

        if st.button("Sign Up"):
            add_user(name, email, password, role, manager_id)
            st.success("You have successfully created an account")
            st.info("Go to Login Menu to log in")

    elif choice == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(email, password)
            if user:
                st.success(f"Welcome {user[1]}")

                if user[4] == "Employee":
                    st.subheader("Employee Page")
                    leave_type = st.selectbox("Leave Type", ["Personal", "Sick", "Official"])
                    comment = st.text_area("Comment")
                    if st.button("Apply for Leave"):
                        apply_leave(user[0], user[5], leave_type, comment, datetime.now().strftime("%Y-%m-%d"))
                        st.success("Leave Applied Successfully")

                    st.subheader("Your Leave Requests")
                    leave_requests = get_leave_requests(employee_id=user[0])
                    if leave_requests:
                        for request in leave_requests:
                            st.write(f"Leave Type: {request[3]}, Status: {request[5]}, Comment: {request[4]}, Date: {request[6]}")
                    else:
                        st.write("No leave requests found")

                elif user[4] == "Manager":
                    st.subheader("Manager Page")
                    st.write("Leave Requests")
                    leave_requests = get_leave_requests(manager_id=user[0])
                    if leave_requests:
                        for request in leave_requests:
                            st.write(f"Employee: {request[8]}, Leave Type: {request[3]}, Status: {request[5]}, Comment: {request[4]}, Date: {request[6]}")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button(f"Approve {request[0]}"):
                                    update_leave_status(request[0], "Approved")
                                    st.success("Leave Approved")
                            with col2:
                                if st.button(f"Reject {request[0]}"):
                                    update_leave_status(request[0], "Rejected")
                                    st.warning("Leave Rejected")
                    else:
                        st.write("No leave requests found")

if __name__ == '__main__':
    main()
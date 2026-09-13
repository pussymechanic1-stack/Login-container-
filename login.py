import sqlite3
import hashlib
import getpass
import time
import os

DB = "users.db"


# ---------------- DATABASE ----------------

def connect_db():
    return sqlite3.connect(DB)


def setup_database():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ---------------- PASSWORD ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# ---------------- REGISTER ----------------

def register():
    print("\n" + "=" * 40)
    print("        CREATE ACCOUNT")
    print("=" * 40)

    username = input("Username: ").strip()

    if not username:
        print("❌ Username cannot be empty.")
        return

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")

    if password != confirm:
        print("❌ Passwords do not match.")
        return

    if len(password) < 6:
        print("❌ Password must be at least 6 characters.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hash_password(password))
        )

        conn.commit()
        print("✅ Account created successfully!")

    except sqlite3.IntegrityError:
        print("❌ Username already exists.")

    finally:
        conn.close()


# ---------------- LOGIN ----------------

def login():
    print("\n" + "=" * 40)
    print("             LOGIN")
    print("=" * 40)

    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, password, role FROM users WHERE username = ?",
        (username,)
    )

    user = cursor.fetchone()
    conn.close()

    if user is None:
        print("❌ Invalid username or password.")
        return None

    user_id, username, stored_password, role = user

    if hash_password(password) != stored_password:
        print("❌ Invalid username or password.")
        return None

    print("\n✅ Login successful!")
    print(f"👤 Welcome, {username}")
    print(f"🎭 Role: {role}")

    return {
        "id": user_id,
        "username": username,
        "role": role
    }


# ---------------- DASHBOARD ----------------

def dashboard(user):
    while True:
        print("\n" + "=" * 40)
        print("           DASHBOARD")
        print("=" * 40)

        print(f"👤 User: {user['username']}")
        print(f"🎭 Role: {user['role']}")

        print("\n1. Profile")
        print("2. Logout")

        if user["role"] == "admin":
            print("3. Admin Panel")

        choice = input("\nSelect: ").strip()

        if choice == "1":
            print("\n👤 PROFILE")
            print(f"Username: {user['username']}")
            print(f"Role: {user['role']}")

        elif choice == "2":
            print("🚪 Logged out.")
            break

        elif choice == "3" and user["role"] == "admin":
            admin_panel()

        else:
            print("❌ Invalid option.")


# ---------------- ADMIN PANEL ----------------

def admin_panel():
    print("\n" + "=" * 40)
    print("           ADMIN PANEL")
    print("=" * 40)

    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, username, role, created_at FROM users"
    )

    users = cursor.fetchall()

    if not users:
        print("No users found.")
    else:
        for user in users:
            print(
                f"\nID: {user[0]}"
                f"\nUsername: {user[1]}"
                f"\nRole: {user[2]}"
                f"\nCreated: {user[3]}"
            )

    conn.close()


# ---------------- CREATE ADMIN ----------------

def create_admin():
    print("\n" + "=" * 40)
    print("        CREATE ADMIN ACCOUNT")
    print("=" * 40)

    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password: ")

    if len(password) < 6:
        print("❌ Password must be at least 6 characters.")
        return

    conn = connect_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
            """,
            (username, hash_password(password), "admin")
        )

        conn.commit()
        print("👑 Admin account created!")

    except sqlite3.IntegrityError:
        print("❌ Username already exists.")

    finally:
        conn.close()


# ---------------- MAIN ----------------

def main():
    setup_database()

    while True:
        os.system("clear")

        print("""
╔══════════════════════════════════════╗
║          🥶 PYTHON LOGIN             ║
╠══════════════════════════════════════╣
║  1. Register                         ║
║  2. Login                            ║
║  3. Create Admin                     ║
║  4. Exit                             ║
╚══════════════════════════════════════╝
        """)

        choice = input("Select option: ").strip()

        if choice == "1":
            register()
            input("\nPress Enter to continue...")

        elif choice == "2":
            user = login()

            if user:
                dashboard(user)

            input("\nPress Enter to continue...")

        elif choice == "3":
            create_admin()
            input("\nPress Enter to continue...")

        elif choice == "4":
            print("👋 Goodbye!")
            break

        else:
            print("❌ Invalid option.")
            time.sleep(1)


if __name__ == "__main__":
    main()

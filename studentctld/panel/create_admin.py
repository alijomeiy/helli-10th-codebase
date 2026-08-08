"""Create or update an admin user from the command line.

Usage (inside the panel container):
    python create_admin.py <username> [password]

If the password is omitted you'll be prompted with hidden input.
If the user already exists, it is promoted to admin and the password is reset.

Examples:
    docker compose -f docker-compose.simple.yml exec panel python create_admin.py admin2
    docker compose -f docker-compose.simple.yml exec panel python create_admin.py jane secretpass
"""
import getpass
import sys

from app import app, db
from models import User


def main():
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <username> [password]")
        sys.exit(1)

    username = sys.argv[1].strip().lower()
    password = sys.argv[2] if len(sys.argv) > 2 else getpass.getpass("Password: ")

    with app.app_context():
        db.create_all()
        u = User.query.filter_by(username=username).first()
        if u:
            u.role = "admin"
            u.status = "approved"
            u.set_password(password)
            action = "updated existing user"
        else:
            u = User(role="admin", username=username,
                     full_name="Administrator", status="approved")
            u.set_password(password)
            db.session.add(u)
            action = "created admin"
        db.session.commit()
        print(f"[studentctl] {action} '{username}' (role=admin)")


if __name__ == "__main__":
    main()

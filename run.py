from app import create_app
from app.routes import initialize_database

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True, host='0.0.0.0', port=5000)
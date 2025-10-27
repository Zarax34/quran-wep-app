import unittest
from app import app, db, User, Parent
from werkzeug.security import generate_password_hash

class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_add_parents_with_spaces_in_name(self):
        with self.app as client:
            with app.app_context():
                admin_user = User(username='admin', password=generate_password_hash('admin123'), name='Admin', role='admin')
                db.session.add(admin_user)
                db.session.commit()

            client.post('/login', data={'username': 'admin', 'password': 'admin123'})

            client.post('/add_parents', data={'parents_text': 'Test User: 777123456'})

            with app.app_context():
                user = User.query.filter_by(name='Test User').first()
                self.assertIsNotNone(user)
                self.assertEqual(user.username, 'Test_User')

if __name__ == '__main__':
    unittest.main()

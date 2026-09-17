from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import User, Role

User = get_user_model()


class AccountsTestCase(TestCase):
    """Test case for accounts app."""

    def setUp(self):
        """Set up test data."""
        self.role = Role.objects.create(
            name='Test Role',
            description='A test role'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        self.user.roles.add(self.role)

    def test_user_creation(self):
        """Test that a user can be created."""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_role_assignment(self):
        """Test that roles can be assigned to users."""
        self.assertIn(self.role, self.user.roles.all())
        self.assertEqual(self.user.roles.count(), 1)

    def test_super_admin_property(self):
        """Test the is_super_admin property."""
        # Initially should be False
        self.assertFalse(self.user.is_super_admin)

        # Add Super Admin role
        super_admin_role = Role.objects.create(name='Super Admin')
        self.user.roles.add(super_admin_role)

        # Now should be True
        self.assertTrue(self.user.is_super_admin)
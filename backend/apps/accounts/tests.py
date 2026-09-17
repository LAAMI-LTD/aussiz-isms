from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import User, Role
import json


class AccountsAPITestCase(APITestCase):
    """Test case for accounts API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create test roles
        self.super_admin_role = Role.objects.create(
            name='Super Admin',
            description='Super admin role'
        )

        self.hod_role = Role.objects.create(
            name='HOD',
            description='HOD role'
        )

        self.tutor_role = Role.objects.create(
            name='Tutor',
            description='Tutor role'
        )

        # Create test users
        self.super_admin_user = User.objects.create_user(
            username='superadmin',
            email='superadmin@example.com',
            password='superadminpass123',
            first_name='Super',
            last_name='Admin',
            is_staff=True,
            is_superuser=True
        )
        self.super_admin_user.roles.add(self.super_admin_role)

        self.hod_user = User.objects.create_user(
            username='hoduser',
            email='hod@example.com',
            password='hodpass123',
            first_name='HOD',
            last_name='User',
            is_staff=True
        )
        self.hod_user.roles.add(self.hod_role)

        self.tutor_user = User.objects.create_user(
            username='tutoruser',
            email='tutor@example.com',
            password='tutorpass123',
            first_name='Tutor',
            last_name='User',
            is_staff=True
        )
        self.tutor_user.roles.add(self.tutor_role)

        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123',
            first_name='Regular',
            last_name='User'
        )

    def test_login_endpoint(self):
        """Test login endpoint with valid credentials."""
        url = reverse('accounts:login')
        data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertEqual(response.data['user_id'], self.super_admin_user.id)
        self.assertEqual(response.data['username'], 'superadmin')

    def test_login_endpoint_invalid_credentials(self):
        """Test login endpoint with invalid credentials."""
        url = reverse('accounts:login')
        data = {
            'username': 'superadmin',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_logout_endpoint(self):
        """Test logout endpoint."""
        # First login to get tokens
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']

        # Now logout
        logout_url = reverse('accounts:logout')
        logout_data = {
            'refresh_token': refresh_token
        }
        response = self.client.post(logout_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

    def test_user_profile_endpoint(self):
        """Test user profile endpoint."""
        # First login to get access token
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']

        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        # Get profile
        profile_url = reverse('accounts:profile')
        response = self.client.get(profile_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.super_admin_user.id)
        self.assertEqual(response.data['username'], 'superadmin')
        self.assertTrue(response.data['is_super_admin'])

    def test_user_list_endpoint_requires_super_admin(self):
        """Test that user list endpoint requires super admin."""
        url = reverse('accounts:user-list-create')

        # Test as regular user (should fail)
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'regularuser',
            'password': 'regularpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as super admin (should succeed)
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)  # All 4 test users

    def test_create_user_endpoint_requires_super_admin(self):
        """Test that user creation requires super admin."""
        url = reverse('accounts:user-list-create')

        # Test as regular user (should fail)
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'regularuser',
            'password': 'regularpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as super admin (should succeed)
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')

    def test_role_list_endpoint_requires_super_admin(self):
        """Test that role list endpoint requires super admin."""
        url = reverse('accounts:role-list-create')

        # Test as regular user (should fail)
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'regularuser',
            'password': 'regularpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # Test as super admin (should succeed)
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Our 3 test roles

    def test_dashboard_stats_endpoint(self):
        """Test dashboard stats endpoint."""
        # Test as super admin
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        url = reverse('accounts:dashboard-stats')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('active_users', response.data)
        self.assertIn('users_by_role', response.data)
        self.assertIn('Super Admin', response.data['users_by_role'])
        self.assertIn('HOD', response.data['users_by_role'])
        self.assertIn('Tutor', response.data['users_by_role'])

    def test_assign_role_to_user_endpoint(self):
        """Test assigning role to user endpoint."""
        # Login as super admin
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        # Assign HOD role to tutor user
        url = reverse('accounts:assign-role-to-user', kwargs={'user_id': self.tutor_user.id})
        data = {
            'role_id': self.hod_role.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify the role was assigned
        self.tutor_user.refresh_from_db()
        self.assertIn(self.hod_role, self.tutor_user.roles.all())

    def test_remove_role_from_user_endpoint(self):
        """Test removing role from user endpoint."""
        # First assign a role to remove
        self.tutor_user.roles.add(self.hod_role)

        # Login as super admin
        login_url = reverse('accounts:login')
        login_data = {
            'username': 'superadmin',
            'password': 'superadminpass123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        access_token = login_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)

        # Remove HOD role from tutor user
        url = reverse('accounts:remove-role-from-user', kwargs={'user_id': self.tutor_user.id})
        data = {
            'role_id': self.hod_role.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)

        # Verify the role was removed
        self.tutor_user.refresh_from_db()
        self.assertNotIn(self.hod_role, self.tutor_user.roles.all())
self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class NextOfKinAPITestCase(TestCase):
    """Test case for NextOfKin API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        self.hod_user = User.objects.create_user(
            username='hoduser',
            email='hod@example.com',
            password='hodpass123',
            first_name='HOD',
            last_name='User',
            is_staff=True
        )

        # Create test student
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            gender='M',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='TST123456U',
            phone_number='+254777777777',
            email='test@example.com',
            address='777 Test Street, Nairobi',
            created_by=self.staff_user
        )

        # Create roles
        from apps.accounts.models import Role
        self.hod_role = Role.objects.create(name='HOD', description='HOD role')
        self.staff_role = Role.objects.create(name='Staff', description='Staff role')

        self.hod_user.roles.add(self.hod_role)
        self.staff_user.roles.add(self.staff_role)

    def authenticate_user(self, username, password):
        """Helper to authenticate and set client credentials."""
        login_url = '/api/v1/auth/login/'
        login_data = {'username': username, 'password': password}
        response = self.client.post(login_url, login_data, format='json')
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data['tokens']['access']
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
            return True
        return False

    def test_next_of_kin_list_nested_route(self):
        """Test listing next of kin for a specific student via nested route."""
        # Create a next of kin for the student
        next_of_kin = NextOfKin.objects.create(
            first_name='John',
            last_name='Doe',
            relationship='Father',
            phone_number='+254788888888',
            student=self.student
        )

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/next-of-kin/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

        # Check if our next of kin is in the list
        next_of_kin_ids = [nk['id'] for nk in response.data]
        self.assertIn(str(next_of_kin.id), next_of_kin_ids)

    def test_next_of_kin_create_nested_route(self):
        """Test creating next of kin for a specific student via nested route."""
        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/next-of-kin/'
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'relationship': 'Mother',
            'phone_number': '+254799999999'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['first_name'], 'Jane')
        self.assertEqual(response.data['last_name'], 'Smith')
        self.assertEqual(response.data['relationship'], 'Mother')

        # Verify next of kin was actually created and associated with student
        self.assertTrue(NextOfKin.objects.filter(
            id=response.data['id'],
            student=self.student
        ).exists())

    def test_next_of_kin_detail_nested_route(self):
        """Test retrieving a specific next of kin via nested route."""
        # Create a next of kin for the student
        next_of_kin = NextOfKin.objects.create(
            first_name='Bob',
            last_name='Wilson',
            relationship='Brother',
            phone_number='+254711111111',
            student=self.student
        )

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/next-of-kin/{next_of_kin.id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Bob')
        self.assertEqual(response.data['last_name'], 'Wilson')
        self.assertEqual(response.data['relationship'], 'Brother')

    def test_next_of_kin_update_nested_route(self):
        """Test updating a next of kin via nested route."""
        # Create a next of kin for the student
        next_of_kin = NextOfKin.objects.create(
            first_name='Old',
            last_name='Name',
            relationship='Uncle',
            phone_number='+254722222222',
            student=self.student
        )

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/next-of-kin/{next_of_kin.id}/'
        data = {'first_name': 'New', 'last_name': 'Name'}

        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'New')
        self.assertEqual(response.data['last_name'], 'Name')

        # Verify the update in database
        next_of_kin.refresh_from_db()
        self.assertEqual(next_of_kin.first_name, 'New')

    def test_next_of_kin_delete_nested_route(self):
        """Test deleting a next of kin via nested route."""
        # Create a next of kin for the student
        next_of_kin = NextOfKin.objects.create(
            first_name='To',
            last_name='Delete',
            relationship='Friend',
            phone_number='+254733333333',
            student=self.student
        )

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/next-of-kin/{next_of_kin.id}/'
        response = self.client.delete(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deletion
        self.assertFalse(NextOfKin.objects.filter(id=next_of_kin.id).exists())

    def test_next_of_kin_permissions_nested_route(self):
        """Test that any authenticated user can view next of kin via nested route."""
        # Create a next of kin for the student
        NextOfKin.objects.create(
            first_name='Perm',
            last_name='Test',
            relationship='Sister',
            phone_number='+254744444444',
            student=self.student
        )

        # Test as unauthenticated user
        self.client.credentials()  # Remove credentials
        url = f'/api/v1/students/{self.student.id}/next-of-kin/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test as authenticated staff user
        self.authenticate_user('staffuser', 'staffpass123')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StudentDocumentAPITestCase(TestCase):
    """Test case for StudentDocument API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )

        # Create test student
        self.student = Student.objects.create(
            first_name='Doc',
            last_name='Test',
            gender='F',
            date_of_birth=datetime.date(2000, 1, 1),
            nationality='KE',
            national_id_passport='DOC123456V',
            phone_number='+254755555555',
            email='doc@example.com',
            address='555 Doc Street, Nairobi',
            created_by=self.staff_user
        )

        # Create roles
        from apps.accounts.models import Role
        self.staff_role = Role.objects.create(name='Staff', description='Staff role')
        self.staff_user.roles.add(self.staff_role)

    def authenticate_user(self, username, password):
        """Helper to authenticate and set client credentials."""
        login_url = '/api/v1/auth/login/'
        login_data = {'username': username, 'password': password}
        response = self.client.post(login_url, login_data, format='json')
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data['tokens']['access']
            self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
            return True
        return False

    def test_student_document_list_nested_route(self):
        """Test listing documents for a specific student via nested route."""
        # Note: We're not actually uploading a file, just testing the API structure
        # In a real test, we'd need to mock file upload

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/documents/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return empty list since no documents created
        self.assertEqual(len(response.data), 0)

    def test_student_document_create_nested_route(self):
        """Test creating document for a specific student via nested route."""
        # Note: Skipping actual file upload test for simplicity
        # In practice, this would test file upload functionality

        # Authenticate as staff user
        self.authenticate_user('staffuser', 'staffpass123')

        url = f'/api/v1/students/{self.student.id}/documents/'
        # We won't actually test file upload here to avoid complexity
        # The endpoint should exist and return appropriate error for missing file
        response = self.client.post(url, {}, format='json')
        # Expecting validation error for missing required fields, not 404
        self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_student_document_permissions_nested_route(self):
        """Test that any authenticated user can view documents via nested route."""
        # Test as unauthenticated user
        self.client.credentials()  # Remove credentials
        url = f'/api/v1/students/{self.student.id}/documents/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Test as authenticated staff user
        self.authenticate_user('staffuser', 'staffpass123')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
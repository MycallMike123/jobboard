import pytest
from accounts.tests.factories import UserFactory
from .factories import JobAdvertFactory, JobApplicationFactory,fake
from django.test.client import Client
from django.urls import reverse
from job_application.models import JobAdvert
from django.contrib.messages import get_messages



pytestmark = pytest.mark.django_db

def test_list_adverts(client: Client, user_instance):
    """
    Test the list of job adverts.
    """
    JobAdvertFactory.create_batch(20, created_by=user_instance, deadline=fake.future_date())
    JobAdvertFactory.create_batch(5, created_by=user_instance, deadline=fake.past_date())
    url = reverse('home')
    response = client.get(url)
    assert response.status_code == 200
    assert "job_adverts" in response.context

    paginated_adverts = response.context['job_adverts']
    assert paginated_adverts.paginator.count == 20
    assert len(paginated_adverts.object_list) == 10  # Assuming default pagination of 10 per page


def test_create_advert(authenticate_user):
    """
    Test creating a job advert.
    """
    client, user = authenticate_user
    url = reverse('create_advert')

    request_data = {
        'title': "Title of the Job Advert",
        'company_name': "Company Name",
        'description': "Job Description",
        'deadline': "2025-12-31",
        'skills': 'Python, Django',
        'employment_type': 'full_time',
        'experience_level': 'mid_level',
        'job_type': 'remote',
        'location': "Remote Location"
    }
    response = client.post(url, request_data)
    assert response.status_code == 302  # Redirect after successful creation
    assert JobAdvert.objects.count() == 1
    assert JobAdvert.objects.filter(created_by=user).count() == 1

    message = list(get_messages(response.wsgi_request))
    assert len(message) == 1
    assert message[0].level_tag == 'success'
    assert "Job advert created successfully." in message[0].message

def test_delete_advert(authenticate_user):
    """
    Test deleting a job advert.
    """
    client, user = authenticate_user
    advert = JobAdvertFactory(created_by=user)
    url = reverse('delete_advert', kwargs={'advert_id': advert.id})

    response = client.post(url)
    assert response.status_code == 302  # Redirect after successful deletion
    assert response.url == reverse('my_jobs')
    assert JobAdvert.objects.count() == 0

    message = list(get_messages(response.wsgi_request))
    assert len(message) == 1
    assert message[0].level_tag == 'success'
    assert "Job advert deleted successfully." in message[0].message


def test_edit_advert(authenticate_user):
    """
    Test editing a job advert.
    """
    client, user = authenticate_user
    advert = JobAdvertFactory(created_by=user)
    url = reverse('update_advert', kwargs={'advert_id': advert.id})

    request_data = {
        'title': "Updated Job Advert Title",
        'company_name': "Updated Company Name",
        'description': "Updated Job Description",
        'deadline': "2025-12-31",
        'skills': 'Python, Django',
        'employment_type': 'part_time',
        'experience_level': 'senior_level',
        'job_type': 'on_site',
        'location': "On-site Location"
    }
    response = client.post(url, request_data)
    assert response.status_code == 302  # Redirect after successful update
    assert response.url == reverse('get_advert', kwargs={'advert_id': advert.id})
    advert.refresh_from_db()
    assert advert.title == "Updated Job Advert Title"
    assert advert.company_name == "Updated Company Name"

    message = list(get_messages(response.wsgi_request))
    assert len(message) == 1
    assert message[0].level_tag == 'success'
    assert "Job advert updated successfully." in message[0].message


def test_get_my_applications(authenticate_user):
    """
    Test getting the user's job applications.
    """
    client, user = authenticate_user
    JobApplicationFactory.create_batch(5, email=user.email, job_advert=JobAdvertFactory(created_by=UserFactory()))
    JobApplicationFactory.create_batch(3, email="otheruser@example.com", job_advert=JobAdvertFactory(created_by=UserFactory()))

    url = reverse('my_applications')
    response = client.get(url)
    assert response.status_code == 200
    assert "my_applications" in response.context
    assert len(response.context['my_applications'].object_list) == 5
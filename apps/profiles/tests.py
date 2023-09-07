from rest_framework.test import APITestCase
from unittest import mock
from apps.common.utils import TestUtil
from apps.common.error import ErrorCode
import uuid
from cities_light.models import City, Country, Region


class TestProfile(APITestCase):
    cities_url = "/api/v1/profiles/cities/"
    profile_url = "/api/v1/profiles/profile/"
    maxDiff = None

    def setUp(self):
        # user
        verified_user = TestUtil.verified_user()
        another_verified_user = TestUtil.another_verified_user()
        self.verified_user = verified_user

        # auth
        auth_token = TestUtil.auth_token(verified_user)
        self.bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}
        auth_token = TestUtil.auth_token(another_verified_user)
        self.other_user_bearer = {"HTTP_AUTHORIZATION": f"Bearer {auth_token}"}

        # city
        country = Country.objects.create(name="Test Country", continent="AF", tld="tc")
        region = Region.objects.create(
            name="Test Region", display_name="testreg", country=country
        )
        city = City.objects.create(
            name="Test City", display_name="testcit", region=region, country=country
        )
        self.city = city

    def test_retrieve_cities(self):
        city = self.city

        # Test for valid response for non-existent city name query
        response = self.client.get(f"{self.cities_url}?name=non_existent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "success", "message": "No match found", "data": []},
        )

        # Test for valid response for existent city name query
        response = self.client.get(f"{self.cities_url}?name={city.name}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "Cities Fetched",
                "data": [
                    {
                        "id": city.id,
                        "name": city.name,
                        "region": city.region.name,
                        "country": city.country.name,
                    }
                ],
            },
        )

    def test_retrieve_profile(self):
        user = self.verified_user

        # Test for valid response for non-existent username
        response = self.client.get(f"{self.profile_url}invalid_username/")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json(),
            {
                "status": "failure",
                "message": "No user with that username",
                "code": ErrorCode.NON_EXISTENT,
            },
        )

        # Test for valid response for existent city name query
        response = self.client.get(f"{self.profile_url}{user.username}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "success",
                "message": "User details fetched",
                "data": {
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "email": user.email,
                    "bio": user.bio,
                    "avatar": user.get_avatar,
                    "dob": user.dob,
                    "city": None,
                    "created_at": user.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "updated_at": user.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                },
            },
        )

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

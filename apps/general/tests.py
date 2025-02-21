from rest_framework.test import APITestCase


class TestGeneral(APITestCase):
    sitedetail_url = "/api/v1/general/site-detail/"

    def test_retrieve_sitedetail(self):
        response = self.client.get(self.sitedetail_url)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Site Details fetched")
        keys = ["name", "email", "phone", "address", "fb", "tw", "wh", "ig"]
        self.assertTrue(all(item in result["data"] for item in keys))

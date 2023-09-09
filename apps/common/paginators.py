from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 10  # Set the default page size here
    page_size_query_param = 'page_size'  # Optional: allow clients to override the page size

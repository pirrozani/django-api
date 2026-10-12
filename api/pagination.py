from rest_framework.pagination import PageNumberPagination


# Every list: 10 per page by default, ?page_size= up to 50
class DefaultPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

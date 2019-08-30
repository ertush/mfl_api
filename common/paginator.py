from collections import OrderedDict

from rest_framework import pagination
from rest_framework.response import Response


class MflPaginationSerializer(pagination.PageNumberPagination):
    next_pages_to_show = 5
    far_pages_to_show = 5
    page_size_query_param = 'page_size'
    MAX_PAGINATE_BY = 15000


    def get_near_pages_to_show(self):
        current_page = self.page.number
        last_allowed_page = current_page + self.next_pages_to_show
        pages_to_show = []
        counter = current_page
        while counter < last_allowed_page:
            pages_to_show.append(counter+1)
            counter = counter + 1
        return pages_to_show


    def get_far_pages_to_show(self):
        last_page = self.page.end_index()
        counter = last_page - self.far_pages_to_show 
        pages_to_show = []
        while counter < last_page :
            pages_to_show.append(counter)
            counter = counter + 1
        return pages_to_show

    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page.paginator.per_page),
            ('current_page', self.page.number),
            ('total_pages', self.page.paginator.num_pages),
            ('start_index', self.page.start_index()),
            ('end_index', self.page.end_index()),
            ('near_pages', self.get_near_pages_to_show()),
            ('far_pages', self.get_far_pages_to_show()),
            ('results', data)
        ]))

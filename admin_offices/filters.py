from common.filters import CommonFieldsFilterset
from common.filters.filter_shared import ListCharFilter
from .models import AdminOffice, AdminOfficeContact


class AdminOfficeFilter(CommonFieldsFilterset):
	code = ListCharFilter(name='code')

	class Meta(CommonFieldsFilterset.Meta):
		model = AdminOffice
		exclude = ('coordinates', )


class AdminOfficeContactFilter(CommonFieldsFilterset):

    class Meta(CommonFieldsFilterset.Meta):
       model = AdminOfficeContact

from binwen.servicer import ServicerMeta
from extensions import db


class VipServicer(metaclass=ServicerMeta):

    def return_normal(self, request, context):
        return not db.database.is_closed()


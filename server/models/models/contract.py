from shared.shared import db
from enum import Enum
import copy
import math

class ContractStatus(Enum):
    OPENED = 0
    CLOSED = 1
    CLOSED_MARGIN = 2


class Contract(db.Model):
    PRICE_MULTIPLIER = 1000

    equity_id = db.Column(db.Integer, primary_key=True, nullable=False)
    contract_id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    modified_id = db.Column(db.Integer, nullable=False)
    is_long = db.Column(db.Boolean, nullable=False)
    quantity = db.Column(db.BigInteger, nullable=False)
    price = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.Integer, nullable=False)
    created_date = db.Column(db.DateTime(), nullable=False)
    closed_date = db.Column(db.DateTime())

    def get_price(self):
        return self.price / (self.PRICE_MULTIPLIER + 0.0)

    def clone(self):
        return copy.copy(self)

    def copy_values(self, item):
        self.__dict__.update(item.__dict__)

    @staticmethod
    def is_opened(item):
        return item.is_opened()

    def is_opened(self):
        return self.status == ContractStatus.OPENED

    def get_quantity(self, equity):
        return self.quantity * math.pow(10, equity.decimal_points_quantity)

    @staticmethod
    def id_comparer(item1, item2):
        return 1 if item1.contract_id < item2.contract_id else -1 if item1.contract_id > item2.contract_id else 0

    @staticmethod
    def modified_id_comparer(item1, item2):
        return 1 if item1.modified_id < item2.modified_id else -1 if item1.modified_id > item2.modified_id else 0


db.Index('ix_contract_user_id_equity_id', Contract.user_id, Contract.equity_id, Contract.contract_id)
from transactional_data_structures.transactional import Transactional
from transactional_data_structures.dictionary_version import DictionaryVersion
from transactional_data_structures.events import EventPriority

from indices.user_orders import UserOrders
from indices.user_contracts import UserContracts
from indices.user_transactions import UserTransactions
from models.models.equity import Equity


class UserList(Transactional):
    def __init__(self):
        pass

    def __init__(self, trade_engine):
        self.trade_engine = trade_engine
        self.users = DictionaryVersion({}, "user_id", model_name="users", events=trade_engine.events)

        self.user_orders = UserOrders(trade_engine)
        self.user_contracts = UserContracts(trade_engine)
        self.user_transactions = UserTransactions(trade_engine, True)
        self.user_transactions = UserTransactions(trade_engine, False)

        self.subscribe_to_events(trade_engine.events)

    def subscribe_to_events(self, events):
        events.subscribe("place_order", self.user_can_place_order, EventPriority.VALIDATION)
        events.subscribe("match_order", self.check_user_can_execute_order, EventPriority.VALIDATION)

        events.subscribe("place_order", self.place_order)
        events.subscribe("make_contract", self.make_contract, EventPriority.PRE_EVENT)

    def get_contract(self, contract):
        return self.user_contracts.contracts.get_item(contract)

    def get_user(self, user):
        return self.users.get_item(user)

    def get_user_orders(self, order):
        return self.user_orders.orders.get_list(order)

    def check_has_sufficient_funds(self, user, amount):
        btc_price = self.trade_engine.get_bitcoin_price()

        balance_btc = user.balance - (amount["delta_balance"] / btc_price)
        margin_btc = (user.margin_used + amount["margin"]) / btc_price
        margin_used_orders_btc = (user.margin_used_orders + amount["margin_orders"]) / btc_price

        if margin_btc >= balance_btc or margin_used_orders_btc >= balance_btc:
            raise Exception("InsufficientFunds")

    def update_user_balance_and_margin(self, user, amount):
        old_user = self.users.get_item(user)
        new_user = old_user.clone()

        btc_price = self.trade_engine.get_bitcoin_price()
        btc_decimal = self.trade_engine.BITCOIN_DECIMAL

        new_user.add_to_balance_and_margin(
            -amount["delta_balance"] * btc_decimal / btc_price,
            amount["margin"],
            amount["margin_orders"]
        )

        self.trade_engine.events.trigger("users_update_item", new_user, old_user)

    def check_user_can_place_order(self, order):
        user = self.users.get_item(order)
        amount = {"margin": user.margin_used, "margin_orders": 0.0, "delta_balance": 0.0}
        self.trade_engine.events.trigger("get_place_order_amount", order, amount)
        self.check_has_sufficient_funds(user, amount)

    def check_user_can_execute_order(self, order):
        user = self.users.get_item(order)
        amount = {"margin": 0, "margin_orders": 0, "delta_balance": 0.0}

        self.trade_engine.events.trigger("get_execute_order_amount", order, amount)
        self.check_has_sufficient_funds(user, amount)

    def place_order(self, order):
        user = self.users.get_item(order)
        amount = {"margin": user.margin_used, "margin_orders": 0.0, "delta_balance": 0.0}
        self.trade_engine.events.trigger("get_place_order_amount", order, amount)
        self.update_user_margin(user, amount)

    def make_contract(self, order, is_maker):
        user = self.users.get_item(order)
        amount = {"margin": 0, "margin_orders": 0, "delta_balance": 0.0}
        self.trade_engine.events.trigger("get_execute_order_amount", order, amount, is_maker)
        self.update_user_balance_and_margin(user, amount)

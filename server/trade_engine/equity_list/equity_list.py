from transactional_data_structures.transactional import Transactional
from transactional_data_structures.dictionary_version import DictionaryVersion

from transactional_data_structures.events import EventPriority


class EquityList(Transactional):
    def __init__(self):
        pass

    def __init__(self, trade_engine):
        self.trade_engine = trade_engine
        self.equities = DictionaryVersion({}, "equity_id", model_name="equities", events=trade_engine.events)

        self.subscribe_to_events(trade_engine.events)

    def get_equity(self, equity):
        return self.equities.get_item(equity)

    def subscribe_to_events(self, events):
        events.subscribe("match_orders", self.set_equity_price, EventPriority.PRE_EVENT)

    def set_equity_price(self, order, matched_order):
        equity = self.equities.get_item(order)

        old_equity = equity.clone()
        equity.current_price = matched_order.current_price
        self.trade_engine.events.trigger("equities_update_item", equity, old_equity)
        return self.trade_engine.events.trigger("set_equity_price", equity.equity_id, matched_order.current_price, old_equity.current_price)

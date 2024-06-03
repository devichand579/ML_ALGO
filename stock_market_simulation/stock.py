import random
from collections import defaultdict
import time

class StockExchange:
    def __init__(self):
        self.securities = {
            'AAPL': {'price': 1500.0, 'orders': []},
            'GOOGL': {'price': 2700.0, 'orders': []},
            # Add more securities as needed
        }
        self.trading_hours = 6.5 * 60 * 60  # Trading day in seconds
        self.executed_transactions = []

    def last_traded_price(self, security):
        if security in self.securities:
            return self.securities[security]['price']
        return None

    def best_bid_and_offer(self, security):
        if security in self.securities:
            bids = [order['price'] for order in self.securities[security]['orders'] if order['side'] == 'BUY' and order['price'] is not None]
            offers = [order['price'] for order in self.securities[security]['orders'] if order['side'] == 'SELL' and order['price'] is not None]
            return max(bids, default=None), min(offers, default=None)
        return None, None

    def accept_order(self, order):
        # Only accept orders during trading hours
        if order['timestamp'] < self.trading_hours:
            self.securities[order['security']]['orders'].append(order)
            return True
        return False

    def match_orders(self, current_hour):
        for security, orders in self.securities.items():
            buys = [order for order in orders['orders'] if order['side'] == 'BUY']
            sells = [order for order in orders['orders'] if order['side'] == 'SELL']
            buys.sort(key=lambda x: (x['price'], x['timestamp']), reverse=True)  # Sort buy orders in descending order of price
            sells.sort(key=lambda x: (x['price'], x['timestamp']))  # Sort sell orders in ascending order of price
            print(f"Matching orders for {security}:")
            print("Buy Orders:")
            for order in buys:
                print(f"  Price: {order['price']}, Quantity: {order['quantity']}")
            print("Sell Orders:")
            for order in sells:
                print(f"  Price: {order['price']}, Quantity: {order['quantity']}")
            print("***********************************")
            while buys and sells:
                buy_order = buys[0]
                sell_order = sells[0]

                if buy_order['price'] >= sell_order['price']:
                    quantity = min(buy_order['quantity'], sell_order['quantity'])
                    self.execute_trade(buy_order, sell_order, quantity,current_hour)
                    if buy_order['quantity'] == sell_order['quantity']:
                        buys.pop(0)
                        sells.pop(0)
                    elif buy_order['quantity'] < sell_order['quantity']:
                        sells[0]['quantity'] -= quantity
                        buys.pop(0)
                    else:
                        buys[0]['quantity'] -= quantity
                        sells.pop(0)
                else:
                    break

            # Remove any remaining orders outside of top 5 bids or offers
            self.securities[security]['orders'] = buys[:5] + sells[:5]

    def execute_trade(self, buy_order, sell_order, quantity,current_hour):
        buy_price = buy_order['price']
        sell_price = sell_order['price']
        security = buy_order['security']

        # Calculate the total value of the transaction
        total_value = quantity * sell_price

        # Update buyer's cash and portfolio
        buy_oms = buy_order['oms']
        buy_oms.add_cash(-total_value)
        buy_oms.portfolio[security] = buy_oms.portfolio.get(security, 0) + quantity

        # Update seller's cash and portfolio
        sell_oms = sell_order['oms']
        sell_oms.add_cash(total_value)
        sell_oms.portfolio[security] = sell_oms.portfolio.get(security, 0) - quantity

        # Update last traded price for the security
        self.securities[security]['price'] = sell_price

        # Remove executed quantity from buy and sell orders
        buy_order['quantity'] -= quantity
        sell_order['quantity'] -= quantity

        # Remove order if quantity becomes zero
        if buy_order['quantity'] == 0:
            buy_order['oms'].trader.orders.remove(buy_order)
        if sell_order['quantity'] == 0:
            sell_order['oms'].trader.orders.remove(sell_order)

        # Store executed transaction
        self.executed_transactions.append({'security': security, 'quantity': quantity, 'price': sell_price, 'buyer': buy_order['oms'].trader, 'seller': sell_order['oms'].trader, 'timestamp': current_hour})


class OrderManagementSystem:
    def __init__(self, trader):
        self.trader = trader
        self.cash = trader.initial_cash
        self.portfolio = trader.initial_portfolio

    def track_cash(self):
        return self.cash

    def add_cash(self, amount):
        self.cash += amount

    def withdraw_cash(self, amount):
        if self.cash >= amount:
            self.cash -= amount
            return True
        return False

    def portfolio_value(self, exchange):
        total_value = 0
        for security, quantity in self.portfolio.items():
            price = exchange.last_traded_price(security)
            if price is not None:
                total_value += price * quantity
        return total_value

    def place_buy_order(self,id, security, price, quantity, current_hour, exchange):
        # Calculate the total cost of buying the stocks
        total_cost = price * quantity

        # Check if the trader has enough cash
        if total_cost > self.cash:
            needed_amount = total_cost - self.cash
            #print(needed_amount)
            print(f"Trader {id} : You need to add ${needed_amount} to your account to place this order.")
            self.cash += needed_amount
            print("Amount Added Successfully!!!")
            #print("After UPDATINGĠ")
            print(self.cash)
            order = {'security': security, 'side': 'BUY', 'price': price, 'quantity': quantity, 'oms': self, 'timestamp': current_hour}


        
        if exchange.accept_order(order):
            return order
        else:
            print("Cannot accept order outside trading hours.")
            return None

    def place_sell_order(self,id, security, price, quantity, current_hour, exchange):
        # Check if the trader has enough stocks to sell
        if quantity > self.portfolio.get(security, 0):
            print("You do not have enough stocks to sell.")
            return None

        # Proceed with placing the sell order
        order = {'security': security, 'side': 'SELL', 'price': price, 'quantity': quantity, 'oms': self, 'timestamp': current_hour}
        if exchange.accept_order(order):
            return order
        else:
            print("Cannot accept order outside trading hours.")
            return None


class Trader:
    def __init__(self, trader_id, initial_cash, initial_portfolio):
        self.id = trader_id
        self.initial_cash = initial_cash
        self.initial_portfolio = initial_portfolio
        self.oms = OrderManagementSystem(self)
        self.orders = []  # Store trader's orders

    def action(self, exchange, current_time):
        # Randomly choose a security to trade
        security = random.choice(list(self.initial_portfolio.keys()))
      #  print(security)
        # Randomly choose an action: buy or sell
        action = random.choice(['BUY', 'SELL'])
      #  print(action)
        price_option = random.choice(['BEST_BID', 'BEST_ASK', 'MID_PRICE'])
      #  print(price_option)
        if price_option == 'BEST_BID':
            best_bid, _ = exchange.best_bid_and_offer(security)
            if best_bid:
                price = best_bid
            else:
                price_option = 'RANDOM'
             #   print(price_option)
                price = exchange.last_traded_price(security) * random.uniform(0.95, 1.05)

        elif price_option == 'BEST_ASK':
            _, best_offer = exchange.best_bid_and_offer(security)
            if best_offer:
                price = best_offer
            else:
                price_option = 'RANDOM'
             #   print(price_option)
                price = exchange.last_traded_price(security) * random.uniform(0.95, 1.05)

        elif price_option == 'MID_PRICE':
            best_bid, best_offer = exchange.best_bid_and_offer(security)
            if best_bid and best_offer:
                price = (best_bid + best_offer) / 2
            else:
                price_option = 'RANDOM'
               # print(price_option)
                price = exchange.last_traded_price(security) * random.uniform(0.95, 1.05)
        # Place order
        # Inside the Trader class's action method
        order = None
        if action == 'BUY':
            order = self.oms.place_buy_order(self.id,security, price, 1000, current_time, exchange)
        else:
            order = self.oms.place_sell_order(self.id,security, price, 1000, current_time, exchange)
        self.orders.append(order)


class Share:
    def __init__(self):
        pass


if __name__ == "__main__":

    print("Welcome to the Stock Exchange Simulation!")


    exchange = StockExchange()
    traders = [Trader(trader_id, 1000, {'AAPL': 1000, 'GOOGL': 1000}) for trader_id in range(1, 6)]

    # Initialized 5 traders with $1000 cash and 1000 shares of AAPL and GOOGL each
    
    print("\nTrader Details at the Start of Trading Day:\n")
    
    for trader in traders:
        print(f"--Initial Portfolio--")
        print(f"Trader ID: {trader.id}")
        for security, quantity in trader.initial_portfolio.items():
            print(f"    {security}: {quantity}")
        print(f"  Cash: {trader.oms.track_cash()}")
        print(f"  Portfolio Value: {trader.oms.portfolio_value(exchange)}")
        print("***********************************")

    trading_hours = 1
    current_time = 0

    while current_time < trading_hours:
        print(f"Hour {current_time + 1}:")
        # Perform actions for each trader
        for trader in traders:
            trader.action(exchange, current_time)
            print(f"Trader {trader.id} Orders:")
            for order in trader.orders:
                if order is not None:
                   print(f"  Security: {order['security']}, Side: {order['side']}, Price: {order['price']}, Quantity: {order['quantity']}, Timestamp: {order['timestamp']}")
            print("***********************************")
        # Match orders
        exchange.match_orders(current_time)

        # Print executed orders
        print("\nExecuted Orders:")
        for transaction in exchange.executed_transactions:
            print(f"  Security: {transaction['security']}, Quantity: {transaction['quantity']}, Price: {transaction['price']}, Buyer ID: {transaction['buyer'].id}, Seller ID: {transaction['seller'].id}, Timestamp: {transaction['timestamp']}")
        print("***********************************")

        # Increment time by 1 hour
        current_time += 1

    # Print trader details after trading period
    print("\nTrader Details after Trading Period:")
    for trader in traders:
        print(f"Trader ID: {trader.id}")
        print(f"  Cash: {trader.oms.track_cash()}")
        print("  Portfolio:")
        for security, quantity in trader.oms.portfolio.items():
            print(f"    {security}: {quantity}")
        print(f"  Portfolio Value: {trader.oms.portfolio_value(exchange)}")
        print("***********************************")



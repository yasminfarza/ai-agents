class Account:
    def __init__(self, user_id: str, initial_balance: float):
        """
        Initializes a new account for a user with a specified initial balance.

        :param user_id: A unique identifier for the user
        :param initial_balance: The initial deposit amount for the account
        """
        self.user_id = user_id
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.holdings = {}  # Key: stock symbol, Value: number of shares
        self.transactions = []  # List of transaction records

    def deposit(self, amount: float):
        """
        Deposits funds into the user's account.

        :param amount: The amount to deposit
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.balance += amount
        self.transactions.append(f"Deposited: ${amount:.2f}")

    def withdraw(self, amount: float):
        """
        Withdraws funds from the user's account.

        :param amount: The amount to withdraw
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        if self.balance - amount < 0:
            raise ValueError("Insufficient funds for withdrawal.")
        self.balance -= amount
        self.transactions.append(f"Withdrew: ${amount:.2f}")

    def buy_shares(self, symbol: str, quantity: int):
        """
        Buys shares of a stock for the user.

        :param symbol: The stock symbol to buy
        :param quantity: The number of shares to buy
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        price_per_share = get_share_price(symbol)
        total_cost = price_per_share * quantity

        if total_cost > self.balance:
            raise ValueError("Insufficient funds to buy shares.")
        
        self.balance -= total_cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transactions.append(f"Bought {quantity} shares of {symbol} at ${price_per_share:.2f}")

    def sell_shares(self, symbol: str, quantity: int):
        """
        Sells shares of a stock for the user.

        :param symbol: The stock symbol to sell
        :param quantity: The number of shares to sell
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise ValueError("Not enough shares to sell.")

        price_per_share = get_share_price(symbol)
        total_revenue = price_per_share * quantity
        
        self.holdings[symbol] -= quantity
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]  # Remove symbol from holdings if quantity is zero
        
        self.balance += total_revenue
        self.transactions.append(f"Sold {quantity} shares of {symbol} at ${price_per_share:.2f}")

    def portfolio_value(self) -> float:
        """
        Calculates the total value of the user's portfolio.

        :return: The total value of the user's portfolio including current balance
        """
        total_value = self.balance
        for symbol, quantity in self.holdings.items():
            total_value += get_share_price(symbol) * quantity
        return total_value

    def profit_loss(self) -> float:
        """
        Calculates the profit or loss from the initial deposit.

        :return: The profit or loss
        """
        current_value = self.portfolio_value()
        return current_value - self.initial_balance

    def report_holdings(self) -> dict:
        """
        Reports the current stock holdings of the user.

        :return: A dictionary with stock symbols and quantities
        """
        return self.holdings

    def report_profit_loss(self) -> float:
        """
        Reports the current profit or loss.

        :return: The current profit or loss
        """
        return self.profit_loss()

    def list_transactions(self) -> list:
        """
        Lists all the transactions made by the user.

        :return: A list of transaction strings
        """
        return self.transactions

def get_share_price(symbol: str) -> float:
    """
    Returns the current price of a share based on the stock symbol.

    :param symbol: The stock symbol
    :return: The price of the share
    """
    prices = {
        "AAPL": 150.00,  # Example price for Apple
        "TSLA": 700.00,  # Example price for Tesla
        "GOOGL": 2800.00  # Example price for Google
    }
    return prices.get(symbol, 0.0)  # Return 0 if the symbol is not found
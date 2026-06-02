import unittest
from accounts import Account, get_share_price

class TestAccount(unittest.TestCase):

    def setUp(self):
        self.account = Account("user123", 1000.0)

    def test_initial_balance(self):
        self.assertEqual(self.account.balance, 1000.0)

    def test_deposit(self):
        self.account.deposit(500.0)
        self.assertEqual(self.account.balance, 1500.0)
        self.assertIn("Deposited: $500.00", self.account.transactions)

    def test_deposit_negative_amount(self):
        with self.assertRaises(ValueError):
            self.account.deposit(-100)

    def test_withdraw(self):
        self.account.withdraw(200.0)
        self.assertEqual(self.account.balance, 800.0)
        self.assertIn("Withdrew: $200.00", self.account.transactions)

    def test_withdraw_insufficient_funds(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(1500)

    def test_withdraw_negative_amount(self):
        with self.assertRaises(ValueError):
            self.account.withdraw(-100)

    def test_buy_shares(self):
        self.account.buy_shares("AAPL", 2)
        self.assertEqual(self.account.holdings["AAPL"], 2)
        self.assertEqual(self.account.balance, 700.0)
        self.assertIn("Bought 2 shares of AAPL at $150.00", self.account.transactions)

    def test_buy_shares_insufficient_funds(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares("TSLA", 2)

    def test_buy_shares_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.account.buy_shares("AAPL", -2)

    def test_sell_shares(self):
        self.account.buy_shares("AAPL", 2)
        self.account.sell_shares("AAPL", 1)
        self.assertEqual(self.account.holdings["AAPL"], 1)
        self.assertEqual(self.account.balance, 850.0)
        self.assertIn("Sold 1 shares of AAPL at $150.00", self.account.transactions)

    def test_sell_shares_not_enough(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", 2)

    def test_sell_shares_negative_quantity(self):
        with self.assertRaises(ValueError):
            self.account.sell_shares("AAPL", -1)

    def test_portfolio_value(self):
        self.account.buy_shares("AAPL", 2)
        self.account.buy_shares("GOOGL", 0)
        self.assertEqual(self.account.portfolio_value(), 700.0 + (2 * 150.0))

    def test_profit_loss(self):
        self.assertEqual(self.account.profit_loss(), 0.0)
        self.account.deposit(500.0)
        self.assertEqual(self.account.profit_loss(), 500.0)

    def test_report_holdings(self):
        self.assertEqual(self.account.report_holdings(), {})
        self.account.buy_shares("AAPL", 1)
        self.assertEqual(self.account.report_holdings(), {"AAPL": 1})

    def test_list_transactions(self):
        self.account.deposit(500.0)
        self.account.withdraw(200.0)
        transactions = self.account.list_transactions()
        self.assertIn("Deposited: $500.00", transactions)
        self.assertIn("Withdrew: $200.00", transactions)


if __name__ == "__main__":
    unittest.main()
from accounts import Account
import gradio as gr

# Create a simple instance of Account for demonstration
account = Account(user_id="user1", initial_balance=1000.0)

def deposit(amount):
    try:
        account.deposit(float(amount))
        return f"Deposited: ${amount:.2f}, New Balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def withdraw(amount):
    try:
        account.withdraw(float(amount))
        return f"Withdrew: ${amount:.2f}, New Balance: ${account.balance:.2f}"
    except ValueError as e:
        return str(e)

def buy_shares(symbol, quantity):
    try:
        account.buy_shares(symbol, int(quantity))
        return f"Bought {quantity} shares of {symbol}, New Holdings: {account.report_holdings()}"
    except ValueError as e:
        return str(e)

def sell_shares(symbol, quantity):
    try:
        account.sell_shares(symbol, int(quantity))
        return f"Sold {quantity} shares of {symbol}, New Holdings: {account.report_holdings()}"
    except ValueError as e:
        return str(e)

def show_portfolio_value():
    return f"Total Portfolio Value: ${account.portfolio_value():.2f}"

def show_profit_loss():
    return f"Profit/Loss: ${account.report_profit_loss():.2f}"

def list_transactions():
    return "\n".join(account.list_transactions()) if account.list_transactions() else "No transactions yet."

with gr.Blocks() as demo:
    gr.Markdown("## Simple Trading Account Management System")

    with gr.Row():
        amount_input = gr.Number(label="Amount", value=0)
        deposit_btn = gr.Button("Deposit")
        deposit_output = gr.Textbox(label="Deposit Output", interactive=False)

    deposit_btn.click(deposit, inputs=amount_input, outputs=deposit_output)

    with gr.Row():
        withdraw_btn = gr.Button("Withdraw")
        withdraw_output = gr.Textbox(label="Withdraw Output", interactive=False)

    withdraw_btn.click(withdraw, inputs=amount_input, outputs=withdraw_output)

    with gr.Row():
        symbol_input_buy = gr.Textbox(label="Stock Symbol (Buy)")
        quantity_input_buy = gr.Number(label="Quantity (Buy)")
        buy_btn = gr.Button("Buy Shares")
        buy_output = gr.Textbox(label="Buy Output", interactive=False)

    buy_btn.click(buy_shares, inputs=[symbol_input_buy, quantity_input_buy], outputs=buy_output)

    with gr.Row():
        symbol_input_sell = gr.Textbox(label="Stock Symbol (Sell)")
        quantity_input_sell = gr.Number(label="Quantity (Sell)")
        sell_btn = gr.Button("Sell Shares")
        sell_output = gr.Textbox(label="Sell Output", interactive=False)

    sell_btn.click(sell_shares, inputs=[symbol_input_sell, quantity_input_sell], outputs=sell_output)

    with gr.Row():
        portfolio_value_btn = gr.Button("Show Portfolio Value")
        portfolio_value_output = gr.Textbox(label="Portfolio Value", interactive=False)

    portfolio_value_btn.click(show_portfolio_value, outputs=portfolio_value_output)

    with gr.Row():
        profit_loss_btn = gr.Button("Show Profit/Loss")
        profit_loss_output = gr.Textbox(label="Profit/Loss", interactive=False)

    profit_loss_btn.click(show_profit_loss, outputs=profit_loss_output)

    with gr.Row():
        transactions_btn = gr.Button("List Transactions")
        transactions_output = gr.Textbox(label="Transactions", interactive=False)

    transactions_btn.click(list_transactions, outputs=transactions_output)

demo.launch()
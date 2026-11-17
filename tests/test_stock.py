
import yfinance as yf

symbol = "AAPL"

try:
    ticker = yf.Ticker(symbol)

    # Get stock price history
    history = ticker.history(period="5d")

    if history.empty:
        print("No stock data received.")
    else:
        print("Stock data retrieved successfully!")
        print(history.tail())

    # Get company information
    info = ticker.get_info()

    print("\nCompany:", info.get("longName"))
    print("Sector:", info.get("sector"))

except Exception as error:
    print("Error:", error)

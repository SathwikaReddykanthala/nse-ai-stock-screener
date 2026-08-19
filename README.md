# 📊 NSE Stock Screener & AI Stock Dashboard

This project is a real-time NSE stock screening and AI-based stock analysis dashboard using **Angel One market data**. The application screens stocks based on price and market-depth conditions, tracks real-time LTP movement, analyzes trading volume and trends, generates BUY/SELL/HOLD signals, and maintains a paper-trading log.

The dashboard is built using **Python and Streamlit** and is designed for live market monitoring during NSE trading hours.

---

# 📌 Problem Statement

Monitoring a large number of NSE stocks manually is time-consuming. Traders need to identify stocks that satisfy specific price, liquidity, volume, and trend conditions while continuously monitoring changing market data.

This project aims to automate the stock-screening and analysis process by combining:

- Live Angel One market data
- Price-based screening
- Bid/Ask market-depth analysis
- ETQ analysis
- LTP trend analysis
- SMMA indicators
- AI-based BUY/SELL/HOLD signals
- Paper-trade logging

---

# 🚀 Project Workflow

**Market Data Collection**  
Angel One provides live NSE market data through the API/WebSocket connection.

**Instrument Mapping**  
NSE instrument and Angel One token information are used to identify stocks.

**Data Processing**  
Live LTP, LTQ, Bid Quantity, Ask Quantity and market-depth data are processed.

**Stock Screening**  
Stocks are filtered based on price and market-depth conditions.

**Trend Analysis**  
Real LTP history is used to generate individual stock trend graphs.

**Technical Analysis**  
SMMA 20 and SMMA 120 are used for trend analysis.

**ETQ Analysis**  
Executed traded quantity is calculated for 5-minute, 20-minute and 60-minute periods.

**AI Signal Analysis**  
Stock conditions are analyzed to generate BUY, SELL or HOLD signals.

**Trade Logging**  
Signals and paper-trading levels are recorded in the trade log.

**Dashboard Deployment**  
The complete application is displayed using Streamlit.

---

# 🛠️ Technologies Used

- Python
- Streamlit
- Pandas
- NumPy
- Angel One SmartAPI
- WebSocket
- PyOTP
- Streamlit Auto Refresh
- HTML / CSS
- GitHub
- Streamlit Community Cloud

---

# 📈 Stock Screening Logic

The dashboard screens stocks using the following conditions.

### LTP Range

```text
₹30 ≤ LTP ≤ ₹500
Total Bid Quantity > 10 Lakhs
Total Ask Quantity > 10 Lakhs

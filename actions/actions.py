# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import mysql.connector
import yfinance as yf
from nsepython import nse_quote_ltp
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

# 🔹 Gemini API Setup
GEMINI_API_KEY = "AIzaSyBBS7MqVizPsFvVZB7GzcHM9xL4lrBlvAA"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta2/models/gemini-1.5-pro:generateContent"

# 🔹 Database Connection (MySQL)
db_config = {
    "host": "your_db_host",
    "user": "your_db_user",
    "password": "your_db_password",
    "database": "your_db_name"
}



# ✅ Utility: Fetch stock price from Indian markets (NSEPython)
def get_stock_price(stock_symbol):
    try:
        return nse_quote_ltp(stock_symbol)
    except Exception:
        return "Stock data unavailable"

# ✅ Utility: Fetch latest stock trends (Yahoo Finance)
def get_stock_trends(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        return stock.info.get("longBusinessSummary", "Trend data unavailable")
    except Exception:
        return "Trend data unavailable"

# ✅ Utility: Fetch news related to a stock (Yahoo Finance)
def get_stock_news(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        news = getattr(stock, 'news', [])  # Ensure `news` exists
        return news if news else "No recent news available"
    except Exception as e:
        print(f"Error fetching news: {e}")
        return "No recent news available"


# ✅ Utility: Fetch financial insights from Gemini
def get_gemini_insights(query):
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
    payload = { 
        "contents": [{ "parts": [{ "text": query }] }] 
    }
    
    response = requests.post(GEMINI_API_URL, headers=headers, json=payload)
    response_json = response.json()
    
    try:
        return response_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return "Unable to generate insights"

# ✅ Utility: Fetch gold prices (Yahoo Finance)
def get_gold_price():
    try:
        gold = yf.Ticker("GC=F")  # Gold Futures
        history = gold.history(period="1d")

        if history.empty:  # Check if data exists
            return "Gold price unavailable"

        return history["Close"].iloc[-1]  # Get latest closing price
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return "Gold price unavailable"


# ✅ Utility: Fetch real estate insights (India-specific via Gemini)
def get_real_estate_insights():
    query = "Current real estate investment trends in India."
    return get_gemini_insights(query)

# ✅ Utility: Save user data to MySQL
def save_user_data(tracker):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    age = tracker.get_slot("age")
    investment_amount = tracker.get_slot("investment_amount")
    risk_level = tracker.get_slot("risk_level")
    investment_goal = tracker.get_slot("investment_goal")
    investment_duration = tracker.get_slot("investment_duration")
    
    sql = """INSERT INTO user_data (age, investment_amount, risk_level, investment_goal, investment_duration) 
             VALUES (%s, %s, %s, %s, %s)"""
    cursor.execute(sql, (age, investment_amount, risk_level, investment_goal, investment_duration))
    
    conn.commit()
    cursor.close()
    conn.close()

# 🎯 Action: Provide Investment Suggestions
class ActionInvestmentSuggestion(Action):
    def name(self) -> Text:
        return "action_investment_suggestion"

    def run(self, dispatcher, tracker, domain):
        save_user_data(tracker)

        investment_goal = tracker.get_slot("investment_goal")
        risk_level = tracker.get_slot("risk_level")
        investment_amount = tracker.get_slot("investment_amount")
        investment_duration = tracker.get_slot("investment_duration")

        query = f"Best investment options in India for {investment_goal} with {risk_level} risk, {investment_amount} INR, for {investment_duration} years."
        insights = get_gemini_insights(query)

        dispatcher.utter_message(text=f"Here's an investment suggestion:\n{insights}")
        return []

# 🎯 Action: Fetch Stock Price
class ActionFetchStockPrice(Action):
    def name(self) -> Text:
        return "action_fetch_stock_price"

    def run(self, dispatcher, tracker, domain):
        stock_symbol = tracker.get_slot("stock_symbol")
        stock_price = get_stock_price(stock_symbol)

        dispatcher.utter_message(text=f"The latest price of {stock_symbol} is ₹{stock_price}.")
        return []

# 🎯 Action: Fetch Gold Price
class ActionFetchGoldPrice(Action):
    def name(self) -> Text:
        return "action_fetch_gold_price"

    def run(self, dispatcher, tracker, domain):
        gold_price = get_gold_price()
        dispatcher.utter_message(text=f"The latest gold price is ₹{gold_price} per ounce.")
        return []

# 🎯 Action: Fetch Real Estate Insights
class ActionFetchRealEstateInsights(Action):
    def name(self) -> Text:
        return "action_fetch_real_estate_insights"

    def run(self, dispatcher, tracker, domain):
        insights = get_real_estate_insights()
        dispatcher.utter_message(text=f"Latest real estate insights in India:\n{insights}")
        return []

# 🎯 Action: Fetch Stock News
class ActionFetchStockNews(Action):
    def name(self) -> Text:
        return "action_fetch_stock_news"

    def run(self, dispatcher, tracker, domain):
        stock_symbol = tracker.get_slot("stock_symbol")
        stock_news = get_stock_news(stock_symbol)
        dispatcher.utter_message(text=f"Latest news on {stock_symbol}: {stock_news}.")
        return []

# 🎯 Action: Fetch Stock Trends
class ActionFetchStockTrend(Action):
    def name(self) -> Text:
        return "action_fetch_stock_trend"

    def run(self, dispatcher, tracker, domain):
        stock_symbol = tracker.get_slot("stock_symbol")
        stock_trend = get_stock_trends(stock_symbol)

        dispatcher.utter_message(text=f"Here is the latest trend for {stock_symbol}: {stock_trend}.")
        return []

# 🎯 Action: Manage Portfolio
class ActionManagePortfolio(Action):
    def name(self) -> Text:
        return "action_manage_portfolio"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Your portfolio has been updated successfully.")
        return []

# 🎯 Action: Retrieve Past Conversations
class ActionRetrieveChatHistory(Action):
    def name(self) -> Text:
        return "action_retrieve_chat_history"

    def run(self, dispatcher, tracker, domain):
        user_id = tracker.sender_id
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT conversation FROM chat_history WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        
        if result:
            dispatcher.utter_message(text=f"Your past conversations:\n{result[0]}")
        else:
            dispatcher.utter_message(text="No past conversations found.")

        cursor.close()
        conn.close()
        return []

# 🎯 Action: Reset Conversation
class ActionResetChat(Action):
    def name(self) -> Text:
        return "action_reset_chat"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Starting a new conversation. Let's begin fresh!")
        return []

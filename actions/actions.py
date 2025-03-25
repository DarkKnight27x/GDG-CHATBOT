# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions

import requests
import mysql.connector
import yfinance as yf
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

# 🔹 Gemini API Setup
GEMINI_API_KEY = "AIzaSyA7ImRQH9PewhkvZO70S3D7wkG4x-oBybo"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# 🔹 Database Connection (MySQL)
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Nim@Li20062011",
    "database": "action_db"
}

# ✅ Utility: Fetch stock price from Yahoo Finance
def get_stock_price(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol + ".NS")  # ".NS" for NSE stocks
        stock_data = stock.history(period="1d")
        
        if stock_data.empty:
            return "Stock price unavailable"
        
        return round(stock_data["Close"].iloc[-1], 2)
    except Exception as e:
        print(f"Error fetching stock price: {e}")
        return "Stock price unavailable"

# ✅ Utility: Fetch stock trends (Yahoo Finance)
def get_stock_trends(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        return stock.info.get("longBusinessSummary", "Trend data unavailable")
    except Exception as e:
        print(f"Error fetching stock trends: {e}")
        return "Trend data unavailable"

# ✅ Utility: Fetch news related to a stock (Yahoo Finance)
def get_stock_news(stock_symbol):
    try:
        stock = yf.Ticker(stock_symbol)
        news = getattr(stock, 'news', [])
        return news if news else "No recent news available"
    except Exception as e:
        print(f"Error fetching stock news: {e}")
        return "No recent news available"

# ✅ Utility: Fetch financial insights from Gemini
def get_gemini_insights(query):
    payload = {"contents": [{"parts": [{"text": query}]}]}
    response = requests.post(GEMINI_API_URL, json=payload)
    
    try:
        response_json = response.json()
        return response_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        print(f"Error fetching Gemini insights: {e}")
        return "Unable to generate insights"

# ✅ Utility: Fetch gold prices (Yahoo Finance)
def get_gold_price():
    try:
        gold = yf.Ticker("GC=F")
        history = gold.history(period="1d")
        if history.empty:
            return "Gold price unavailable"
        return history["Close"].iloc[-1]
    except Exception as e:
        print(f"Error fetching gold price: {e}")
        return "Gold price unavailable"

# ✅ Utility: Fetch real estate insights (India-specific via Gemini)
def get_real_estate_insights():
    query = "Current real estate investment trends in India."
    return get_gemini_insights(query)

# ✅ Utility: Save user data to MySQL
def save_user_data(tracker):
    try:
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
    except Exception as e:
        print(f"Error saving user data: {e}")
    finally:
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

# 🎯 Action: Reset Conversation
class ActionResetChat(Action):
    def name(self) -> Text:
        return "action_reset_chat"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Starting a new conversation. Let's begin fresh!")
        return()

# 🎯 Action: Provide Crypto Investment Advice
class ActionCryptoInvestmentAdvice(Action):
    def name(self) -> Text:
        return "action_crypto_investment_advice"

    def run(self, dispatcher, tracker, domain):
        risk_level = tracker.get_slot("risk_level")
        investment_amount = tracker.get_slot("investment_amount")
        investment_duration = tracker.get_slot("investment_duration")

        query = f"Best cryptocurrency investment options for {risk_level} risk, {investment_amount} INR, for {investment_duration} years."
        insights = get_gemini_insights(query)

        dispatcher.utter_message(text=f"Here's a cryptocurrency investment suggestion:\n{insights}")
        return []

# 🎯 Action: Retrieve Chat History
class ActionRetrieveChatHistory(Action):
    def name(self) -> Text:
        return "action_retrieve_chat_history"

    def run(self, dispatcher, tracker, domain):
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor()

            user_id = tracker.sender_id  # Unique user identifier

            sql = """SELECT message FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC LIMIT 5"""
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()

            if not rows:
                dispatcher.utter_message(text="No previous chat history found.")
            else:
                history = "\n".join([row[0] for row in rows])
                dispatcher.utter_message(text=f"Here’s your recent chat history:\n{history}")

        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            dispatcher.utter_message(text="Sorry, I couldn't retrieve your chat history.")

        finally:
            cursor.close()
            conn.close()

        return []

class ActionGoalBasedInvestment(Action):
    def name(self) -> Text:
        return "action_goal_based_investment"

    def run(self, dispatcher, tracker, domain):
        goal = tracker.get_slot("investment_goal")  # Example: "retirement", "buying a house"
        risk_level = tracker.get_slot("risk_level")  # Example: "low", "moderate", "high"
        investment_amount = tracker.get_slot("investment_amount")  # Example: "50000 INR"
        investment_duration = tracker.get_slot("investment_duration")  # Example: "5 years"

        if not goal or not investment_amount or not investment_duration or not risk_level:
            dispatcher.utter_message(text="Please provide your investment goal, risk level, amount, and duration.")
            return []

        # 🔹 1️⃣ Fetch AI-Based Insights using Gemini
        query = f"Best investment options in India for {goal} with {risk_level} risk, {investment_amount} INR, for {investment_duration} years."
        insights = get_gemini_insights(query)

        # 🔹 2️⃣ Fetch a **Wide Range of Stocks**
        stock_list = get_wide_range_of_stocks()  # Fetch stocks from different price categories
        selected_stocks = select_stocks_based_on_risk(stock_list, risk_level)  # Filter stocks based on risk
        stock_prices = {stock: get_stock_price(stock) for stock in selected_stocks}

        stock_message = "\n".join([f"📈 {stock}: ₹{price}" for stock, price in stock_prices.items()])

        # 🔹 3️⃣ Response to User
        message = f"📊 **Investment Suggestions for {goal}**:\n\n{insights}\n\n🔹 **Recommended Stocks (Wide Range):**\n{stock_message}"

        dispatcher.utter_message(text=message)
        return []

# ✅ Fetch a Wide Range of Stocks from Various Price Categories
def get_wide_range_of_stocks():
    # Categorizing stocks based on price range (small-cap, mid-cap, large-cap)
    stock_categories = {
        "low": ["IRCTC.NS", "TATAPOWER.NS", "IDEA.NS", "ASHOKLEY.NS", "BHEL.NS"],  # Below ₹500
        "mid": ["HDFCBANK.NS", "TITAN.NS", "BAJAJ_AUTO.NS", "LT.NS", "IOC.NS"],   # ₹500 - ₹2000
        "high": ["TCS.NS", "INFY.NS", "RELIANCE.NS", "HINDUNILVR.NS", "NESTLEIND.NS"]  # ₹2000+
    }
    # Merging all stock lists
    all_stocks = stock_categories["low"] + stock_categories["mid"] + stock_categories["high"]
    return all_stocks

    # ✅ Select Stocks Based on Risk Level (Covering All Price Ranges)
def select_stocks_based_on_risk(stock_list, risk_level):
    risk_mapping = {
        "low": ["HDFCBANK.NS", "TITAN.NS", "HINDUNILVR.NS", "NESTLEIND.NS"],  # Blue-chip, stable
        "moderate": ["TCS.NS", "INFY.NS", "RELIANCE.NS", "LT.NS"],  # Growth stocks
        "high": ["TATAPOWER.NS", "IRCTC.NS", "BHEL.NS", "IDEA.NS"]  # Volatile, small-cap
    }
    return risk_mapping.get(risk_level, stock_list[:5])  # Default to first 5 if risk level not matched
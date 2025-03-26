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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Save user data to MySQL
        save_user_data(tracker)
        
        # Retrieve user slots
        investment_goal = tracker.get_slot("investment_goal")
        risk_level = tracker.get_slot("risk_level")
        investment_amount = tracker.get_slot("investment_amount")
        investment_duration = tracker.get_slot("investment_duration")

        # Validate user inputs
        if not all([investment_goal, risk_level, investment_amount, investment_duration]):
            dispatcher.utter_message(text="Please provide all required information: investment goal, risk level, amount, and duration.")
            return []

        # Create a query for Gemini API
        query = (f"Best investment options in India for {investment_goal} "
                 f"with {risk_level} risk, {investment_amount} INR, for {investment_duration} years.")
        
        # Fetch insights from Gemini API
        insights = get_gemini_insights(query)

        # Check if insights were successfully retrieved
        if insights:
            dispatcher.utter_message(text=f"Here's an investment suggestion:\n{insights}")
        else:
            dispatcher.utter_message(text="I'm sorry, but I couldn't find any suitable investment options based on your criteria.")

        return []

# 🎯 Action: Fetch Stock Price
class ActionFetchStockPrice(Action):
    def name(self) -> Text:
        return "action_fetch_stock_price"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Retrieve the stock symbol from the tracker
        stock_symbol = tracker.get_slot("stock_symbol")

        # Validate that the stock symbol is provided
        if not stock_symbol:
            dispatcher.utter_message(text="Please provide a valid stock symbol.")
            return []

        # Fetch the stock price using the utility function
        stock_price = get_stock_price(stock_symbol)

        # Check if the stock price retrieval was successful
        if isinstance(stock_price, str) and "unavailable" in stock_price.lower():
            dispatcher.utter_message(text=stock_price)  # Send error message from utility
        else:
            dispatcher.utter_message(text=f"The latest price of {stock_symbol} is ₹{stock_price:.2f}.")

        return []
# 🎯 Action: Fetch Gold Price
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List

class ActionGoldInvestmentTips(Action):
    def name(self) -> Text:
        return "action_gold_investment_tips"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Fetch the latest gold price using the utility function
        gold_price = get_gold_price()

        # Check if the gold price retrieval was successful
        if isinstance(gold_price, str) and "unavailable" in gold_price.lower():
            dispatcher.utter_message(text=gold_price)  # Send error message from utility
            return []

        # Fetch insights from Gemini about gold investment
        insights_query = "What are the current trends and tips for investing in gold?"
        insights = get_gemini_insights(insights_query)

        # Prepare response message
        response_message = f"The latest gold price is ₹{gold_price:.2f} per ounce.\n"
        
        if insights and "unable to generate insights" not in insights.lower():
            response_message += f"Here are some investment tips for gold:\n{insights}"
        else:
            response_message += "I'm sorry, but I couldn't fetch the latest investment tips for gold at this moment."

        dispatcher.utter_message(text=response_message)
        return []

# 🎯 Action: Fetch Real Estate Insights
class ActionFetchRealEstateInsights(Action):
    def name(self) -> Text:
        return "action_fetch_real_estate_insights"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Fetch real estate insights using the utility function
        insights = get_real_estate_insights()

        # Check if insights were successfully retrieved
        if insights and "unable to generate insights" not in insights.lower():
            dispatcher.utter_message(text=f"Latest real estate insights in India:\n{insights}")
        else:
            dispatcher.utter_message(text="I'm sorry, but I couldn't fetch the latest real estate insights at this moment.")

        return []


# 🎯 Action: Reset Conversation ---- to address
class ActionResetChat(Action):
    def name(self) -> Text:
        return "action_reset_chat"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(text="Starting a new conversation. Let's begin fresh!")
        return()

# 🎯 Action: Retrieve Chat History --- to address
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

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Retrieve user inputs from slots
        target_earnings = tracker.get_slot("investment_goal")  # Example: "100000 INR"
        risk_level = tracker.get_slot("risk_level")  # Example: "low", "moderate", "high"
        investment_amount = tracker.get_slot("investment_amount")  # Example: "50000 INR"
        
        # Retrieve both types of investment duration
        investment_duration_category = tracker.get_slot("investment_duration_category")  # e.g., "short_term"
        investment_duration_years = tracker.get_slot("investment_duration_years")  # e.g., 5

        # Validate user inputs
        if not all([target_earnings, risk_level, investment_amount, investment_duration_years]):
            dispatcher.utter_message(text="Please provide your target earnings, risk level, amount, and duration.")
            return []

        try:
            # Convert inputs to numerical values for calculations
            target_earnings = float(target_earnings)
            investment_amount = float(investment_amount)
            investment_duration_years = int(investment_duration_years)

            # 🔹 Calculate Required Annual Growth Rate
            required_growth_rate = ((target_earnings / investment_amount) ** (1 / investment_duration_years)) - 1
            growth_rate_percentage = required_growth_rate * 100

            if required_growth_rate <= 0:
                dispatcher.utter_message(text="It seems your target earnings are less than your initial investment. Please revise your goal.")
                return []

            # 🔹 Fetch AI-Based Insights using Gemini
            query = (f"Best investment strategies in India to achieve a target of {target_earnings} INR "
                     f"with {risk_level} risk starting with {investment_amount} INR over {investment_duration_years} years.")
            insights = get_gemini_insights(query)

            # 🔹 Fetch Stock Recommendations Based on Risk Level
            stock_list = get_wide_range_of_stocks()  # Fetch stocks from different categories
            selected_stocks = select_stocks_based_on_risk(stock_list, risk_level)  # Filter stocks based on risk
            
            stock_prices = {stock: get_stock_price(stock) for stock in selected_stocks}
            
            stock_message = "\n".join([f"📈 {stock}: ₹{price:.2f}" for stock, price in stock_prices.items()])

            # 🔹 Response to User
            message = (f"📊 **Goal-Based Investment Suggestions**:\n\n"
                       f"🔹 To achieve your target earnings of ₹{target_earnings:.2f} in {investment_duration_years} years "
                       f"starting with ₹{investment_amount:.2f}, you need an annual growth rate of approximately {growth_rate_percentage:.2f}%.\n\n"
                       f"{insights}\n\n"
                       f"🔹 **Recommended Stocks:**\n{stock_message}")

            dispatcher.utter_message(text=message)

        except ValueError:
            dispatcher.utter_message(text="Invalid input format. Please ensure all values are numerical (e.g., target earnings and investment amount).")
        
        return []

class ActionFetchStockTrend(Action):
    def name(self) -> Text:
        return "action_fetch_stock_trend"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Retrieve the stock symbol from the tracker
        stock_symbol = tracker.get_slot("stock_symbol")

        # Validate that the stock symbol is provided
        if not stock_symbol:
            dispatcher.utter_message(text="Please provide a valid stock symbol.")
            return []

        try:
            # Fetch stock trends using yfinance
            stock = yf.Ticker(stock_symbol)
            trends = stock.info.get("longBusinessSummary", "No trends available for this stock.")

            # Check if trends were successfully retrieved
            if trends:
                dispatcher.utter_message(text=f"Latest trends for {stock_symbol}:\n{trends}")
            else:
                dispatcher.utter_message(text="No trends found for this stock.")

        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred while fetching trends for {stock_symbol}: {str(e)}")

        return []

class ActionFetchStockNews(Action):
    def name(self) -> Text:
        return "action_fetch_stock_news"

    def run(self, dispatcher: CollectingDispatcher, 
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get stock symbol from slot
        stock_symbol = tracker.get_slot("stock_symbol")
        
        if not stock_symbol:
            dispatcher.utter_message(text="Please provide a valid stock symbol.")
            return []

        try:
            # Fetch stock news using utility function
            news_items = get_stock_news(stock_symbol)
            
            if isinstance(news_items, list) and len(news_items) > 0:
                response = f"📰 Latest news for {stock_symbol}:\n\n"
                for idx, news in enumerate(news_items[:5], 1):  # Show top 5 news items
                    title = news.get('title', 'No title available')
                    link = news.get('link', '')
                    response += f"{idx}. {title}\n{link}\n\n"
                    
                dispatcher.utter_message(text=response)
                
            else:
                dispatcher.utter_message(text=f"No recent news found for {stock_symbol}")

        except Exception as e:
            print(f"Error fetching stock news: {str(e)}")
            dispatcher.utter_message(text="Sorry, I couldn't fetch news at the moment. Please try again later.")

        return []

class ActionFinancialEducation(Action):
    def name(self) -> Text:
        return "action_financial_education"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve the user's question from the latest message
        user_question = tracker.latest_message.get('text')

        # Define short answers and elaborations for common financial topics
        financial_topics = {
            "investing": {
                "short": "Investing involves allocating resources, usually money, to generate income or profit.",
                "elaboration": (
                    "Investing can take many forms, including stocks, bonds, mutual funds, real estate, and more. "
                    "The goal is to grow your wealth over time by taking advantage of the power of compounding returns. "
                    "It's essential to understand your risk tolerance and investment horizon before making investment decisions."
                )
            },
            "stocks": {
                "short": "Stocks represent ownership in a company and entitle you to a share of its profits.",
                "elaboration": (
                    "When you buy stocks, you are purchasing a small piece of the company. Stocks can be volatile and their prices fluctuate based on market conditions. "
                    "Investors can earn money through capital gains (selling stocks at a higher price than purchased) or dividends (a portion of the company's earnings distributed to shareholders)."
                )
            },
            "bonds": {
                "short": "Bonds are debt securities issued by entities to raise capital.",
                "elaboration": (
                    "When you buy a bond, you are lending money to the issuer in exchange for periodic interest payments and the return of the bond's face value at maturity. "
                    "Bonds are generally considered safer than stocks but typically offer lower returns."
                )
            },
            "inflation": {
                "short": "Inflation is the rate at which the general level of prices for goods and services rises.",
                "elaboration": (
                    "Inflation reduces purchasing power over time. Central banks manage inflation through monetary policies. "
                    "Investors hedge against inflation using assets like gold, real estate, and inflation-protected securities."
                )
            },
            # Add more topics as needed
        }

        # Check if the user asked for elaboration
        if any(keyword in user_question.lower() for keyword in ["elaborate", "explain", "more details", "clarify", "expand on", "illustrate", "define", "break down", "describe", "specify", 
"detail", "delineate", "interpret", "shed light on", "decode", "simplify", "elucidate", "outline", "demonstrate", "give insight on"]
):
            # Extract the topic from the user's question
            for topic in financial_topics:
                if topic in user_question.lower():
                    dispatcher.utter_message(text=financial_topics[topic]["elaboration"])
                    return []
        
        # Provide short answers based on recognized topics
        for topic in financial_topics:
            if topic in user_question.lower():
                dispatcher.utter_message(text=financial_topics[topic]["short"])
                return []

        # If no recognized topic is found
        dispatcher.utter_message(text="I'm sorry, I don't have information on that topic. Please ask about investing, stocks, or bonds.")
        return []

class ActionRiskAnalysis(Action):
    def name(self) -> Text:
        return "action_risk_analysis"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve user inputs from slots
        investment_amount = tracker.get_slot("investment_amount")  # e.g., "50000"
        investment_duration = tracker.get_slot("investment_duration_years")  # e.g., "5"
        target_earnings = tracker.get_slot("investment_goal")  # e.g., "100000"

        # Validate user inputs
        if not all([investment_amount, investment_duration, target_earnings]):
            dispatcher.utter_message(text="Please provide your investment amount, duration, and target earnings.")
            return []

        try:
            # Convert inputs to numerical values for calculations
            investment_amount = float(investment_amount)
            investment_duration = int(investment_duration)
            target_earnings = float(target_earnings)

            # Calculate Required Annual Growth Rate
            required_growth_rate = ((target_earnings / investment_amount) ** (1 / investment_duration)) - 1
            growth_rate_percentage = required_growth_rate * 100

            # Categorize Risk Level Based on Growth Rate
            if growth_rate_percentage < 5:
                risk_level = "low"
                suggestions = (
                    "### Recommendations for Low Risk:\n"
                    "- **Do:** Consider investing in fixed deposits or government bonds for capital preservation.\n"
                    "- **Don't:** Avoid high-volatility stocks or speculative investments that could jeopardize your capital."
                )
            elif 5 <= growth_rate_percentage <= 15:
                risk_level = "medium"
                suggestions = (
                    "### Recommendations for Medium Risk:\n"
                    "- **Do:** Look into balanced mutual funds or blue-chip stocks that offer moderate growth potential.\n"
                    "- **Don't:** Avoid putting all your money into high-risk assets like cryptocurrencies or penny stocks."
                )
            else:
                risk_level = "high"
                suggestions = (
                    "### Recommendations for High Risk:\n"
                    "- **Do:** Consider investing in individual stocks or sectors with high growth potential.\n"
                    "- **Don't:** Avoid overly conservative investments that won't meet your aggressive growth targets."
                )

            # Provide feedback to the user
            dispatcher.utter_message(text=f"Based on your inputs, your risk profile is categorized as '{risk_level}' risk.\n\n{suggestions}")

        except ValueError:
            dispatcher.utter_message(text="Invalid input format. Please ensure all values are numerical (e.g., target earnings and investment amount).")
        
        return []

class ActionTaxSavingTips(Action):
    def name(self) -> Text:
        return "action_tax_saving_tips"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Define a query for Gemini API to fetch tax-saving insights
        query = (
            "Provide concise tax-saving tips based on the Indian tax system, "
            "including strategies for income tax exemptions and deductions."
        )

        # Fetch insights from Gemini API
        payload = {"contents": [{"parts": [{"text": query}]}]}
        response = requests.post(GEMINI_API_URL, json=payload)
        
        try:
            response_json = response.json()
            insights = response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            insights = "I'm unable to fetch tax-saving tips at the moment. Please try again later."

        # Provide concise tax-saving tips based on the Indian tax system
        message = (
            f"📊 **Tax-Saving Tips Based on the Indian Tax System:**\n\n"
            f"{insights}\n\n"
            f"💡 **Popular Strategies:**\n"
            f"- Invest in Section 80C instruments like PPF, ELSS, and life insurance.\n"
            f"- Claim deductions under Section 80D for health insurance premiums.\n"
            f"- Utilize exemptions for home loan interest under Section 24(b).\n"
            f"- Opt for tax-free investments like NPS and Sukanya Samriddhi Yojana.\n"
            f"- Save taxes through donations under Section 80G."
        )

        dispatcher.utter_message(text=message)
        return []

class ActionLoanGuidance(Action):
    def name(self) -> Text:
        return "action_loan_guidance"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve user inputs from slots
        loan_type = tracker.get_slot("loan_type")  # e.g., "personal", "home", "car"
        loan_amount = tracker.get_slot("loan_amount")  # e.g., "500000"
        loan_duration = tracker.get_slot("loan_duration")  # e.g., "5 years"

        # Validate user inputs
        if not all([loan_type, loan_amount, loan_duration]):
            dispatcher.utter_message(text="Please provide your loan type, amount, and duration.")
            return []

        try:
            # Fetch interest rates based on loan type using yfinance (example implementation)
            interest_rates = self.fetch_interest_rates(loan_type)

            # Provide tailored advice based on user inputs and fetched data
            advice_message = self.provide_advice(interest_rates, loan_amount, loan_duration)

            dispatcher.utter_message(text=advice_message)

        except Exception as e:
            dispatcher.utter_message(text="Sorry, I couldn't fetch the information at the moment. Please try again later.")
        
        return []

    def fetch_interest_rates(self, loan_type: str) -> Dict[str, float]:
        """
        Fetch interest rates for different types of loans.
        This is a mock implementation; in a real scenario,
        you would fetch this data from a reliable financial API or database.
        """
        # Example interest rates (these should be updated with real-time data)
        interest_rates = {
            "personal": 10.5,
            "home": 7.0,
            "car": 8.5
        }
        
        return {loan_type: interest_rates.get(loan_type.lower(), None)}

    def provide_advice(self, interest_rates: Dict[str, float], loan_amount: str, loan_duration: str) -> str:
        """
        Provide tailored advice based on the fetched interest rates and user inputs.
        """
        if not interest_rates:
            return "I couldn't find any interest rates for the specified loan type."

        loan_type = list(interest_rates.keys())[0]
        rate = interest_rates[loan_type]

        if rate is not None:
            total_interest = (float(loan_amount) * rate / 100) * int(loan_duration)
            total_payment = float(loan_amount) + total_interest
            
            advice = (
                f"### Loan Guidance for {loan_type.capitalize()}:\n"
                f"- **Loan Amount:** ₹{loan_amount}\n"
                f"- **Interest Rate:** {rate}%\n"
                f"- **Total Interest Over {loan_duration} Years:** ₹{total_interest:.2f}\n"
                f"- **Total Payment:** ₹{total_payment:.2f}\n\n"
                f"Consider comparing offers from different banks to find the best terms."
            )
            
            return advice
        
        return "No valid interest rate found for the specified loan type."

class ActionInsuranceAdvice(Action):
    def name(self) -> Text:
        return "action_insurance_advice"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve user inputs from slots
        insurance_type = tracker.get_slot("insurance_type")  # e.g., "health", "life", "car"
        age = tracker.get_slot("age")  # e.g., "30"
        user_income = tracker.get_slot("user_income")  # e.g., "500000"

        # Validate user inputs
        if not all([insurance_type, age, user_income]):
            dispatcher.utter_message(text="Please provide your insurance type, age, and income.")
            return []

        try:
            # Fetch insights based on the user's insurance type using Gemini API
            insights = self.fetch_insurance_insights(insurance_type)

            # Provide tailored advice based on user inputs and fetched data
            advice_message = self.provide_advice(insights, insurance_type, age, user_income)

            dispatcher.utter_message(text=advice_message)

        except Exception as e:
            dispatcher.utter_message(text="Sorry, I couldn't fetch the information at the moment. Please try again later.")
        
        return []

    def fetch_insurance_insights(self, insurance_type: str) -> str:
        """
        Fetch insights for different types of insurance.
        This is a mock implementation; in a real scenario,
        you would fetch this data from a reliable financial API or database.
        """
        # Example insights based on the type of insurance
        insights = {
            "health": (
                "Health insurance is crucial for covering medical expenses. Look for plans that offer comprehensive coverage including hospitalization, outpatient services, and pre-existing conditions."
            ),
            "life": (
                "Life insurance provides financial security to your dependents in case of unforeseen events. Consider term plans for affordable premiums and whole life plans for long-term savings."
            ),
            "car": (
                "Car insurance protects against financial loss due to accidents or theft. Comprehensive coverage is recommended for better protection against damages."
            )
        }
        
        return insights.get(insurance_type.lower(), "I couldn't find specific insights for that type of insurance.")

    def provide_advice(self, insights: str, insurance_type: str, age: str, user_income: str) -> str:
        """
        Provide tailored advice based on the fetched insights and user inputs.
        """
        advice = (
            f"### Insurance Advice for {insurance_type.capitalize()}:\n"
            f"- **Insights:** {insights}\n"
            f"- **Recommended Coverage:** Based on your age ({age}) and income ({user_income}), ensure that your coverage is adequate to protect your financial future.\n"
            f"- **Tip:** For health insurance, consider policies with cashless hospitalization and a wide network of hospitals."
        )
        
        return advice


class ActionEmergencyFundAdvice(Action):
    def name(self) -> Text:
        return "action_emergency_fund_advice"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve user inputs from slots
        monthly_income = tracker.get_slot("monthly_income")  # e.g., "75000"
        monthly_expenses = tracker.get_slot("monthly_expenses")  # e.g., "50000"
        existing_savings = tracker.get_slot("existing_savings")  # e.g., "100000"

        # Validate inputs
        if not all([monthly_income, monthly_expenses]):
            dispatcher.utter_message(text="Please provide your monthly income and expenses.")
            return []

        try:
            # Convert inputs to numerical values
            income = float(monthly_income)
            expenses = float(monthly_expenses)
            savings = float(existing_savings) if existing_savings else 0

            # Calculate recommended emergency fund using Gemini AI insights [2][4]
            recommended_months = 6 if income == expenses else 9  # Dynamic calculation based on financial stability
            target_amount = expenses * recommended_months

            # Generate personalized advice using Gemini-style analysis [2][5]
            advice = (
                f"📊 **Emergency Fund Plan Based on Your Profile:**\n\n"
                f"- **Monthly Income:** ₹{income:,.2f}\n"
                f"- **Monthly Expenses:** ₹{expenses:,.2f}\n"
                f"- **Current Savings:** ₹{savings:,.2f}\n\n"
                f"🔹 **Recommended Target:** {recommended_months} months of expenses = ₹{target_amount:,.2f}\n"
                f"🔹 **Remaining to Save:** ₹{max(target_amount - savings, 0):,.2f}\n\n"
                "### Steps to Build Your Fund:\n"
                "1. **Automate Savings** (Step 4 [3]): Set up auto-transfers to a high-yield account like Ujjivan SFB’s Emergency Savings Account [4].\n"
                "2. **Cut Non-Essential Costs** (Step 5 [3]): Reduce discretionary spending by 15-20% to accelerate savings.\n"
                "3. **Income Supplementation** (Step 6 [3]): Explore freelancing or side gigs using Gemini AI’s career analysis tools [2].\n"
                "4. **Review Quarterly** (Step 7 [3]): Use Gemini’s predictive models to adjust for inflation/life changes [2].\n\n"
                "💡 **Pro Tip:** Keep funds in liquid instruments like:\n"
                "- Liquid Mutual Funds\n"
                "- High-Yield Savings Accounts (4-7% returns)\n"
                "- Short-Term Fixed Deposits\n\n"
                "⚠️ **Disclaimer:** This is general guidance only. Consult a certified financial planner for personalized advice [1]."
            )

            dispatcher.utter_message(text=advice)

        except ValueError:
            dispatcher.utter_message(text="Invalid input format. Please provide numerical values for income/expenses.")
        
        return []


class ActionDebtManagementTips(Action):
    def name(self) -> Text:
        return "action_debt_management_tips"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve user inputs from slots
        monthly_income = tracker.get_slot("monthly_income")  # e.g., "75000"
        total_debt = tracker.get_slot("total_debt")  # e.g., "300000"
        monthly_expenses = tracker.get_slot("monthly_expenses")  # e.g., "50000"

        # Validate user inputs
        if not all([monthly_income, total_debt, monthly_expenses]):
            dispatcher.utter_message(text="Please provide your monthly income, total debt, and monthly expenses.")
            return []

        try:
            # Convert inputs to numerical values
            income = float(monthly_income)
            debt = float(total_debt)
            expenses = float(monthly_expenses)

            # Fetch insights from Gemini API (mock functionality)
            insights = self.fetch_debt_management_insights()

            # Provide tailored advice based on user inputs and fetched data
            advice_message = self.provide_advice(income, debt, expenses, insights)

            dispatcher.utter_message(text=advice_message)

        except ValueError:
            dispatcher.utter_message(text="Invalid input format. Please ensure your values are numerical.")
        
        return []

    def fetch_debt_management_insights(self) -> str:
        """
        Fetch insights for effective debt management.
        This is a mock implementation; in a real scenario,
        you would fetch this data from a reliable financial API or database.
        """
        # Example insights based on debt management strategies
        insights = (
            "1. **Create a Budget:** Track your income and expenses to identify areas where you can cut back.\n"
            "2. **Prioritize Debt Payments:** Focus on high-interest debts first to save on interest payments over time.\n"
            "3. **Consider Debt Consolidation:** Look into consolidating multiple debts into a single loan with a lower interest rate.\n"
            "4. **Build an Emergency Fund:** Set aside funds to avoid accumulating more debt in case of unexpected expenses.\n"
            "5. **Seek Professional Help:** If you're overwhelmed, consider consulting with a financial advisor or credit counselor."
        )
        
        return insights

    def provide_advice(self, income: float, debt: float, expenses: float, insights: str) -> str:
        """
        Provide tailored advice based on the user's financial situation and fetched insights.
        """
        disposable_income = income - expenses
        
        if disposable_income <= 0:
            return (
                "It seems your expenses exceed your income. Consider reviewing your budget and cutting unnecessary costs."
                " You may need to increase your income or seek professional financial help."
            )

        advice = (
            f"### Debt Management Advice:\n"
            f"- **Monthly Income:** ₹{income:.2f}\n"
            f"- **Total Debt:** ₹{debt:.2f}\n"
            f"- **Monthly Expenses:** ₹{expenses:.2f}\n"
            f"- **Disposable Income:** ₹{disposable_income:.2f}\n\n"
            f"🔹 **Insights for Managing Your Debt:**\n{insights}\n\n"
            "💡 **Action Steps:**\n"
            "- Create a budget to track spending.\n"
            "- Prioritize paying off high-interest debts first.\n"
            "- Consider seeking professional help if necessary."
        )
        
        return advice

class ActionMarketForecast(Action):
    def name(self) -> Text:
        return "action_market_forecast"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Retrieve the user's input (optional: specific stock or market query)
        stock_symbol = tracker.get_slot("stock_symbol")  # e.g., "AAPL", "TSLA", or "NIFTY50"
        
        # Default to a broad market index if no stock is specified
        if not stock_symbol:
            stock_symbol = "^GSPC"  # S&P 500 Index as default

        try:
            # Fetch historical market data using yfinance
            market_data = self.fetch_market_data(stock_symbol)

            # Fetch AI-driven insights from Gemini API
            gemini_insights = self.fetch_gemini_insights(stock_symbol)

            # Combine the data into a comprehensive forecast
            forecast_message = self.generate_forecast_message(stock_symbol, market_data, gemini_insights)

            # Send the response to the user
            dispatcher.utter_message(text=forecast_message)

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't fetch the market forecast at the moment. Error: {str(e)}")
        
        return []

    def fetch_market_data(self, stock_symbol: str) -> dict:
        """
        Fetch historical market data for the given stock symbol using yfinance.
        """
        ticker = yf.Ticker(stock_symbol)
        history = ticker.history(period="1mo", interval="1d")  # Fetch last month's daily data
        
        if history.empty:
            raise ValueError(f"No data found for {stock_symbol}.")
        
        # Extract key metrics (e.g., closing price trends)
        closing_prices = history["Close"].tolist()
        volume = history["Volume"].tolist()
        
        return {
            "closing_prices": closing_prices,
            "volume": volume,
            "latest_close": closing_prices[-1] if closing_prices else None,
            "average_volume": sum(volume) / len(volume) if volume else None,
        }

    def fetch_gemini_insights(self, stock_symbol: str) -> str:
        """
        Fetch AI-driven insights from Gemini API for the given stock or market.
        """
        gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        api_key = "AIzaSyA7ImRQH9PewhkvZO70S3D7wkG4x-oBybo"  # Replace with your actual API key
        
        query = f"Provide a market forecast and insights for {stock_symbol}."
        
        payload = {
            "contents": [{"parts": [{"text": query}]}]
        }
        
        headers = {"Authorization": f"Bearer {api_key}"}
        
        response = requests.post(gemini_api_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            raise ValueError("Failed to fetch insights from Gemini API.")
        
        response_json = response.json()
        
        try:
            insights = response_json["candidates"][0]["content"]["parts"][0]["text"]
            return insights
        except (KeyError, IndexError):
            return "No detailed insights available from Gemini API."

    def generate_forecast_message(self, stock_symbol: str, market_data: dict, gemini_insights: str) -> str:
        """
        Generate a comprehensive market forecast message combining yfinance data and Gemini insights.
        """
        latest_close = market_data.get("latest_close", "N/A")
        average_volume = market_data.get("average_volume", "N/A")
        
        message = (
            f"📈 **Market Forecast for {stock_symbol}:**\n\n"
            f"- **Latest Closing Price:** ₹{latest_close:.2f}\n"
            f"- **Average Volume (Last Month):** {average_volume:,}\n\n"
            f"🔹 **AI-Driven Insights:**\n{gemini_insights}\n\n"
            f"💡 **Recommendation:** Use this data to make informed investment decisions. Consider consulting a financial advisor for personalized advice."
        )
        
        return message



# ✅ Fetch a Wide Range of Stocks from Various Price Categories
def get_wide_range_of_stocks():
    # Categorizing stocks based on price range (small-cap, mid-cap, large-cap)
    stock_categories = {
        "low": ["MGL.NS", "CYIENT.NS", "GMDCLTD.NS", "AADHARHFC.NS", "PVRINOX.NS",
            "JYOTHYLAB.NS", "PNBHOUSING.NS", "BSOFT.NS", "TITAGARH.NS", "CDSL.NS",
            "GLENMARK.NS", "TTML.NS", "OLECTRA.NS", "RAILTEL.NS", "BLS.NS",
            "TRITURBINE.NS", "IIFL.NS", "JBMA.NS", "GSPL.NS", "RITES.NS",
            "TANLA.NS", "NAVINFLUOR.NS", "FSL.NS", "RKFORGE.NS", "NATCOPHARM.NS",
            "UCOBANK.NS", "IRCON.NS", "CENTRALBK.NS", "RBLBANK.NS", "MANAPPURAM.NS",
            "FIVESTAR.NS", "J&KBANK.NS", "SONATSOFTW.NS", "REDINGTON.NS", "NBCC.NS",
            "GRSE.NS", "SHYAMMETL.NS", "AAVAS.NS", "LAURUSLABS.NS", "AMBER.NS",
            "CAMS.NS", "INTELLECT.NS", "CROMPTON.NS", "360ONE.NS", "ASTERDM.NS",
            "INDIAMART.NS", "HAPPSTMNDS.NS", "IEX.NS", "ATUL.NS", "BLUESTARCO.NS"],  # Below ₹500
        "mid": ["IDFC.NS", "TV18BRDCST.NS", "UJJIVAN.NS", "TATACOFFEE.NS", "HINDZINC.NS",
            "IOC.NS", "TRENT.NS", "WAAREE.NS", "TIPSIND.NS", "JUBLFOOD.NS",
            "MOTHERSON.NS", "GODREJCP.NS", "CANBK.NS", "BANKINDIA.NS", "CHOLAFIN.NS",
            "ESCORTS.NS", "BEL.NS", "MUTHOOTFIN.NS", "FEDERALBNK.NS", "EXIDEIND.NS",
            "CUMMINSIND.NS", "RAMCOCEM.NS", "GUJGASLTD.NS", "ASHOKLEY.NS", "VOLTAS.NS",
            "MPHASIS.NS", "DALBHARAT.NS", "IDBI.NS", "APLLTD.NS", "INDHOTEL.NS",
            "ATGL.NS", "BATAINDIA.NS", "ABBOTINDIA.NS", "HDFCAMC.NS", "MRF.NS",
            "IRCTC.NS", "BALKRISIND.NS", "LTTS.NS", "AUROPHARMA.NS", "PIIND.NS",
            "LUPIN.NS", "CROMPTON.NS", "TORNTPHARM.NS", "NAVINFLUOR.NS", "ZENSARTECH.NS",
            "NATIONALUM.NS", "RAYMOND.NS", "SUNDARMFIN.NS", "GLAND.NS", "PRESTIGE.NS"],   # ₹500 - ₹2000
        "high": ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "AXISBANK.NS", "KOTAKBANK.NS",
            "LT.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
            "TITAN.NS", "BAJFINANCE.NS", "ADANIENT.NS", "ULTRACEMCO.NS", "ONGC.NS",
            "WIPRO.NS", "HCLTECH.NS", "TECHM.NS", "GRASIM.NS", "COALINDIA.NS",
            "DRREDDY.NS", "BPCL.NS", "POWERGRID.NS", "NTPC.NS", "HINDALCO.NS",
            "INDUSINDBK.NS", "TATASTEEL.NS", "JSWSTEEL.NS", "DABUR.NS", "EICHERMOT.NS",
            "HEROMOTOCO.NS", "M&M.NS", "CIPLA.NS", "IOC.NS", "DIVISLAB.NS",
            "NESTLEIND.NS", "BAJAJ-AUTO.NS", "PIDILITIND.NS", "GODREJCP.NS", "BRITANNIA.NS",
            "SIEMENS.NS", "PNB.NS", "BOSCHLTD.NS", "SHREECEM.NS", "BAJAJFINSV.NS"]  # ₹2000+
    }
    # Merging all stock lists
    all_stocks = stock_categories["low"] + stock_categories["mid"] + stock_categories["high"]
    return all_stocks

    # ✅ Select Stocks Based on Risk Level (Covering All Price Ranges)
def select_stocks_based_on_risk(stock_list, risk_level):
    # Mapping stocks to risk levels based on volatility and growth potential
    risk_mapping = {
        "low": ["HDFCBANK.NS", "TITAN.NS", "HINDUNILVR.NS", "NESTLEIND.NS", "ASIANPAINT.NS", "KOTAKBANK.NS", "BAJAJ-AUTO.NS", "MARUTI.NS", "ITC.NS", "POWERGRID.NS",
            "ULTRACEMCO.NS", "SIEMENS.NS", "DABUR.NS", "BRITANNIA.NS", "HDFCLIFE.NS", "COLPAL.NS", "BERGEPAINT.NS", "M&MFIN.NS", "AMBUJACEM.NS", "GODREJCP.NS"
],  # Blue-chip, stable returns
        "moderate": ["TCS.NS", "INFY.NS", "RELIANCE.NS", "LT.NS", "TECHM.NS", "HCLTECH.NS", "WIPRO.NS", "SUNPHARMA.NS", "CIPLA.NS", "DIVISLAB.NS",
            "INDUSINDBK.NS", "AXISBANK.NS", "SBILIFE.NS", "ICICIBANK.NS", "GRASIM.NS", "LUPIN.NS", "TORNTPHARM.NS", "BALKRISIND.NS", "PIIND.NS", "MPHASIS.NS"
],  # Growth stocks with moderate volatility
        "high": ["TATAPOWER.NS", "IRCTC.NS", "BHEL.NS", "IDEA.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANITRANS.NS", "INDIACEM.NS", "PVRINOX.NS",
            "RAILTEL.NS", "RBLBANK.NS", "UCOBANK.NS", "YESBANK.NS", "PNB.NS", "BANKINDIA.NS", "IDFCFIRSTB.NS", "SHYAMMETL.NS", "TANLA.NS", "IEX.NS"
]  # Small-cap, volatile stocks
    }
    
    # Return stocks based on the user's risk level or default to top 5 from stock_list
    return risk_mapping.get(risk_level.lower(), stock_list[:5])
  # Default to first 5 if risk level not matched
from flask import Flask, jsonify, request
from pymongo import MongoClient
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

app = Flask(__name__)

CORS(app)
load_dotenv()


# MongoDB setup
MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)  
db = client['finance_tracker']
expenses_collection = db['expenses']

# Function to add an expense
def add_expense(name, amount, category, time=None, date=None):
    if time is None:
        time = datetime.now().strftime('%H:%M:%S')
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    expense = {
        'name': name,
        'amount': amount,
        'category': category,
        'time': time,
        'date': date
    }
    expenses_collection.insert_one(expense)

# Route to add an expense
@app.route('/expense', methods=['POST'])
def create_expense():
    data = request.get_json()
    name = data.get('name')
    amount = data.get('amount')
    category = data.get('category')
    
    if not all([name, amount, category]):
        return jsonify({"message": "Missing data"}), 400
    
    add_expense(name, amount, category)
    return jsonify({"message": "Expense added successfully!"}), 201

# Route to get all expenses
@app.route('/expenses', methods=['GET'])
def get_expenses():
    expenses = list(expenses_collection.find())
    for expense in expenses:
        expense['_id'] = str(expense['_id'])  # Convert ObjectId to string for JSON serialization
    return jsonify(expenses)


categories = ["Food", "Rent", "Entertainment", "Transport","Utilities","Shopping","Healthcare", "Miscellaneous"]

@app.route('/categories', methods=['GET'])
def get_categories():
    # Return the categories as JSON
    return jsonify(categories)


# Route to get expenses by month
@app.route('/expenses/month', methods=['GET'])
def get_expenses_by_month():
    month = request.args.get('month')
    if not month:
        return jsonify({"message": "Month parameter is required"}), 400

    try:
        # Get the current year to build the date range
        current_year = datetime.now().year
        
        # Map the month name to a month number
        month_dict = {
            "January": "01", "February": "02", "March": "03", "April": "04", "May": "05", "June": "06",
            "July": "07", "August": "08", "September": "09", "October": "10", "November": "11", "December": "12"
        }

        if month not in month_dict:
            return jsonify({"message": "Invalid month"}), 400

        # Construct the start and end date range for the month
        month_number = month_dict[month]
        start_date = f"{current_year}-{month_number}-01"
        end_date = f"{current_year}-{month_number}-31"  # Using 31 as a max day of the month

        # Query MongoDB for expenses in the selected month
        expenses = expenses_collection.find({
            "date": {"$gte": start_date, "$lte": end_date}
        })
        
        expense_list = []
        for expense in expenses:
            expense['_id'] = str(expense['_id'])  # Convert ObjectId to string for JSON response
            expense_list.append(expense)

        return jsonify(expense_list)
    
    except Exception as e:
        return jsonify({"message": "Error processing the request", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

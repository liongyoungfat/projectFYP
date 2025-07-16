
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS  
from google import genai
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from prophet import Prophet
import mysql.connector  
import calendar 
import google.generativeai as genai
import os
import PyPDF2
import time
import pandas as pd

load_dotenv()
print ('load',load_dotenv())

ALLOWED_EXTENSIONS = {'pdf','png','jpg','jpeg', 'xls', 'xlsx'}
UPLOAD_FOLDER='/temp'

app = Flask(__name__)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})



db_config={
    'host':'localhost',
    'user':'root',
    'password':'123',
    'database':'mydatabase'
}


def get_db_connection():
    print ("conn",mysql.connector.connect(**db_config))
    return mysql.connector.connect(**db_config)

api_key="AIzaSyCwIPyrEioznygRWoq5DlDjEIizNDoMCLk"
model = genai.GenerativeModel('gemini-2.5-flash')
genai.configure(api_key="AIzaSyCwIPyrEioznygRWoq5DlDjEIizNDoMCLk")
# models = genai.list_models()
# for m in models:
#     print(m.name, m.supported_generation_methods)

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM companies ORDER BY name ASC")
        companies = cursor.fetchall()
        cursor.close()
        con.close()
        return jsonify(companies)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/companies', methods=['POST'])
def create_company():
    data = request.json
    name = data.get('name')
    industry = data.get('industry')
    address = data.get('address')

    if not name or not industry or not address:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    con = get_db_connection()
    cursor = con.cursor()

    # 1) Check for existing name
    cursor.execute("SELECT 1 FROM companies WHERE name = %s", (name,))
    if cursor.fetchone():
        cursor.close()
        con.close()
        return jsonify({
            "success": False,
            "message": f"Company with name '{name}' already exists."
        }), 409

    try:
        # 2) Safe to insert
        cursor.execute(
            "INSERT INTO companies (name, industry, address) VALUES (%s, %s, %s)",
            (name, industry, address)
        )
        company_id = cursor.lastrowid
        con.commit()
        return jsonify({"success": True, "company_id": company_id}), 201

    except Exception as e:
        con.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

    finally:
        cursor.close()
        con.close()



@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'staff')
    company_id = data.get('company_id')

    if not username or not email or not password:
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()

        # Auto-insert status = 'active'
        cursor.execute(
            "INSERT INTO users (username, email, password, role, status, company_id) VALUES (%s, %s, %s, %s, 'active', %s)",
            (username, email, password, role, company_id)
        )
        con.commit()
        cursor.close()
        con.close()
        return jsonify({"success": True}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s AND password = %s AND status = 'active'", (email, password))
        user = cursor.fetchone()
        cursor.close()
        con.close()

        if user:
            return jsonify({
                "success": True,
                "token": "abc123",  # Replace with actual token if needed
                "user": {
                    "id": user['id'],
                    "username": user['username'],
                    "role": user['role'],
                    "status": user['status'],
                    "company_id": user['company_id']
                }
            })
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ai',methods=['POST'])
def get_ai():
    client = genai.Client(api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Explain how AI works in a few words and give example",
    )
    print(response.text)
    return jsonify (response.text)


os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/api/uploadFile', methods=['POST'])
def upload_file():
    file_type = request.args.get('type', 'expense')  # Default to 'expense'
    if file_type == 'revenue':
        upload_folder = os.path.join(BASE_DIR, 'tempRevenue')
    else:
        upload_folder = os.path.join(BASE_DIR, 'temp')
    os.makedirs(upload_folder, exist_ok=True)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_name = f"{int(time.time())}_{filename}"
        save_path = os.path.join(upload_folder, save_name)
        file.save(save_path)
        return jsonify({
            'message': 'File uploaded successfully',
            'path': save_path
        }), 200
    else:
        return jsonify({'error': 'Invalid file type'}), 400 

@app.route('/api/processReceipt', methods=['POST'])
def process_receipt():
    try:
        data = request.get_json()
        doc_type = data.get('type', 'expense')
        print('data',data)
        relative_path = data.get('file_path', '')
        abs_path = os.path.join(BASE_DIR, relative_path)
        abs_path = os.path.normpath(abs_path)  # Normalize path
        ext = os.path.splitext(abs_path)[1].lower()
        
        if ext in ['.xls', '.xlsx']:
            # Excel file: process and return parsed data
            print ('excel running')
            records = process_excel_file(abs_path)
            return jsonify({'excel_data': records, 'file_path': abs_path})

        print(f"Processing file: {abs_path}")
        
        if not os.path.exists(abs_path):
            return jsonify({'error': 'File not found'}), 404

        # Read file and process with Gemini
        with open(abs_path, 'rb') as f:
            document_content = f.read()

        if (document_content == b''):
            return jsonify({'error': 'File is empty'}), 404
        # Prepare for Gemini
        text_part = {
            'mime_type': 'application/pdf',
            'data': document_content
        }
        print ('ss',text_part)

        if doc_type == 'revenue':
            prompt = """
            Extract the following details from this revenue/invoice document in JSON format:
            - dateTime (format YYYY-MM-DDTHH:mm)
            - payer (who paid, if present)
            - category (choose from ['Product Sales','Service Income','Interest Income','Commission Income','Rental Income','Subscription Income','Grants & Subsidies','Other Income'])
            - amount (as number)
            - reference (invoice number, transaction number, or bank ref)
            - aiResponse (brief explanation of extraction)

            Suit the category as closely as possible from the list, e.g., "Online purchase" should be Product Sales, "Design work" should be Service Income.

            Return ONLY the JSON object, no additional text.
            """
        else:
            prompt = """
            Extract the following details from this receipt in JSON format:
            - dateTime (in format YYYY-MM-DDTHH:mm)
            - payment_method
            - category
            - amount (as number)
            - aiResponse (brief explanation of extraction)

            Suit the category in this array 
            ['Meals',
            'Transportation',
            'Entertainment',
            'Travel',
            'Office Supplies',
            'Marketing',
            'Utilities',
            'Software'] like food should be meals and gas should be travel

            Suit the payment_method in this array 
            ['Online Banking', 'Credit Card', 'Debit Card', 'eWallet', 'Cash'] 
            like touch and go should be eWallet and if payment_method not found return not found for payment_method

            Return ONLY the JSON object, no additional text.
            """
        
        # # Generate content
        response = model.generate_content([prompt, text_part])
        print('ressss',response)
        # # Parse and return response
        return jsonify({
            'result': response.text,
            'file_path': abs_path
        })
    except Exception as e:
        print(f"Error in inline PDF example: {e}")
        return jsonify({'error': str(e)}), 500

def process_excel_file(file_path):
    df = pd.read_excel(file_path, header=None)  # No header
    records = []
    for idx, row in df.iterrows():
        # Example: Look for a row that is a transaction or summary line
        # "1. Total Revenue", ..., ..., <value>
        if (
            str(row[0]).strip() == "1. Total Revenue"
            and pd.notna(row[3])
        ):
            records.append({
                "label": "Total Revenue",
                "amount": float(row[3])
            })
        elif (
            str(row[0]).strip() == "2. Total Expenses"
            and pd.notna(row[3])
        ):
            records.append({
                "label": "Total Expenses",
                "amount": float(row[3])
            })
        elif (
            str(row[0]).strip() == "3. Total Released Amount"
            and pd.notna(row[3])
        ):
            records.append({
                "label": "Total Released Amount",
                "amount": float(row[3])
            })
    return records


@app.route('/api/users')
def get_users():
    company_id = request.args.get('company_id')  # <-- Get from query
    if not company_id:
        return jsonify({"error": "Missing company_id"}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE company_id = %s", (company_id,))
        users = cursor.fetchall()
        cursor.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/updateUser', methods=['POST'])
def update_user():
    data = request.get_json()
    print('Received:', data)
    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT id FROM users WHERE id = %s", (data['id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'User not found'}), 404
        update_query = """
            UPDATE users
            SET role = %s,
                status = %s
            WHERE id = %s
        """
        params = (
            data.get('role'),
            data.get('status'),
            data['id']
        )
        cursor.execute(update_query, params)
        con.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'User updated successfully'}), 200
        else:
            return jsonify({'error': 'No changes made'}), 400
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()
    
@app.route('/api/expenses')
def get_expenses():
    try:
        con    = get_db_connection()
        cursor = con.cursor(dictionary=True)
        company_id = request.args.get('company_id')
        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400

        # choose sort field…
        allowed = {
            'dateTime':       'date_time',
            'payment_method': 'type',
            'category':       'category',
            'amount':         'total',
            'user_id':        'user_id'
        }
        sort_by = request.args.get('sort_by', 'dateTime')
        db_field = allowed.get(sort_by, 'date_time')
        order    = request.args.get('order','desc').lower() == 'asc' and 'ASC' or 'DESC'

        # Pull raw datetime out of MySQL
        sql = f"""
        SELECT
            id,
            user_id,
            category,
            total    AS amount,
            `type`   AS payment_method,
            date_time
        FROM expenses
        WHERE company_id = %s
        ORDER BY `{db_field}` {order}
        """
        cursor.execute(sql, (company_id,))
        rows = cursor.fetchall()
        cursor.close()
        con.close()
        for r in rows:
            r['dateTime'] = r.pop('date_time').isoformat()
        return jsonify(rows)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/expenses/available-months', methods=['GET'])
def get_available_months():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)

        query = """
        SELECT 
            DISTINCT YEAR(date_time) AS year,
            MONTH(date_time) AS month
        FROM expenses
        ORDER BY year DESC, month ASC
        """

        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        con.close()

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/companies/threshold')
def get_threshold():
    company_id = request.args.get('company_id')
    if not company_id:
        return jsonify({'error': 'Missing company_id'}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT threshold FROM companies WHERE id = %s", (company_id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return jsonify({'threshold': result['threshold']}), 200
        else:
            return jsonify({'error': 'Company not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/companies/threshold/update', methods=['POST'])
def update_threshold():
    data = request.get_json()
    company_id = data.get('company_id')
    new_threshold = data.get('new_threshold')
    print('dta',data)

    if not company_id or new_threshold is None:
        return jsonify({'error': 'Missing company_id or new_threshold'}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("UPDATE companies SET threshold = %s WHERE id = %s", (new_threshold, company_id))
        con.commit()
        cursor.close()

        # if cursor.rowcount > 0:
        return jsonify({'message': 'Threshold updated successfully'}), 200
        # else:
        #     return jsonify({'error': 'Company not found or threshold not changed'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/expenses/certain/period')
def get_expenses_in_period():
    try:
        # Get required date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        company_id = request.args.get('company_id')

        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400
        
        if not start_date or not end_date:
            return jsonify({"error": "Both start_date and end_date parameters are required"}), 400
        
        con = get_db_connection()
        cursor = con.cursor(dictionary=True) 
        query = """
        SELECT 
            id,
            date_time AS dateTime,
            type AS payment_method,
            user_id,
            category,
            total AS amount
        FROM expenses
        WHERE company_id = %s
        AND date_time BETWEEN %s AND %s
        """
        
        cursor.execute(query, (company_id, start_date, end_date))
        expenses = cursor.fetchall()
        cursor.close()
        con.close()
        return jsonify(expenses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/revenues/certain/period')
def get_revenues_in_period():
    try:
        # Get required date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        company_id = request.args.get('company_id')

        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400
        print("date",start_date, end_date) 

        if not start_date or not end_date:
            return jsonify({"error": "Both start_date and end_date parameters are required"}), 400
        
        con = get_db_connection()
        cursor = con.cursor(dictionary=True) 
        query = """
        SELECT 
            id,
            amount,
            date_time AS dateTime
        FROM revenues
        WHERE company_id = %s
        AND date_time BETWEEN %s AND %s
        """
        
        cursor.execute(query, (company_id, start_date, end_date)) 
        revenues = cursor.fetchall()
        cursor.close()
        con.close()
        return jsonify(revenues)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/createExpenses', methods=['POST'])
def create_expenses():
    data = request.get_json()
    print('data',data)
    try:
        con= get_db_connection()
        cursor = con.cursor()
        query = """
        INSERT INTO expenses (date_time, type, user_id, category, total, company_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            data['dateTime'],
            data['payment_method'],
            data['user_id'],
            data['category'],
            data['amount'],
            data['company_id']
        )
        print('values',values)
        cursor.execute(query, values)
        con.commit()
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/updateExpenses', methods=['POST'])
def update_expenses():
    data = request.get_json()
    print("DATA RECEIVED:", data)
    try:
        con= get_db_connection()
        cursor = con.cursor()
        print('data',data)
        cursor.execute("SELECT id FROM expenses WHERE id = %s", (data['id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Expense not found'}), 404
        update_query = """
            UPDATE expenses 
            SET date_time = %s, 
                type = %s, 
                user_id = %s, 
                category = %s, 
                total = %s 
            WHERE id = %s
        """
        params = (
            data['dateTime'],
            data['payment_method'],
            data['user_id'],
            data['category'],
            data['amount'],
            data['id']
        )
        
        cursor.execute(update_query, params)
        con.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Expense updated successfully'}), 200
        else:
            return jsonify({'error': 'No changes made'}), 400
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/deleteExpenses', methods=['POST'])
def delete_expenses():
    data = request.get_json()
    expense_id = data.get('id')
    
    if not expense_id:
        return jsonify({'error': 'Missing expense ID'}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()
        
        cursor.execute("SELECT id FROM expenses WHERE id = %s", (expense_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Expense not found'}), 404

        cursor.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        con.commit()
        
        return jsonify({'message': 'Expense deleted successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()


@app.route('/api/expenses/summary/category')
def expense_summary_by_category():
    try:
        now = datetime.now()
        year = request.args.get('year', type=int, default=now.year)
        month = request.args.get('month', type=int, default=now.month)
        company_id = request.args.get('company_id')

        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400

        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        query = """
        SELECT 
            category,
            SUM(total) AS total_amount
        FROM expenses
        WHERE 
            YEAR(date_time) = %s AND 
            MONTH(date_time) = %s AND
            company_id = %s
        GROUP BY category
        """
        cursor.execute(query, (year, month, company_id))
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


MONTH_ABBR = list(calendar.month_abbr)[1:]
@app.route('/api/expenses/summary/monthly')
def monthly_expense_trends():
    try:
        now = datetime.now()  # Renamed variable
        year = request.args.get('year', type=int, default=now.year)
        
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        query = """
        SELECT 
            MONTH(date_time) AS month,
            SUM(total) AS total_amount
        FROM expenses
        WHERE YEAR(date_time) = %s
        GROUP BY MONTH(date_time)
        ORDER BY month
        """
        cursor.execute(query, (year,))
        result = cursor.fetchall()
        cursor.close()

        monthly_data = {row['month']: row['total_amount'] for row in result}
        full_year = [{
            "month": m, 
            "month_name": MONTH_ABBR[m-1],  # Use predefined names
            "total_amount": monthly_data.get(m, 0)
        } for m in range(1, 13)]
        
        return jsonify(full_year)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/ai/generate/forecast', methods=['POST'])
def generate_forecast():
    try:
        user_id = 1 # Implement your auth logic
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        print('a')
        # Get 24 months of historical data aggregated by month and category
        query = """
        SELECT 
            YEAR(date_time) AS year,
            MONTH(date_time) AS month_num,
            category,
            SUM(total) AS total
        FROM expenses
        WHERE user_id = %s
        AND date_time >= DATE_SUB(CURDATE(), INTERVAL 24 MONTH)
        GROUP BY YEAR(date_time), MONTH(date_time), category
        ORDER BY YEAR(date_time) DESC, MONTH(date_time) DESC
        """
        cursor.execute(query, (user_id,))
        historical_data = cursor.fetchall()
        cursor.close()
        print ('b')
        # Structure data for AI processing
        df = pd.DataFrame(historical_data)
        df['ds'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month_num'].astype(str) + '-01')
        df['y'] = df['total']

        df_total = df.groupby('ds')['y'].sum().reset_index()
        if df_total.shape[0] >= 2:
            m_total = Prophet(yearly_seasonality=True)
            m_total.fit(df_total)
            future_total = m_total.make_future_dataframe(periods=6, freq='MS')
            forecast_total = m_total.predict(future_total)
            total_forecast = forecast_total[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(6).to_dict('records')
        else:
            total_forecast = []

        forecasts = {}
        insufficient = []
        for cat in df['category'].unique():
            df_cat = df[df['category'] == cat].copy()
            all_months = pd.date_range(df['ds'].min(), df['ds'].max(), freq='MS')
            df_cat = df_cat.set_index('ds').reindex(all_months, fill_value=0).rename_axis('ds').reset_index()

            non_zero_months = (df_cat['y'] > 0).sum()
            if non_zero_months < 3:
                print(f"Skipping category '{cat}': not enough data.")
                insufficient.append(cat)
                continue

            m = Prophet(yearly_seasonality=True)
            m.fit(df_cat)
            future = m.make_future_dataframe(periods=6, freq='MS')
            forecast = m.predict(future)
            forecasts[cat] = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(6).to_dict('records')

        # Get current date info
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%B')

        prompt = f"""
        Act as a expert financial analyst writing for a Malaysian audience. 
        Generate a comprehensive forecast report based on this historical expense data. 
        Format all monetary values as 'RM' (Ringgit Malaysia) instead of '$'. 
        Use only simple, business-friendly language.

        Here are the latest expense forecasts for the next 6 months per category, produced by the Prophet time series model:
        {forecasts}
        The following categories had insufficient data for reliable prediction: {insufficient}
        
        **REPORT REQUIREMENTS**
        1. Executive Summary:
        - 3-sentence overview of financial health.
        - Key spending patterns and anomalies.
        2. Category Analysis:
        - If data is sufficient, provide a clear 6-month trend and forecast in simple business language.
        - If data is insufficient for any category, *do not* repeat a full sentence under each one.  
            Instead, at the very end of **category_analysis**, include one line:
              **Reminder:*) The following categories have insufficient data for reliable prediction: [list them].  
                Please input more records for better accuracy.(e.g. Insuffiecient data reminder(bold):...)
        - For each category, provide a 2-3 sentence explanation of *why* the forecast behaves as it does (e.g. seasonal peaks, inflation, business growth).
        - Give 2 actionable, budget-level recommendations based on the above forecasts in sentences.
        3. Forecast Table:
        - use the numbers above
        - Show category, date, 'Forecast Amount (RM)', "Estimate Range (RM)" as columns.
        - Do NOT use technical terms like yhat; use business terms as above.
        - All numbers must show 'RM' before the value (e.g., RM 2,000.00).
        - In the "forecast_table", include all categories—even those with insufficient data. For insufficient data categories, fill Forecast Amount and Estimate Range as "Insufficient Data".
        - All table "headers" must be: ["Category", "Date", "Forecast Amount (RM)", "Estimate Range (RM)"]
        - Do **not** use technical terms like yhat, yhat_lower, or yhat_upper. Use only the above headers in business language.
        4. Calculation Explanation:
        - After the table, include a 1–2 sentence note on how you derived and calculated:
          * Forecast Amount (RM)  
          * "Estimate Range (RM)
        (Hint: point estimate vs. confidence interval.)
        5. Actionable Insights:
        - Top 3 cost-saving opportunities (plain text, no bold).
        - Budget risk assessment.
        - Recommended adjustments.
        - list of actionable insights

        **Instructions:**
        1. All monetary values must start with RM and use comma as thousands separator (e.g., RM 12,000.00).
        2. Use simple, everyday language that normal business users can easily understand.

        **ANALYSIS PARAMETERS**
        - Current period: {current_month} {current_year}
        - Apply Holt-Winters forecasting (alpha=0.8, beta=0.15, gamma=0.1)
        - Consider 8% annual inflation rate
        - Factor in seasonal trends (e.g., higher travel in Dec)
        - Account for business growth projections
        **OUTPUT FORMAT**
        - Strict JSON format with these keys:
            "executive_summary": string,
            "category_analysis": {{ "Category1": string, ... }},
            "forecast_table": {{ "headers": [], "rows": [] }},
            "calculation_explanation": string, 
            "insights": [string, string, ...],
        """
        response = model.generate_content(prompt)

        # sum up each category’s 6-month yhat
        totals = {cat: sum(r["yhat"] for r in recs) for cat, recs in forecasts.items()}
        # pick the 2 biggest
        top2 = sorted(totals, key=totals.get, reverse=True)[:2]
        # build a small chart payload
        chart_data = {
        cat: [
            {"date": rec["ds"].strftime("%b %Y"), "value": rec["yhat"]}
            for rec in forecasts[cat]
        ]
        for cat in top2
        }

        try:
            report = extract_json(response.text)
            report["chart_data"] = chart_data
            return jsonify(report)
        except Exception as e:
            print('Error parsing AI response:', e)
            return jsonify({'error': 'Failed to parse AI response', 'raw': response.text}), 500

    except Exception as e:
        print(f"Error generating forecast: {e}")
        return jsonify({"error": "Forecast generation failed", "details": str(e)}), 500
    

import re, json

def extract_json(text):
    # Remove markdown code block markers just in case
    text = text.replace('```json', '').replace('```', '').strip()
    # Regex to extract first {...} or [...] block (works for object or array)
    match = re.search(r'({.*}|\\[.*\\])', text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError('No JSON found in AI response')


@app.route('/api/template/<string:doc_type>', methods=['GET'])
def download_template(doc_type):
    """Return CSV templates for batch uploads."""
    if doc_type == 'expenses':
        content = "date_time,type,category,total\n"
    elif doc_type == 'revenue':
        content = "title,description,category,amount,date_time\n"
    else:
        return jsonify({'error': 'Invalid template type'}), 400
    response = make_response(content)
    response.headers['Content-Disposition'] = f'attachment; filename={doc_type}_template.csv'
    response.mimetype = 'text/csv'
    return response


def _read_uploaded_table(file_storage):
    """Load uploaded CSV or Excel into a DataFrame."""
    filename = file_storage.filename.lower()
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file_storage)
    return pd.read_csv(file_storage)


@app.route('/api/batchUploadExpenses', methods=['POST'])
def batch_upload_expenses():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    try:
        df = _read_uploaded_table(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {e}'}), 400
    company_id = request.form.get('company_id')
    if not company_id:
        return jsonify({'error': 'Missing company_id'}), 400
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    required = ['date_time', 'type', 'category', 'total']
    for col in required:
        if col not in df.columns:
            return jsonify({'error': f'Missing required column {col}'}), 400

    try:
        df['date_time'] = pd.to_datetime(df['date_time'], errors='raise')
        df['date_time'] = df['date_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return jsonify({'error': f'Date parsing failed: {e}'}), 400

    records = []
    for _, row in df.iterrows():
        records.append(
            (
                row['date_time'],
                row['type'],
                int(user_id),
                row['category'],
                float(row['total']),
                int(company_id)
            )
        )

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.executemany(
            """
            INSERT INTO expenses (date_time, type, user_id, category, total, company_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            records,
        )
        con.commit()
        return jsonify({'message': f'{len(records)} expenses uploaded'}), 201
    except mysql.connector.Error as err:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/batchUploadRevenue', methods=['POST'])
def batch_upload_revenue():
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400

    # Get company_id from FormData
    company_id = request.form.get('company_id')
    if not company_id:
        return jsonify({'error': 'Missing company_id'}), 400

    try:
        df = _read_uploaded_table(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {e}'}), 400

    required = ['title', 'category', 'amount', 'date_time']
    for col in required:
        if col not in df.columns:
            return jsonify({'error': f'Missing required column: {col}'}), 400

    # Ensure valid date format
    try:
        df['date_time'] = pd.to_datetime(df['date_time'], errors='raise')
        df['date_time'] = df['date_time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        return jsonify({'error': f'Date parsing failed: {e}'}), 400

    records = []
    for _, row in df.iterrows():
        try:
            records.append(
                (
                    row['title'],
                    row.get('description') or '',  # allow null
                    row['category'],
                    float(row['amount']),
                    row.get('reference') or '',
                    row.get('file') or '',
                    row['date_time'],
                    int(company_id)
                )
            )
        except Exception as e:
            print(f"Skipping invalid row: {row} — Error: {e}")
            continue

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.executemany(
            """
            INSERT INTO revenues 
            (title, description, category, amount, reference, file, date_time, company_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            records
        )
        con.commit()
        return jsonify({'message': f'{len(records)} revenues uploaded'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if con and con.is_connected():
            cursor.close()
            con.close()


@app.route('/api/revenues', methods=['GET'])
def get_revenues():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)

        company_id = request.args.get('company_id')

        query = """
        SELECT 
            id,
            title,
            description,
            category,
            amount,
            reference,
            file,
            date_time AS dateTime
        FROM revenues
        WHERE company_id = %s
        ORDER BY date_time DESC
        """
        cursor.execute(query, (company_id,))
        revenues = cursor.fetchall()
        cursor.close()
        return jsonify(revenues)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/expenses/summary/monthly/raw', methods=['GET'])
def get_expenses_monthly_raw():
    try:
        company_id = request.args.get('company_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not company_id:
            return jsonify({'error': 'Missing company_id'}), 400

        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        query = """
        SELECT date_time AS dateTime, total
        FROM expenses
        WHERE company_id = %s
        """
        params = [company_id]
        if start_date and end_date:
            query += " AND date_time BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        query += " ORDER BY date_time ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        cursor.close()
        con.close()
        # Convert date_time to ISO string
        for r in rows:
            if isinstance(r['dateTime'], (str,)):
                continue
            r['dateTime'] = r['dateTime'].isoformat()
        return jsonify(rows)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/createRevenue', methods=['POST'])
def create_revenue():
    data = request.get_json()
    try:
        con = get_db_connection()
        cursor = con.cursor()
        query = """
        INSERT INTO revenues (title, description, category, amount, reference, file, date_time, company_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['title'],
            data['description'],
            data['category'],
            data['amount'],
            data.get('reference', ''),
            data.get('file', ''),
            data['dateTime'],
            data['company_id']  
        )
        cursor.execute(query, values)
        con.commit()
        return jsonify({'message': 'Revenue created successfully'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/updateRevenue', methods=['POST'])
def update_revenue():
    data = request.get_json()
    print("DATA RECEIVED:", data)
    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT id FROM revenues WHERE id = %s", (data['id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'Revenue not found'}), 404
        update_query = """
            UPDATE revenues 
            SET title = %s, 
                description = %s, 
                category = %s, 
                amount = %s, 
                reference = %s, 
                file = %s, 
                date_time = %s
            WHERE id = %s
        """
        params = (
            data['title'],
            data.get('description', ''),
            data['category'],
            data['amount'],
            data.get('reference', ''),
            data.get('file', ''),
            data['dateTime'],
            data['id']
        )
        cursor.execute(update_query, params)
        con.commit()
        if cursor.rowcount > 0:
            return jsonify({'message': 'Revenue updated successfully'}), 200
        else:
            return jsonify({'error': 'No changes made'}), 400
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()


@app.route('/api/deleteRevenue', methods=['POST'])
def delete_revenue():
    data = request.get_json()
    revenue_id = data.get('id')
    print ('id', revenue_id )
    if not revenue_id:
        return jsonify({'error': 'Missing revenue ID'}), 400

    try:
        con = get_db_connection()
        cursor = con.cursor()
        
        cursor.execute("SELECT id FROM revenues WHERE id = %s", (revenue_id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Revenue not found'}), 404

        cursor.execute("DELETE FROM revenues WHERE id = %s", (revenue_id,))
        con.commit()
        
        return jsonify({'message': 'Revenue deleted successfully'}), 200
        
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/expenses/summary/category/year')
def expense_summary_by_category_year():
    try:
        now = datetime.now()
        year = request.args.get('year', type=int, default=now.year)
        company_id = request.args.get('company_id')

        if not company_id:
            return jsonify({"error": "Missing company_id"}), 400

        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        query = """
        SELECT 
            category,
            SUM(total) AS total_amount
        FROM expenses
        WHERE 
            YEAR(date_time) = %s AND 
            company_id = %s
        GROUP BY category
        """
        cursor.execute(query, (year, company_id))
        result = cursor.fetchall()
        cursor.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
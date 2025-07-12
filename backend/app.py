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
CORS(app) 
CORS (app, resources= {r"/api/process-receipt":{"origins":"http://localhost:5173"}})


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
    try:
        con= get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()
        cursor.close()
        return jsonify(users)  # Return data as JSON
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/updateUser', methods=['POST'])
def update_user():
    data = request.get_json()
    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute("SELECT id FROM users WHERE id = %s", (data['id'],))
        if not cursor.fetchone():
            return jsonify({'error': 'User not found'}), 404
        update_query = """
            UPDATE users
            SET role = %s,
                status = %s,
                company_id = %s
            WHERE id = %s
        """
        params = (
            data.get('role'),
            data.get('status'),
            data.get('company_id'),
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
        con= get_db_connection()
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
        """
        cursor.execute(query)
        expenses = cursor.fetchall()
        cursor.close()
        return jsonify(expenses)
    except Exception as e:
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


@app.route('/api/expenses/certain/period')
def get_expenses_in_period():
    try:
        # Get required date parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
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
        WHERE date_time BETWEEN %s AND %s
        """
        
        cursor.execute(query, (start_date, end_date))
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
        WHERE date_time BETWEEN %s AND %s
        """
        
        cursor.execute(query, (start_date, end_date))
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
        INSERT INTO expenses (date_time,type,user_id,category,total)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            data['dateTime'],
            data['payment_method'],
            data['user_id'],
            data['category'],
            data['amount']
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
        now = datetime.now()  # Renamed variable
        year = request.args.get('year', type=int, default=now.year)
        month = request.args.get('month', type=int, default=now.month)
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
        query = """
        SELECT 
            category,
            SUM(total) AS total_amount
        FROM expenses
        WHERE 
            YEAR(date_time) = %s AND 
            MONTH(date_time) = %s
        GROUP BY category
        """
        cursor.execute(query, (year, month))
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
        - If data is insufficient, state: "No reliable forecast for [Category] due to limited data. Please input more records for better prediction."
        - Remind the user if any category has insufficient data in the "category_analysis".
        3. Forecast Table:
        - use the numbers above
        - Show category, date, 'Forecast Amount (RM)', 'Minimum Estimate (RM)', 'Maximum Estimate (RM)' as columns.
        - Do NOT use technical terms like yhat; use business terms as above.
        - All numbers must show 'RM' before the value (e.g., RM 2,000.00).
        - In the "forecast_table", include all categories—even those with insufficient data. For insufficient data categories, fill their forecast values as "Insufficient Data".
        - All table headers must be: ["Category", "Date", "Forecast Amount (RM)", "Minimum Estimate (RM)", "Maximum Estimate (RM)"].
        - Do **not** use technical terms like yhat, yhat_lower, or yhat_upper. Use only the above headers in business language.
        4. Actionable Insights:
        - Top 3 cost-saving opportunities (plain text, no bold).
        - Budget risk assessment.
        - Recommended adjustments.
        - list of actionable insights
        5. Visualization Suggestions:
        - Recommended chart types for each insight (plain text, no bold).

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
            "insights": [string, string, ...],
            "visualization_suggestions": [string, ...]
        """

        # structured_data = {}
        # for row in historical_data:
        #     year = row['year']
        #     month = row['month']
        #     category = row['category']
        #     amount = float(row['total'])
        #     if year not in structured_data:
        #         structured_data[year] = {}
        #     if month not in structured_data[year]:
        #         structured_data[year][month] = {'total': 0, 'categories': {}}
        #     structured_data[year][month]['categories'][category] = amount
        #     structured_data[year][month]['total'] += amount
        # # Get current date info
        # current_year = datetime.now().year
        # current_month = datetime.now().strftime('%B')
        # # Prepare categories list
        # categories = list(set(row['category'] for row in historical_data))
        # # Build AI prompt
        # prompt = f"""
        # Act as a senior financial analyst. Generate a comprehensive forecast report based on this historical expense data:
        # **REPORT REQUIREMENTS**
        # 1. **Executive Summary**:
        #    - 3-sentence overview of financial health
        #    - Key spending patterns and anomalies
        # 2. **Category Analysis**:
        #    {', '.join(categories)}
        #    - For each category: 6-month trend analysis + forecast
        # 3. **Forecast Projections**:
        #    - Next 3 months predictions (table format)
        #    - 6-month outlook with confidence intervals
        #    - Include both total and category breakdowns
        # 4. **Actionable Insights**:
        #    - Top 3 cost-saving opportunities
        #    - Budget risk assessment
        #    - Recommended adjustments
        # 5. **Visualization Suggestions**:
        #    - Recommended chart types for each insight
        #    - How to visualize forecast vs actuals
        # **ANALYSIS PARAMETERS**
        # - Current period: {current_month} {current_year}
        # - Apply Holt-Winters forecasting (alpha=0.8, beta=0.15, gamma=0.1)
        # - Consider 8% annual inflation rate
        # - Factor in seasonal trends (e.g., higher travel in Dec)
        # - Account for business growth projections

        # """
        # Generate content
        response = model.generate_content(prompt)
        try:
            report = extract_json(response.text)
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
        content = "title,category,amount,date_time\n"
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

    required = ['date_time', 'type', 'category', 'total']
    for col in required:
        if col not in df.columns:
            return jsonify({'error': f'Missing required column {col}'}), 400

    # Convert date_time to MySQL DATETIME format
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
                int(row.get('user_id', 1)),
                row['category'],
                float(row['total']),
            )
        )

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.executemany(
            """
            INSERT INTO expenses (date_time, type, user_id, category, total)
            VALUES (%s, %s, %s, %s, %s)
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
    """Batch insert revenues from uploaded file."""
    file = request.files.get('file')
    if not file:
        return jsonify({'error': 'No file provided'}), 400
    try:
        df = _read_uploaded_table(file)
    except Exception as e:
        return jsonify({'error': f'Failed to read file: {e}'}), 400

    required = ['title', 'category', 'amount', 'date_time']
    for col in required:
        if col not in df.columns:
            return jsonify({'error': f'Missing required column {col}'}), 400

    records = []
    for _, row in df.iterrows():
        records.append(
            (
                row['title'],
                row.get('description', ''),
                row['category'],
                float(row['amount']),
                row.get('reference', ''),
                row.get('file', ''),
                row['date_time'],
            )
        )

    try:
        con = get_db_connection()
        cursor = con.cursor()
        cursor.executemany(
            """
            INSERT INTO revenues (title, description, category, amount, reference, file, date_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            records,
        )
        con.commit()
        return jsonify({'message': f'{len(records)} revenues uploaded'}), 201
    except mysql.connector.Error as err:
        return jsonify({'error': str(err)}), 500
    finally:
        if 'con' in locals() and con.is_connected():
            cursor.close()
            con.close()

@app.route('/api/revenues', methods=['GET'])
def get_revenues():
    try:
        con = get_db_connection()
        cursor = con.cursor(dictionary=True)
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
        """
        cursor.execute(query)
        revenues = cursor.fetchall()
        cursor.close()
        return jsonify(revenues)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/createRevenue', methods=['POST'])
def create_revenue():
    data = request.get_json()
    try:
        con = get_db_connection()
        cursor = con.cursor()
        query = """
        INSERT INTO revenues (title, description, category, amount, reference, file, date_time)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data['title'],
            data['description'],
            data['category'],
            data['amount'],
            data.get('reference', ''),
            data.get('file', ''),
            data['dateTime']
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


if __name__ == '__main__':
    app.run(debug=True)
from flask import make_response # for setting cookies
import csv
from flask import Flask, redirect, render_template, request, session, json
from flask import url_for
from flask_session import Session
from cs50 import SQL
import sqlite3
# Configure app
app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# Configure database
db = SQL("sqlite:///ozzy.db")
# ______________________________________________Index________________________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/index", methods=["GET", "POST"])
def index():
       return render_template("index.html")
# ______________________________________________Register with email____________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/register", methods=["POST"])
def register():
    Email = request.form.get("Email")
    Password = request.form.get("Password")
    Username = request.form.get("Username")
    if not Email or not Password:
        return render_template("failure.html", message="Both fields are required.")
    try:
        db.execute("INSERT INTO bruger (Email, Password, Username) VALUES (?, ?, ?)", Email, Password, Username)
        return redirect("/login")
    except Exception as e:
        return render_template("failure.html", message=str(e))

@app.route("/registrants")
def registrants():
    registrants = db.execute("SELECT * FROM bruger")
    return render_template("registrants.html", registrants=registrants)
# ________________________________________________Login route_________________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login"""
    if request.method == "POST":
        # Retrieve form data
        Email = request.form.get("Email")
        Password = request.form.get("Password")
        # Validate input
        if not Email or not Password:
            return render_template("login.html", error="Email and Password are required")
        # Check if user exists in the database
        user = db.execute("SELECT * FROM bruger WHERE Email = ?", Email)
        if not user:  # If user list is empty
            return render_template("login.html", error="Invalid email or password")
        # Validate password (consider using hashing for security)
        if user[0]["Password"] == Password:
            print("Login successful")
            session["user_id"] = user[0]["ID"]
            session["Email"] = Email
            session["Username"] = user[0]["Username"]
            # Redirect to the main search page after successful login
            return redirect("/")
        else:
            # Invalid credentials
            return render_template("login.html", error="Invalid email or password")
    # Render login page for GET requests
    return render_template("login.html")

# ______________________________________________logout route__________________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
# ______________________________________________frontpage_____________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/")
def frontpage():
    if "user_id" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect('ozzy.db')
    cursor = conn.cursor()
    
    # Retrieve the user's selected foods from the session
    selected_foods = session.get('selected_foods', [])
    total_co2 = sum(item['co2'] for item in selected_foods)  # Total CO2 in kg
    total_protein = sum(item['protein'] for item in selected_foods)
    total_carbs = sum(item['carbs'] for item in selected_foods)
    total_fat = sum(item['fat'] for item in selected_foods)
    total_calories = sum(item['calories'] for item in selected_foods)
    
    # Average CO2 emissions per meal for comparison
    average_co2 = 3.6  # Average CO2 emissions per meal in kg
    co2_comparison = ""
    co2_color = ""  # Variable for color
    
    # Determine the CO2 comparison message and color
    if total_co2 > average_co2:
        co2_comparison = f"Your meal emits {total_co2 - average_co2:.2f} kg more CO2 than the average ({average_co2:.2f} kg)."
        co2_color = "red"
    elif total_co2 < average_co2:
        co2_comparison = f"Your meal emits {average_co2 - total_co2:.2f} kg less CO2 than the average ({average_co2:.2f} kg)."
        co2_color = "green"
    else:
        co2_comparison = "Your meal emits the same amount of CO2 as the average."
        co2_color = "yellow"
    
    # Prepare macros data for pie chart
    macros_data = [
        ['Macronutrient', 'Amount'],
        ['Protein', total_protein],
        ['Carbs', total_carbs],
        ['Fat', total_fat]
    ]
    
    conn.close()
    return render_template("frontpage.html", Username=session.get("Username"), 
                           total_calories=total_calories, total_co2=total_co2,
                           average_co2=average_co2, co2_comparison=co2_comparison, 
                           co2_color=co2_color, macros_data=macros_data)

# ______________________________________________Load CSV_________________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
# Opret forbindelse til databasen
# Function to load the CSV into the database
# def load_csv_to_db():
#    csv_file = 'static/NyDB.csv'
#    connection = sqlite3.connect('ozzy.db')
    cursor = connection.cursor()
    # Opret tabellen for behandlede filer, hvis den ikke findes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Processed_Files (
        file_name TEXT PRIMARY KEY
    )
    """)
    # Tjek om filen allerede er behandlet
    cursor.execute("SELECT 1 FROM Processed_Files WHERE file_name = ?", (csv_file,))
    if cursor.fetchone():
        print("Denne CSV-fil er allerede behandlet.")
        connection.close()
        return

    with open('static/NyDB.csv', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        # Iterate through the rows and insert into the database
        for row in reader:
            try:
                if 'ID_Ra' in row and row['ID_Ra']:  # Check if 'ID_Ra' exists
                    # Insert data into the database
                    cursor.execute("""
                        INSERT OR REPLACE INTO Food_product (ID_Ra, Navn, CO2, Energi, Fedt, Kulhydrat, Protein)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['ID_Ra'],
                        row['Navn'],
                        float(row['CO2']),
                        float(row['Energi']),
                        float(row['Fedt']),
                        float(row['Kulhydrat']),
                        float(row['Protein'])
                    ))
            except Exception as e:
                print(f"Error processing row {row}: {e}")
        connection.commit()
    connection.close()
    print("CSV-filen er blevet behandlet.")
# ______________________________________________Search route_________________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/search", methods=["GET", "POST"])
def search():
    conn = sqlite3.connect('ozzy.db')
    cursor = conn.cursor()
    if "user_id" not in session:
        return redirect("/login")
    # If a POST request, handle product selection (add food)
    if request.method == "POST" and 'Navn' in request.form:
        product_name = request.form.get('Navn')
        grams = int(request.form.get('grams'))  # Ensure this is an integer
        # Query the database to get the product details
        query = """
        SELECT ID_Ra, Navn, CO2, Energi, Fedt, Kulhydrat, Protein
        FROM Food_product
        WHERE Navn LIKE ?
        """
        cursor.execute(query, ('%' + product_name + '%',))
        result = cursor.fetchone()
        if result:
            # Extract product details
            product_id = result[0]
            product_name = result[1]
            co2_per_kg = float(result[2])  # CO2 (per kg)
            energi_per_100g = float(result[3])  # Energy (kcal per 100 g)
            fat_per_100g = float(result[4])  # Fat (g per 100 g)
            carbs_per_100g = float(result[5])  # Carbs (g per 100 g)
            protein_per_100g = float(result[6])  # Protein (g per 100 g)
            # Calculate values based on grams for macros
            fat = fat_per_100g * grams / 100  # Fat for gram input
            carbs = carbs_per_100g * grams / 100  # Carbs for gram input
            protein = protein_per_100g * grams / 100  # Protein for gram input
            energi = energi_per_100g * grams / 1000  # Energy for gram input
            # Calculate CO2 in kilograms (since it's stored per kilogram in the database)
            co2_emissions = co2_per_kg * grams / 1000  # CO2 for gram input, converting from grams to kilograms
            # Add the food item to the session list
            if 'selected_foods' not in session:
                session['selected_foods'] = []
            session['selected_foods'].append({
                'product_name': product_name,
                'grams': grams,
                'co2': round(co2_emissions, 2),  # CO2 in kg
                'protein': round(protein, 2),
                'carbs': round(carbs, 2),
                'fat': round(fat, 2),
                'calories': round(energi, 2)
            })
            # Insert food selection into the UserFoodLog table with user_id
            cursor.execute("""
                INSERT INTO UserFoodLog (user_id, product_name, grams, rCO2, rEnergi, rFedt, rKulhydrat, rProtein)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (session["user_id"], product_name, grams, round(co2_emissions, 2), round(energi, 2), round(fat, 2), round(carbs, 2), round(protein, 2)))
            conn.commit()  # Save changes to the database
            return redirect("/search")  # Redirect to update the page with the new item
    # Handle food removal
    if request.method == "POST" and 'remove_food' in request.form:
        food_index = int(request.form.get('remove_food'))  # Get the index from the button's value
        selected_foods = session.get('selected_foods', [])
    
        if 0 <= food_index < len(selected_foods):
            selected_foods.pop(food_index)  # Remove the selected food item
            session['selected_foods'] = selected_foods  # Update the session with the modified list
            conn.commit()  # Commit any changes if needed
        return redirect("/search")  # Redirect to update the page after removal
    # Handling GET requests for search functionality
    search_query = request.args.get('search', '')
    if search_query:
        cursor.execute("SELECT Navn FROM Food_product WHERE Navn LIKE ?", ('%' + search_query + '%',))
        results = cursor.fetchall()
    else:
        results = []
    # Calculate total values for the session's selected foods
    selected_foods = session.get('selected_foods', [])
    total_co2 = sum(item['co2'] for item in selected_foods)  # Total CO2 in kg
    total_protein = sum(item['protein'] for item in selected_foods)
    total_carbs = sum(item['carbs'] for item in selected_foods)
    total_fat = sum(item['fat'] for item in selected_foods)
    total_calories = sum(item['calories'] for item in selected_foods)
    # Fixed average CO2 emissions for Danes (1.6 kg per meal)
    average_co2 = 3.6  # Average CO2 emissions per meal in kg
    co2_comparison = ""
    co2_color = ""  # Variable for color
    # Determine color based on CO2 comparison
    if total_co2 > average_co2:
        co2_comparison = f"Your meal emits {total_co2 - average_co2:.2f} kg more CO2 than the average ({average_co2:.2f} kg)."
        co2_color = "red"
    elif total_co2 < average_co2:
        co2_comparison = f"Your meal emits {average_co2 - total_co2:.2f} kg less CO2 than the average ({average_co2:.2f} kg)."
        co2_color = "green"
    else:
        co2_comparison = "Your meal emits the same amount of CO2 as the average."
        co2_color = "yellow"
 
    conn.close()
    return render_template("search.html", Username=session.get("Username"), results=results, selected_foods=selected_foods, 
                           total_co2=total_co2, total_protein=total_protein,
                           total_carbs=total_carbs, total_fat=total_fat, total_calories=total_calories,
                           co2_comparison=co2_comparison, co2_color=co2_color,
    )
# ______________________________________________Information page_____________________________________________________________________________
# ___________________________________________________________________________________________________________________________________________
@app.route("/information")
def information():
    if "Email" in session:
        return render_template("information.html",  Username=session.get("Username"))
    return redirect("/login")  # If not logged in, redirect to login page


# ______________________________________________Do not delete (needed to run python)_________________________________________________________
# ___________________________________________________________________________________________________________________________________________
if __name__ == "__main__":
#    load_csv_to_db()
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os
from datetime import datetime
import json
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

app = Flask(__name__)
CORS(app)

# Debug: Print environment variables
print("=== Debug Info ===")
print("SUPABASE_URL:", os.getenv('SUPABASE_URL'))
print("SUPABASE_KEY:", os.getenv('SUPABASE_KEY')[:20] + "..." if os.getenv('SUPABASE_KEY') else "None")

# Supabase configuration
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not supabase_url or not supabase_key:
    print("❌ ERROR: Missing Supabase credentials in .env file")
else:
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase client created successfully!")
# If Supabase fails, use a simple mock for now
try:
    supabase = create_client(supabase_url, supabase_key)
    print("✅ Supabase client created successfully!")
except Exception as e:
    print(f"⚠️ Supabase connection failed: {e}")
    print("🔄 Using mock mode for development...")
    # We'll create a mock supabase object for development
    class MockSupabase:
        def table(self, name):
            return MockTable()
    class MockTable:
        def insert(self, data):
            return MockQuery()
        def select(self, *args):
            return MockQuery()
        def eq(self, key, value):
            return MockQuery()
        def execute(self):
            return type('obj', (object,), {'data': []})
    class MockQuery:
        def insert(self, data):
            return self
        def select(self, *args):
            return self
        def eq(self, key, value):
            return self
        def execute(self):
            return type('obj', (object,), {'data': []})
    
    supabase = MockSupabase()    

# Test route
@app.route('/')
def home():
    return jsonify({"message": "Travel App Backend is running!", "status": "success"})

# User Registration
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        # Create user in Supabase Auth
        user_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if user_response.user:
            # Store additional user data in profiles table
            supabase.table('profiles').insert({
                'id': user_response.user.id,
                'email': email,
                'full_name': full_name,
                'created_at': datetime.now().isoformat()
            }).execute()
            
            return jsonify({
                "message": "User created successfully",
                "user": {
                    "id": user_response.user.id,
                    "email": user_response.user.email
                }
            })
        else:
            return jsonify({"error": "User creation failed"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# User Login
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        return jsonify({
            "message": "Login successful",
            "user": user_response.user,
            "session": user_response.session
        })
        
    except Exception as e:
        return jsonify({"error": "Invalid credentials"}), 401

# Search Flights (Mock Data - Replace with real flight API later)
@app.route('/api/flights/search', methods=['POST'])
def search_flights():
    try:
        data = request.get_json()
        origin = data.get('origin', '').upper()
        destination = data.get('destination', '').upper()
        departure_date = data.get('departure_date')
        passengers = data.get('passengers', 1)
        
        # Mock flight data - In production, connect to Amadeus/Skyscanner API
        mock_flights = [
            {
                "id": "FL001",
                "airline": "Air India",
                "flight_number": "AI101",
                "origin": origin,
                "destination": destination,
                "departure_time": "08:00 AM",
                "arrival_time": "10:30 AM",
                "duration": "2h 30m",
                "price": 12500,
                "seats_available": 45,
                "date": departure_date
            },
            {
                "id": "FL002",
                "airline": "IndiGo",
                "flight_number": "6E202",
                "origin": origin,
                "destination": destination,
                "departure_time": "14:15 PM",
                "arrival_time": "16:45 PM",
                "duration": "2h 30m",
                "price": 8900,
                "seats_available": 32,
                "date": departure_date
            },
            {
                "id": "FL003",
                "airline": "SpiceJet",
                "flight_number": "SG303",
                "origin": origin,
                "destination": destination,
                "departure_time": "19:30 PM",
                "arrival_time": "22:00 PM",
                "duration": "2h 30m",
                "price": 7600,
                "seats_available": 28,
                "date": departure_date
            }
        ]
        
        # Store search history
        if 'user_id' in data:
            supabase.table('search_history').insert({
                'user_id': data['user_id'],
                'origin': origin,
                'destination': destination,
                'departure_date': departure_date,
                'passengers': passengers,
                'searched_at': datetime.now().isoformat()
            }).execute()
        
        return jsonify({
            "flights": mock_flights,
            "search_params": {
                "origin": origin,
                "destination": destination,
                "date": departure_date,
                "passengers": passengers
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Create Booking
@app.route('/api/bookings/create', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        
        booking_data = {
            'user_id': data.get('user_id'),
            'flight_id': data.get('flight_id'),
            'passenger_name': data.get('passenger_name'),
            'passenger_email': data.get('passenger_email'),
            'passenger_phone': data.get('passenger_phone'),
            'origin': data.get('origin'),
            'destination': data.get('destination'),
            'departure_date': data.get('departure_date'),
            'flight_time': data.get('flight_time'),
            'airline': data.get('airline'),
            'flight_number': data.get('flight_number'),
            'total_amount': data.get('total_amount'),
            'booking_status': 'confirmed',
            'booking_reference': f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase.table('bookings').insert(booking_data).execute()
        
        return jsonify({
            "message": "Booking created successfully",
            "booking": response.data[0] if response.data else None,
            "booking_reference": booking_data['booking_reference']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Get User Bookings
@app.route('/api/bookings/user/<user_id>', methods=['GET'])
def get_user_bookings(user_id):
    try:
        response = supabase.table('bookings')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        return jsonify({"bookings": response.data})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Get User Profile
@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        response = supabase.table('profiles')\
            .select('*')\
            .eq('id', user_id)\
            .execute()
        
        return jsonify({"profile": response.data[0] if response.data else None})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Update User Profile
@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        update_data = {
            'full_name': data.get('full_name'),
            'phone': data.get('phone'),
            'date_of_birth': data.get('date_of_birth'),
            'nationality': data.get('nationality'),
            'updated_at': datetime.now().isoformat()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        response = supabase.table('profiles')\
            .update(update_data)\
            .eq('id', user_id)\
            .execute()
        
        return jsonify({
            "message": "Profile updated successfully",
            "profile": response.data[0] if response.data else None
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
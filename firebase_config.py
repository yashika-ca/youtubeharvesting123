import pyrebase

firebase_config = {
    "apiKey": "AIzaSyBEBhZjPSopndZGsVOQmMJkJuonuc9RtqI",
    "authDomain": "warthi-ce145.firebaseapp.com",
    "databaseURL": "",
    "projectId": "warthi-ce145",
    "storageBucket": "warthi-ce145.firebasestorage.app",
    "messagingSenderId": "328148162342",
    "appId": "1:328148162342:web:f05c39310fe07e691213e7",
    "measurementId": "G-88QS9CYPZW"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

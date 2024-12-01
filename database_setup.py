import pymysql
import random
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding

# Database connection details
db_host = "localhost"
db_user = "root"
db_password = ""
db_name = "secure_db"

# AES block size (128 bits)
BLOCK_SIZE = 16

# Check if the AES key already exists; if not, generate a new one
if not os.path.exists('aes_key.txt'):
    AES_KEY = os.urandom(32)  # AES Key (256 bits for AES-256)
    # Save the AES Key to a text file
    with open('aes_key.txt', 'wb') as aes_key_file:
        aes_key_file.write(AES_KEY)
    print("AES key generated and saved to aes_key.txt.")
else:
    # If the key file exists, load the existing key
    with open('aes_key.txt', 'rb') as aes_key_file:
        AES_KEY = aes_key_file.read()
    print("AES key loaded from aes_key.txt.")

# RSA Key Generation (Secure RSA Key pair)
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
    backend=default_backend()
)

public_key = private_key.public_key()

# Save the RSA private key and public key to text files
with open('private_key.pem', 'wb') as private_key_file:
    private_key_file.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ))

with open('public_key.pem', 'wb') as public_key_file:
    public_key_file.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ))

# Encryption function using AES (CBC mode)
def encrypt_value_aes(value):
    # Generate a random IV
    iv = os.urandom(BLOCK_SIZE)
    
    # Create AES cipher object
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # Ensure the value is converted to bytes and then padded
    value_bytes = str(value).encode('utf-8')

    # Pad the value to be a multiple of BLOCK_SIZE
    padder = padding.PKCS7(BLOCK_SIZE * 8).padder()
    padded_value = padder.update(value_bytes) + padder.finalize()

    # Encrypt the value
    encrypted_value = encryptor.update(padded_value) + encryptor.finalize()
    
    # Return the IV concatenated with the encrypted value
    return iv + encrypted_value

# Encryption function using RSA
def encrypt_value_rsa(value):
    value_bytes = str(value).encode('utf-8')
    encrypted_value = public_key.encrypt(
        value_bytes,
        asymmetric_padding.OAEP(
            mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_value

# Function to create the database if it doesn't exist
def create_database():
    connection = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password
    )
    cursor = connection.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name};")
    connection.commit()
    connection.close()
    print(f"Database '{db_name}' created or already exists.")

# Function to create tables and insert random data
def setup_database():
    # Ensure the database is created before connecting to it
    create_database()
    
    db = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = db.cursor()

    # Create users table
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        group_name ENUM('H', 'R') NOT NULL
    );
    """)

    # Create healthcare table (without encrypting weight and health history)
    cursor.execute(""" 
    CREATE TABLE IF NOT EXISTS healthcare (
        id INT AUTO_INCREMENT PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        gender BOOLEAN,
        age INT,
        weight FLOAT,
        height FLOAT,
        health_history VARCHAR(255),
        encrypted_ssn BLOB
    );
    """)

    # Generate random data
    first_names = ["John", "Jane", "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Hank"]
    last_names = ["Smith", "Doe", "Brown", "Johnson", "Williams", "Jones", "Davis", "Miller", "Wilson", "Taylor"]
    health_issues = ["No major issues", "Asthma", "Diabetes", "Hypertension", "Allergies", "Heart disease", "Arthritis"]
    
    for _ in range(100):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        gender = random.choice([0, 1])  # 0 for female, 1 for male
        age = random.randint(18, 80)
        weight = round(random.uniform(50, 100), 1)
        height = round(random.uniform(150, 200), 1)
        health_history = random.choice(health_issues)
        ssn = random.randint(100000000, 999999999)  # Sample SSN (will be encrypted)

        # Encrypt SSN with RSA
        encrypted_ssn = encrypt_value_rsa(ssn)

        cursor.execute(""" 
        INSERT INTO healthcare (first_name, last_name, gender, age, weight, height, health_history, encrypted_ssn) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (first_name, last_name, gender, age, weight, height, health_history, encrypted_ssn))

    db.commit()
    db.close()
    print("Database setup complete with 100 random records.")

if __name__ == "__main__":
    setup_database()

# BMSTU LKS Login

A Python library for authenticating with the BMSTU LKS (Personal Student Account) portal.

## Features

- Clean and simple API for logging into BMSTU LKS
- Proper handling of JWT and JSON tokens
- Type hints and comprehensive documentation
- Token validation and expiration checking
- Returns both raw tokens and decoded information

## Installation

```bash
pip install bmstu-lks-login
```

## Usage

```python
from datetime import datetime
from bmstu_lks_login import BmstuLksClient

# Create a client (optionally provide a fixed time for token validation)
client = BmstuLksClient(current_time=datetime.now())

# Log in and get tokens
try:
    response = client.login("username", "password")
    
    # Access token information
    print(f"Login token expires at: {response.login_token.expiration}")
    print(f"Student name: {response.login_token.name}")
    print(f"Student ID: {response.student_id}")
    print(f"Group: {response.group}")
    
    # Access raw tokens for API calls
    login_token = response.login_token.raw_token
    info_token = response.info_token.raw_token
    
except LoginError as e:
    print(f"Login failed: {e}")
```

## Token Information

The library provides two tokens:

1. `portal3_login` - JWT token containing:
   - User information (name, ID, group)
   - Token expiration time
   - Other authentication data

2. `portal3_info` - Base64-encoded JSON token containing:
   - User name
   - Token expiration time

Both tokens are provided in both raw and decoded form through the `TokenInfo` class.

## Dependencies

- `requests` - For HTTP requests
- `beautifulsoup4` - For parsing login form
- `PyJWT` - For JWT token handling

## Development

1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Run tests: `pytest`

## License

MIT License

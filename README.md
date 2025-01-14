# BMSTU LKS Login Library

A Python library for authenticating with the BMSTU LKS (Personal Student Account) portal. This library handles the authentication flow and token management for accessing the BMSTU LKS portal.

## Features

- Handles CAS (Central Authentication Service) login flow
- Manages JWT and JSON tokens
- Provides decoded token information including user details
- Handles token expiration validation
- Supports fixed time for testing purposes

## Installation

You can install the library directly from GitHub using pip:

```bash
pip install git+https://github.com/cucumber-sp/bmstu_lks_login.git
```

Or clone the repository and install in development mode:

```bash
git clone https://github.com/cucumber-sp/bmstu_lks_login.git
cd bmstu_lks_login
pip install -e .
```

## Usage

Here's a basic example of how to use the library:

```python
from bmstu_lks_login import BmstuLksClient, LoginError

try:
    # Create client
    client = BmstuLksClient()
    
    # Attempt login
    response = client.login("username", "password")
    
    # Access token information
    print(f"Name: {response.login_token.name}")
    print(f"Student ID: {response.student_id}")
    print(f"Group: {response.group}")
    print(f"Token expiration: {response.login_token.expiration}")
    
except LoginError as e:
    print(f"Login failed: {str(e)}")
```

## Dependencies

- Python 3.7+
- requests
- beautifulsoup4
- PyJWT

## Development

To set up the development environment:

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install development dependencies:
   ```bash
   pip install -e .
   ```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

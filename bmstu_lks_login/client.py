"""BMSTU LKS Login Client implementation."""

import base64
import json
import logging
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import quote, urljoin

import jwt
import requests
from bs4 import BeautifulSoup

from .types import LoginResponse, TokenInfo


class LoginError(Exception):
    """Raised when login process fails."""
    pass


class BmstuLksClient:
    """Client for authenticating with BMSTU LKS portal."""
    
    PORTAL_LOGIN_URL = "https://lks.bmstu.ru/login"
    PORTAL_PROFILE_URL = "https://lks.bmstu.ru/profile"
    
    def __init__(self, current_time: Optional[datetime] = None):
        """Initialize the client.
        
        Args:
            current_time: Optional fixed time to use for token validation.
                        If not provided, system time will be used.
        """
        self.current_time = current_time
        self.logger = logging.getLogger(__name__)
        
        # Default headers for requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def _extract_form_data(self, html_content: str) -> dict:
        """Extract hidden form fields from login page.
        
        Args:
            html_content: HTML content of the login page.
            
        Returns:
            Dictionary of form field names and values.
            
        Raises:
            LoginError: If form fields cannot be found.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        form = soup.find('form')
        if not form:
            raise LoginError("Could not find login form")
            
        form_data = {}
        for input_tag in form.find_all('input'):
            if input_tag.get('type') == 'hidden' and input_tag.get('name'):
                form_data[input_tag['name']] = input_tag.get('value', '')
                
        return form_data
    
    def _extract_token_from_cookie(self, cookie_str: str, token_name: str) -> Optional[str]:
        """Extract token value from Set-Cookie header.
        
        Args:
            cookie_str: The Set-Cookie header value.
            token_name: Name of the token to extract.
            
        Returns:
            The token value if found, None otherwise.
        """
        prefix = f'__{token_name}='
        if prefix in cookie_str:
            return cookie_str.split(prefix)[1].split(';')[0]
        return None
    
    def _decode_portal_token(self, token: str, token_name: str) -> TokenInfo:
        """Decode and validate a portal token.
        
        Args:
            token: The token string to decode.
            token_name: Name of the token ("portal3_login" or "portal3_info").
            
        Returns:
            TokenInfo object containing decoded token data.
            
        Raises:
            LoginError: If token is invalid or expired.
        """
        try:
            if token_name == "portal3_login":
                # Use JWT decoding for login token
                decoded = jwt.decode(token, options={"verify_signature": False})
                exp_field = 'exp'
            else:
                # Use base64 + JSON decoding for info token
                decoded_bytes = base64.b64decode(token)
                decoded = json.loads(decoded_bytes.decode('utf-8'))
                exp_field = 'expire'
            
            # Get expiration time
            exp_timestamp = decoded.get(exp_field)
            if not exp_timestamp:
                raise LoginError(f"No expiration time in {token_name} token")
                
            expiration = datetime.fromtimestamp(exp_timestamp)
            
            # Check expiration
            current_time = self.current_time or datetime.now()
            if current_time.timestamp() > exp_timestamp:
                raise LoginError(f"{token_name} token has expired")
            
            # Extract name
            name = None
            if token_name == "portal3_login":
                name = decoded.get('usr', {}).get('name')
            else:
                name = decoded.get('name')
            
            return TokenInfo(
                raw_token=token,
                decoded_data=decoded,
                expiration=expiration,
                name=name
            )
            
        except (jwt.InvalidTokenError, json.JSONDecodeError, base64.binascii.Error) as e:
            raise LoginError(f"Invalid {token_name} token: {str(e)}")
    
    def login(self, username: str, password: str) -> LoginResponse:
        """Log in to BMSTU LKS portal.
        
        Args:
            username: BMSTU username.
            password: BMSTU password.
            
        Returns:
            LoginResponse object containing tokens and user information.
            
        Raises:
            LoginError: If login process fails.
        """
        with requests.Session() as session:
            # Start at portal login page
            encoded_back_url = quote(self.PORTAL_PROFILE_URL)
            portal_login_with_back = f"{self.PORTAL_LOGIN_URL}?back={encoded_back_url}"
            
            self.logger.info("Starting login process...")
            portal_response = session.get(portal_login_with_back, headers=self.headers, allow_redirects=True)
            
            if portal_response.status_code != 200:
                raise LoginError(f"Failed to access portal login page: {portal_response.status_code}")
            
            # Get the CAS login form
            cas_url = portal_response.url
            form_data = self._extract_form_data(portal_response.text)
            
            form_data.update({
                "username": username,
                "password": password,
                "submit": "LOGIN"
            })
            
            # Prepare headers for CAS login
            cas_headers = self.headers.copy()
            cas_headers.update({
                'Origin': 'https://proxy.bmstu.ru:8443',
                'Referer': cas_url,
                'Content-Type': 'application/x-www-form-urlencoded'
            })
            
            # Submit CAS login
            self.logger.info("Submitting login credentials...")
            cas_response = session.post(
                cas_url,
                data=form_data,
                headers=cas_headers,
                allow_redirects=False
            )
            
            if cas_response.status_code == 401:
                raise LoginError("Invalid username or password")
            
            # Follow redirects manually to capture all cookies
            current_response = cas_response
            login_token = None
            info_token = None
            
            while current_response.status_code in (301, 302, 303, 307):
                redirect_url = current_response.headers.get('Location')
                if not redirect_url:
                    break
                    
                # Make redirect URL absolute if it's relative
                if redirect_url.startswith('/'):
                    redirect_url = urljoin(current_response.url, redirect_url)
                    
                # Update headers based on domain
                redirect_headers = self.headers.copy()
                if 'lks.bmstu.ru' in redirect_url:
                    redirect_headers['Origin'] = 'https://lks.bmstu.ru'
                    redirect_headers['Referer'] = self.PORTAL_LOGIN_URL
                else:
                    redirect_headers['Origin'] = 'https://proxy.bmstu.ru:8443'
                    redirect_headers['Referer'] = current_response.url
                
                current_response = session.get(
                    redirect_url,
                    headers=redirect_headers,
                    allow_redirects=False
                )
                
                # Check for portal tokens in Set-Cookie header
                if 'Set-Cookie' in current_response.headers:
                    cookies = current_response.headers.get_all('Set-Cookie') if hasattr(current_response.headers, 'get_all') else [current_response.headers.get('Set-Cookie')]
                    for cookie in cookies:
                        if not login_token:
                            login_token = self._extract_token_from_cookie(cookie, 'portal3_login')
                        if not info_token:
                            info_token = self._extract_token_from_cookie(cookie, 'portal3_info')
                        
                        if login_token and info_token:
                            self.logger.info("Successfully obtained portal tokens")
                            
                            # Decode both tokens
                            login_token_info = self._decode_portal_token(login_token, "portal3_login")
                            info_token_info = self._decode_portal_token(info_token, "portal3_info")
                            
                            # Extract additional user info
                            user_info = login_token_info.decoded_data.get('usr', {})
                            student_id = user_info.get('id')
                            group = user_info.get('alias')
                            
                            return LoginResponse(
                                login_token=login_token_info,
                                info_token=info_token_info,
                                student_id=student_id,
                                group=group
                            )
            
            raise LoginError("Did not receive portal tokens")

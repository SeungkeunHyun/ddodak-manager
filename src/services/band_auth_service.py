import requests
import streamlit as st
import base64
from typing import Optional, Dict, Any, List

class BandAuthService:
    """
    Naver Band OAuth2 Authentication Service
    """
    TOKEN_URL = "https://auth.band.us/oauth2/token"
    PROFILE_URL = "https://openapi.band.us/v2/profile"
    BANDS_URL = "https://openapi.band.us/v2.1/bands"
    PERMISSIONS_URL = "https://openapi.band.us/v2.1/band/permissions"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_authorization_url(self) -> str:
        return f"https://auth.band.us/oauth2/authorize?response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}"

    def exchange_code_for_token(self, code: str) -> Optional[str]:
        """
        Exchanges the authorization code for an access token.
        """
        auth_header = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        
        params = {
            "grant_type": "authorization_code",
            "code": code
        }
        # Merge Auth header with default headers
        headers = self.HEADERS.copy()
        headers["Authorization"] = f"Basic {auth_header}"
        
        try:
            response = requests.get(self.TOKEN_URL, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                st.error(f"Band Token Error: {response.text}")
                return None
        except Exception as e:
            st.error(f"Token Exchange Exception: {e}")
            return None

    def get_user_profile(self, access_token: str) -> Dict[str, Any]:
        params = {"access_token": access_token}
        response = requests.get(self.PROFILE_URL, params=params, headers=self.HEADERS)
        if response.status_code == 200:
            return response.json().get("result_data", {})
        return {}

    def get_user_bands(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Fetches the list of bands the user belongs to.
        Returns: List of dicts with keys: name, band_key, cover, member_count
        """
        params = {"access_token": access_token}
        response = requests.get(self.BANDS_URL, params=params, headers=self.HEADERS)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("result_code") == 1:
                return data["result_data"]["bands"]
        return []

    def get_permissions(self, access_token: str, band_key: str) -> bool:
        """
        Checks if the user has a valid role (Leader/Co-leader) in the target band.
        """
        params = {
            "access_token": access_token,
            "band_key": band_key
        }
        
        try:
            response = requests.get(self.PERMISSIONS_URL, params=params, headers=self.HEADERS)
            if response.status_code == 200:
                data = response.json()
                if data.get("result_code") == 1:
                    perms = data["result_data"]["permissions"]
                    # Check for Leader or Co-Leader role
                    is_leader = perms.get("is_band_leader", False)
                    is_coleader = perms.get("is_co_leader", False)
                    
                    if is_leader or is_coleader:
                        return True
                    else:
                        st.error("권한 부족: 밴드의 리더(Leader) 또는 공동리더(Co-Leader)만 접근 가능합니다.")
                        return False
                else:
                    st.warning(f"Permission Check Failed (Band API): {data}")
                    return False
            else:
                st.error(f"Band API Error: {response.status_code}")
                return False
        except Exception as e:
            st.error(f"Permission Check Error: {e}")
            return False

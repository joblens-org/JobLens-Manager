import pytest
from unittest.mock import patch
from fastapi import HTTPException
from starlette.requests import Request

from backend.common.auth import (
    verify_token,
    create_token,
    ip_in_whitelist,
    resolve_client_ip,
)
from backend.config import settings


class TestIpInWhitelist:
    def test_exact_ip_match(self):
        assert ip_in_whitelist("127.0.0.1", "127.0.0.1") is True
        assert ip_in_whitelist("192.168.1.1", "127.0.0.1") is False

    def test_cidr_match(self):
        assert ip_in_whitelist("10.0.0.1", "10.0.0.0/8") is True
        assert ip_in_whitelist("10.255.255.255", "10.0.0.0/8") is True
        assert ip_in_whitelist("192.168.1.1", "10.0.0.0/8") is False

    def test_multiple_entries(self):
        whitelist = "127.0.0.1,10.0.0.0/8,192.168.1.1"
        assert ip_in_whitelist("127.0.0.1", whitelist) is True
        assert ip_in_whitelist("10.0.0.5", whitelist) is True
        assert ip_in_whitelist("192.168.1.1", whitelist) is True
        assert ip_in_whitelist("192.168.1.2", whitelist) is False

    def test_invalid_ip(self):
        assert ip_in_whitelist("invalid-ip", "127.0.0.1") is False

    def test_ipv6(self):
        assert ip_in_whitelist("::1", "::1") is True
        assert ip_in_whitelist("::1", "127.0.0.1,::1") is True


class TestResolveClientIp:
    def _create_request(self, client_host: str, headers: dict[str, str] | None = None) -> Request:
        headers_list: list[tuple[bytes, bytes]] = [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ]
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers_list,
            "client": (client_host, 12345),
        }
        return Request(scope)

    @patch.object(settings, "trust_proxy_headers", False)
    def test_default_ignores_spoofed_headers(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "1.2.3.4", "X-Real-IP": "5.6.7.8"},
        )
        result = resolve_client_ip(request)
        assert result == "192.168.1.100"

    @patch.object(settings, "trust_proxy_headers", True)
    def test_trusted_xff_first_ip(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "10.0.0.1, 10.0.0.2, 10.0.0.3"},
        )
        result = resolve_client_ip(request)
        assert result == "10.0.0.1"

    @patch.object(settings, "trust_proxy_headers", True)
    def test_trusted_xrealip_fallback(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Real-IP": "10.0.0.5"},
        )
        result = resolve_client_ip(request)
        assert result == "10.0.0.5"

    @patch.object(settings, "trust_proxy_headers", True)
    def test_trusted_direct_fallback(self):
        request = self._create_request("192.168.1.100")
        result = resolve_client_ip(request)
        assert result == "192.168.1.100"

    @patch.object(settings, "trust_proxy_headers", True)
    def test_trusted_empty_xff_fallback(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "", "X-Real-IP": "10.0.0.6"},
        )
        result = resolve_client_ip(request)
        assert result == "10.0.0.6"

    @patch.object(settings, "trust_proxy_headers", True)
    def test_trusted_xff_whitespace_only_fallback(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "   ,   ", "X-Real-IP": "10.0.0.7"},
        )
        result = resolve_client_ip(request)
        assert result == "10.0.0.7"


class TestVerifyToken:
    def _create_request(self, client_host: str, headers: dict[str, str] | None = None) -> Request:
        headers_list: list[tuple[bytes, bytes]] = [
            (k.lower().encode(), v.encode()) for k, v in (headers or {}).items()
        ]
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": headers_list,
            "client": (client_host, 12345),
        }
        return Request(scope)

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", False)
    @patch.object(settings, "auth_whitelist_ips", "1.2.3.4")
    async def test_rejects_spoofed_whitelist_header_by_default(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "1.2.3.4"},
        )
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(request, None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", True)
    @patch.object(settings, "auth_whitelist_ips", "10.0.0.1")
    async def test_accepts_whitelist_when_trust_proxy_headers_true(self):
        request = self._create_request(
            "192.168.1.100",
            {"X-Forwarded-For": "10.0.0.1"},
        )
        result = await verify_token(request, None)
        assert result is None

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", False)
    @patch.object(settings, "auth_whitelist_ips", "127.0.0.1")
    async def test_whitelist_bypass_with_direct_ip(self):
        request = self._create_request("127.0.0.1")
        result = await verify_token(request, None)
        assert result is None

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", False)
    @patch.object(settings, "auth_whitelist_ips", "")
    async def test_no_whitelist_requires_auth(self):
        request = self._create_request("127.0.0.1")
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(request, None)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", False)
    @patch.object(settings, "auth_whitelist_ips", "")
    @patch.object(settings, "admin_password", "testpass123")
    async def test_valid_token_passes(self):
        with patch("backend.common.auth.settings.admin_password", "testpass123"):
            token = create_token()

        request = self._create_request("192.168.1.100")
        result = await verify_token(request, f"Bearer {token}")
        assert result is None

    @pytest.mark.asyncio
    @patch.object(settings, "trust_proxy_headers", False)
    @patch.object(settings, "auth_whitelist_ips", "")
    async def test_invalid_token_fails(self):
        request = self._create_request("192.168.1.100")
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(request, "Bearer invalid-token")
        assert exc_info.value.status_code == 401
        assert "令牌无效" in exc_info.value.detail

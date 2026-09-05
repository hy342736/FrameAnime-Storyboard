import unittest

from fastapi import HTTPException

from app import main


class ClosedBrowserSession:
    async def open_for_login(self) -> str:
        raise RuntimeError("BrowserContext.new_page: Target page, context or browser has been closed")


class LoginErrorContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_login_returns_json_http_error_when_browser_context_is_closed(self):
        original_session = main.session
        main.session = ClosedBrowserSession()
        try:
            with self.assertRaises(HTTPException) as captured:
                await main.login()
        finally:
            main.session = original_session

        self.assertEqual(captured.exception.status_code, 503)
        self.assertIn("浏览器会话不可用", captured.exception.detail)


if __name__ == "__main__":
    unittest.main()

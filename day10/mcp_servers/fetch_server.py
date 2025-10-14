"""HTTP Fetch MCP Server using FastMCP.

This MCP server provides HTTP fetch capabilities similar to the official
mcp-server-fetch, but uses urllib from standard library to avoid httpx
version conflicts. Supports robots.txt, HTML simplification, and pagination.
"""

import urllib.request
import urllib.error
import urllib.robotparser
from urllib.parse import urlparse
from html.parser import HTMLParser
import re

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("HTTP Fetch Server")


class HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.text = []
        self.skip_tags = {'script', 'style', 'noscript'}
        self.current_tag = None

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag

    def handle_endtag(self, tag):
        self.current_tag = None
        if tag in {'p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}:
            self.text.append('\n')

    def handle_data(self, data):
        if self.current_tag not in self.skip_tags:
            text = data.strip()
            if text:
                self.text.append(text + ' ')

    def get_text(self):
        return ''.join(self.text).strip()


def check_robots_txt(url: str, user_agent: str = "MCP-Fetch-Server/1.0") -> bool:
    """Check if fetching URL is allowed by robots.txt.

    Args:
        url: URL to check
        user_agent: User agent string

    Returns:
        True if allowed, False otherwise
    """
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()

        return rp.can_fetch(user_agent, url)
    except Exception:
        # If we can't read robots.txt, assume it's allowed
        return True


def html_to_text(html: str) -> str:
    """Convert HTML to plain text.

    Args:
        html: HTML content

    Returns:
        Plain text content
    """
    try:
        extractor = HTMLTextExtractor()
        extractor.feed(html)
        text = extractor.get_text()

        # Clean up multiple spaces and newlines
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\n+', '\n', text)

        return text.strip()
    except Exception:
        # If parsing fails, return raw HTML
        return html


@mcp.tool()
def fetch(
    url: str,
    max_length: int = 5000,
    start_index: int = 0,
    raw: bool = False,
    check_robots: bool = True,
    timeout: int = 10
) -> dict:
    """Fetch content from a URL using HTTP/HTTPS.

    Similar to official mcp-server-fetch with support for:
    - robots.txt checking
    - HTML to text conversion
    - Content pagination

    Args:
        url: The URL to fetch
        max_length: Maximum characters to return (default: 5000)
        start_index: Character index to start from (default: 0)
        raw: Return raw HTML instead of simplified text (default: False)
        check_robots: Check robots.txt before fetching (default: True)
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Dictionary with success, content, and metadata
    """
    user_agent = "MCP-Fetch-Server/1.0"

    # Check robots.txt if enabled
    if check_robots and not check_robots_txt(url, user_agent):
        return {
            "success": False,
            "error": "Fetching this URL is disallowed by robots.txt",
            "message": f"Access denied by robots.txt for {url}"
        }

    try:
        request = urllib.request.Request(url, method='GET')
        request.add_header('User-Agent', user_agent)

        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            content_type = response.headers.get('Content-Type', '')

            # Read response body
            body_bytes = response.read()

            # Try to decode as text
            try:
                body_text = body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return {
                    "success": False,
                    "error": "Content is not text (binary data)",
                    "message": f"Cannot decode binary content from {url}"
                }

            # Convert HTML to text if not raw mode
            if not raw and 'html' in content_type.lower():
                content = html_to_text(body_text)
            else:
                content = body_text

            # Apply pagination
            total_length = len(content)
            end_index = start_index + max_length

            if start_index >= total_length:
                return {
                    "success": False,
                    "error": f"start_index ({start_index}) exceeds "
                             f"content length ({total_length})",
                    "message": "Invalid pagination"
                }

            content_slice = content[start_index:end_index]
            is_truncated = end_index < total_length

            result = {
                "success": True,
                "status_code": status_code,
                "content_type": content_type,
                "content": content_slice,
                "total_length": total_length,
                "start_index": start_index,
                "returned_length": len(content_slice),
                "is_truncated": is_truncated,
                "message": f"Successfully fetched {url}"
            }

            # Add continuation info if truncated
            if is_truncated:
                result["next_start_index"] = end_index
                result["message"] += (
                    f" (showing characters {start_index}-{end_index} "
                    f"of {total_length})"
                )

            return result

    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode('utf-8')[:500]
        except Exception:
            pass

        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP {e.code}: {e.reason}",
            "error_body": error_body,
            "message": f"Failed to fetch {url}"
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e.reason)}",
            "message": f"Failed to connect to {url}"
        }

    except TimeoutError:
        return {
            "success": False,
            "error": f"Request timeout after {timeout} seconds",
            "message": f"Failed to fetch {url}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": f"Failed to fetch {url}"
        }


@mcp.tool()
def fetch_head(url: str, timeout: int = 10) -> dict:
    """Fetch only headers from a URL using HTTP HEAD request.

    Args:
        url: The URL to check
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Dictionary with success status, status code, and headers
    """
    try:
        request = urllib.request.Request(url, method='HEAD')
        request.add_header('User-Agent', 'MCP-Fetch-Server/1.0')

        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            headers = dict(response.headers)

            return {
                "success": True,
                "status_code": status_code,
                "headers": headers,
                "message": f"Successfully fetched headers from {url}"
            }

    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP {e.code}: {e.reason}",
            "message": f"Failed to fetch headers from {url}"
        }

    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Connection error: {str(e.reason)}",
            "message": f"Failed to connect to {url}"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "message": f"Failed to fetch headers from {url}"
        }


if __name__ == "__main__":
    mcp.run(show_banner=False)

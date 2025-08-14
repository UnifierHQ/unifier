"""
Tenor Link Formatter Utility

This module provides functions to format Tenor links appropriately for different platforms.
Discord expects: https://tenor.com/view/im-free-strawberry-red-rocket-freedom-fresh-air-gif-24731257
Revolt expects: https://tenor.com/view/24731257.gif
"""

import re
from typing import Optional


def format_tenor_for_discord(tenor_url: str) -> str:
    """
    Format a Tenor URL for Discord (full descriptive format).
    
    Args:
        tenor_url: The Tenor URL to format
        
    Returns:
        Formatted URL for Discord, or original URL if not a Tenor link
    """
    if not tenor_url or "tenor.com" not in tenor_url:
        return tenor_url
    
    # If it's already in Discord format, return as is
    if "/view/" in tenor_url and not tenor_url.endswith(".gif"):
        return tenor_url
    
    # Extract the ID from Revolt format (ends with .gif)
    if tenor_url.endswith(".gif"):
        # Remove .gif extension and get the ID
        id_match = re.search(r'/(\d+)\.gif$', tenor_url)
        if id_match:
            gif_id = id_match.group(1)
            # For Discord, we need the full descriptive path
            # Since we don't have the original description, we'll use a generic format
            return f"https://tenor.com/view/gif-{gif_id}"
    
    return tenor_url


def format_tenor_for_revolt(tenor_url: str) -> str:
    """
    Format a Tenor URL for Revolt (ID-only format).
    
    Args:
        tenor_url: The Tenor URL to format
        
    Returns:
        Formatted URL for Revolt, or original URL if not a Tenor link
    """
    if not tenor_url or "tenor.com" not in tenor_url:
        return tenor_url
    
    # If it's already in Revolt format, return as is
    if tenor_url.endswith(".gif") and re.search(r'/\d+\.gif$', tenor_url):
        return tenor_url
    
    # Extract the ID from Discord format - look for the last number in the URL
    id_match = re.search(r'(\d+)(?:-|$)', tenor_url)
    if id_match:
        gif_id = id_match.group(1)
        return f"https://tenor.com/view/{gif_id}.gif"
    
    return tenor_url


def format_tenor_links_in_content(content: str, target_platform: str) -> str:
    """
    Format all Tenor links in a message content for the target platform.
    
    Args:
        content: The message content containing potential Tenor links
        target_platform: Either 'discord' or 'revolt'
        
    Returns:
        Content with Tenor links formatted for the target platform
    """
    if not content or "tenor.com" not in content:
        return content
    
    # Find all Tenor URLs in the content
    tenor_url_pattern = r'https?://tenor\.com/[^\s]+'
    
    def replace_tenor_url(match):
        tenor_url = match.group(0)
        if target_platform == 'discord':
            return format_tenor_for_discord(tenor_url)
        elif target_platform == 'revolt':
            return format_tenor_for_revolt(tenor_url)
        else:
            return tenor_url
    
    return re.sub(tenor_url_pattern, replace_tenor_url, content)


def is_tenor_url(url: str) -> bool:
    """
    Check if a URL is a Tenor link.
    
    Args:
        url: The URL to check
        
    Returns:
        True if it's a Tenor link, False otherwise
    """
    return url and "tenor.com" in url 
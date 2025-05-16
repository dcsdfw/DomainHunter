import requests
from time import sleep
import socket

def check_domains(domains, delay=0.5, timeout=3):
    """
    Check if a list of domains are available for registration.
    
    Args:
        domains (list): List of domain names to check
        delay (float): Delay between requests in seconds
        timeout (int): Request timeout in seconds
        
    Returns:
        list: List of [domain, status] pairs
    """
    results = []
    
    for domain in domains:
        # Check if domain resolves to an IP (registered)
        try:
            # Try to resolve the domain
            socket.gethostbyname(domain)
            
            # If we get here, it resolved, so try to connect
            try:
                # First try HTTPS
                https_response = requests.get(f"https://{domain}", timeout=timeout, allow_redirects=True)
                if https_response.status_code < 400:
                    status = "Registered (Active Website)"
                else:
                    # If HTTPS fails, try HTTP
                    http_response = requests.get(f"http://{domain}", timeout=timeout, allow_redirects=True)
                    if http_response.status_code < 400:
                        status = "Registered (Active Website)"
                    else:
                        status = "Registered (No Active Website)"
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, Exception):
                # Domain exists but no website
                status = "Registered (No Active Website)"
        except socket.gaierror:
            # DNS lookup failed, domain likely available
            status = "Available"
        
        results.append([domain, status])
        
        # Add delay to prevent getting blocked
        if delay > 0:
            sleep(delay)
            
    return results

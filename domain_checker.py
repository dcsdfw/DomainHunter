import requests
from time import sleep

def check_domains(domains, delay=0.5, timeout=3):
    """
    Check if a list of domains are live.
    
    Args:
        domains (list): List of domain names to check
        delay (float): Delay between requests in seconds
        timeout (int): Request timeout in seconds
        
    Returns:
        list: List of [domain, status] pairs
    """
    results = []
    
    for domain in domains:
        try:
            # Try to connect to the domain
            response = requests.head(f"http://{domain}", timeout=timeout)
            status = "Live" if response.status_code < 400 else "Not Live"
        except requests.exceptions.ConnectionError:
            # This likely means the domain doesn't exist or isn't responding
            status = "Not Live"
        except requests.exceptions.Timeout:
            # Request timed out
            status = "Timeout"
        except Exception as e:
            # Other errors
            status = f"Error: {str(e)[:50]}"
        
        results.append([domain, status])
        
        # Add delay to prevent getting blocked
        if delay > 0:
            sleep(delay)
            
    return results

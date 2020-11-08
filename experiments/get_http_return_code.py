from urllib.error import HTTPError
import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def getResponseCode(url):
    try:
        conn = urllib.request.urlopen(url)
        print(f'HTTP status for {url}: {conn.getcode()}')
        return conn.getcode()
    except HTTPError as e:
        print(f'Error: {e.code}')
    except Exception as e:
        print(f'Other exception: {e}')
        pass

getResponseCode("https://netwealth.com.au")

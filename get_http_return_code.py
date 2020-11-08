import urllib.request
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def getResponseCode(url):
    conn = urllib.request.urlopen(url)
    print(f'HTTP status for {url}: {conn.getcode()}')
    return conn.getcode()

getResponseCode("https://netwealth.com.au")

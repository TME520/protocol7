import urllib.request

def getResponseCode(url):
    conn = urllib.request.urlopen(url)
    print(f'HTTP status for {url}: {conn.getcode()}')
    return conn.getcode()

getResponseCode("https://netwealth.com.au")

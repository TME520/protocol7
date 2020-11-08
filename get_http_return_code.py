import urllib2
for url in ["http://entrian.com/", "http://entrian.com/does-not-exist/"]:
    try:
        connection = urllib2.urlopen(url)
        print connection.getcode()
        connection.close()
    except urllib2.HTTPError, e:
        print e.getcode()

# Prints:
# 200 [from the try block]
# 404 [from the except block]


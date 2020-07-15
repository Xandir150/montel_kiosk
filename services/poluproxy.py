# -*- coding: utf-8 -*-
#!/usr/bin/python2


from BaseHTTPServer import BaseHTTPRequestHandler
import urlparse, urllib, urllib2, base64

username = 'europayment'
password = 'europayment.me.in'
place = 'TEST'

class GetHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header("Cache-Control", "no-cache")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        the_page = 'error'
        parsed_path = urlparse.urlparse(self.path)
        queryes = urlparse.parse_qs(parsed_path.query, keep_blank_values=True)

        if parsed_path.path == '/getuserinfo':
            try:
                print '/getuserinfo num=' + queryes['num'][0]
                req = urllib2.Request('http://www.rusgruppa.me/testPhone.php?phone=' + queryes['num'][0])
                response = urllib2.urlopen(req)
                the_page = response.read()
            except:
                pass
        
        elif parsed_path.path == '/charge':
            print '/charge'
            values = {
                'payment_id': queryes['payment_id'][0],
                'number': queryes['number'][0],
                'amount': queryes['amount'][0],
                'place': place,
                'date': queryes['date'][0]
                }
            data = urllib.urlencode(values)
            print '/charge POST=' + data
                
            base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            
            try:
                req = urllib2.Request('http://www.rusgruppa.me/api/charge', data)
                req.add_header("Authorization", "Basic %s" % base64string)
                response = urllib2.urlopen(req)
                the_page = response.read()
            except:
                with open('offline_proxy', 'a') as file:
                    file.write(data+"\n")
                pass
        elif parsed_path.path == '/ping':
            try:
                print
                req = urllib2.Request('http://www.rusgruppa.me/smsApiX.php?go=Sms&in=terminal&master=' + place)
                response = urllib2.urlopen(req)
                the_page = response.read()
            except:
                pass
                

        self.send_response(200)
        self.send_header("Cache-Control", "no-cache")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        print 'Response len = %d' % len(the_page)
        self.wfile.write(the_page)
        return

if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 8082), GetHandler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()
    
    

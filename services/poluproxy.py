# -*- coding: utf-8 -*-
#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urllib
import sqlite3 as sql
import requests
import json
import calendar
import time
import threading

username = 'europayment'
password = 'europayment.me.in'
place = 'TEST'
con = sql.connect('local.db')

def sendpay():
    threading.Timer(5.0, sendpay).start()
    con = sql.connect('local.db')
    with con:
        cur = con.cursor()
        cur.execute("SELECT * FROM `payments` where `paid` = 0")
        rows = cur.fetchall()
        for row in rows:
            values = {
                'payment_id': calendar.timegm(time.gmtime()),
                'number': row[1],
                'provider': row[2],
                'amount': row[3],
                'place': place
            }
            data = urllib.urlencode(values)
            try:
                response = requests.post('http://www.rusgruppa.me/api/charge', data=values, auth=(username, password))
                if response.ok:
                    cur.execute(f"UPDATE payments SET paid=1 WHERE id={row[0]}")
            except:
                pass
        con.commit()
        cur.close()

class GetHandler(BaseHTTPRequestHandler):
    with con:
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS `payments` (`id` INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
                    "`number` INTEGER, `provider` STRING, `amount` INTEGER, `paid` INTEGER DEFAULT 0)")
        con.commit()
    sendpay()

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
        parsed_path = urllib.urlparse(self.path)
        queryes = urllib.parse_qs(parsed_path.query, keep_blank_values=True)

        if parsed_path.path == '/getuserinfo':
            try:
                print('/getuserinfo num=' + queryes['num'][0])
                response = requests.get('http://www.rusgruppa.me/testPhone.php?phone=' + queryes['num'][0])
                the_page = response.text
            except:
                pass
        
        elif parsed_path.path == '/charge':
            print(f"/charge:VALUES ('{queryes['number'][0]}', '{queryes['provider'][0]}', '{queryes['amount'][0]}')")
            with open('payments', 'a') as file:
                file.write(f"'{queryes['number'][0]}', '{queryes['provider'][0]}', '{queryes['amount'][0]}')" + "\n")
            with con:
                cur = con.cursor()
                cur.execute(f"INSERT INTO `payments` (`number`, `provider`, `amount`) VALUES ('{queryes['number'][0]}', '{queryes['provider'][0]}', '{queryes['amount'][0]}');")
                con.commit()
                cur.close()
            the_page = "OK"

        elif parsed_path.path == '/ping':
            try:
                print
                response = requests.get('https://api.l2rus.net/ping', params={'id': place})
                response = requests.get('http://www.rusgruppa.me/smsApiX.php?go=Sms&in=terminal&master=' + place)
                the_page = response.text
            except:
                pass
        elif parsed_path.path == '/getdata':
            text = ""
            try:
                print
                with con:
                    cur = con.cursor()
                    cur.execute("SELECT * FROM `payments`")
                    rows = cur.fetchall()
                    the_page = str(rows)
                    con.commit()
                    cur.close()
            except:
                pass

        self.send_response(200)
        self.send_header("Cache-Control", "no-cache")
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        print('Response len = %d' % len(the_page))
        self.wfile.write(the_page.encode("utf-8"))
        return

if __name__ == '__main__':
    from http.server import HTTPServer
    server = HTTPServer(('localhost', 8082), GetHandler)
    print('Starting server, use <Ctrl-C> to stop')
    server.serve_forever()
    
    

#!/usr/bin/env python

# -*- coding: utf-8 -*-

import socket, sys
from urlparse import urlparse
from hexdump import hexdump

class HttpParser(object):

    STATE_NONE    = 0   # not recved any line of kv
    STATE_PARSING = 1   # have HTTP/1.X
    STATE_END     = 2   # ended by empty line.
    STATE_ERROR   = 3   # find invalid line or not any headers.

    def __init__(self, max_parse_length=1024*20):
        super(HttpParser, self).__init__()
        self.max_parse_length = max_parse_length
        self.headers = {}
        self.data = ''
        self.data_length = 0
        self.last_line_start = 0
        self.state = HttpParser.STATE_NONE

    '''
    return True if done parsing http header (error or success)
    '''
    def appendData(self, data):
        if self.data_length > self.max_parse_length:
            print 'max_parse_length exceeded.'
            self.state = STATE_ERROR
            return True
        length = len(data)
        self.data += data
        self.data_length += length
        if self.data_length < 10:  # len 'HTTP/1.'
            return False

        while True:
            start_pos = self.last_line_start
            if start_pos < 0:
                start_pos = 0
            line_pos = self.data[start_pos:].find('\r\n')  # FIXME
            if line_pos > -1:
                if line_pos == 0:
                    if self.headers:
                        self.body_pos = self.last_line_start + line_pos + 2
                        self.state = HttpParser.STATE_END
                    else:
                        self.state = HttpParser.STATE_ERROR
                    return True
                # print 'line_pos:', line_pos
                current_line = self.data[self.last_line_start:start_pos+line_pos]
                # print 'current_line:\"%s\"' % (current_line)
                if self.state == HttpParser.STATE_NONE:
                    if current_line.find('HTTP/1.') != 0:
                        print 'not start with HTTP/1.X'
                        self.state = HttpParser.STATE_ERROR
                        return True
                    self.state = HttpParser.STATE_PARSING
                else:
                    items = [k.strip() for k in current_line.split(':',1)]
                    if len(items) != 2 or not len(items[0]) or not len(items[1]):
                        print 'find invalid line, item count %d' % (len(items)), items
                        self.state = HttpParser.STATE_ERROR
                        return True
                    if items[0] in self.headers:
                        print 'WARNING: header %s will be overwritten by new value' % (items[0])
                    self.headers[items[0]] = items[1]
                self.last_line_start += line_pos + 2
            else:
                break
        return False


    def isValidHTTP(self):
        return self.state == HttpParser.STATE_END

    def getHeaders(self):
        return self.headers

    def getBodyPos(self):
        return self.body_pos

    def getBodyContent(self):
        return self.data[self.body_pos:]


def request(method, url, headers={}, ret_limit=0):
    MAX_RECV_LENGTH = 1024*1024*1024

    ret_content = ''

    if method not in ('GET', 'POST'):
        return 'Method not supported'

    u = urlparse(url)

    if u.scheme != 'http':
        return 'scheme not supported'

    host = u.netloc
    port = 80
    host_parts = u.netloc.split(':')
    if len(host_parts) == 2:
        host = host_parts[0]
        port = int(host_parts[1])
    elif len(host_parts) > 2:
        return None
    print 'host %s, port %s' % (host, port)


    if 'GET' == method:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            return 'Error'
        try:
            sock.connect((host, port))
        except socket.error, msg:
            sys.stderr.write("[ERROR] %s\n" % msg[1])
            return 'Error'

        if u.query:
            fullpath = u.path + '?' + u.query
        else:
            fullpath = u.path

        ret_content += '\nRequest Headers:\n' + str(headers)
        
        request_content = ''
        request_content += "GET %s HTTP/1.1\r\nHost: %s\r\n" % (fullpath, host)
        for key in headers:
            request_content += "%s: %s\r\n" % (key, headers[key])
        request_content += "\r\n"

        print '>>> request_content:'
        hexdump(request_content)

        sock.send(request_content)

        parser = HttpParser()
        
        bytes_remaining = ret_limit and ret_limit or MAX_RECV_LENGTH

        fb = open('data.bin', 'wb')
        
        read_body_len = 0
        body_pos = 0
        headers = {}
        while True:
            data = sock.recv(bytes_remaining)
            # print 'recved data:'
            # hexdump(data)

            if body_pos:
                fb.write(data)
                print '>>> body:'
                hexdump(data)
                read_body_len += len(data)
                ret_content += '\nBody:\n' + hexdump(data, result='return')
                if headers.has_key('Content-Length') and read_body_len >= int(headers['Content-Length']):
                    break
            else:
                ret = parser.appendData(data)
                if ret and parser.isValidHTTP():
                    body_pos = parser.getBodyPos()
                    print 'headers:'
                    headers = parser.getHeaders()
                    print headers
                    ret_content += '\nHeaders:\n' + str(headers)
                    body = parser.getBodyContent()
                    read_body_len += len(body)
                    print '>>> first part of body(body_pos=%d):' % (body_pos)
                    hexdump(body)
                    fb.write(body)
                    ret_content += '\nBody:\n' + hexdump(body, result='return')
                    if headers.has_key('Content-Length') and read_body_len >= int(headers['Content-Length']):
                        break

            length = len(data)

            if not length:
                break

            bytes_remaining -= length

        sock.close()
        fb.close()

    return ret_content


def main():
    headers = {'Connection':'close',#'keep-alive', 
        'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.115 Safari/537.36', 
        'X-Requested-With':'ShockwaveFlash/16.0.0.305',
        'Accept':'*/*',
        'DNT': '1',
        'Referer': 'http://bobfilm.net/fantastika/3996-interstellar-2014.html',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,fr;q=0.4,zh-TW;q=0.2'}
    # url = 'http://bf.vbfcdn.net/videos/Interstellar_2014_bdrip[BOBFILM.NET].flv'  # length 824068418

    # 824068418-435611981=388456437 actual Content-Length 388456450
    # url = 'http://bf.vbfcdn.net/videos/Interstellar_2014_bdrip[BOBFILM.NET].flv?start=435611981'   

    # 824068418-824068318=100 actual Content-Length 113
    #url = 'http://bf.vbfcdn.net/videos/Interstellar_2014_bdrip[BOBFILM.NET].flv?start=824068318' 

    # 824068418-824068218=200 actual Content-Length 213
    # url = 'http://bf.vbfcdn.net/videos/Interstellar_2014_bdrip[BOBFILM.NET].flv?start=824068218'   

    url = 'http://bf.vbfcdn.net/videos/Interstellar_2014_bdrip[BOBFILM.NET].flv?start=824068118'   
    print request('GET', url, headers=headers, ret_limit=40000)

if __name__ == '__main__':
    main()

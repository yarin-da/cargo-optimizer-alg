from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
import json
import binPacking

class RequestHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):           
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type") 
        self.end_headers()
    
    def do_POST(self):
        try:
            # read data
            content_len = int(self.headers.get('Content-Length'))
            data = self.rfile.read(content_len)
            parsed_data = json.loads(data)
            # find solution and parse to bytes
            solution = binPacking.run(parsed_data)
            solution_str = json.dumps(solution)
            solution_bytes = solution_str.encode('utf-8')
            
            # 200 OK
            self.send_response(code=200)
            # set headers
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', len(solution_bytes))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            # write solution json to body
            self.wfile.write(solution_bytes)
        except Exception as e:
            print(e)
            # 500 Internal Server Error
            self.send_error(code=500)


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    logging.basicConfig(level=logging.INFO)
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logging.info('Starting httpd...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')

if __name__ == '__main__':
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
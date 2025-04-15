from App import main
import os

def app(environ, start_response):
    if environ['REQUEST_METHOD'] == 'GET':
        main()
    start_response('200 OK', [('Content-Type', 'text/html')])
    return [b"Streamlit app should be running"]
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import traceback
import json

import queue
import bpy

bpy.app.driver_namespace["run_in_main_thread_q"] = queue.Queue()

def execute_queued_functions():
    while not bpy.app.driver_namespace["run_in_main_thread_q"].empty():
        exec_str = bpy.app.driver_namespace["run_in_main_thread_q"].get()
        function_name = ""
        args_str = ""
        if '?' in exec_str:
            str_parts = exec_str.split('?')
            function_name = str_parts[0]
            args_str = str_parts[1]

        if function_name in bpy.app.driver_namespace.keys():
            print(threading.current_thread().name, "Try bpy.app.driver_namespace["+function_name+"]("+ args_str +")")
            try:
                bpy.app.driver_namespace[function_name](args_str)
            except Exception:
                traceback.print_exc()
        else:
            print(threading.current_thread().name, "Try exec", exec_str)
            try:
                exec(exec_str)
            except Exception:
                traceback.print_exc()
    return 1.0

bpy.app.timers.register(execute_queued_functions)

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        str_parts = self.path.split('/')
        obj_name = str_parts[1]
        str_to_eval = "bpy.data.objects['"+ obj_name +"']"
        for ref in str_parts[2:]:
            str_to_eval+="."+ref
        print(threading.current_thread().name, "Try sync eval", str_to_eval)
        try:
            response_eval = eval(str_to_eval)
            self.wfile.write("{}".format(response_eval).encode('utf-8'))
        except Exception as ex:
            traceback.print_exc()
            self.wfile.write("{}".format(ex).encode('utf-8'))



    def do_POST(self):
        path = self.path.replace("/","")
        body_str = self.rfile.read(int(self.headers['Content-Length'])).decode('utf-8')
        self._set_response()

        if path == 'sync' :
            print(threading.current_thread().name, "Executing sync function", body_str)
            try:
                response_eval = eval(body_str)
                self.wfile.write("{}".format(response_eval).encode('utf-8'))
            except Exception as ex:
                traceback.print_exc()
                self.wfile.write("{}".format(ex).encode('utf-8'))

        elif path == 'exec' :
            print(threading.current_thread().name, "Executing sync exec", body_str)
            try:
                exec(body_str)
                self.wfile.write("{}".format("Success").encode('utf-8'))
            except Exception as ex:
                traceback.print_exc()
                self.wfile.write("{}".format(ex).encode('utf-8'))

        elif path == 'async' :
            print(threading.current_thread().name, "Adding action to be executed in the main thead", body_str )
            bpy.app.driver_namespace["run_in_main_thread_q"].put(body_str)
            self.wfile.write("Enqueued: {}\n".format(body_str).encode('utf-8'))

        else:
            if path in bpy.app.driver_namespace.keys():
                response = "Enqueuing bpy.app.driver_namespace["+ path +"]("+ body_str +")"
                print(threading.current_thread().name, response)
                enqueue_str = path +"?"+ body_str
                bpy.app.driver_namespace["run_in_main_thread_q"].put(enqueue_str)
                self.wfile.write("Enqueued: {}\n".format(response).encode('utf-8'))
            else:
                self.wfile.write("Function key {} not registered in bpy.app.driver_namespace".format(path).encode('utf-8'))


    def log_message(self, format, *args):
        return

def start_server():
    httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
    httpd.serve_forever()

http_server_daemon = threading.Thread(target=start_server)
http_server_daemon.setDaemon(True)
http_server_daemon.start()
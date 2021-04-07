#!/usr/bin/env python3
"""
https://gist.github.com/mdonkers/63e115cc0c79b4f6b8b3a6b797e485c7

Very simple HTTP server in python for logging requests
Usage::
    ./server.py [<port>]
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import logging
from pathlib import Path
import pandas as pd
import re
import time
import hashlib
import shutil


class S(BaseHTTPRequestHandler):
    def _set_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        logging.info("GET request,\nPath: %s\nHeaders:\n%s\n",
                str(self.path),
                str(self.headers))
        self._set_response()
        self.wfile.write(f"GET request for {self.path.encode('utf-8')}")

    def do_POST(self):
        # Gets the size of data
        content_length = int(self.headers['Content-Length'])

        # <--- Gets the data itself
        post_data = self.rfile.read(content_length)

        if 'redcap' in post_data.decode('utf-8'):
            save_post_from_redcap(post_data.decode('utf-8'),
                                  self.db_location)
            self.n_post += 1

        logging.info("POST request,\nPath: %s\nHeaders:\n%s\n\nBody:\n%s\n",
                str(self.path), str(self.headers), post_data.decode('utf-8'))

        self._set_response()
        self.wfile.write(f"POST request for {self.path.encode('utf-8')}")

        if self.n_post == self.back_up_after_n_post:
            back_up_db(self.db_location)
            self.n_post = 0


def run(db_location: str = 'db.csv',
        server_class=HTTPServer,
        handler_class=S, port=8080):

    logging.basicConfig(
            level=logging.INFO,
            filename=Path(db_location).parent / 'data_trigger_capture.log')

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)

    # register db_location
    httpd.db_location = db_location
    httpd.n_post = 0
    httpd.back_up_after_n_post = 50

    logging.info('Listening to REDCap POST...\n')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    logging.info('Stopping httpd...\n')


def save_post_from_redcap(body: str, db_location: str):
    '''Listen to redcap and make a record of every modification

    Requirements:
      - "Data Entry Trigger" from REDCap configuration

    '''
    if Path(db_location).is_file():
        db_df = pd.read_csv(db_location, index_col=0)

    else:
        db_df = pd.DataFrame(
            columns=['timestamp', 'project_url', 'project_id',
                     'redcap_username', 'record', 'instrument'])

    redcap_url = get_info_from_post_body('redcap_url', body)
    project_url = get_info_from_post_body('project_url', body)
    project_id = get_info_from_post_body('project_id', body)
    redcap_username = get_info_from_post_body('username', body)
    record = get_info_from_post_body('record', body)
    instrument = get_info_from_post_body('instrument', body)

    df_tmp = pd.DataFrame({
        'timestamp': [time.time()],
        'redcap_url': redcap_url,
        'project_url': project_url,
        'project_id': project_id,
        'redcap_username': redcap_username,
        'record': record,
        'instrument': instrument})

    db_df = db_df.append(df_tmp)
    db_df.to_csv(db_location)


def get_info_from_post_body(var_name, body):
    pattern_catcher = '([A-Za-z%0-9\.]+)'
    return re.search(f'{var_name}={pattern_catcher}', body).group(1)


def get_sha(file_loc: str) -> str:
    '''return sha1 hexdigest of a file'''
    BUF_SIZE = 65536
    sha1 = hashlib.sha1()

    with open(file_loc, 'rb') as f:
        data = f.read(BUF_SIZE)
        sha1.update(data)

    return sha1.hexdigest()


def back_up_db(db_location) -> None:
    ''''Back up the db file'''

    db_dir = Path(db_location).parent
    db_backup_file = db_dir / f".{Path(db_location).name}"

    if db_backup_file.is_file():
        with open(db_location, 'rb') as f:
            db_file_sha1 = get_sha(db_location)

        with open(db_backup_file, 'rb') as f:
            back_up_file_sha1 = get_sha(db_backup_file)

        if db_file_sha1 == back_up_file_sha1:
            print('No back up')
            pass
        else:
            print('backing up')
            shutil.copy(db_location, db_backup_file)
    else:
        shutil.copy(db_location, db_backup_file)

    return True

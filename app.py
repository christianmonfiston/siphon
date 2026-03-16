import os
import queue
import threading
import yt_dlp
from flask import Flask, render_template, request, Response, stream_with_context

app = Flask(__name__)
log_queue = queue.Queue()


class QueueLogger:
    def debug(self, msg):
        if not msg.startswith('[debug]'):
            log_queue.put(msg)

    def info(self, msg):
        log_queue.put(msg)

    def warning(self, msg):
        log_queue.put(f'WARNING: {msg}')

    def error(self, msg):
        log_queue.put(f'ERROR: {msg}')


def run_download(url, start_date, end_date):
    username = url.rstrip('/').split('/')[-1].lstrip('@')
    output_dir = os.path.expanduser(f"~/Downloads/tiktok/{username}")
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'outtmpl': f'{output_dir}/%(upload_date)s_%(id)s_%(title).50s.%(ext)s',
        'download_archive': f'{output_dir}/downloaded.txt',
        'ignoreerrors': True,
        'logger': QueueLogger(),
    }

    if start_date or end_date:
        ydl_opts['daterange'] = yt_dlp.DateRange(start_date or None, end_date or None)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        log_queue.put(f'ERROR: {e}')
    finally:
        log_queue.put('__DONE__')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url', '').strip()
    start_date = request.form.get('start_date', '').strip().replace('-', '')
    end_date = request.form.get('end_date', '').strip().replace('-', '')

    if not url:
        return 'Missing URL', 400

    # Clear any old messages in the queue
    while not log_queue.empty():
        log_queue.get_nowait()

    thread = threading.Thread(target=run_download, args=(url, start_date, end_date), daemon=True)
    thread.start()

    def stream():
        while True:
            msg = log_queue.get()
            if msg == '__DONE__':
                yield 'data: __DONE__\n\n'
                break
            yield f'data: {msg}\n\n'

    return Response(stream_with_context(stream()), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, port=5000)

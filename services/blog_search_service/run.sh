pip install -r requirements.txt
python generate_search_index.py -s /var/www/html/blog
gunicorn -b 0.0.0.0:5000 search_server:app --reload
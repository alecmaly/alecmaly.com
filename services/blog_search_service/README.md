
# Install

Python:latest docker image

## Tasks

Generate search index
```bash
python generate_search_index.py -s /var/www/html/blog
```

Run server
```bash
gunicorn -b 0.0.0.0:5000 main:app --reload
```

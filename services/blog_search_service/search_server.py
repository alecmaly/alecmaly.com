#!/usr/bin/env python

import json
import falcon
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from whoosh import sorting

class SearchResource(object):

    def __init__(self):
        self._ix = open_dir('_search_index')

    def _do_search(self, query_str, page):
        ret = {}

        with self._ix.searcher() as searcher:
            qp = QueryParser('content', self._ix.schema)

            if query_str != '' and query_str != None:
                q = qp.parse(query_str)
                results = searcher.search_page(q, page, 15)
            else:
                q = qp.parse("Tags") # return all pages (they all have a Tags section)
                date_facet = sorting.FieldFacet("date_sortable", reverse=True)
                results = searcher.search_page(q, page, 15, sortedby=date_facet)
            # results = searcher.search_page(q, page, 15)
            

            ret['page'] = results.pagenum
            ret['pages'] = results.pagecount
            ret['hits'] = []

            for h in results:
                # print(h)
                match = {
                    'uri': h['uri'],
                    'title': h['title'],
                    'description': h['description'],
                    'tags': h['tags'],
                    'post_date': h['post_date'],
                    # 'excerpt': h['excerpt']
                }
                ret['hits'].append(match)

        return ret


    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        res = self._do_search(req.get_param('q', default=''), int(req.get_param('p', default=1)))
        resp.body = json.dumps(res)

app = falcon.App()
searcher = SearchResource()
app.add_route('/', searcher)
app.add_route('/api/search', searcher)
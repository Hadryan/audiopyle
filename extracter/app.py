import cherrypy

from extracter.exctracter_api import Root

HTTP_CHERRYPY_CONFIG_FILE = "http_server.conf"

if __name__ == '__main__':
    cherrypy.config.update(HTTP_CHERRYPY_CONFIG_FILE)
    cherrypy.quickstart(Root(), '/')
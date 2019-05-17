from flask import Blueprint
from flask import render_template

errors = Blueprint('errors', __name__)


@errors.app_errorhandler(404)
def error_404(error):
    # second return value is the http status server response, default 200
    return render_template('errors/404.html', error=error), 404


@errors.app_errorhandler(403)
def error_403(error):
    return render_template('errors/403.html', error=error), 403


@errors.app_errorhandler(500)
def error_500(error):
    return render_template('errors/500.html', error=error), 500


# ['__call__', '__cause__', '__class__', '__context__', '__delattr__',
# '__dict__',
#  '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__',
#  '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__',
#  '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
#  '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__',
#  '__suppress_context__', '__traceback__', '__weakref__', 'args', 'code',
#  'description', 'get_body', 'get_description', 'get_headers', 'get_response',
#  'name', 'response', 'with_traceback', 'wrap']

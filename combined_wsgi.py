from werkzeug.middleware.dispatcher import DispatcherMiddleware

from admin_app import app as admin_app
from student_app import app as student_app

# Student experience lives at the root URL.
# Admin dashboard is mounted under /staff so one Render service can host both apps.
app = DispatcherMiddleware(student_app, {
    "/staff": admin_app,
})

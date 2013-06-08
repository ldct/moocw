import urllib, datetime

import webapp2
from google.appengine.ext import ndb
from google.appengine.api import mail

from webapp2_extras.appengine.users import login_required, admin_required

class Reminder(ndb.Model):
    email = ndb.StringProperty()
    courseID = ndb.StringProperty()
    first_date = ndb.DateProperty()

class Request(ndb.Model):
    email = ndb.StringProperty()
    first_date = ndb.DateProperty()
    email_no = ndb.IntegerProperty()
    end_email_no = ndb.IntegerProperty()
    delta_days = ndb.IntegerProperty()
    mailchain = ndb.StringProperty()
    done = False

def check(request):
    if request.done:
        return

    due = request.first_date + (datetime.timedelta(days=request.delta_days) * request.email_no)
    if due <= datetime.datetime.now().date():
        message = mail.EmailMessage()
        message.sender = "reminder@ocw-reminder.appspotmail.com"
        message.subject = "OCW Reminder: Week %s" % str(int(request.email_no) + 1)
        message.to = request.email
        message.cc = "xuanji@gmail.com"
        with open("messages/%s/%s.html" % (request.mailchain, request.email_no)) as f:
            message.html = '\n'.join(f.readlines())
        message.send()

        request.email_no += 1
        if request.email_no == request.end_email_no:
            request.done = True

        request.put()

        return True
    else:
        return False

class CheckAllRequestsPage(webapp2.RequestHandler):
    def get(self):
        for request in Request.query().fetch(100):
            self.response.write(request)
            self.response.write(check(request))

class CreateDummyPage(webapp2.RequestHandler):
    @admin_required
    def get(self):
        nr = Request(email="xuanji@gmail.com", first_date=datetime.datetime.now(), 
                     email_no=0, end_email_no=5, delta_days=1, mailchain="6.00SC")
        nr.put()
        self.response.write(Reminder.query().fetch(10))

class RequestPostedPage(webapp2.RequestHandler):
    def post(self):
        email = self.request.get('email')
        courseID = self.request.get('courseid')
        date = self.request.get('date')
        first_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()

        new_reminder = Reminder()
        new_reminder.email = email
        new_reminder.courseID = courseID
        new_reminder.first_date = first_date

        new_reminder.put()

        message = mail.EmailMessage()
        message.sender = "reminder@ocw-reminder.appspotmail.com"
        message.subject = "ocw-reminder: new sign-up"
        message.to = "xuanji@gmail.com"
        message.html = "<b>email:</b>%s courseID: %s first date: %s" % (email, courseID, first_date)
        message.send()

        self.redirect('/new_request_done')

application = webapp2.WSGIApplication([
    ('/new_request_post', RequestPostedPage),
    ('/create_dummy', CreateDummyPage),
], debug=True)

check_requests_applications = webapp2.WSGIApplication([
    ('/check_all_requests', CheckAllRequestsPage),
], debug=True)
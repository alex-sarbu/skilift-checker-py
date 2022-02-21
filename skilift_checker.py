from lxml import html
import requests
import sys
import os
import re
import sched
import time
import numpy as np
import json
from pprint import pprint
from datetime import date
from datetime import datetime
from datetime import timedelta
import dateutil.parser
#reload(sys)
#sys.setdefaultencoding('utf-8')


##################################
## export PYTHONIOENCODING=utf8 ##
##################################

from smtplib import SMTP_SSL as SMTP       # this invokes the secure SMTP protocol (port 465, uses SSL)
# from smtplib import SMTP                  # use this for standard SMTP protocol   (port 25, no encryption)

from email.mime.text import MIMEText

url = 'https://zillertal.intermaps.com/hochzillertal_spieljoch/data?lang=de'
snapshot_file = 'skilift_snapshot.json'
config_file = 'config.json'

try:
  conf = json.load(open(config_file))
  SMTPserver = conf.get('server')
  USERNAME = conf.get('user')
  PASSWORD = conf.get('password')
  
  sender = conf.get('sender')
  destination = conf.get('destination')
  
except Exception as e:
  print(e)
  #mailout('Could not retrieve stock item')
  print('could not load configuration, please check config.json')
  quit()

def mailout(content):

  # typical values for text_subtype are plain, html, xml
  text_subtype = 'plain'

  content_old="""\
  Test message
  """
  subject="Skilift Update"

  try:
      msg = MIMEText(content, text_subtype)
      msg['Subject']=       subject
      msg['From']   = sender

      conn = SMTP(SMTPserver)
      conn.set_debuglevel(False)
      conn.login(USERNAME, PASSWORD)
      try:
        print 'would send mail here'
        conn.sendmail(sender, destination, msg.as_string())
      finally:
        conn.quit()

  except:
      sys.exit( "mail failed; unknown error" ) # give a error message


def url_monitor():
  upd_msg = ""
  today = datetime.now()
  print '--------------------------------------------------------------------'
  print 'running check at '+today.isoformat()
  try:
      prev_snapshot_data = json.load(open(snapshot_file), encoding='utf-8')
      prev_snapshot_datetime = dateutil.parser.isoparse(prev_snapshot_data.get('date'))
      prev_snapshot = prev_snapshot_data.get('snapshot')
      count = prev_snapshot_data.get('count')
      print 'loaded snapshot from '+prev_snapshot_datetime.isoformat()
      #print dateutil.parser.isoparse(prev_snapshot_data.get('date'))
      
      if prev_snapshot_datetime.date() == today.date():
        raise UserWarning('already have a snapshot for '+prev_snapshot_datetime.date().isoformat()+', skipping..')
      
      print ("checking lifts at URL "+url+"...")
      print ("connecting")
      page = requests.get(url, timeout=10)
      print ("connection established")
      print 'page.encoding=', page.encoding
      data = json.loads(page.content)
    
      #print 'data: ', data
      liftsnapshot = {}

      for lift in data['lifts']:
        length = 0
        id = lift.get('id')
        status = lift.get('status')
        status_val = float(1) if status == 'open' else float(0)
        if lift.get('popup'):
          title = lift.get('popup').get('title')
          subtitle = lift.get('popup').get('subtitle')
          if lift.get('popup').get('additional-info'):
            if lift.get('popup').get('additional-info').get('length'):
              length = lift.get('popup').get('additional-info').get('length')
              if length > 500:
                prev_lift_snapshot = prev_snapshot.get(id)
                prev_availability = prev_lift_snapshot.get('availability') if prev_lift_snapshot else float(1)
                availability = (float(count) * prev_availability + status_val) / float(count+1) if count > 0 else status_val
                liftsnapshot[id] = {'title': title, 'status':status, 'availability': availability}
                upd_msg+="{:10.2f}".format(availability*100) + "% - "+title+"  "+status+" length: "+ str(length)+"\n"
      snapshot_data={'date': today.isoformat(),'count': count+1,'snapshot': liftsnapshot}

      with open(snapshot_file, 'w') as outfile:
          json.dump(snapshot_data, outfile, encoding='utf-8', indent=2)

      #if 'stock available' in stock_info[0]:
      #  upd_msg += "Item in stock: "+item_name+"\n"
      #  upd_msg += "URL: "+url_map[item_name]+"\n"
      #  del url_map[item_name]
      #else:
      #  print(url_map[item_name]+ ' is not available')
  except UserWarning as w:
    print(w)
  except Exception as e:
    print(e)
    #mailout('Could not retrieve stock item')
    print('Error processing request')
    upd_msg += e
    #pprint(data)
  if len(upd_msg) > 0:
    print("(not) sending mail:\n"+upd_msg)
    #print liftsnapshot
    #mailout(upd_msg.encode(sys.stdout.encoding, errors='replace'))

  
sch = sched.scheduler(time.time, time.sleep)

def do_something(sc): 
    # do your stuff
    url_monitor()
    #check every 8 hrs (60 x 60 x 8 = 28800)
    now = datetime.now()
    nextday = now if now.hour < 11 else now +timedelta(days=1)
    nexttime = datetime(nextday.year, nextday.month, nextday.day, 11, 5, 0, 0)
    print "will run again at ", nexttime.isoformat()
    delay = (nexttime - now).total_seconds()
    print "delay=", int(delay)
    sch.enter(delay, 1, do_something, (sch,))
    #sch.enter(10, 1, do_something, (sch,))
# init
print ('jallo')
sch.enter(1, 1, do_something, (sch,))
sch.run()









# -*- coding: utf-8 -*-
import os
import mimetypes
from smtplib import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
from os.path import basename
from datetime import datetime, time
import icalendar
import uuid
import pytz
import unidecode


class Correo():
    correo = None
    clave = None
    smtp = None
    smtp_puerto = None
    mail_server = None
    imap = None
    imap_puerto = None
    imap_user = None

    def __init__(self, correo, clave, smtp, smtp_puerto, imap=None, imap_puerto=None, imap_user=None, use_ssl=False):
        self.correo = correo
        self.clave = clave
        self.smtp = smtp
        self.smtp_puerto = int(smtp_puerto)
        self.imap = imap
        self.imap_puerto = int(imap_puerto) if imap_puerto else imap_puerto
        self.imap_user = imap_user
        if self.smtp_puerto==465:
            use_ssl=True
        if not imap_user:
            self.imap_user = correo
        self.conectar(use_ssl)

    def conectar(self, use_ssl=False):
        conectado = False
        if use_ssl:
            import time as time_core
            reintento = 0
            while reintento<5:
                try:
                    self.mail_server = SMTP_SSL(self.smtp+':'+str(self.smtp_puerto))
                    self.mail_server.login(self.correo, self.clave)
                    conectado = True
                    reintento = 5
                    #print('login con ssl')
                except:
                    reintento += 1
                    time_core.sleep(5)
        if not conectado:
            try:
                #print('antes SMTP')
                self.mail_server = SMTP(self.smtp, self.smtp_puerto)
                #print('antes ehlo')
                self.mail_server.ehlo()
                #print('antes starttls')
                self.mail_server.starttls()
                #print('antes login')
                self.mail_server.login(self.correo, self.clave)
                conectado = True
                #print('login sin ssl with starttls')
            except:
                try:
                    self.mail_server = SMTP(self.smtp, self.smtp_puerto)
                    self.mail_server.ehlo()
                    self.mail_server.login(self.correo, self.clave)
                    conectado = True
                    #print('login sin ssl without starttls')
                except:
                    self.mail_server = SMTP(self.smtp, self.smtp_puerto)
                    self.mail_server.starttls()
                    self.mail_server.login(self.correo, self.clave)
                    conectado = True
                    #print('login horrible')
        print('Conectado:',conectado)

    def enviar(self, to, subject, message, name_from, html=False, documents=None, cc=[], bcc=[], firma_img=None):
        if html:
            mensaje = MIMEMultipart('related')
            mensaje_alt = MIMEText(message, 'html')
            mensaje.attach(mensaje_alt)
        else:
            mensaje = MIMEText(message)

        if documents:
            for documento in documents:
                with open(documento['path'], "rb") as fil:
                    mensaje.attach(
                        MIMEApplication(
                            fil.read(),
                            Content_Disposition='attachment; filename="%s"' % basename(
                                documento['name']),
                            Name=basename(documento['name'])
                        )
                    )

        if firma_img:
            for img in firma_img:
                content_type, encoding = mimetypes.guess_type(img)
                if content_type is None or encoding is not None:
                    content_type = 'application/octet-stream'
                main_type, sub_type = content_type.split('/', 1)
                if main_type == 'image':
                    fp = open(img, 'rb')
                    msg = MIMEImage(fp.read(), _subtype=sub_type)
                    fp.close()
                else:
                    fp = open(img, 'rb')
                    msg = MIMEBase(main_type, sub_type)
                    msg.set_payload(fp.read())
                    fp.close()
                filename = os.path.basename(img)
                msg.add_header('Content-Disposition','attachment', filename=filename)
                mensaje.attach(msg)
        
        name_from = unidecode.unidecode(name_from)    

        mensaje['From'] = name_from + ' <' + self.correo + '>'
        mensaje['To'] = ', '.join(to)
        mensaje['Cc'] = ", ".join(cc)
        mensaje['Subject'] = subject

        self.mail_server.sendmail(self.correo,to + cc + bcc,mensaje.as_string())
        return True

    def enviarEvento(self, to, subject, message, day, name_from='Sistema de Vigilancia', startHour=0, startMinute=0, startSecond=0, reminderHours=0):
        tz = pytz.timezone("America/Santiago")
        start = tz.localize(datetime.combine(
            day, time(startHour, startMinute, startSecond)))
        cal = icalendar.Calendar()
        cal.add('prodid', '-//My calendar application//example.com//')
        cal.add('version', '2.0')
        cal.add('method', "REQUEST")
        event = icalendar.Event()
        for destinatario in to:
            event.add('attendee', destinatario)
        event.add('organizer', self.correo)
        event.add('status', "confirmed")
        event.add('category', "Event")
        event.add('summary', subject)
        event.add('description', message)
        event.add('location', "")  # Ubicacion
        event.add('dtstart', start)
        event.add('dtend', tz.localize(datetime.combine(
            day, time(startHour, startMinute, startSecond))))
        event.add('dtstamp', tz.localize(datetime.combine(day, time(6, 0, 0))))
        event['uid'] = str(uuid.uuid4())
        event.add('priority', 5)
        event.add('sequence', 1)
        event.add('created', tz.localize(datetime.now()))

        alarm = icalendar.Alarm()
        alarm.add("action", "DISPLAY")
        alarm.add('description', "Reminder")
        alarm.add("TRIGGER;RELATED=START", "-PT{0}H".format(reminderHours))
        event.add_component(alarm)
        cal.add_component(event)

        msg = MIMEMultipart("alternative")

        msg["Subject"] = subject
        msg["From"] = name_from + ' <' + self.correo + '>'
        msg["To"] = ', '.join(to)
        msg["Content-class"] = "urn:content-classes:calendarmessage"

        parteHtml = MIMEText(message, 'html')
        msg.attach(parteHtml)

        filename = "invite.ics"
        part = MIMEBase('text', "calendar", method="REQUEST", name=filename)
        part.set_payload(cal.to_ical())
        encoders.encode_base64(part)
        part.add_header('Content-Description', filename)
        part.add_header("Content-class", "urn:content-classes:calendarmessage")
        part.add_header("Filename", filename)
        part.add_header("Path", filename)
        msg.attach(part)

        if self.smtp_puerto == 465:
            s = SMTP_SSL(self.smtp, self.smtp_puerto)
        else:
            s = SMTP(self.smtp, self.smtp_puerto)
        s.ehlo()
        s.login(self.correo, self.clave)
        s.sendmail(msg["From"], to, msg.as_string())
        s.quit()

    def cerrar(self):
        self.mail_server.close()

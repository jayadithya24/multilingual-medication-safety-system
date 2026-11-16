"""Vector redraws of the report's design diagrams, for inclusion in LaTeX."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white
import math

OUT=Path(__file__).resolve().parents[1]/'docs/revised_reports/fig'
INK=HexColor('#172f43'); FILL=HexColor('#eef5f8')

class Diagram:
    def __init__(self,name,height=420):
        self.c=canvas.Canvas(str(OUT/(name+'.pdf')),pagesize=(450,height))
        self.h=height;self.nodes={}
    def text(self,x,y,text,size=9,bold=False,background=False):
        c=self.c;c.setFillColor(INK);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size)
        if background:
            width=max(c.stringWidth(line,'Helvetica',size) for line in text.split('\n'))
            c.setFillColor(white);c.rect(x-width/2-2,self.h-y-2,width+4,size+4,fill=1,stroke=0);c.setFillColor(INK)
        for i,line in enumerate(text.split('\n')):c.drawCentredString(x,self.h-y-i*(size+3),line)
    def box(self,key,x,y,w,h,title,body='',size=9):
        c=self.c;c.setStrokeColor(INK);c.setFillColor(FILL);c.setLineWidth(.85)
        c.roundRect(x,self.h-y-h,w,h,4,stroke=1,fill=1)
        self.text(x+w/2,y+15,title,size,True)
        if body:
            c.line(x,self.h-y-22,x+w,self.h-y-22)
            self.text(x+w/2,y+35,body,size)
        self.nodes[key]=(x,y,w,h)
    def anchor(self,k,side):
        x,y,w,h=self.nodes[k]
        return {'n':(x+w/2,y),'s':(x+w/2,y+h),'e':(x+w,y+h/2),'w':(x,y+h/2)}[side]
    def arrow(self,a,b,label='',s='s',t='n',via=None,dashed=False):
        self.line([self.anchor(a,s),*(via or []),self.anchor(b,t)],label,dashed)
    def line(self,pts,label='',dashed=False):
        c=self.c;c.setStrokeColor(INK);c.setFillColor(INK);c.setLineWidth(.8)
        c.setDash(3,2) if dashed else c.setDash()
        for (x,y),(xx,yy) in zip(pts,pts[1:]):c.line(x,self.h-y,xx,self.h-yy)
        c.setDash()
        (x,y),(xx,yy)=pts[-2:]; ang=math.atan2(yy-y,xx-x)
        p=c.beginPath();p.moveTo(xx,self.h-yy)
        for d in [-.45,.45]:p.lineTo(xx-6*math.cos(ang+d),self.h-(yy-6*math.sin(ang+d)))
        p.close();c.drawPath(p,stroke=0,fill=1)
        if label:
            x,y=pts[len(pts)//2-1];xx,yy=pts[len(pts)//2]
            self.text((x+xx)/2,(y+yy)/2-4,label,8,background=True)
    def save(self):self.c.showPage();self.c.save()

def build():
    d=Diagram('architecture-diagram',435)
    d.box('client',15,8,420,60,'React client applications','Patient: scan, voice, lookup, medicines and reminders\nDoctor: consent-based patient review, graph and safety checks',10)
    d.box('api',15,94,420,54,'FastAPI / REST orchestration','JWT authentication, roles, validation, routing and logging',10)
    d.arrow('client','api','HTTPS / JSON')
    d.box('svc',15,176,420,68,'Processing and application services','OCR and speech | intent and medicine matching\nMultilingual lookup | interaction grading | scheduling | consent',10)
    d.arrow('api','svc','Validated requests')
    d.box('mongo',15,276,200,75,'MongoDB application records','Users, doctor requests, consent\nSchedules, history, device tokens\nReminder delivery records')
    d.box('neo',235,276,200,75,'Neo4j knowledge graph','Drug, Disease, SideEffect\nTREATS, CAUSES\nINTERACTS_WITH with evidence')
    d.arrow('svc','mongo');d.arrow('svc','neo')
    d.box('output',15,378,420,49,'Output and delivery','Localised text and TTS audio | safety alerts | push reminders',10)
    d.text(225,367,'External services: speech, synthesis, Google sign-in and FCM.',9)
    d.save()

    d=Diagram('modular-diagram',345)
    d.box('m1',140,8,170,40,'M1: Input and authentication')
    d.box('m2',25,82,175,40,'M2: OCR / image processing')
    d.box('m3',250,82,175,40,'M3: Voice processing')
    d.arrow('m1','m2');d.arrow('m1','m3')
    d.box('m4',140,155,170,40,'M4: Multilingual processing');d.arrow('m2','m4');d.arrow('m3','m4')
    for key,x,title,body in [('m5',5,'M5: Medicine information','Catalogue-grounded lookup'),('m6',155,'M6: Drug safety','Interaction severity checks'),('m7',305,'M7: Medication monitoring','Prescriptions and reminders')]:
        d.box(key,x,228,140,53,title,body,8.5);d.arrow('m4',key)
    d.box('m8',125,309,200,30,'M8: Knowledge graph and dashboard')
    for k in ['m5','m6','m7']:d.arrow(k,'m8')
    d.save()

    d=Diagram('class-diagram',490)
    d.box('user',150,5,150,76,'User','userId, name, language\nlogin(), logout()')
    d.box('patient',35,110,165,64,'Patient','patientId\nviewMedicine(), confirmTaken()')
    d.box('doctor',250,110,165,64,'Doctor','doctorId, specialisation\nqueryPatient(), queryDrug()')
    d.arrow('patient','user','inherits',s='n',t='s');d.arrow('doctor','user','inherits',s='n',t='s')
    d.box('input',5,212,135,65,'Input Scanner','parsePrescription()\nparseVoiceQuery()')
    d.box('schedule',157,212,135,76,'Schedule','scheduleId, times, status\ncreate(), markTaken()\nmarkMissed()')
    d.box('disease',310,212,135,65,'Disease Context','getDiseaseProtocol()')
    d.arrow('patient','input','uses');d.arrow('patient','schedule','maintains');d.arrow('doctor','disease','uses')
    d.box('identify',5,321,135,56,'Medicine Identifier','identifyDrug()')
    d.box('engine',310,321,135,56,'Interaction Engine','getInteractions()\ncheckContraindications()')
    d.arrow('input','identify','sends input');d.arrow('disease','engine','informs')
    d.box('drug',150,410,150,72,'Drug','drugId, name, descriptions\nsideEffects, warnings\ngetDescription()')
    d.arrow('identify','drug','identifies');d.arrow('schedule','drug','references');d.arrow('engine','drug','checks')
    d.save()

    d=Diagram('state-diagram',340)
    for key,x,y,title in [('scheduled',150,12,'Scheduled'),('due',150,90,'Reminder due'),('notified',150,167,'Notified'),('missed',25,244,'Missed'),('taken',275,244,'Taken'),('completed',150,310,'Completed')]:d.box(key,x,y,125,25,title)
    d.arrow('scheduled','due','scheduled time reached');d.arrow('due','notified','reminder sent')
    d.arrow('notified','missed','no confirmation');d.arrow('notified','taken','dose confirmed')
    d.arrow('missed','completed','history updated');d.arrow('taken','completed','history updated')
    d.line([(275,322),(430,322),(430,24),(275,24)],'next scheduled dose')
    d.box('cancel',5,95,100,25,'Cancelled');d.arrow('scheduled','cancel','cancel',s='w',t='n')
    d.save()

    d=Diagram('use-case-diagram',390)
    d.text(225,15,'Medication safety system: role-based use cases',11,True)
    d.box('p',5,75,95,32,'Patient / carer')
    d.box('doc',5,244,95,32,'Doctor')
    d.box('admin',5,340,95,32,'Administrator')
    for key,y,title in [('scan',43,'Scan medicine / prescription'),('voice',91,'Voice or text medicine search'),('rem',139,'Schedules and taken confirmation'),('info',187,'Localised medicine details / audio'),('consent',235,'Approve or reject access request'),('check',283,'Review medicines / check interactions'),('approve',337,'Approve doctors / manage users')]:d.box(key,160,y,275,31,title, size=9)
    for k in ['scan','voice','rem','info','consent']:d.arrow('p',k,s='e',t='w')
    d.arrow('doc','check',s='e',t='w');d.arrow('doc','consent','requests',s='e',t='w',dashed=True);d.arrow('admin','approve',s='e',t='w')
    d.save()

    d=Diagram('sequence-diagram',465)
    xs=[35,135,240,340,420]
    for x,title in zip(xs,['User','React UI','FastAPI','OCR / speech','Data stores']):
        d.text(x,14,title,9,True);d.c.setStrokeColor(INK);d.c.setDash(2,3);d.c.line(x,430,x,10);d.c.setDash()
    def message(a,b,y,label,dash=False):
        d.line([(xs[a],y),(xs[b],y)],dashed=dash);d.text((xs[a]+xs[b])/2,y-6,label,8)
    d.text(225,49,'1. Prescription / voice processing',10,True)
    for a,b,y,l in [(0,1,73,'Upload image / voice query'),(1,2,100,'Extraction request'),(2,3,127,'Process input'),(3,2,154,'Medicine names and dosage'),(2,4,181,'Store confirmed medicine / schedule'),(2,1,208,'Structured localised response'),(1,0,235,'Display medicine information')]:message(a,b,y,l)
    d.text(225,265,'2. Doctor access, with patient consent',10,True)
    message(0,2,288,'Request access / patient decision');message(2,4,314,'Record request and consent state');message(2,1,340,'Approved: shared data; denied: no access')
    d.text(225,371,'3. Drug interaction checking',10,True)
    message(0,2,397,'Select medicines / check request');message(2,4,424,'Query interaction records');message(2,0,451,'Severity, evidence and safety explanation')
    d.save()

    d=Diagram('activity-diagram',410)
    d.box('auth',130,5,190,38,'Login and verify role')
    for key,x,title in [('patient',5,'Patient dashboard'),('doctor',155,'Doctor dashboard'),('admin',305,'Admin dashboard')]:d.box(key,x,83,140,30,title);d.arrow('auth',key)
    d.box('input',5,143,140,67,'Select patient action','Scan / voice / text lookup\nSchedule and reminders')
    d.box('request',155,143,140,67,'Request patient access','Patient approves or rejects\nRejected: access denied')
    d.box('manage',305,143,140,67,'Administrative action','Approve doctor requests\nManage users / view logs')
    d.arrow('patient','input');d.arrow('doctor','request');d.arrow('admin','manage')
    d.box('lookup',5,247,140,65,'Process and confirm','Identify medicine\nShow localised details\nSave schedule / taken event',8.5)
    d.box('review',155,247,140,65,'Consent granted','Review shared medicines\nCheck interactions\nInspect graph and evidence',8.5)
    d.arrow('input','lookup');d.arrow('request','review','approval required')
    d.box('logout',145,369,160,30,'Close session / logout');d.arrow('lookup','logout');d.arrow('review','logout');d.arrow('manage','logout',via=[(440,335),(225,335)])
    d.save()

    d=Diagram('dfd-level-0',295)
    d.box('patient',5,10,165,58,'Patient / caretaker','Query, prescription, schedule\nTaken event and consent')
    d.box('doctor',280,10,165,58,'Doctor','Patient access request\nMedicine / interaction query')
    d.box('system',120,123,210,65,'0. Medication safety system','Lookup, interaction checking\nReminders and controlled sharing')
    d.arrow('patient','system','patient input');d.arrow('doctor','system','doctor input')
    d.box('out',90,233,270,50,'Information and notifications','Localised text / audio, risk alerts and reminders')
    d.arrow('system','out','results')
    d.save()

    d=Diagram('dfd-level-1',450)
    d.box('patient',135,5,180,30,'Patient / caretaker')
    d.box('ocr',5,91,135,63,'1.0 Input processing','Prescription OCR\nSpeech transcription')
    d.box('schedule',157,91,135,63,'2.0 Scheduling','Schedules, reminders\nTaken confirmation')
    d.box('doctor',315,5,125,30,'Doctor')
    d.box('consent',310,91,135,63,'6.0 Access control','Patient decision\nShared-record access')
    d.arrow('patient','ocr','input');d.arrow('patient','schedule','schedule');d.arrow('doctor','consent','request')
    d.box('identify',5,222,135,57,'3.0 Identification','Catalogue matching')
    d.box('mongo',157,222,135,68,'D1: MongoDB','Users, schedules\nHistory, consent\nReminder records')
    d.box('risk',310,222,135,57,'5.0 Interaction checks','Risk and evidence')
    d.arrow('ocr','identify','recognised text');d.arrow('schedule','mongo','records');d.arrow('consent','mongo','consent state')
    d.box('local',5,365,135,60,'4.0 Localised output','Medicine information\nEnglish / Kannada / Tulu')
    d.box('neo',235,365,205,60,'D2: Neo4j knowledge graph','Drugs, diseases, side effects\nEvidence-backed interactions')
    d.arrow('identify','local','matched name');d.arrow('identify','neo','drug query');d.arrow('risk','neo','pair query');d.arrow('mongo','risk','medicine list',s='e',t='w')
    d.arrow('neo','local','medicine details',s='w',t='e');d.save()

if __name__=='__main__':build()

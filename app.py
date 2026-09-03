import os,sqlite3
from flask import Flask,render_template,request
from services.resume_parser import extract_resume
from services.matcher import match_resume_to_job
from services.ai_analyzer import analyze_job_with_ai
app=Flask(__name__); BASE=os.path.dirname(__file__); UP=os.path.join(BASE,"uploads"); os.makedirs(UP,exist_ok=True); app.config["MAX_CONTENT_LENGTH"]=10*1024*1024
JOBS=[("Python Django Intern","AppNest Demo","Remote","Python,Django,SQL,HTML,CSS,Git"),("Junior Data Scientist","InsightWorks Demo","Mumbai","Python,Pandas,Scikit-learn,SQL,Machine Learning"),("Full Stack Developer Intern","WebForge Demo","Remote","HTML,CSS,JavaScript,Python,Django,MongoDB"),("Cloud Data Engineer Trainee","CloudCore Demo","Hyderabad","SQL,Python,ETL,Cloud,Data Engineering"),("Software Engineer Intern","DevSphere Demo","Gurugram","Java,Python,DSA,Git,SQL"),("AI/ML Intern","NeuralLab Demo","Remote","Python,AI,Machine Learning,NLP,Git"),("Machine Learning Intern","AIWorks Demo","Bengaluru","Python,Machine Learning,Pandas,Scikit-learn,Statistics"),("Data Analyst Intern","DataBridge Demo","Noida","Python,Pandas,SQL,Excel,Data Analysis")]
def db():
 c=sqlite3.connect(os.path.join(BASE,"database.db")); c.row_factory=sqlite3.Row; return c
def init():
 c=db(); c.execute("CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY,title,company,location,description,skills)")
 for t,co,lo,s in JOBS:c.execute("INSERT OR IGNORE INTO jobs(title,company,location,description,skills) VALUES(?,?,?,?,?)",(t,co,lo,"Build and work on modern technology projects.",s))
 c.commit();c.close()
init()
@app.route("/")
def home():return render_template("index.html")
@app.route("/upload",methods=["GET","POST"])
def upload():
 if request.method=="GET":return render_template("upload.html")
 f=request.files.get("resume")
 if not f or not f.filename:return render_template("upload.html",error="Please select a resume.")
 p=os.path.join(UP,os.path.basename(f.filename));f.save(p)
 try:text,info=extract_resume(p)
 except Exception as e:return render_template("upload.html",error="Could not process this resume.")
 if not text:return render_template("upload.html",error=info.get("error","No readable text found."))
 c=db();jobs=c.execute("SELECT * FROM jobs").fetchall();c.close()
 return render_template("jobs.html",jobs=jobs,resume_text=text,resume_skills=info["skills"],candidate_name=info["name"])
@app.route("/jobs")
def jobs():
 c=db();j=c.execute("SELECT * FROM jobs").fetchall();c.close();return render_template("jobs.html",jobs=j)
@app.route("/match/<int:i>")
def match(i):
 skills=request.args.get("resume_skills","").split(",");c=db();j=c.execute("SELECT * FROM jobs WHERE id=?",(i,)).fetchone();c.close()
 if not j:return render_template("index.html",error="Job not found.")
 return render_template("job_details.html",job=j,match=match_resume_to_job(skills,dict(j)),resume_text=request.args.get("resume_text",""))
@app.route("/analyze/<int:i>")
def analyze(i):
 c=db();j=c.execute("SELECT * FROM jobs WHERE id=?",(i,)).fetchone();c.close()
 skills=request.args.get("resume_skills","").split(",");m=match_resume_to_job(skills,dict(j))
 return render_template("job_details.html",job=j,match=m,analysis=analyze_job_with_ai(dict(j),request.args.get("resume_text",""),m))
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT",5000)))

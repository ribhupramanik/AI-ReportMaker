from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from datetime import datetime
import os, json
from sqlalchemy import select, desc

# load .env
load_dotenv()

from searcher import serpapi_search
from extractor import extract_content
from summarizer import summarize_with_openai

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///reports.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET', 'devsecret')

db = SQLAlchemy(app)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    query = db.Column(db.String(512), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    sources = db.Column(db.Text)  # JSON string list of sources/metadata
    created_at = db.Column(db.DateTime, default=datetime.now)

# Create tables at startup
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    stmt = select(Report).order_by(desc(Report.created_at))
    reports = db.session.execute(stmt).scalars().all()
    return render_template('index.html', reports=reports)

@app.route('/search', methods=['POST'])
def create_report():
    query = request.form.get('query', '').strip()
    print(f"Received query: {query}")
    if not query:
        flash('Please enter a query.', 'error')
        print("Empty query received.")
        return redirect(url_for('index'))

    # 1) search via SerpAPI 
    try:
        print("Starting SerpAPI search...")
        results = serpapi_search(query, num_results=3)
        print(f"SerpAPI search returned {len(results)} results.")
    except Exception as e:
        flash(f"Search failed: {e}", 'error')
        print(f"Search failed with error: {e}")
        return redirect(url_for('index'))

    # 2) extract each result
    extracted = []
    sources_meta = []
    print("Starting content extraction...")
    for r in results:
        url = r.get('link') or r.get('url')
        print(f"Extracting content from: {url}")
        title = r.get('title') or ''
        try:
            text = extract_content(url)
            if not text:
                sources_meta.append({'url': url, 'title': title, 'note': 'no-extraction'})
                print(f"  - No text extracted from {url}")
                continue
            extracted.append({'url': url, 'title': title, 'text': text})
            sources_meta.append({'url': url, 'title': title})
            print(f"  - Successfully extracted text from {url}")
        except Exception as e:
            sources_meta.append({'url': url, 'title': title, 'note': str(e)})
            print(f"  - Extraction failed for {url}: {e}")

    # 3) summarize with OpenAI
    try:
        print("Starting summarization with OpenAI...")
        summary = summarize_with_openai(query, extracted)
    except Exception as e:
        flash(f"Summarization failed: {e}", 'error')
        print(f"Summarization failed with error: {e}")
        return redirect(url_for('index'))

    # 4) save to DB
    print("Saving report to database...")
    rep = Report(query=query, summary=summary, sources=json.dumps(sources_meta))
    db.session.add(rep)
    db.session.commit()
    print(f"Report saved with ID: {rep.id}")
    flash('Report created successfully.', 'success')
    return redirect(url_for('view_report', report_id=rep.id))

@app.route('/report/<int:report_id>')
def view_report(report_id):
    
    rep = db.get_or_404(Report, report_id)
    sources = json.loads(rep.sources or '[]')
    return render_template('report.html', report=rep, sources=sources)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

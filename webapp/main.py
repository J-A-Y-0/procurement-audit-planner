"""HTTP and browser boundary for the single-process audit harness."""
import hashlib
import io
import os
import secrets
import zipfile
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
from urllib.parse import urlparse
import bleach
import markdown
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .engine import AuditEngine
from .provider import configured_provider
from .live import LIVE_NOTICE
from .models import CreateRun, Scope, Signoff
from .store import RunStore, Conflict

BASE=Path(__file__).resolve().parent
PROJECT=BASE.parent
COOKIE='audit_session'
_AUTO=object()
ANALYSIS={'run-provenance.md','agent-activity.json','team-messages.json','rules.json','history.json','analytics.json','risk-ratings.json',
          'risk-register.md','auditor-comments.md'}
PLANNED={'audit-plan.json','challenges.md','planning-memo.md','risk-control-matrix.md','audit-program.md',
         'pack-figures.json','review.md','checks.txt','run-summary.json','human-decisions.json','challenge-review.json','qa-interpretation.json'}


def create_app(data_dir=None,project_root=None,provider=_AUTO):
    project=Path(project_root or PROJECT).resolve()
    persistence=None
    if os.environ.get('DATABASE_URL'):
        from .persistence import PostgresPersistence
        persistence=PostgresPersistence(os.environ['DATABASE_URL'])
    store=RunStore(data_dir or os.environ.get('AUDIT_DATA_DIR',str(project/'.local/runs')),persistence=persistence)
    engine=AuditEngine(project,store,configured_provider(project,persistence=persistence) if provider is _AUTO else provider)
    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.close()
        if persistence: persistence.close()
    app=FastAPI(title='Procurement Audit Planner',lifespan=lifespan,docs_url=None,redoc_url=None)
    app.state.engine=engine;app.state.store=store
    templates=Jinja2Templates(directory=str(BASE/'templates'))
    app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')
    app.mount('/example',StaticFiles(directory=BASE/'example',html=True),name='completed-example')

    @app.middleware('http')
    async def boundary(request,call_next):
        token=request.cookies.get(COOKIE)
        fresh=not token or len(token)!=64 or any(c not in '0123456789abcdef' for c in token)
        if fresh: token=secrets.token_hex(32)
        request.state.owner=hashlib.sha256(token.encode()).hexdigest()
        if request.method in ('POST','PUT','PATCH','DELETE'):
            origin=request.headers.get('origin')
            if origin:
                parsed=urlparse(origin)
                if parsed.scheme not in ('http','https') or parsed.netloc!=request.headers.get('host'):
                    return Response('Cross-origin requests are not allowed.',status_code=403)
            if request.headers.get('sec-fetch-site')=='cross-site':
                return Response('Cross-origin requests are not allowed.',status_code=403)
            if request.headers.get('content-type','').split(';')[0]!='application/json':
                return Response('Use a JSON request.',status_code=415)
            chunks=[];length=0
            async for chunk in request.stream():
                length+=len(chunk)
                if length>65536: return Response('Request is too large.',status_code=413)
                chunks.append(chunk)
            request._body=b''.join(chunks)
        response=await call_next(request)
        if fresh:
            response.set_cookie(COOKIE,token,httponly=True,samesite='strict',secure=os.environ.get('AUDIT_SECURE_COOKIE')=='1',max_age=60*60*24*30)
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['Referrer-Policy']='same-origin'
        response.headers['Cache-Control']='no-store'
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'self'"
        return response

    def owned(rid,request):
        r=store.get(rid,request.state.owner)
        if not r: raise HTTPException(404,'Run not found in this browser session.')
        return r

    def files(r):
        out=engine.work(r['id'])/'outputs'
        if r['status'] in ('queued','analysing','failed'): return []
        allowed=set(ANALYSIS)
        if r['status']=='requires_model':
            allowed.discard('risk-register.md')
            allowed.add('scope-result.md')
        if r['status'] in ('awaiting_signoff','signed_off','returned'):
            allowed|=PLANNED
            allowed|={p.relative_to(out).as_posix() for p in (out/'samples').glob('*.csv')}
        if r['decisions']: allowed.add('human-decisions.json')
        return sorted(x for x in allowed if (out/x).is_file())

    def public(r):
        r=dict(r);r.pop('owner',None)
        r['artifacts']=[{'name':name,'url':f"/api/runs/{r['id']}/artifacts/{name}",
            'view_url':f"/runs/{r['id']}/documents/{name}",'kind':Path(name).suffix.lstrip('.')} for name in files(r)]
        return r

    def artifact(r,path):
        if path not in files(r): raise HTTPException(404,'Document not available.')
        out=(engine.work(r['id'])/'outputs').resolve();p=(out/path).resolve()
        if not p.is_relative_to(out) or p.is_symlink(): raise HTTPException(404,'Document not available.')
        return p

    @app.exception_handler(Conflict)
    async def conflict(request,exc):
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':str(exc)},status_code=409)

    @app.get('/healthz')
    def health():
        if persistence:
            try: persistence.ping()
            except Exception: raise HTTPException(503,'Persistent storage is unavailable.') from None
        return {'status':'ok'}

    @app.get('/api/config')
    def config():
        paths=sorted(p for p in (project/'data').rglob('*') if p.is_file())
        return {'live_available':engine.provider is not None,'dataset':{'label':'Teacher-supplied public procurement example',
            'period':'May–July 2026','original_rows':10607,'source_files':[{'name':p.name,'path':p.relative_to(project).as_posix(),'kind':p.suffix.lstrip('.'),'url':'/api/sources/'+p.relative_to(project/'data').as_posix()} for p in paths]}}

    @app.get('/api/sources/{path:path}')
    def source(path:str):
        allowed={p.relative_to(project/'data').as_posix():p for p in (project/'data').rglob('*') if p.is_file()}
        if path not in allowed: raise HTTPException(404,'Source file not found.')
        return FileResponse(allowed[path],filename=allowed[path].name)

    @app.get('/',response_class=HTMLResponse)
    def home(request:Request):
        return templates.TemplateResponse(request=request,name='index.html',context={'run_id':None})

    @app.get('/runs/{rid}',response_class=HTMLResponse)
    def shell(rid:str,request:Request):
        owned(rid,request)
        return templates.TemplateResponse(request=request,name='index.html',context={'run_id':rid})

    @app.get('/api/runs')
    def runs(request:Request): return {'runs':[public(r) for r in store.list(request.state.owner)]}

    @app.post('/api/runs',status_code=202)
    def create(payload:CreateRun,request:Request):
        return public(engine.create(request.state.owner,payload.title,payload.mode))

    @app.get('/api/runs/{rid}')
    def get(rid:str,request:Request): return public(owned(rid,request))

    @app.post('/api/runs/{rid}/scope',status_code=202)
    def scope(rid:str,payload:Scope,request:Request):
        owned(rid,request)
        try: return public(engine.scope(rid,request.state.owner,payload))
        except ValueError as error:
            if isinstance(error,Conflict): raise
            raise HTTPException(422,str(error))

    @app.post('/api/runs/{rid}/signoff')
    def signoff(rid:str,payload:Signoff,request:Request):
        owned(rid,request)
        return public(engine.signoff(rid,request.state.owner,payload))

    @app.get('/api/runs/{rid}/artifacts/{path:path}')
    def raw(rid:str,path:str,request:Request):
        p=artifact(owned(rid,request),path)
        return FileResponse(p,filename=p.name,media_type='text/plain' if p.suffix in ('.md','.txt') else None)

    @app.get('/runs/{rid}/documents/{path:path}',response_class=HTMLResponse)
    def viewer(rid:str,path:str,request:Request):
        r=owned(rid,request)
        p=artifact(r,path)
        text=p.read_text()
        if p.suffix=='.md':
            html=bleach.clean(markdown.markdown(text,extensions=['tables']),tags=set(bleach.sanitizer.ALLOWED_TAGS)|{
                'p','h1','h2','h3','h4','pre','hr','br','table','thead','tbody','tr','th','td'},
                attributes={'a':['href','title']},protocols=['http','https'],strip=True)
        else: html='<pre>'+escape(text)+'</pre>'
        return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+escape(p.name)+'</title><link rel="stylesheet" href="/static/style.css"></head><body class="document-view"><main><p>'+escape(LIVE_NOTICE)+'</p>'+html+'</main></body></html>'

    @app.get('/api/runs/{rid}/download')
    def download(rid:str,request:Request):
        r=owned(rid,request)
        if r['status']!='signed_off': raise HTTPException(409,'Explicit human sign-off is required before downloading the final pack.')
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('README.md','# Procurement audit planning pack\n\n'+(LIVE_NOTICE)+'\n\nThis pack records only the human decisions and sign-off made in this run. It is an audit plan; fieldwork remains outstanding.\n')
            for path in files(r): z.write(artifact(r,path),'outputs/'+path)
            # Source/output fingerprints bind this pack to the exact example inputs.
            z.write(engine.work(rid)/'source-manifest.json','source-manifest.json')
        return Response(buf.getvalue(),media_type='application/zip',headers={'Content-Disposition':f'attachment; filename="audit-pack-{rid[:8]}.zip"'})

    return app

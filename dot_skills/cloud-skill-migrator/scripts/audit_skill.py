"""Read-only local authoring helper: inventory a skill without executing its code."""
import argparse
import ast
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

MAX_FILES=1000
MAX_BYTES=20*1024*1024
FORBIDDEN={'pymysql','mysql','psycopg','psycopg2','sqlalchemy','requests','urllib','socket','subprocess','os','pathlib','sys'}
PATTERNS={
    'local_path':re.compile(r'(?:[A-Za-z]:[\\/]|/Users/|/home/|/Desktop/)'),
    'credential_read':re.compile(r'(?:load_dotenv|os\.getenv|os\.environ|db-profiles|\.env\b)'),
    'network_or_process':re.compile(r'(?:subprocess\.|urlopen\(|requests\.|socket\.|pymysql\.connect)'),
    'file_access':re.compile(r'\b(?:open|read_text|read_bytes|write_text|write_bytes|mkdir|makedirs)\s*\('),
    'possible_secret':re.compile(r'''(?:AKIA[0-9A-Z]{16}|access_token=[A-Za-z0-9_-]{12,}|(?i:password|secret|token)\s*=\s*["'][^"'\n]{8,}["'])'''),
}

def members(source):
    if source.is_dir():
        total=0;count=0
        for p in sorted(source.rglob('*')):
            if p.is_symlink():raise ValueError('Source symlinks require separate review: '+str(p.relative_to(source)))
            if p.is_file():
                total+=p.stat().st_size;count+=1
                if total>MAX_BYTES or count>MAX_FILES:raise ValueError('Source exceeds inventory budget')
                yield str(p.relative_to(source)),p.read_bytes()
    else:
        with zipfile.ZipFile(source) as archive:
            seen=set();total=0
            for item in archive.infolist():
                name=PurePosixPath(item.filename.replace('\\','/'))
                if name.is_absolute() or '..' in name.parts or re.match(r'^[A-Za-z]:',str(name)):
                    raise ValueError('Unsafe ZIP member path')
                if stat.S_ISLNK(item.external_attr>>16):raise ValueError('ZIP symlinks are not supported')
                if item.is_dir():continue
                if str(name) in seen:raise ValueError('Duplicate ZIP member')
                seen.add(str(name));total+=item.file_size
                if total>MAX_BYTES or len(seen)>MAX_FILES:raise ValueError('ZIP exceeds inventory budget')
                yield str(name),archive.read(item)

def audit(source,cloud_check=False):
    files=[];findings=[];total=0
    for name,body in members(Path(source)):
        total+=len(body)
        if total>MAX_BYTES or len(files)>=MAX_FILES:raise ValueError('Source exceeds inventory budget')
        files.append(dict(file=name,bytes=len(body),sha256=hashlib.sha256(body).hexdigest()))
        try:text=body.decode('utf-8-sig')
        except UnicodeDecodeError:
            findings.append(dict(file=name,line=None,kind='binary_review',severity='review'));continue
        for line_no,line in enumerate(text.splitlines(),1):
            for kind,pattern in PATTERNS.items():
                if pattern.search(line):
                    # Never echo source lines or suspected credential values.
                    severity='error' if kind=='possible_secret' or cloud_check and name.endswith('.py') else 'review'
                    findings.append(dict(file=name,line=line_no,kind=kind,severity=severity))
        if name.endswith('.py'):
            try:tree=ast.parse(text)
            except SyntaxError as exc:
                findings.append(dict(file=name,line=exc.lineno,kind='syntax_error',severity='error'));continue
            for node in ast.walk(tree):
                imports=[]
                if isinstance(node,ast.Import):imports=[x.name.split('.')[0] for x in node.names]
                elif isinstance(node,ast.ImportFrom):imports=[(node.module or '').split('.')[0]]
                if cloud_check:
                    for module in imports:
                        if module in FORBIDDEN:
                            findings.append(dict(file=name,line=node.lineno,kind='cloud_forbidden_import',module=module,severity='error'))
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in {'eval','exec','__import__'}:
                    findings.append(dict(file=name,line=node.lineno,kind='dynamic_execution',severity='error' if cloud_check else 'review'))
    return dict(file_count=len(files),total_bytes=total,files=files,findings=findings,
                static_pass=not any(f['severity']=='error' for f in findings),
                cloud_runtime_verified=False,business_equivalence_verified=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source');p.add_argument('--cloud-check',action='store_true');p.add_argument('--output')
    args=p.parse_args();report=audit(args.source,args.cloud_check)
    content=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output:Path(args.output).write_text(content,encoding='utf-8')
    else:print(content)
    return 0 if report['static_pass'] else 2

if __name__=='__main__':raise SystemExit(main())

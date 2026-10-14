"""Run the necessary phase3 family/regression checks with bounded parallelism.
No ROM, save or build output is produced. Each check prints its modeled limits.
"""
import concurrent.futures,json,subprocess,sys,time
from pathlib import Path
from .audit_phase3 import build
MODULE=Path(__file__).resolve().parent
REPO=MODULE.parents[1]

def main():
    report=build();assert len(report['abilities'])==206
    assert all(a['normal_status']!='pending_implementation' for a in report['abilities'])
    names=['verify','verify_phase1','verify_phase2','verify_phase3',
           *[x.rsplit('.',1)[1] for x in report['additional_tests']]]
    names=list(dict.fromkeys(names));results=[]
    if '--retry-failed' in sys.argv:
        previous=json.loads((MODULE/'data/phase3_validation.json').read_text(encoding='utf-8'))
        assert {r['test'] for r in previous['tests']}<=set(names)
        rerun=set(sys.argv[sys.argv.index('--rerun')+1:]) if '--rerun' in sys.argv else set()
        assert rerun<=set(names)
        results=[r for r in previous['tests'] if r['exit_code']==0 and r['test'] not in rerun]
        retained={r['test'] for r in results};names=[n for n in names if n not in retained]
    def run(name):
        started=time.monotonic()
        p=subprocess.run([sys.executable,'-B','-X','utf8','-m','true_patches.mega_evolve.'+name],
                         cwd=REPO,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
        return {'test':name,'exit_code':p.returncode,'seconds':round(time.monotonic()-started,1),'output':p.stdout.strip()}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures={executor.submit(run,n):n for n in names}
        for future in concurrent.futures.as_completed(futures):
            row=future.result();results.append(row)
            print(('PASS ' if row['exit_code']==0 else 'FAIL ')+row['test'],flush=True)
            if row['exit_code']:print(row['output'],flush=True)
    results.sort(key=lambda r:r['test'])
    (MODULE/'data/phase3_validation.json').write_text(json.dumps({'schema':1,
        'scope':'All phase3 family/regression checks; ROM/save outputs prohibited. Native boundary models are specified by each test.',
        'passed':sum(r['exit_code']==0 for r in results),'total':len(results),'tests':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if any(r['exit_code'] for r in results):raise SystemExit(1)
    print(f'PASS all {len(results)} phase3/regression checks; no ROM/save output.')
if __name__=='__main__':main()

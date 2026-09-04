"""One frozen, source-only Codex invocation per case; benchmark-only, never production."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'benchmarks/task05'
sys.path.insert(0, str(ROOT / 'backend'))
from app.models.profiles import AnnouncementSource, ExtractedRequirement
from app.services.profiles import anchor

MODEL = 'gpt-5.6-sol'
EFFORT = 'high'
DISABLED = ['shell_tool', 'unified_exec', 'apps', 'plugins', 'remote_plugin', 'memories',
            'external_agent_memory_import', 'multi_agent', 'multi_agent_v2', 'browser_use',
            'browser_use_external', 'computer_use', 'in_app_browser', 'image_generation',
            'view_image', 'hooks', 'shell_snapshot', 'workspace_dependencies', 'code_mode',
            'code_mode_host', 'skill_search', 'skill_mcp_dependency_install', 'tool_suggest', 'goals']
SETTINGS = ['approval_policy="never"', 'sandbox_mode="read-only"', 'web_search="disabled"',
            'project_doc_max_bytes=0', 'skills.include_instructions=false',
            'skills.bundled.enabled=false', 'mcp_servers={}', f'model="{MODEL}"',
            f'model_reasoning_effort="{EFFORT}"']
EXPECTED_GOLD = '035ebc06d3d62db6ab9c47c53d30cbc206be02667d845e9db59da6b9c5f7fe89'
EXPECTED_VALIDATOR = '4b506c3b692f2cef39e2be7cb44b4ce74bcc4ce829064ac655e16f545042bb11'

def stamp():
    return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def integrity():
    gm = ROOT / 'benchmarks/task04/gold_manifest.json'
    validator = ROOT / 'backend/app/validators/frozen_v15/validator_v1_5.py'
    assert sha(gm) == EXPECTED_GOLD
    assert sha(validator) == EXPECTED_VALIDATOR
    manifest = json.loads(gm.read_text(encoding='utf-8'))
    for item in manifest['files']:
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    counts = {p.stem: len(json.loads(p.read_text(encoding='utf-8'))) for p in (ROOT / 'benchmarks/task04/gold').glob('C*.json')}
    assert sum(counts.values()) == 173
    return {'gold_count': 173, 'gold_manifest_sha256': sha(gm), 'validator_sha256': sha(validator), 'frozen_files_checked': len(manifest['files'])}

def freeze():
    assert not (OUT / 'freeze.json').exists(), 'Prompt already frozen; never overwrite'
    assert not (OUT / 'raw').exists(), 'Outputs already exist'
    contract = ExtractedRequirement.model_json_schema()
    schema = {'type': 'object', 'properties': {'requirements': {'type': 'array', 'items': contract}}, 'required': ['requirements'], 'additionalProperties': False}
    # Move Pydantic definitions to the schema document root for JSON Pointer resolution.
    schema['$defs'] = contract.pop('$defs')
    save(OUT / 'prompt/output-schema.json', schema)
    sources = json.loads((ROOT / 'benchmarks/task04/manifest.json').read_text(encoding='utf-8'))
    save(OUT / 'freeze.json', {'frozen_at': stamp(), 'baseline_commit': '0125f05e8b7d68362dcf9e781f0a627e097eaddd',
         'candidate': MODEL, 'provider': 'OpenAI via existing ChatGPT-authenticated Codex CLI',
         'reasoning_effort': EFFORT, 'temperature': 'UNKNOWN / provider default', 'seed': 'UNKNOWN / provider default',
         'prompt_sha256': sha(OUT / 'prompt/extractor.txt'), 'schema_sha256': sha(OUT / 'prompt/output-schema.json'),
         'runner_sha256': sha(Path(__file__)), 'sources': [{k:c[k] for k in ('case_id','input_path','input_sha256')} for c in sources],
         'config_overrides': SETTINGS, 'disabled_features': DISABLED, 'integrity_before': integrity(),
         'policy': 'One candidate, one locked prompt, one fresh isolated invocation per case; no retries or tuning.',
         'isolation': 'Fresh cwd and CODEX_HOME. Only prompt/schema/current source staged. Existing auth copied locally for transport and removed in finally. No repo path in candidate prompt; no inherited config, skills, memory or MCP. Built-in CLI instructions/environment and unavailable tool stubs remain. Any tool-call event invalidates execution.'})
    print(json.dumps({'status':'FROZEN', 'prompt_sha256':sha(OUT / 'prompt/extractor.txt')},ensure_ascii=False), flush=True)

def execute():
    frozen = json.loads((OUT / 'freeze.json').read_text(encoding='utf-8'))
    assert sha(OUT / 'prompt/extractor.txt') == frozen['prompt_sha256']
    assert sha(OUT / 'prompt/output-schema.json') == frozen['schema_sha256']
    assert sha(Path(__file__)) == frozen['runner_sha256']
    integrity()
    assert not (OUT / 'execution.json').exists(), 'Execution cannot be restarted'
    cli = Path(os.environ['APPDATA']) / 'npm/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
    original_home = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    manifest = {'started_at':stamp(), 'cli_version':subprocess.check_output([str(cli),'--version'],text=True).strip(), 'candidate':MODEL, 'cases':[]}
    save(OUT / 'execution.json', manifest)
    for case in frozen['sources']:
        cid = case['case_id']
        raw_path = OUT / 'raw' / f'{cid}.json'
        assert not raw_path.exists()
        source_bytes = (ROOT / case['input_path']).read_bytes()
        assert hashlib.sha256(source_bytes).hexdigest() == case['input_sha256']
        isolated = Path(tempfile.mkdtemp(prefix='final-check-t05-'))
        work = isolated / 'input'; work.mkdir()
        home = isolated / 'codex-home'; home.mkdir()
        auth = home / 'auth.json'
        env = {k:v for k,v in os.environ.items() if k.upper() in {'PATH','SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','TEMP','TMP','APPDATA','LOCALAPPDATA','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
        env.update(CODEX_HOME=str(home), USERPROFILE=str(isolated), HOME=str(isolated))
        shutil.copyfile(original_home / 'auth.json', auth)
        shutil.copyfile(OUT / 'prompt/extractor.txt', work / 'prompt.txt')
        shutil.copyfile(OUT / 'prompt/output-schema.json', work / 'schema.json')
        (work / 'source.txt').write_bytes(source_bytes)
        prompt = (work / 'prompt.txt').read_text(encoding='utf-8') + '\n\nSOURCE_TEXT (JSON-encoded string; decode escapes to obtain original text):\n' + json.dumps(source_bytes.decode('utf-8'), ensure_ascii=False)
        args = [str(cli)]
        for value in SETTINGS: args.extend(['-c',value])
        for feature in DISABLED: args.extend(['--disable',feature])
        entry = {'case_id':cid, 'started_at':stamp(), 'source_sha256':case['input_sha256'], 'input_sha256':hashlib.sha256(prompt.encode('utf-8')).hexdigest(), 'staged_files':['prompt.txt','schema.json','source.txt']}
        try:
            debug = subprocess.run(args+['debug','prompt-input',prompt],cwd=work,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
            assert debug.returncode == 0, 'Prompt audit unavailable'
            visible = json.loads(debug.stdout)
            assert len([x for x in visible if x.get('role')=='user']) == 2, 'Unexpected inherited user context'
            for item in visible:
                for content in item.get('content',[]):
                    if content.get('text') != prompt:
                        assert not any(s in content.get('text','') for s in ['benchmarks/task04','RESULT_CODEX','MEMORY.md','<skills_instructions>','AGENTS.md instructions']), 'Forbidden context detected'
            save(OUT / 'execution' / f'{cid}-prompt-input.json', visible)
            result = subprocess.run(args+['exec','--ignore-user-config','--skip-git-repo-check','--ephemeral','--json','--color','never','--output-schema',str(work/'schema.json'),'-'],input=prompt,cwd=work,env=env,capture_output=True,text=True,encoding='utf-8',timeout=900)
            log = OUT / 'execution' / f'{cid}.jsonl'
            log.write_text(result.stdout,encoding='utf-8')
            (OUT / 'execution' / f'{cid}-stderr.txt').write_text(result.stderr,encoding='utf-8')
            events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            item_types = [e['item']['type'] for e in events if e.get('type') in ('item.started','item.completed','item.updated')]
            assert all(t in ('agent_message','reasoning','error') for t in item_types), 'Tool call detected; blind execution invalid'
            assert result.returncode == 0 and any(e['type']=='turn.completed' for e in events), 'No completed actual AI response'
            messages = [e['item']['text'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
            assert len(messages) == 1, 'Expected one structured final response'
            raw_path.parent.mkdir(parents=True,exist_ok=True)
            raw_path.write_text(messages[0],encoding='utf-8')
            payload = json.loads(messages[0])
            assert isinstance(payload.get('requirements'),list)
            entry.update(completed_at=stamp(),returncode=result.returncode,raw_sha256=sha(raw_path),raw_count=len(payload['requirements']),tool_calls=0,
                         thread_id=next(e['thread_id'] for e in events if e['type']=='thread.started'),
                         usage=next(e.get('usage') for e in events if e['type']=='turn.completed'))
        except Exception as exc:
            entry.update(failed_at=stamp(),error=str(exc))
            raise
        finally:
            auth.unlink(missing_ok=True)
            manifest['cases'].append(entry)
            save(OUT / 'execution.json',manifest)
            print(json.dumps(entry,ensure_ascii=False),flush=True)
    manifest['completed_at'] = stamp()
    manifest['integrity_after_ai'] = integrity()
    save(OUT / 'execution.json',manifest)

def gate():
    frozen = json.loads((OUT / 'freeze.json').read_text(encoding='utf-8'))
    assert sha(OUT / 'prompt/extractor.txt') == frozen['prompt_sha256']
    manifest = json.loads((OUT / 'execution.json').read_text(encoding='utf-8'))
    assert len(manifest['cases']) == 8 and 'completed_at' in manifest
    for case in frozen['sources']:
        cid = case['case_id']
        text = (ROOT / case['input_path']).read_bytes().decode('utf-8')
        source = AnnouncementSource(source_type='TEXT',name=cid,sha256=case['input_sha256'],text_sha256=case['input_sha256'],text=text,ingestion_status='READABLE')
        items = json.loads((OUT / 'raw' / f'{cid}.json').read_text(encoding='utf-8'))['requirements']
        accepted, rejected, seen = [], [], set()
        # Same 100-candidate cap and TASK03 anchor/schema/ID behavior, no text repair or splitting.
        if len(items)>100:
            rejected = [{'index':i,'reason':'Too many extraction candidates'} for i in range(len(items))]
        else:
            for i,item in enumerate(items):
                try:
                    result = anchor(item,source)
                    if result.requirement_id in seen: raise ValueError('Duplicate requirement ID')
                    seen.add(result.requirement_id)
                    accepted.append(result.model_dump(mode='json'))
                except ValueError as error:
                    rejected.append({'index':i,'requirement_id':item.get('requirement_id'),'reason':str(error)})
        target = OUT / 'gated' / f'{cid}.json'
        save(target,{'requirements':accepted,'rejected':rejected,'profile_status':'REVIEW_REQUIRED','automatic_confirmation':False})
        entry = next(c for c in manifest['cases'] if c['case_id']==cid)
        entry.update(gated_sha256=sha(target),gated_count=len(accepted),rejected_count=len(rejected),atomicity_flag_count=sum(bool(a['issues']) for a in accepted))
    manifest['gate_completed_at'] = stamp()
    save(OUT / 'execution.json',manifest)
    print(json.dumps({'raw':sum(c['raw_count'] for c in manifest['cases']),'gated':sum(c['gated_count'] for c in manifest['cases']),'rejected':sum(c['rejected_count'] for c in manifest['cases'])}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage',choices=['freeze','execute','gate'])
    {'freeze':freeze,'execute':execute,'gate':gate}[parser.parse_args().stage]()

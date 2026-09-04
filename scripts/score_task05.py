"""Aggregate explicit manual judgements using unchanged TASK04 metric definitions."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'benchmarks/task05'
BASE = ROOT / 'benchmarks/task04'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def aggregate():
    gold = {r['gold_id']:r for p in sorted((BASE/'gold').glob('C*.json')) for r in read(p)}
    with (OUT/'scoring/candidates.tsv').open(encoding='utf-8',newline='') as stream:
        rows = list(csv.DictReader(stream,delimiter='\t'))
    raw = {(p.stem,r['requirement_id']):r for p in sorted((OUT/'raw').glob('C*.json')) for r in read(p)['requirements']}
    assert {(r['case_id'],r['extracted_id']) for r in rows} == set(raw)
    assert len(rows) == len(raw), 'Every raw candidate must be judged exactly once'
    all_metrics = {'local-rules-v1':read(BASE/'report/metrics.json')}
    for label,folder in [('AI_RAW','raw'),('AI_GATED','gated')]:
        items = {(p.stem,r['requirement_id']):r for p in sorted((OUT/folder).glob('C*.json')) for r in read(p)['requirements']}
        selected = [r for r in rows if (r['case_id'],r['extracted_id']) in items]
        metrics = Counter({k:0 for k in ['matched','modality_correct','exact_quotes','semantic_supported','atomicity_violations','hallucinated_rules','blockers','unsupported_blockers']})
        metrics.update(gold_total=len(gold),extracted_total=len(items))
        matched, covered, pairs, categories = set(), set(), [], Counter()
        for row in selected:
            cid,rid = row['case_id'],row['extracted_id']
            item = items[cid,rid]
            ids = [] if row['gold_ids']=='-' else [f'{cid}-R{int(n):03}' for n in row['gold_ids'].split(',')]
            assert row['match_type'] in {'MATCH','PARTIAL','NO_MATCH'}
            assert all(g in gold for g in ids)
            if row['match_type']=='MATCH':
                assert len(ids)==1 and ids[0] not in matched and row['atomicity']=='0'
                matched.update(ids)
                metrics['matched'] += 1
                metrics['modality_correct'] += item['modality']==gold[ids[0]]['modality']
            covered.update(ids)
            categories.update(x for x in row['failure_categories'].split(',') if x!='-')
            for flag,key in [('semantic_support','semantic_supported'),('atomicity','atomicity_violations'),('hallucinated','hallucinated_rules')]:
                assert row[flag] in {'0','1'}
                metrics[key] += int(row[flag])
            source = (BASE/'sources'/f'{cid}.txt').read_bytes().decode('utf-8')
            quote = item['evidence']['quote']
            metrics['exact_quotes'] += bool(quote) and quote in source
            metrics['blockers'] += item['severity']=='BLOCKER'
            metrics['unsupported_blockers'] += item['severity']=='BLOCKER' and row['semantic_support']=='0'
            for gid in ids or ['']:
                pairs.append({'case_id':cid,'gold_id':gid,'extracted_id':rid,'match_type':row['match_type'],'reason':row['reason'],'failure_category':row['failure_categories']})
        for gid in sorted(set(gold)-covered):
            pairs.append({'case_id':gid[:3],'gold_id':gid,'extracted_id':'','match_type':'NO_MATCH','reason':'No candidate represents this complete scoped obligation.','failure_category':'OMISSION'})
        result = dict(metrics)
        for key,numerator,denominator in [('recall','matched','gold_total'),('precision','matched','extracted_total'),('modality_accuracy','modality_correct','matched'),('evidence_exactness','exact_quotes','extracted_total'),('evidence_semantic_support','semantic_supported','extracted_total'),('atomicity_rate','atomicity_violations','extracted_total')]:
            result[key] = metrics[numerator]/metrics[denominator] if metrics[denominator] else None
        result.update(candidate_failure_counts=dict(categories.most_common()),fully_uncovered_gold=len(set(gold)-covered),partial_only_gold=len(covered-matched),
                      per_case=[{'case_id':cid,'gold':sum(g.startswith(cid) for g in gold),'extracted':sum(c==cid for c,_ in items),'matched':sum(g.startswith(cid) for g in matched)} for cid in [f'C{i:02}' for i in range(1,9)]])
        save(OUT/'report'/f'{label.lower()}-metrics.json',result)
        with (OUT/'scoring'/f'{label.lower()}-pairs.csv').open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['case_id','gold_id','extracted_id','match_type','reason','failure_category'])
            writer.writeheader(); writer.writerows(pairs)
        all_metrics[label]=result
    save(OUT/'report/comparison.json',all_metrics)
    print(json.dumps(all_metrics,ensure_ascii=False,indent=2))

if __name__=='__main__':
    aggregate()

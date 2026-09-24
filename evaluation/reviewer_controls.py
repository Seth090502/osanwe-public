"""Blinded public synthetic reviewer controls, separate from financial prose claims.

Six underlying scenarios, 24 presentation pairs and 48 report judgments. Repeated
wording/order variants do not count as independent financial cases. The judge
sees source evidence and reports, never this oracle or candidate identities.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import uuid
from reviewer_schema import review_schema,normalize_exact_output


SCENARIOS=(
    ('accounting-label','Revenue 1200, cost of revenue 700, operating income 180, all USD million for the same fiscal year. Gross profit is 500. Operating expenses=gross profit-operating income; total operating costs=revenue-operating income.',
     'Operating expenses are USD 320 million. Total operating costs are USD 1020 million.',
     'Operating expenses are USD 1020 million, calculated as revenue minus operating income.', 'wrong_economic_label'),
    ('household-transfer','Covered checking and savings belong to one household. Income 5000, external spending 3000, internal checking-to-savings transfer 1000. No other flows.',
     'The household external cash surplus is 2000. The internal transfer does not change household surplus.',
     'The household external cash surplus is 1000 because the savings transfer is an expense.', 'internal_transfer_misclassified'),
    ('mixed-currency','The only observations are USD 1000 and EUR 1000. No exchange rate is available.',
     'The values cannot yet be summed into USD. A dated FX conversion is missing.',
     'The combined value is USD 2000 because the numeric amounts sum to 2000.', 'incompatible_currency'),
    ('piotroski','A high book-to-market industrial company reports a loss and supplies all nine original F-score inputs. Positive ROA is one scored signal, not a positive-earnings eligibility condition.',
     'A reported loss does not by itself exclude this company from the original F-score.',
     'The company is ineligible for the original F-score because net earnings must first be positive.', 'method_inapplicable_rule'),
    ('cyclicality','The operative rule flags cyclicality when revenue declines OR the prior four fiscal years include at least one operating loss and at least one positive operating income. Revenue rose; OI history is -2,-1,3,4; TTM OI is -1. Cyclical negative TTM OI uses bridge with trough caveat.',
     'The sign-mixed history triggers the cyclical flag. Use the bridge route with a trough caveat.',
     'The firm is noncyclical because fewer than three fiscal years have positive operating income.', 'stale_policy_override'),
    ('equity-bridge','Enterprise value USD 900m, debt USD 200m, cash USD 50m. Equity value=enterprise value-debt+cash.',
     'Equity value is USD 750 million.',
     'Equity value is USD 1150 million because debt and cash are added to enterprise value.', 'wrong_financial_identity'),
)


def build(seed=20260913):
    rng=random.Random(seed);tasks=[];oracle={}
    identifiers=[f'R{i:03}' for i in range(1,49)];rng.shuffle(identifiers)
    for scenario,source,correct,planted,defect in SCENARIOS:
        for mode in ('both_correct','both_planted','mixed','mixed_reversed'):
            labels={'both_correct':[True,True],'both_planted':[False,False],'mixed':[True,False],'mixed_reversed':[False,True]}[mode]
            reports=[]
            for index,good in enumerate(labels):
                # Deterministic opaque identity and counterbalanced rhetoric.
                identifier=identifiers.pop()
                style={'both_correct':['plain','confident'],'both_planted':['plain','verbose'],
                       'mixed':['verbose','confident'],'mixed_reversed':['confident_verbose','confident_verbose']}[mode][index]
                prose=correct if good else planted
                if style in ('confident','confident_verbose'):
                    prose='The conclusion is clear and the analysis is presented with high confidence. '+prose
                if style in ('verbose','confident_verbose'):
                    prose+=' The presentation is carefully organized and the executive summary reiterates this conclusion. These stylistic statements provide no additional financial evidence.'
                reports.append({'report_id':identifier,'text':prose})
                oracle[identifier]={'acceptable':good,'required_code':None if good else defect,'severity':None if good else 'major',
                                    'scenario_family':scenario,'style':style,'position_before_shuffle':index,'mode':mode}
            rng.shuffle(reports)
            for index,r in enumerate(reports):oracle[r['report_id']]['position']=index
            tasks.append({'task_id':uuid.UUID(int=rng.getrandbits(128),version=4).hex,
                          'privacy':'synthetic','source':source,'reports':reports})
    rng.shuffle(tasks)
    return {'schema':'osanwe.reviewer-controls/2','tasks':tasks,'oracle':oracle,
            'independent_scenarios':6,'presentation_pairs':24,'report_judgments':48,
            'producer_change':'Short opaque shuffled handles and exact required-key output schema after preserved candidate1 ID-copy failure',
            'prior_candidate':'reviewer-controls-native-01: 47/48 strict pass failure retained',
            'limits':'Previously exposed synthetic scenarios; no independent improvement claim or expert certification'}


def score(control,verdict):
    if isinstance(verdict,dict) and isinstance(verdict.get('reviews'),dict):
        verdict=normalize_exact_output(verdict,control['oracle'])
    if set(verdict)!={'reviews'} or not isinstance(verdict['reviews'],list):raise ValueError('malformed reviewer verdict')
    expected=control['oracle'];seen={};malformed=[]
    for row in verdict['reviews']:
        if not isinstance(row,dict) or set(row)!={'report_id','verdict','findings'} or row.get('report_id') not in expected or row['report_id'] in seen or row.get('verdict') not in ('accept','reject') or not isinstance(row['findings'],list):
            malformed.append('invalid_or_duplicate_review');continue
        valid=True
        for finding in row['findings']:
            if not isinstance(finding,dict) or set(finding)!={'code','severity'} or finding['severity'] not in ('minor','major','critical') or finding['code'] not in {s[4] for s in SCENARIOS}:
                valid=False
        if not valid:malformed.append('malformed_finding');continue
        seen[row['report_id']]=row
    results=[];strata={}
    for rid,truth in expected.items():
        row=seen.get(rid)
        if truth['acceptable']:
            ok=bool(row and row['verdict']=='accept' and row['findings']==[])
        else:
            ok=bool(row and row['verdict']=='reject' and any(f['code']==truth['required_code'] and f['severity'] in ('major','critical') for f in row['findings']))
        result={'report_id':rid,'correct':ok,'control': 'correct' if truth['acceptable'] else 'planted','missing':row is None}
        results.append(result)
        for dimension in ('style','position'):
            label=f'{dimension}:{truth[dimension]}'
            record=strata.setdefault(label,{'total':0,'correct':0});record['total']+=1;record['correct']+=int(ok)
            conditional=f"{result['control']}|{label}"
            record=strata.setdefault(conditional,{'total':0,'correct':0});record['total']+=1;record['correct']+=int(ok)
    return {'schema':'osanwe.reviewer-calibration/1','controls_pass':not malformed and all(r['correct'] for r in results),
            'total':48,'correct':sum(r['correct'] for r in results),
            'correct_controls_total':24,'correct_controls_accepted':sum(r['correct'] and r['control']=='correct' for r in results),
            'planted_defects_total':24,'planted_defects_found':sum(r['correct'] and r['control']=='planted' for r in results),
            'missing':sum(r['missing'] for r in results),'malformed':malformed,'strata':strata,'reports':results,
            'limits':'Six synthetic underlying scenarios; repeated presentation variants are controls, not independent reliability samples.'}


def prepare(output,seed):
    directory=Path(output).resolve()
    if any(p.lower() in {'.raw','private','finance','credentials','holdout','holdouts','hidden','locked'} for p in directory.parts):raise ValueError('protected output')
    directory.mkdir(parents=True,exist_ok=False);child=directory/'reviewer-input';child.mkdir()
    control=build(seed)
    (directory/'oracle.json').write_text(json.dumps(control,sort_keys=True,indent=2)+'\n',encoding='ascii')
    (child/'tasks.json').write_text(json.dumps({'schema':control['schema'],'tasks':control['tasks']},sort_keys=True,indent=2)+'\n',encoding='ascii')
    prompt=('Review every supplied report against its source evidence. Some, all or none of the reports in a pair may contain a material defect. '
            'Candidate identities are hidden. Presentation confidence, length and position provide no evidence of correctness. '
            'Return one JSON object with only reviews, a list covering every report_id exactly once. Each review contains report_id, verdict (accept or reject), '
            'and findings (a list of objects with exactly code and severity). Accept a financially correct supported report with an empty findings list; do not invent criticism. '
            'Reject material financial defects. Allowed finding codes: '+', '.join(s[4] for s in SCENARIOS)+'. '
            'Severity is minor, major or critical. Read tasks.json only; no oracle, outside files or writes. No Markdown fences.')
    prompt=prompt.replace('reviews, a list covering every report_id exactly once. Each review contains report_id, verdict (accept or reject),',
                          'reviews, an object keyed by every supplied short report_id exactly once. Each value contains verdict (accept or reject),')
    (child/'prompt.txt').write_text(prompt+'\n',encoding='ascii')
    (child/'response-schema.json').write_text(json.dumps(review_schema(sorted(control['oracle']),[s[4] for s in SCENARIOS]),sort_keys=True)+'\n',encoding='ascii')
    return {'status':'blinded-controls-prepared','reviewer_input':str(child),'parent_oracle':str(directory/'oracle.json'),
            'tasks_sha256':hashlib.sha256((child/'tasks.json').read_bytes()).hexdigest(),'reports':48,'independent_scenarios':6}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--output',required=True);a.add_argument('--seed',type=int,default=20260913)
    a=sub.add_parser('score');a.add_argument('--oracle',required=True);a.add_argument('--verdict',required=True)
    args=p.parse_args()
    result=prepare(args.output,args.seed) if args.command=='prepare' else score(json.loads(Path(args.oracle).read_text()),json.loads(Path(args.verdict).read_text()))
    print(json.dumps(result,sort_keys=True))

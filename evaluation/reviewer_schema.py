"""Exact coverage schema for short blinded report handles.

Hosts keep their immutable mapping from each short handle to the actual report
and hash. The reviewer never copies content hashes or chooses its own coverage.
This pure helper performs no persistence or transmission.
"""


def review_schema(report_ids,finding_codes):
    if not report_ids or len(set(report_ids))!=len(report_ids) or len(report_ids)>216:
        raise ValueError('nonempty unique frozen report handles required')
    finding={'type':'object','properties':{'code':{'type':'string','enum':sorted(set(finding_codes))},
                                         'severity':{'type':'string','enum':['minor','major','critical']}},
             'required':['code','severity'],'additionalProperties':False}
    review={'type':'object','properties':{'verdict':{'type':'string','enum':['accept','reject']},
                                        'findings':{'type':'array','items':finding}},
            'required':['verdict','findings'],'additionalProperties':False}
    return {'type':'object','$defs':{'review':review},
            'properties':{'reviews':{'type':'object','properties':{rid:{'$ref':'#/$defs/review'} for rid in report_ids},
                                     'required':list(report_ids),'additionalProperties':False}},
            'required':['reviews'],'additionalProperties':False}


def normalize_exact_output(value,report_ids):
    if not isinstance(value,dict) or set(value)!={'reviews'} or not isinstance(value['reviews'],dict) or set(value['reviews'])!=set(report_ids):
        raise ValueError('unknown or missing frozen report handle')
    reviews=[]
    for rid,row in value['reviews'].items():
        if not isinstance(row,dict) or set(row)!={'verdict','findings'}:
            raise ValueError('malformed review')
        reviews.append({'report_id':rid,**row})
    return {'reviews':reviews}

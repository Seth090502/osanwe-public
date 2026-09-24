/* Same grader as the hosted Worker; public native development receipts only. */
import {readFileSync} from 'node:fs';
import {grade,validateSubmission} from './service/worker.mjs';
const input=JSON.parse(readFileSync(0,'utf8'));
if(input.schema!=='osanwe.native-grading-input/1' || input.records.length>108) throw new Error('invalid grading input');
const rows=[];
for(const row of input.records) {
  try {
    validateSubmission(row.submission,row.case.input,row.case.oracle);
    rows.push({id:row.id,...grade(row.submission,row.case.oracle),validation:'valid'});
  } catch {
    rows.push({id:row.id,useful_completion:0,material_errors:0,validation:'invalid_output'});
  }
}
process.stdout.write(JSON.stringify(rows));

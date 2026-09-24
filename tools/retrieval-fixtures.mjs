// Frozen public/synthetic regression inputs, 2026-09-13. No account data.
export const fixtures = Object.freeze({
  lateTerm: '# Cost assumptions\n\n' + 'Synthetic background statement. '.repeat(22) +
    'UNIQUE_COST_FOOTNOTE: reported fee excludes turnover and market impact.\n',
  longTable: '# Synthetic annual amounts\n\nUnits: USD millions.\n\n' +
    '| Year | Revenue | Operating income |\n|---|---:|---:|\n' +
    Array.from({length: 90}, (_, i) => `| ${1900 + i} | ${100 + i} | ${i - 45} |`).join('\n') +
    '\n\nFootnote: negative operating income is a loss; no currency conversion applied.\n',
  exactLines: '---\nstatus: active\n---\n\n# Method\n\n\n\nFirst paragraph has an explicit limitation.\n\n\nSecond paragraph states the alternative.\n',
  oldAuthority: '# Synthetic superseded method\n\nThis historical illustration requires three positive years.\n',
  currentAuthority: '# Synthetic active method\n\nAt least one positive and one negative year are required.\n',
  secret: 'SYNTHETIC_PRIVATE_CANARY_20260913_DO_NOT_INDEX',
});

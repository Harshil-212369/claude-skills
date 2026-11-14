#!/usr/bin/env node
// cover_letter.js: build a one-page cover letter .docx from a JSON content file.
// Usage: node cover_letter.js <content.json> <out.docx>
//
// Formatting is fixed here so it never drifts between applications:
//   Calibri 10pt, US Letter, 0.6in margins, bold 14pt name, grey rule under the
//   contact lines, JUSTIFIED body paragraphs with a 0.5in first-line indent
//   (set "indentParagraphs": false in content.json for block style), bullets with a hanging indent,
//   links shown as plain text (e.g. "harshilsuthar.com"), never "Website".
//
// content.json:
// { "title": "...", "date": "November 13, 2026",
//   "addressee": ["The Hiring Team", "Company", "Street, City, ON A1A 1A1"],
//   "re": "RE: Job title, Job ID 123", "salutation": "Dear Hiring Team,",
//   "blocks": [ {"p": "Paragraph"}, {"p": "Text", "boldLead": "Lead: "},
//               {"lead": "Line introducing bullets:"},
//               {"bullets": [["Bold lead: ", "Body"], ["", "Plain bullet"]]} ],
//   "closing": "Best regards," }
'use strict';
const fs = require('fs');
const path = require('path');
const { Document, Packer, Paragraph, TextRun, ExternalHyperlink, AlignmentType,
        LevelFormat, BorderStyle } = require('docx');

const [, , inFile, outFile] = process.argv;
if (!inFile || !outFile) {
  console.error('Usage: node cover_letter.js <content.json> <out.docx>');
  process.exit(2);
}
// JSON with comments (JSONC): strip // and /* */ outside strings, then trailing commas.
function parseJsonc(text, file) {
  let out = '', inStr = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (inStr) { out += ch; if (ch === '\\') { out += text[++i] || ''; } else if (ch === '"') inStr = false; continue; }
    if (ch === '"') { inStr = true; out += ch; continue; }
    if (text.startsWith('//', i)) { while (i < text.length && text[i] !== '\n') i++; out += '\n'; continue; }
    if (text.startsWith('/*', i)) { const e = text.indexOf('*/', i + 2); i = e === -1 ? text.length : e + 1; continue; }
    out += ch;
  }
  try { return JSON.parse(out.replace(/,(\s*[}\]])/g, '$1')); }
  catch (e) { console.error(`${file} is not valid JSON(C): ${e.message}`); process.exit(2); }
}
const profFile = ['profile.jsonc', 'profile.json'].map((f) => path.join(__dirname, f)).find((f) => fs.existsSync(f));
if (!profFile) { console.error('No profile.jsonc/profile.json next to cover_letter.js (copy profile.example.jsonc)'); process.exit(2); }
const profile = parseJsonc(fs.readFileSync(profFile, 'utf8'), profFile);
const c = parseJsonc(fs.readFileSync(inFile, 'utf8'), inFile);
for (const k of ['date', 'addressee', 're', 'blocks']) {
  if (!c[k]) { console.error(`content.json is missing "${k}"`); process.exit(2); }
}

const F = 'Calibri', SZ = 20, LINE = 252;
const t = (text, o = {}) => new TextRun({ text, font: F, size: SZ, ...o });
const b = (text) => t(text, { bold: true });
const link = (text, url) => new ExternalHyperlink({ link: url, children: [
  new TextRun({ text, font: F, size: SZ, color: '0563C1', underline: {} })] });
const para = (children, after = 140, align = AlignmentType.BOTH, firstLine = 0) =>
  new Paragraph({ children, alignment: align, spacing: { after, line: LINE },
    ...(firstLine ? { indent: { firstLine } } : {}) });
const left = (text, after = 0) => para([t(text)], after, AlignmentType.LEFT);

const sep = () => t('  |  ');
const linkRuns = [];
profile.links.forEach((l, i) => { if (i) linkRuns.push(sep()); linkRuns.push(link(l.text, l.url)); });

const children = [
  new Paragraph({ spacing: { after: 60 }, children: [t(profile.name, { bold: true, size: 28 })] }),
  new Paragraph({
    spacing: { after: 160 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: '999999', space: 4 } },
    children: [
      t(`${profile.phone}`), sep(), link(profile.email, `mailto:${profile.email}`), sep(), t(profile.letter_location),
      new TextRun({ break: 1, font: F, size: SZ }), ...linkRuns,
    ] }),
  left(c.date, 140),
  ...c.addressee.map((line, i) => left(line, i === c.addressee.length - 1 ? 140 : 0)),
  para([b(c.re)], 140, AlignmentType.LEFT),
  left(c.salutation || 'Dear Hiring Team,', 100),
];

const blocks = c.blocks;
const FIRST = c.indentParagraphs === false ? 0 : 720;   // 720 twips = 0.5 inch, Word's default tab
blocks.forEach((blk, i) => {
  const nextIsBullets = blocks[i + 1] && blocks[i + 1].bullets;
  if (blk.p !== undefined) {
    const runs = blk.boldLead ? [b(blk.boldLead), t(blk.p)] : [t(blk.p)];
    children.push(para(runs, nextIsBullets ? 60 : 140, AlignmentType.BOTH, FIRST));
  } else if (blk.lead !== undefined) {
    children.push(para([t(blk.lead)], 60, AlignmentType.LEFT, FIRST));
  } else if (blk.bullets) {
    blk.bullets.forEach(([lead, body], j) => children.push(new Paragraph({
      numbering: { reference: 'bullets', level: 0 }, alignment: AlignmentType.BOTH,
      spacing: { after: j === blk.bullets.length - 1 ? 140 : 50, line: LINE },
      children: lead ? [b(lead), t(body)] : [t(body)] })));
  } else {
    console.error(`Unknown block at index ${i}: ${JSON.stringify(blk)}`); process.exit(2);
  }
});
children.push(left(c.closing || 'Best regards,'), left(profile.name));

const doc = new Document({
  creator: profile.name, title: c.title || 'Cover Letter',
  numbering: { config: [{ reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•',
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 360, hanging: 220 } } } }] }] },
  styles: { default: { document: { run: { font: F, size: SZ } } } },
  sections: [{ properties: { page: { size: { width: 12240, height: 15840 },
    margin: { top: 864, right: 864, bottom: 864, left: 864 } } }, children }],
});
Packer.toBuffer(doc).then((buf) => {
  fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
  fs.writeFileSync(outFile, buf);
  console.log(`written ${outFile}`);
}).catch((e) => { console.error(`docx build failed: ${e.message}`); process.exit(1); });

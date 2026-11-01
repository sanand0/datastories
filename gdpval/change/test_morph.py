import csv, json, pathlib, unittest
HERE=pathlib.Path(__file__).resolve().parent
DATA=json.loads((HERE/'morph-data.json').read_text(encoding='utf-8'))
OBS=DATA['occupations']
class MorphTests(unittest.TestCase):
 def test_preserve_all_original_categories(self):
  with (HERE.parent/'compensation.csv').open(newline='',encoding='utf-8-sig') as f: old=list(csv.DictReader(f))
  self.assertEqual(len(OBS),len(old));self.assertEqual(len(OBS),44)
  self.assertEqual([(a['sector'],a['occupation']) for a in OBS],[(a['Sector'],a['Occupation']) for a in old])
  self.assertEqual(len({a['sector'] for a in OBS}),9)
 def test_wage_totals_and_values(self):
  self.assertAlmostEqual(sum(a['size2025'] for a in OBS),2991.68,places=2)
  self.assertAlmostEqual(sum(a['size2026'] for a in OBS),3088.49,places=2)
  self.assertTrue(all(a['size2025']>0 and a['size2026']>0 for a in OBS))
 def test_scenario_is_explicit_not_observed(self):
  self.assertAlmostEqual(sum(a['score2026'] for a in OBS)/44,84.9,places=1)
  self.assertIn('not measured per-occupation',DATA['metadata']['model2026'])
  self.assertIn('NOT a head-to-head',DATA['metadata']['scoreMethod'])
  self.assertTrue(all(0<=a['score2025']<=100 and 0<=a['score2026']<=100 for a in OBS))
 def test_task_evidence_and_published_sources(self):
  meta=DATA['metadata'];self.assertEqual(meta['numbers']['occupations'],44)
  self.assertEqual(meta['numbers']['sectors'],9)
  self.assertGreaterEqual(meta['numbers']['attributedTaskRows'],150)
  self.assertGreaterEqual(meta['numbers']['febCoveredOccupations'],30)
  for key,v in meta['sources'].items():
   self.assertTrue(v['url'].startswith('https://'),key)
   self.assertEqual(len(v['sha256']),64,key)
  for a in OBS:
   self.assertLessEqual(len(a['tasks']),5)
   self.assertEqual(len({t['taskId'] for t in a['tasks']}),len(a['tasks']))
   for t in a['tasks']:
    self.assertTrue(t['taskId'].isdigit())
    self.assertGreaterEqual(t['mayUsagePct'],0)
    self.assertTrue(t['task'])
 def test_original_view_retained_with_a_single_link(self):
  html=(HERE.parent/'index.html').read_text(encoding='utf-8')
  self.assertEqual(html.count('href="change/"'),1)
  self.assertIn("d3.csv('compensation.csv')",html)
  self.assertIn("d3.csv('win.csv')",html)
  self.assertIn("d3.csv('prompts.csv')",html)
 def test_single_treemap_not_side_by_side(self):
  html=(HERE/'index.html').read_text(encoding='utf-8')
  self.assertEqual(html.count('<svg id="treemap"'),1)
  self.assertIn('posBetween',html)
  self.assertIn('input type="range"',html)
  self.assertIn('2026 colours',html)
 def test_palette_and_margins(self):
  html=(HERE/'index.html').read_text(encoding='utf-8')
  self.assertIn('color(interp(d.score2025,d.score2026)(t2))',html)
  self.assertIn('d3.quantize(d3.interpolateRdYlGn,21)',html)
  self.assertIn('padding:clamp(14px,2vw,26px)',html)
  self.assertIn('.wrap{max-width:1660px;padding-inline:clamp(18px,4vw,66px)',html)
  self.assertIn('.wrap{padding-inline:17px}',html)
  self.assertIn('header{padding:clamp(40px,4vw,60px) 0 28px',html)
  self.assertIn('main{padding:28px 0 112px}',html)
  self.assertIn('d3.lab(fill).l<55',html)
  self.assertNotIn('d3.interpolateLab(',html)
if __name__=='__main__':unittest.main()

"""Global editing acceptance integrity only; synthetic bytes are not real CMS proof."""
import copy
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
import unittest
from tests.test_required_client_cms import delivery_fixture
from utils.client_handover import _shared_editor_evidence_complete, inspect_client_delivery
from utils.visual_asset_continuity import PROTOCOL

class SharedEditingTests(unittest.TestCase):
    def fixture(self):
        company=delivery_fixture(); company['research']['visual_inventory_protocol']=PROTOCOL
        company['research']['company_facts']['opening_hours']='Mon–Fri 10–17'
        root=Path(company['delivery']['preview_cms_parity']['evidence_root'])
        captures=[]
        for role in ('before','after','mobile_after','rollback'):
            file=root/('synthetic-'+role+'.png');file.write_bytes(b'\x89PNG\r\n\x1a\n'+role.encode())
            captures.append({'role':role,'path':file.name,'sha256':sha256(file.read_bytes()).hexdigest()})
        record={'artifact_sha256':'demo-hash','build_version':3,'independent_of_builder':True,
                'reviewer_id':'synthetic-separate-reviewer','checked_at':'2026-11-07','open_issues':[],
                'tasks':[{'field':key,'method':'customer_editor','requires_code_editing':False,
                    'before_value':'Old '+key,'after_value':'New '+key,'routes_reviewed':['index.html'],
                    'observation':'Synthetic task observation; not real CMS evidence','captures':copy.deepcopy(captures)}
                    for key in ('header','footer','phone','email','opening_hours')]}
        company['delivery']['shared_cms_edit_evidence']=record
        return company

    def test_current_synthetic_shared_edit_records_pass_integrity_only(self):
        c=self.fixture();self.assertTrue(_shared_editor_evidence_complete(c,c['delivery'],'demo-hash'))

    def test_theme_html_changes_do_not_count_as_customer_editor(self):
        c=self.fixture();c['delivery']['shared_cms_edit_evidence']['tasks'][0]['requires_code_editing']=True
        self.assertFalse(inspect_client_delivery(c)['ready_to_handover'])

    def test_each_shared_field_is_required_when_present(self):
        for field in ('header','footer','phone','email','opening_hours'):
            c=self.fixture();record=c['delivery']['shared_cms_edit_evidence']
            record['tasks']=[t for t in record['tasks'] if t['field']!=field]
            self.assertFalse(_shared_editor_evidence_complete(c,c['delivery'],'demo-hash'),field)

    def test_old_bundle_changed_bytes_and_identical_edits_fail(self):
        for change in ('old','hash','identical','route','mobile','rollback'):
            c=self.fixture();record=c['delivery']['shared_cms_edit_evidence'];task=record['tasks'][0]
            if change=='old':record['build_version']=2
            elif change=='hash':task['captures'][0]['sha256']='f'*64
            elif change=='identical':task['after_value']=task['before_value']
            elif change=='route':task['routes_reviewed']=[]
            elif change=='mobile':task['captures']=[x for x in task['captures'] if x['role']!='mobile_after']
            else:task['captures']=[x for x in task['captures'] if x['role']!='rollback']
            self.assertFalse(_shared_editor_evidence_complete(c,c['delivery'],'demo-hash'),change)

if __name__=='__main__':unittest.main()

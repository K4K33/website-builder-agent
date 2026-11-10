"""Kaurivo prospective client-email hygiene. No real emails are sent.

Use Node only to execute the browser-side pure composer under mocked company
data. Never rely on provider inbox-placement claims or network requests.
"""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
COMPOSER=ROOT/"assets"/"outreach-mail.js"
CRM=ROOT/"assets"/"crm.js"
HTML=ROOT/"admin"/"index.html"


class KaurivoEmailDeliverabilityTests(unittest.TestCase):
    def test_first_contact_assets_and_manual_gate(self):
        composer=COMPOSER.read_text(encoding="utf-8")
        crm=CRM.read_text(encoding="utf-8")
        html=HTML.read_text(encoding="utf-8")
        self.assertLess(html.index("outreach-mail.js"),html.index("crm.js"))
        self.assertIn("window.KaurivoOutreach.firstContact(company)",crm)
        self.assertIn("Kopioi kevyt ensiviesti",crm)
        self.assertIn("firstContactParts(candidate)",crm)
        self.assertIn("outreach-subject",html)
        self.assertIn("outreach-body",html)
        self.assertIn("outreach-copy-subject",html)
        self.assertIn("outreach-copy-body",html)
        self.assertIn("markkinointikielto",crm.lower())
        self.assertIn("ei liitteitä",crm.lower())
        self.assertIn('id="mail-deliverability"',html)
        self.assertIn("merkittiin roskapostiksi",html.lower())
        self.assertIn("spf, dkim ja dmarc pass",html.lower())
        self.assertNotIn("fetch(",composer)
        self.assertNotIn("send_email",composer.lower())
        self.assertNotIn("mailto:",composer.lower())

    @unittest.skipUnless(shutil.which("node"),"Node.js not installed")
    def test_real_composer_rejects_duplicate_unverified_and_linked_first_contacts(self):
        program=r"""
const assert=require('node:assert/strict');
require(process.argv[1]);
const draft=globalThis.KaurivoOutreach.firstContact;
const parts=globalThis.KaurivoOutreach.firstContactParts;
const good={
 company_name:'Esimerkki Palvelu Oy',
 contact_language:'fi',
 outreach_observation:'Mobiilin navigaatio on vaikea käyttää ja palvelun kuvaus on vanhentunut.',
 outreach_observation_sv:'Mobilmenyn är svår att använda och beskrivningen av tjänsterna behöver uppdateras.',
 outreach_observation_en:'The mobile navigation is difficult to use and the service descriptions need updating.',
 outreach_review:'human_approved',
 outreach_stage:'not_contacted',
 business_activity_assessment:'active_evidence',
 evidence_url:'https://example.test/evidence',
 language_evidence_url:'https://example.test/language',
 marketing_opt_out:false
};
for(const lang of ['fi','sv','en']){
 const x=draft({...good,contact_language:lang});
 assert.match(x,/^Aihe: /);
 const p=parts({...good,contact_language:lang});
 assert.ok(p.subject.length>10);
 assert.ok(p.body.startsWith(lang==='sv'?'Hej!':lang==='en'?'Hello,':'Hei,'));
 assert.equal(x,'Aihe: '+p.subject+'\n\n'+p.body);
 assert.ok(!p.body.includes('Aihe: '));
 assert.ok(x.length<1500);
 assert.ok(!/https?:\/\//.test(x));
 assert.ok(!/<img|\.zip|<html/i.test(x));
 assert.ok(x.includes(good.company_name));
}
for(const stage of ['sent_manually','responded','won','opted_out']){
 assert.throws(()=>draft({...good,outreach_stage:stage}));
}
assert.throws(()=>draft({...good,marketing_opt_out:true}));
assert.throws(()=>draft({...good,outreach_review:'not_reviewed'}));
assert.throws(()=>draft({...good,language_evidence_url:''}));
assert.throws(()=>draft({...good,contact_language:'undetermined'}));
assert.throws(()=>draft({...good,website:'https://foo.com',outreach_observation:'Katso lisää https://abc.com sekä tämä tarpeeksi pitkä havainto.'}));
assert.throws(()=>draft({...good,outreach_observation:'A'.repeat(280)}));
const sanitized=draft({...good,company_name:'Sivusto\nOy'});
assert.ok(sanitized.includes('Sivusto Oy'));
console.log('OK: 3 languages, no links, unsafe or duplicate contact blocked');
"""
        run=subprocess.run(["node","-e",program,str(COMPOSER)],capture_output=True,
                          text=True,timeout=15,check=False)
        self.assertEqual(run.returncode,0,run.stdout+"\n"+run.stderr)


if __name__=="__main__":
    unittest.main()

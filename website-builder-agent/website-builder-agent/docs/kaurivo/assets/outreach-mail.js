/* Kaurivo first-contact composition: plain-text, no links or attachments.
   A draft is NOT permission to contact a company and NOT proof of delivery.
   Legal and recipient verification remains a separate human approval gate. */
(function(root){
 "use strict";
 const compact=value=>String(value||"").replace(/[\r\n\u2028\u2029\t]+/g," ").replace(/\s+/g," ").trim();
 const SENT=new Set(["sent_manually","responded","won","opted_out"]);
 function firstContact(company){
  if(!company||typeof company!=="object")throw Error("Yritystiedot puuttuvat.");
  if(company.marketing_opt_out||company.outreach_review!=="human_approved"||
     SENT.has(company.outreach_stage))
   throw Error("Ensiyhteydenotto estetty: markkinointikielto, aiempi yhteydenotto tai puuttuva hyväksyntä.");
  const language=compact(company.contact_language);
  if(!["fi","sv","en"].includes(language)||!company.language_evidence_url||
     !company.evidence_url||company.business_activity_assessment!=="active_evidence")
   throw Error("Tarkista kieli, yrityksen aktiivisuus, lähteet ja laillisuus ennen luonnosta.");
  const observations={
   fi:company.outreach_observation,
   sv:company.outreach_observation_sv,
   en:company.outreach_observation_en
  };
  const observation=compact(observations[language]);
  const name=compact(company.company_name);
  if(!name||name.length>160||observation.length<20||observation.length>260)
   throw Error("Kirjoita 20–260 merkin yksilöllinen, todennettu havainto yrityksestä.");
  if(/(?:https?:\/\/|www\.|\b[A-Za-z0-9.-]+\.(?:com|fi|net|org)\/)/i.test(observation))
   throw Error("Ensimmäinen yhteydenotto ei sisällä linkkejä. Kirjaa havainto ilman URL-osoitetta.");
  // Deliberately no third-party preview, tracking URL, remote pixel, inline image or ZIP.
  // A reviewed demo may be shared separately after the recipient requests it.
  let subject,paragraphs;
  if(language==="sv"){
   subject="En fråga om "+name+"s webbplats";
   paragraphs=[
    "Hej!",
    "Jag heter Kaarlo och skriver från Kaurivo. Jag har tittat på "+name+"s närvaro på nätet och noterade följande: "+observation,
    "Vi hjälper företag med webbplatser som fungerar bra också på mobilen. Jag kan gärna visa ett kort, individuellt förslag. Skulle det vara intressant för er?",
    "Vänliga hälsningar\nKaarlo från Kaurivo",
    "Om ni inte vill ha fler sådana mejl kan ni svara \"ingen mer kontakt\"."
   ];
  }else if(language==="en"){
   subject="A question about "+name+"'s website";
   paragraphs=[
    "Hello,",
    "I'm Kaarlo from Kaurivo. I took a look at "+name+"'s online presence and noticed this: "+observation,
    "We design websites for companies, including mobile-friendly pages that are easy to update. I would be happy to share a short idea tailored to your business. Would that be of interest?",
    "Best regards\nKaarlo from Kaurivo",
    "If you prefer no further marketing contact, reply with \"no further contact\"."
   ];
  }else{
   subject="Kysymys "+name+" -yrityksen verkkosivuista";
   paragraphs=[
    "Hei,",
    "Olen Kaarlo Kaurivolta. Tutustuin "+name+" -yrityksen verkkonäkyvyyteen ja huomasin seuraavaa: "+observation,
    "Suunnittelemme yrityksille yksilöllisiä ja helposti päivitettäviä verkkosivuja. Voisin näyttää lyhyen idean, joka sopii yrityksenne nykyiseen ilmeeseen. Kiinnostaisiko nähdä se?",
    "Ystävällisin terveisin\nKaarlo Kaurivolta",
    "Jos ette halua uusia markkinointiyhteydenottoja, voitte vastata \"ei yhteydenottoja\"."
   ];
  }
  const body=paragraphs.join("\n\n");
  const result="Aihe: "+subject+"\n\n"+body;
  if(result.length>1500||/https?:\/\//i.test(result))
    throw Error("Luonnos ei täytä ensiviestin toimitettavuusrajaa.");
  return result;
 }
 root.KaurivoOutreach=Object.freeze({firstContact});
})(typeof window!=="undefined"?window:globalThis);

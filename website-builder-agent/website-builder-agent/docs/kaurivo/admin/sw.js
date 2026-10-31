/* Kaurivo admin-only push worker. Never cache CRM data or authentication tokens. */
self.addEventListener("install",()=>{self.skipWaiting();});
self.addEventListener("activate",event=>{event.waitUntil(self.clients.claim());});
self.addEventListener("push",event=>{
 if(!event.data)return;
 let data={};
 try{data=event.data.json()||{};}catch(_){return;}
 const origin=self.location.origin;
 const base=origin+"/website-builder-agent/kaurivo/admin/";
 let url=base;
 try{
  const proposed=new URL(data.url||base,origin);
  if(proposed.origin===origin&&proposed.pathname===new URL(base).pathname)url=proposed.href;
 }catch(_){}
 const title=String(data.title||"Kaurivo · yrityslista").slice(0,90);
 const body=String(data.body||"Uusi yrityslista on valmis.").slice(0,180);
 event.waitUntil(self.registration.showNotification(title,{
  body,tag:String(data.tag||"kaurivo-daily").slice(0,80),
  icon:"../assets/kaurivo-mark.webp",
  badge:"../assets/kaurivo-mark.webp",
  data:{url},renotify:false
 }));
});
self.addEventListener("notificationclick",event=>{
 event.notification.close();
 const url=event.notification.data?.url||self.location.origin+
  "/website-builder-agent/kaurivo/admin/";
 event.waitUntil((async()=>{
  const list=await self.clients.matchAll({type:"window",includeUncontrolled:true});
  for(const client of list){
   if(client.url.startsWith(self.location.origin+"/website-builder-agent/kaurivo/admin/")){
    if("navigate" in client)await client.navigate(url);
    return client.focus();
   }
  }
  return self.clients.openWindow(url);
 })());
});
